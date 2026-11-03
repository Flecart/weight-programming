"""Evaluate base (full precision and as-shown rounded) and edited actors on l/h2_car_ramp.
Actions sampled from the policy (each entry independently from softmax of its logits); also one argmax episode.
Usage: python evaluate.py N_EPISODES [BATCH]"""
import sys, json, time, math
import numpy as np, jax, jax.numpy as jnp
import kcommon as K

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1024
B = int(sys.argv[2]) if len(sys.argv) > 2 else 256
env, env_params, sp, s0 = K.make_env()
roll = K.make_rollout(env, env_params, s0)
roll_greedy = K.make_rollout(env, env_params, s0, greedy=True)

nets = {
    "base_full_precision": K.load_actor(f"{K.REPO}/networks/ppo_final_seed0.npz"),
    "base_as_shown_rounded": K.load_rounded_from_prompt(f"{K.REPO}/runs/oneshot_repair/reply/prompt.txt"),
    "edited": K.load_actor(f"{K.REPO}/networks/edited_actor.npz"),
}
results = {}
for i, (name, actor) in enumerate(nets.items()):
    p = K.to_jax(actor)
    outs, lens, rets = [], [], []
    t = time.time()
    for b in range(0, N, B):
        keys = jax.random.split(jax.random.PRNGKey(1000 * (i + 1) + b), B)
        o, l, r = roll(p, keys)
        outs.append(np.asarray(o)); lens.append(np.asarray(l)); rets.append(np.asarray(r))
    o = np.concatenate(outs)[:N]; l = np.concatenate(lens)[:N]; r = np.concatenate(rets)[:N]
    go, gl, gr = roll_greedy(p, jax.random.split(jax.random.PRNGKey(7), 1))
    counts = {K.OUTCOME_NAMES[c]: int((o == c).sum()) for c in K.OUTCOME_NAMES}
    res = {
        "episodes": N,
        "counts": counts,
        "success": counts["success"] / N, "fail": counts["red"] / N,
        "timeout": counts["timeout"] / N, "invalid": counts["invalid"] / N,
        "mean_return": float(r.mean()), "mean_length": float(l.mean()),
        "argmax_outcome": K.OUTCOME_NAMES[int(go[0])], "argmax_length": int(gl[0]),
        "seconds": round(time.time() - t, 1),
    }
    results[name] = res
    print(name, json.dumps(res), flush=True)
json.dump(results, open("raw_eval.json", "w"), indent=1)
