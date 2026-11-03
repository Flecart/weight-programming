"""Evaluate the released MinAtar hand-written networks (exp5_write_from_scratch) on official MinAtar 1.0.15.

Protocol (from the repo README / prompts): official minatar.Environment with sticky_action_prob=0.1, actions sampled
from softmax(logits), episodes cut at 10,000 steps, mean score over N episodes. Also evaluates a uniform-random and a
no-op policy, and records animation frames.

The network weights are loaded with np.load(allow_pickle=False); no code from the repo is executed.

Usage:
  python -I eval_minatar.py --repo <exp5 dir> --out <out dir> [--episodes 1000] [--workers 20]
  python -I eval_minatar.py --repo <exp5 dir> --out <out dir> --games <game> --net <other.npz> [--no-frames]
    (--net scores a different .npz for a single game with the same protocol and seeds; no reference comparison)
"""
import argparse
import json
import math
import os
import time
from multiprocessing import Pool

import numpy as np
from minatar import Environment

GAMES = ["breakout", "seaquest", "asterix"]
MAX_STEPS = 10_000
STICKY = 0.1

# 6-channel remapping, exactly as written in runs/<game>/reply/prompt.txt ("How the 6 channels are built"):
# out channel index -> list of native MinAtar channel names; a cell is 1 if any source channel is 1.
# 0 player, 1 danger, 2 reward, 3 projectile, 4 trail, 5 gauge
CHANNEL_MAP = {
    "breakout": [["paddle"], [], ["brick"], ["ball"], ["trail"], []],
    "seaquest": [["sub_front", "sub_back"],
                 ["enemy_fish", "enemy_sub", "enemy_bullet"],
                 ["enemy_fish", "enemy_sub", "diver"],
                 ["friendly_bullet"],
                 ["trail", "sub_back"],
                 ["oxygen_guage", "diver_guage"]],
    "asterix": [["player"], ["enemy"], ["gold"], [], ["trail"], []],
}


def make_obs_fn(env, game):
    names = env.env.channels  # native name -> index
    idx = [[names[n] for n in srcs] for srcs in CHANNEL_MAP[game]]

    def obs(state):
        out = np.zeros((10, 10, 6), dtype=np.float64)
        for c, srcs in enumerate(idx):
            if srcs:
                out[:, :, c] = state[:, :, srcs].any(axis=2)
        # input index (row*10 + col)*6 + channel == C-order flatten of (row, col, channel)
        return out.reshape(600)
    return obs


def load_net(path):
    d = np.load(path, allow_pickle=False)
    k = lambda n: d[n].astype(np.float64)
    return (k("actor/dense1/kernel"), k("actor/dense1/bias"), k("actor/dense2/kernel"), k("actor/dense2/bias"),
            k("actor/logits/kernel"), k("actor/logits/bias"))


def logits_fn(net, x):
    W1, b1, W2, b2, W3, b3 = net
    h1 = np.tanh(x @ W1 + b1)
    h2 = np.tanh(h1 @ W2 + b2)
    return h2 @ W3 + b3


def sample_softmax(z, rng):
    z = z - z.max()
    p = np.exp(z)
    p /= p.sum()
    return int(rng.choice(6, p=p))


def run_episode(game, policy, seed, net=None, record=False, max_steps=MAX_STEPS):
    env = Environment(game, sticky_action_prob=STICKY)
    env.seed(seed)
    env.reset()
    rng = np.random.RandomState(seed + 7_919_000)  # policy RNG, independent from env RNG
    obs_fn = make_obs_fn(env, game)
    inv = {v: k for k, v in env.env.channels.items()}
    total, steps, frames = 0.0, 0, []
    terminal = False

    def snap():
        s = env.state()
        return {inv[c]: [[int(r), int(cc)] for r, cc in zip(*np.nonzero(s[:, :, c]))] for c in range(s.shape[2])}

    while not terminal and steps < max_steps:
        if record:
            chans = snap()
        if policy == "net":
            a = sample_softmax(logits_fn(net, obs_fn(env.state())), rng)
        elif policy == "random":
            a = int(rng.randint(6))
        else:
            a = 0
        r, terminal = env.act(a)
        total += r
        steps += 1
        if record:
            # 'action' is the policy's chosen action; 'executed' is what the env ran after sticky repeat
            frames.append({"channels": chans, "action": a, "executed": int(env.last_action), "reward": float(r)})
    if record:
        return total, steps, terminal, frames, [inv[c] for c in range(len(inv))]
    return total, steps, terminal


_NET = {}


def _worker(args):
    game, policy, seed, net_path = args
    net = None
    if policy == "net":
        if net_path not in _NET:
            _NET[net_path] = load_net(net_path)
        net = _NET[net_path]
    return run_episode(game, policy, seed, net)


def stats(results):
    s = np.array([r[0] for r in results])
    L = np.array([r[1] for r in results])
    n = len(s)
    return {"mean": float(s.mean()), "se": float(s.std(ddof=1) / math.sqrt(n)) if n > 1 else None,
            "episodes": n, "max": float(s.max()), "min": float(s.min()), "mean_len": float(L.mean()),
            "truncated_at_10000": int(sum(1 for r in results if not r[2]))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--episodes", type=int, default=1000)
    ap.add_argument("--baseline-episodes", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 2))
    ap.add_argument("--games", default=",".join(GAMES))
    ap.add_argument("--net", default=None, help="score this .npz instead of networks/<game>/hand.npz (one game)")
    ap.add_argument("--no-frames", action="store_true", help="skip writing episodes.json")
    args = ap.parse_args()
    games = args.games.split(",")
    if args.net and len(games) != 1:
        ap.error("--net needs exactly one game in --games")
    ref_all = json.load(open(os.path.join(args.repo, "eval", "minatar_eval.json")))

    val_path = os.path.join(args.out, "validation.json")
    validation = json.load(open(val_path)) if os.path.exists(val_path) else {}
    with Pool(args.workers) as pool:
        for gi, game in enumerate(games):
            net_path = args.net or os.path.join(args.repo, "networks", game, "hand.npz")
            gi = GAMES.index(game)  # seeds depend on the game only, not on the --games order
            entry = {"network": os.path.abspath(args.net) if args.net else f"networks/{game}/hand.npz (ref key {game}.hand)",
                     "protocol": {"minatar": "1.0.15", "sticky_action_prob": STICKY, "max_steps": MAX_STEPS,
                                  "action_selection": "sample softmax(logits)"}}
            base = 1_000_000 * (gi + 1)
            for policy, n in [("net", args.episodes), ("random", args.baseline_episodes),
                              ("noop", args.baseline_episodes)]:
                t = time.time()
                jobs = [(game, policy, base + 100_000 * ["net", "random", "noop"].index(policy) + i, net_path)
                        for i in range(n)]
                res = pool.map(_worker, jobs, chunksize=1)
                st = stats(res)
                st["wall_s"] = round(time.time() - t, 1)
                entry["ours" if policy == "net" else policy] = st
                print(game, policy, st, flush=True)
            if args.net:
                validation[game] = entry
                json.dump(validation, open(val_path, "w"), indent=1)
                continue
            ref = ref_all[game]["hand"]
            entry["reference"] = {"mean": ref["mean"], "se": ref["se"], "episodes": ref["episodes"],
                                  "mean_len": ref["mean_length"], "max": ref["max"]}
            o = entry["ours"]
            z = (o["mean"] - ref["mean"]) / math.sqrt(o["se"] ** 2 + ref["se"] ** 2)
            entry["z_diff"] = round(z, 3)
            entry["verdict"] = "validated" if abs(z) <= 2.0 else "not validated"
            validation[game] = entry
            json.dump(validation, open(val_path, "w"), indent=1)

    if args.no_frames:
        return
    # Animation frames: 1 network episode + 1 random episode per game, 300 steps max.
    ep = {"note": "Per step: native MinAtar 1.0.15 channels as [row, col] lists (row 0 = top), the state BEFORE the "
                  "action; 'action' = policy choice, 'executed' = action after sticky repeat (p=0.1); 'reward' = "
                  "reward of that step. Capped at 300 steps.",
          "games": {}}
    for gi, game in enumerate(games):
        net = load_net(args.net or os.path.join(args.repo, "networks", game, "hand.npz"))
        g = {}
        for policy in ["net", "random"]:
            seed = 42 + gi
            total, steps, term, frames, names = run_episode(game, policy, seed, net, record=True, max_steps=300)
            g["channel_names"] = names
            g["network" if policy == "net" else "random"] = {
                "seed": seed, "score": total, "steps": steps, "terminated": bool(term), "frames": frames}
        ep["games"][game] = g
    with open(os.path.join(args.out, "episodes.json"), "w") as f:
        json.dump(ep, f, separators=(",", ":"))


if __name__ == "__main__":
    main()
