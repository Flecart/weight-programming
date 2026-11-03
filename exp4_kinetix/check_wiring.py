"""Sanity checks: observation layout vs prompt.txt, weight sources, and edit-count reproduction."""
import json, numpy as np, jax, jax.numpy as jnp
import kcommon as K

env, env_params, sp, s0 = K.make_env()
obs = np.asarray(env.get_obs(s0))
print("obs len", obs.shape)
poly_slots = [0, 4, 5, 6, 7, 8, 9, 10, 11]
for i, sid in enumerate(poly_slots):
    f = obs[26 * i:26 * i + 26]
    print(f"poly {sid}: pos {f[0]:.3f},{f[1]:.3f} invm {f[4]:.3f} role {f[8:12]} sincos {f[12]:.3f},{f[13]:.3f} verts {np.round(f[17:25],3)} tri {f[25]}")
for i, sid in enumerate([12, 13, 14, 15]):
    f = obs[234 + 18 * i:234 + 18 * i + 18]
    print(f"circle {sid}: pos {f[0]:.3f},{f[1]:.3f} role {f[8:12]} radius {f[16]:.3f} flag {f[17]}")
for j in range(2):
    f = obs[306 + 54 * j:306 + 54 * j + 54]
    print(f"joint {j}: active {f[0]} posb {f[2:4]} posa {f[4:6]} speed {f[8]} power {f[9]} on {f[10]} binding {f[12:16]} b1h {np.argmax(f[22:38])} a1h {np.argmax(f[38:54])}")
print("gravity entry", obs[678])

base = K.load_actor(f"{K.REPO}/networks/ppo_final_seed0.npz")
rounded = K.load_rounded_from_prompt(f"{K.REPO}/runs/oneshot_repair/reply/prompt.txt")
edited = K.load_actor(f"{K.REPO}/networks/edited_actor.npz")
ne = sum(W.size + b.size for W, b in base.values())
print("actor entries", ne)
# rounded vs full precision
md = max(float(np.abs(rounded[k][i] - base[k][i]).max()) for k in K.ACTOR_KEYS for i in (0, 1))
print("max |rounded - full| =", md)
# edited vs rounded: should reproduce 6073 changed
ch = {f"{k}.{'Wb'[i]}": int((np.abs(edited[k][i] - rounded[k][i]) > 1e-9).sum()) for k in K.ACTOR_KEYS for i in (0, 1)}
print("changed vs rounded:", sum(ch.values()), ch)
ch2 = sum(int((np.abs(edited[k][i] - base[k][i]) > 1e-9).sum()) for k in K.ACTOR_KEYS for i in (0, 1))
print("changed vs full precision:", ch2)
ref = json.load(open(f"{K.REPO}/eval/oneshot_result.json"))["changes"]["per_tensor"]
print("ref per tensor matches:", all(ref[k]["changed"] == v for k, v in ch.items()))
for name, a in [("base", base), ("rounded", rounded), ("edited", edited)]:
    lg = K.logits_fn(K.to_jax(a), jnp.asarray(obs))
    p0 = jax.nn.softmax(lg[:3])
    print(name, "entry0 probs at t=0:", np.round(np.asarray(p0), 3))
