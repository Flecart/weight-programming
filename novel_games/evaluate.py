"""Evaluate trained seeds, scripted and random baselines; export the best seed per game.

Usage: python evaluate.py --runs runs --out .   (reads runs/<game>/seed*.npz and train_info.json)
Writes networks/<game>.npz, networks/<game>_actor.txt, meta/<game>.json, episodes.json, baselines.json.
"""
import argparse
import glob
import json
import os
import re

import jax
import jax.numpy as jnp
import numpy as np

from envs import GAMES, DIRS, GOAL, MAX_STEPS, manhattan
from ppo import actor_logits, CONFIG

N_EPISODES = 1280


# ------------------------------------------------------------------ scripted baselines (act on the true state)
def corner_push_table():
    """Exact optimal policy for one coin: value iteration over (agent cell, coin cell), 64x64 states."""
    cells = [(r, c) for r in range(1, 9) for c in range(1, 9)]
    idx = {p: i for i, p in enumerate(cells)}
    INF = 10 ** 6
    D = np.full((64, 64), INF)
    nxt = np.zeros((64, 64, 5, 2), int)
    scores = np.zeros((64, 64, 5), bool)
    ins = lambda p: 1 <= p[0] <= 8 and 1 <= p[1] <= 8
    for ai, a in enumerate(cells):
        for ci, c in enumerate(cells):
            for act in range(5):
                d = tuple(np.array(DIRS[act]))
                na = (a[0] + d[0], a[1] + d[1])
                na2, nc2 = a, c
                if act != 0 and na == c:
                    nc = (c[0] + d[0], c[1] + d[1])
                    if ins(nc):
                        na2, nc2 = na, nc
                elif ins(na):
                    na2 = na
                nxt[ai, ci, act] = (idx[na2], idx[nc2])
                scores[ai, ci, act] = nc2 == (1, 1)
    for _ in range(200):
        nd = np.where(scores, 1, 1 + D[nxt[..., 0], nxt[..., 1]]).min(-1)
        nd = np.minimum(nd, INF)
        if np.array_equal(nd, D):
            break
        D = nd
    q = np.where(scores, 1, 1 + D[nxt[..., 0], nxt[..., 1]]).astype(float)
    q[..., 0] += 0.5  # never prefer no-op on ties
    best = q.argmin(-1)
    return jnp.array(best), D


def scripted_policy(game):
    if game == "corner_push":
        table, _ = corner_push_table()

        def pi(key, obs, st):
            a = (st["agent"][0] - 1) * 8 + st["agent"][1] - 1
            c = (st["coin"][0] - 1) * 8 + st["coin"][1] - 1
            return table[a, c]
        return pi
    if game == "mirror_twin":
        def pi(key, obs, st):
            dr = st["target"][0] - st["twin"][0]
            dc = st["target"][1] - st["twin"][1]
            return jnp.where(dr < 0, 1, jnp.where(dr > 0, 2, jnp.where(dc > 0, 3, jnp.where(dc < 0, 4, 0))))
        return pi
    if game.startswith("charge_pad"):
        def pi(key, obs, st):
            na = st["agent"][None] + DIRS
            na = jnp.where(((na >= 1) & (na <= 8)).all(1, keepdims=True), na, st["agent"][None])
            danger = jnp.min(manhattan(na[:, None], st["haz"][None]), axis=1)  # [5]
            cost = manhattan(na, st["pad"][None]) + 100.0 * jnp.maximum(0, 2 - danger)
            return jnp.argmin(cost)
        return pi
    raise ValueError(game)


def net_policy(params, mode):
    def pi(key, obs, st):
        logits = actor_logits(params, obs)
        if mode == "greedy":
            return jnp.argmax(logits)
        return jax.random.categorical(key, logits)
    return pi


def random_policy(key, obs, st):
    return jax.random.randint(key, (), 0, 5)


def rollout(env, pi, key, n=N_EPISODES, record=False):
    """Run n episodes (one per env, no reset) for up to MAX_STEPS steps."""
    k0, k1 = jax.random.split(key)
    st = jax.vmap(env.reset)(jax.random.split(k0, n))

    def step(carry, k):
        st, alive = carry
        ka, ks = jax.random.split(k)
        obs = jax.vmap(env.obs)(st)
        act = jax.vmap(pi)(jax.random.split(ka, n), obs, st)
        st2, r, done = jax.vmap(env.step)(jax.random.split(ks, n), st, act)
        out = dict(r=r * alive, alive=alive, act=act,
                   chan=(obs.reshape(n, 100, 5).max(1) > 0) & alive[:, None])
        if record:
            out["obs"] = obs
        return (st2, alive & ~done), out

    _, tr = jax.lax.scan(step, (st, jnp.ones(n, bool)), jax.random.split(k1, MAX_STEPS))
    return tr


def summarize(tr, mode):
    tr = jax.device_get(tr)
    ret = tr["r"].sum(0)
    length = tr["alive"].sum(0)
    alive = tr["alive"]
    acts = np.array([((tr["act"] == a) & alive).sum() for a in range(5)]) / alive.sum()
    chan = tr["chan"].sum((0, 1)) / alive.sum()
    return dict(mode=mode, episodes=int(ret.shape[0]), mean_return=float(ret.mean()),
                se_return=float(ret.std(ddof=1) / np.sqrt(len(ret))), mean_length=float(length.mean()),
                reward_per_step=float(ret.sum() / length.sum()),
                channel_usage=[round(float(x), 4) for x in chan], action_usage=[round(float(x), 4) for x in acts])


def load_params(path):
    d = np.load(path)
    p = {}
    for k in d.files:
        net, layer, w = k.split("/")
        p.setdefault(net, {}).setdefault(layer, {})[w] = jnp.array(d[k])
    return p


def write_actor_txt(path, params):
    a = params["actor"]
    f = lambda v: " ".join(f"{x:.3f}" for x in np.asarray(v).reshape(-1))
    lines = ["Policy network weights. Forward pass: h1 = tanh(x @ W1 + b1); h2 = tanh(h1 @ W2 + b2); "
             "logits = h2 @ W3 + b3. Values rounded to 3 decimals.", "",
             "W1 (layer 1 weights), shape 500 x 32: one line per row (row i = input i), 32 values per line"]
    lines += [f(r) for r in np.asarray(a["dense1"]["kernel"])]
    lines += ["", "b1 (layer 1 biases), shape 32:", f(a["dense1"]["bias"]), "",
              "W2 (layer 2 weights), shape 32 x 32: one line per row"]
    lines += [f(r) for r in np.asarray(a["dense2"]["kernel"])]
    lines += ["", "b2 (layer 2 biases), shape 32:", f(a["dense2"]["bias"]), "",
              "W3 (output layer weights), shape 32 x 5: one line per row"]
    lines += [f(r) for r in np.asarray(a["logits"]["kernel"])]
    lines += ["", "b3 (output layer biases), shape 5:", f(a["logits"]["bias"])]
    open(path, "w").write("\n".join(lines).replace("-0.000", "0.000") + "\n")


def episodes_for(env, params, key, n=2):
    tr = jax.device_get(rollout(env, net_policy(params, "sample"), key, n=n, record=True))
    eps = []
    for e in range(n):
        frames = []
        for t in range(MAX_STEPS):
            if not tr["alive"][t, e]:
                break
            o = tr["obs"][t, e].reshape(10, 10, 5)
            cells = lambda ch, interior=False: [[int(r), int(c)] for r, c in zip(*np.nonzero(o[:, :, ch]))
                                                if not interior or (1 <= r <= 8 and 1 <= c <= 8)]
            frames.append(dict(agent=cells(0), movers=cells(1), targets=cells(2),
                               obstacles_interior=cells(3, True), prev=cells(4),
                               action=int(tr["act"][t, e]), reward=float(tr["r"][t, e])))
        eps.append(dict(episode=e, length=len(frames), total_reward=float(sum(f["reward"] for f in frames)),
                        frames=frames))
    return eps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default=".")
    ap.add_argument("--games", nargs="+", default=list(GAMES))
    args = ap.parse_args()
    os.makedirs(os.path.join(args.out, "networks"), exist_ok=True)
    os.makedirs(os.path.join(args.out, "meta"), exist_ok=True)
    ep_path = os.path.join(args.out, "episodes.json")
    all_eps = json.load(open(ep_path)) if os.path.exists(ep_path) else {}
    bl_path = os.path.join(args.out, "baselines.json")
    baselines = json.load(open(bl_path)) if os.path.exists(bl_path) else {}
    key = jax.random.PRNGKey(12345)
    for game in args.games:
        env = GAMES[game]
        run_dir = os.path.join(args.runs, game)
        info = json.load(open(os.path.join(run_dir, "train_info.json")))
        log = [json.loads(l) for l in open(os.path.join(run_dir, "train_log.jsonl"))]
        seeds = {}
        for path in sorted(glob.glob(os.path.join(run_dir, "seed*.npz"))):
            s = int(re.findall(r"seed(\d+)", path)[0])
            params = load_params(path)
            seeds[s] = dict(params=params, sample=summarize(
                rollout(env, net_policy(params, "sample"), jax.random.fold_in(key, s)), "sample"))
            print(game, "seed", s, "sample", round(seeds[s]["sample"]["mean_return"], 3), flush=True)
        best = max(seeds, key=lambda s: seeds[s]["sample"]["mean_return"])
        params = seeds[best]["params"]
        perf = dict(sample=seeds[best]["sample"],
                    greedy=summarize(rollout(env, net_policy(params, "greedy"), jax.random.fold_in(key, 100)),
                                     "greedy"),
                    random=summarize(rollout(env, random_policy, jax.random.fold_in(key, 200)), "random"),
                    scripted=summarize(rollout(env, scripted_policy(game), jax.random.fold_in(key, 300)),
                                       "scripted"))
        baselines[game] = dict(random=perf["random"], scripted=perf["scripted"])
        for m in perf:
            print(game, m, round(perf[m]["mean_return"], 3), perf[m]["action_usage"], flush=True)
        # export
        flat = {f"{n}/{l}/{w}": np.asarray(params[n][l][w], np.float32)
                for n in params for l in params[n] for w in params[n][l]}
        np.savez(os.path.join(args.out, "networks", f"{game}.npz"), **flat)
        write_actor_txt(os.path.join(args.out, "networks", f"{game}_actor.txt"), params)
        shapes = {f"{l}/{w}": list(np.shape(params["actor"][l][w])) for l in params["actor"]
                  for w in params["actor"][l]}
        meta = dict(id=game, game=game, seed=best, actor_dims=[500, 32, 32, 5], critic_dims=[500, 32, 32, 1],
                    actor_shapes=dict(sorted(shapes.items())),
                    actor_parameters=int(sum(np.size(v) for l in params["actor"].values() for v in l.values())),
                    critic_parameters=int(sum(np.size(v) for l in params["critic"].values() for v in l.values())),
                    training_config=info["training_config"], env_steps=info["env_steps"],
                    final_performance=perf,
                    final_train_return=log[-1]["mean_ep_return"][info["seeds"].index(best)],
                    seed_returns={str(s): dict(sample_mean_return=seeds[s]["sample"]["mean_return"],
                                               sample_se_return=seeds[s]["sample"]["se_return"],
                                               final_train_return=log[-1]["mean_ep_return"][info["seeds"].index(s)])
                                  for s in sorted(seeds)},
                    selection="best seed by mean sampled-action return over 1,280 episodes")
        json.dump(meta, open(os.path.join(args.out, "meta", f"{game}.json"), "w"), indent=1)
        all_eps[game] = dict(seed=best, note="frames are the state BEFORE the action; reward is that step's reward",
                             episodes=episodes_for(env, params, jax.random.fold_in(key, 400)))
    json.dump(all_eps, open(ep_path, "w"))
    json.dump(baselines, open(bl_path, "w"), indent=1)


if __name__ == "__main__":
    main()
