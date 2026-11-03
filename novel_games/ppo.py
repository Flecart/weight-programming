"""PPO (purejaxrl-style) with the exact settings of the paper's exp1 networks.

Actor 500-32-32-5 tanh, separate critic 500-32-32-1 tanh, orthogonal init (hidden sqrt(2), actor out 0.01,
critic out 1.0), biases 0. Several seeds are trained in parallel with vmap.

Usage: python ppo.py <game> --steps 100000000 --seeds 0 1 2 --out runs/<game>
"""
import argparse
import json
import os
import time

import jax
import jax.numpy as jnp
import numpy as np
import optax

from envs import GAMES, auto_step

CONFIG = dict(LR=5e-4, ANNEAL_LR=True, NUM_ENVS=64, NUM_STEPS=128, UPDATE_EPOCHS=4, NUM_MINIBATCHES=8,
              GAMMA=0.99, GAE_LAMBDA=0.95, CLIP_EPS=0.2, ENT_COEF=0.01, VF_COEF=0.5, MAX_GRAD_NORM=0.5,
              HIDDEN=32, ACTIVATION="tanh",
              INIT="orthogonal: hidden gain sqrt(2), actor output 0.01, critic output 1.0; biases 0",
              MAX_STEPS_IN_EPISODE=200)


def dense_init(key, n_in, n_out, scale):
    return dict(kernel=jax.nn.initializers.orthogonal(scale)(key, (n_in, n_out), jnp.float32),
                bias=jnp.zeros((n_out,), jnp.float32))


def init_params(key, obs_dim=500, n_act=5, hidden=32):
    k = jax.random.split(key, 6)
    s2 = float(np.sqrt(2))
    return dict(
        actor=dict(dense1=dense_init(k[0], obs_dim, hidden, s2), dense2=dense_init(k[1], hidden, hidden, s2),
                   logits=dense_init(k[2], hidden, n_act, 0.01)),
        critic=dict(dense1=dense_init(k[3], obs_dim, hidden, s2), dense2=dense_init(k[4], hidden, hidden, s2),
                    value=dense_init(k[5], hidden, 1, 1.0)))


def mlp(p, x, out):
    h = jnp.tanh(x @ p["dense1"]["kernel"] + p["dense1"]["bias"])
    h = jnp.tanh(h @ p["dense2"]["kernel"] + p["dense2"]["bias"])
    return h @ p[out]["kernel"] + p[out]["bias"]


def actor_logits(params, x):
    return mlp(params["actor"], x, "logits")


def critic_value(params, x):
    return mlp(params["critic"], x, "value")[..., 0]


def make_train(env, total_steps, chunk_updates):
    c = CONFIG
    num_updates = total_steps // (c["NUM_ENVS"] * c["NUM_STEPS"])
    num_chunks = int(np.ceil(num_updates / chunk_updates))
    num_updates = num_chunks * chunk_updates
    mb_size = c["NUM_ENVS"] * c["NUM_STEPS"] // c["NUM_MINIBATCHES"]

    def lr_sched(count):
        frac = 1.0 - (count // (c["NUM_MINIBATCHES"] * c["UPDATE_EPOCHS"])) / num_updates
        return c["LR"] * frac

    tx = optax.chain(optax.clip_by_global_norm(c["MAX_GRAD_NORM"]),
                     optax.adam(learning_rate=lr_sched if c["ANNEAL_LR"] else c["LR"], eps=1e-5))

    v_reset = jax.vmap(env.reset)
    v_obs = jax.vmap(env.obs)
    v_step = jax.vmap(lambda k, s, a: auto_step(env, k, s, a))

    def init(key):
        k1, k2, k3 = jax.random.split(key, 3)
        params = init_params(k1)
        opt_state = tx.init(params)
        est = v_reset(jax.random.split(k2, c["NUM_ENVS"]))
        obs = v_obs(est)
        ep_ret = jnp.zeros(c["NUM_ENVS"])
        return (params, opt_state, est, obs, ep_ret, k3)

    def loss_fn(params, obs, act, logp_old, adv, targets, v_old):
        logits = actor_logits(params, obs)
        logp_all = jax.nn.log_softmax(logits)
        logp = jnp.take_along_axis(logp_all, act[:, None], axis=1)[:, 0]
        ent = -(jnp.exp(logp_all) * logp_all).sum(-1).mean()
        v = critic_value(params, obs)
        v_clip = v_old + jnp.clip(v - v_old, -c["CLIP_EPS"], c["CLIP_EPS"])
        vloss = 0.5 * jnp.maximum((v - targets) ** 2, (v_clip - targets) ** 2).mean()
        ratio = jnp.exp(logp - logp_old)
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        pl = -jnp.minimum(ratio * adv, jnp.clip(ratio, 1 - c["CLIP_EPS"], 1 + c["CLIP_EPS"]) * adv).mean()
        total = pl + c["VF_COEF"] * vloss - c["ENT_COEF"] * ent
        return total, (pl, vloss, ent)

    def update(runner, _):
        params, opt_state, est, obs, ep_ret, key = runner

        def env_step(carry, _):
            est, obs, ep_ret, key = carry
            key, ka, ke = jax.random.split(key, 3)
            logits = actor_logits(params, obs)
            act = jax.random.categorical(ka, logits)
            logp = jnp.take_along_axis(jax.nn.log_softmax(logits), act[:, None], axis=1)[:, 0]
            val = critic_value(params, obs)
            est2, obs2, r, done = v_step(jax.random.split(ke, c["NUM_ENVS"]), est, act)
            ep_ret = ep_ret + r
            fin_ret = jnp.where(done, ep_ret, 0.0)
            ep_ret = jnp.where(done, 0.0, ep_ret)
            tr = (obs, act, logp, val, r, done, fin_ret)
            return (est2, obs2, ep_ret, key), tr

        (est, obs, ep_ret, key), traj = jax.lax.scan(env_step, (est, obs, ep_ret, key), None, c["NUM_STEPS"])
        t_obs, t_act, t_logp, t_val, t_r, t_done, t_fin = traj
        last_val = critic_value(params, obs)

        def gae_step(carry, x):
            gae, next_val = carry
            done, val, r = x
            delta = r + c["GAMMA"] * next_val * (1 - done) - val
            gae = delta + c["GAMMA"] * c["GAE_LAMBDA"] * (1 - done) * gae
            return (gae, val), gae

        _, adv = jax.lax.scan(gae_step, (jnp.zeros_like(last_val), last_val),
                              (t_done.astype(jnp.float32), t_val, t_r), reverse=True)
        targets = adv + t_val

        batch = (t_obs, t_act, t_logp, adv, targets, t_val)
        batch = jax.tree.map(lambda x: x.reshape((-1,) + x.shape[2:]), batch)

        def epoch(carry, _):
            params, opt_state, key = carry
            key, kp = jax.random.split(key)
            perm = jax.random.permutation(kp, mb_size * c["NUM_MINIBATCHES"])
            mbs = jax.tree.map(lambda x: x[perm].reshape((c["NUM_MINIBATCHES"], mb_size) + x.shape[1:]), batch)

            def mb_step(carry, mb):
                params, opt_state = carry
                (l, aux), g = jax.value_and_grad(loss_fn, has_aux=True)(params, *mb)
                upd, opt_state = tx.update(g, opt_state, params)
                return (optax.apply_updates(params, upd), opt_state), (l,) + aux

            (params, opt_state), losses = jax.lax.scan(mb_step, (params, opt_state), mbs)
            return (params, opt_state, key), losses

        (params, opt_state, key), losses = jax.lax.scan(epoch, (params, opt_state, key), None,
                                                        c["UPDATE_EPOCHS"])
        n_done = t_done.sum()
        metrics = dict(ret_sum=t_fin.sum(), n_done=n_done, rew_sum=t_r.sum(),
                       loss=losses[0].mean(), ent=losses[3].mean())
        return (params, opt_state, est, obs, ep_ret, key), metrics

    def run_chunk(runner):
        return jax.lax.scan(update, runner, None, chunk_updates)

    return init, run_chunk, num_updates, num_chunks


def save_params(path, params):
    flat = {}
    for net in params:
        for layer in params[net]:
            for w in params[net][layer]:
                flat[f"{net}/{layer}/{w}"] = np.asarray(params[net][layer][w], np.float32)
    np.savez(path, **flat)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game")
    ap.add_argument("--steps", type=int, default=100_000_000)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--chunk", type=int, default=500, help="updates per jitted chunk (one log line each)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    env = GAMES[args.game]
    out = args.out or f"runs/{args.game}"
    os.makedirs(out, exist_ok=True)
    init, run_chunk, num_updates, num_chunks = make_train(env, args.steps, args.chunk)
    steps_per_update = CONFIG["NUM_ENVS"] * CONFIG["NUM_STEPS"]
    keys = jnp.stack([jax.random.PRNGKey(s) for s in args.seeds])
    runner = jax.jit(jax.vmap(init))(keys)
    run = jax.jit(jax.vmap(run_chunk))
    log = open(os.path.join(out, "train_log.jsonl"), "a")
    t0 = time.time()
    for ch in range(num_chunks):
        runner, m = run(runner)
        m = jax.device_get(m)
        ret = m["ret_sum"].sum(1) / np.maximum(m["n_done"].sum(1), 1)
        rps = m["rew_sum"].sum(1) / (chunk_steps := args.chunk * steps_per_update)
        steps = (ch + 1) * chunk_steps
        rec = dict(chunk=ch, env_steps=int(steps), time=round(time.time() - t0, 1),
                   mean_ep_return=[float(x) for x in ret], reward_per_step=[float(x) for x in rps],
                   entropy=[float(x) for x in m["ent"].mean(1)])
        log.write(json.dumps(rec) + "\n"); log.flush()
        print(f"{args.game} {steps/1e6:8.1f}M {rec['time']:7.0f}s ret " +
              " ".join(f"{x:7.2f}" for x in ret) + " ent " + " ".join(f"{x:.2f}" for x in rec["entropy"]),
              flush=True)
        params = runner[0]
        for i, s in enumerate(args.seeds):
            save_params(os.path.join(out, f"seed{s}.npz"), jax.tree.map(lambda x: x[i], params))
    json.dump(dict(game=args.game, seeds=args.seeds, env_steps=int(num_updates * steps_per_update),
                   num_updates=int(num_updates), training_config=dict(CONFIG, TOTAL_TIMESTEPS=args.steps)),
              open(os.path.join(out, "train_info.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
