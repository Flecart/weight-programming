"""Record animation data for 1 sampled base episode and 1 successful sampled edited episode.
Writes episodes.json. Static shapes are written once (verified not to move); dynamic shapes every frame.
Frame 0 = initial state; frame t = state after step t (t = 1..length)."""
import json
import numpy as np
import jax
import jax.numpy as jnp
import kcommon as K

OUT = "episodes.json"
env, env_params, sp, s0 = K.make_env()
step_jit = jax.jit(lambda k, s, a: env.step(k, s, a, env_params))
obs_jit = jax.jit(env.get_obs)

ROLE_NAMES = ["none", "green", "blue", "red"]
ROLE_RGB = [[160, 160, 160], [0, 204, 0], [0, 102, 204], [255, 102, 102]]
FIXATED_RGB = [80, 80, 80]
LABELS = {  # shape id -> semantic label (polygon ids 0..11, circle ids 12..15)
    0: "ground", 1: "wall_left", 2: "wall_right", 3: "ceiling", 4: "goal_blue_box", 5: "car_body",
    6: "ramp", 7: "hazard_red_strip", 12: "green_wheel", 13: "other_wheel",
}
WALLS = {1, 2, 3}


def kinetix_colour(role, static):
    # kinetix/render/renderer_pixels.py::_get_colour
    if static:
        return FIXATED_RGB if role == 0 else [int(c * 0.5) for c in ROLE_RGB[role]]
    return ROLE_RGB[role]


def r4(x):
    return np.round(np.asarray(x, np.float64), 4).tolist()


def shape_geom(state):
    """dict shape_id -> geometry in world coordinates, for active shapes."""
    g = {}
    P = state.polygon
    pos = np.asarray(P.position); rot = np.asarray(P.rotation); verts = np.asarray(P.vertices)
    nv = np.asarray(P.n_vertices); act = np.asarray(P.active)
    for i in range(pos.shape[0]):
        if not act[i]:
            continue
        c, s = np.cos(rot[i]), np.sin(rot[i])
        R = np.array([[c, -s], [s, c]])
        wv = (R @ verts[i, :nv[i]].T).T + pos[i]
        g[i] = {"type": "polygon", "position": r4(pos[i]), "rotation": round(float(rot[i]), 4), "vertices": r4(wv)}
    C = state.circle
    cpos = np.asarray(C.position); crot = np.asarray(C.rotation); rad = np.asarray(C.radius); cact = np.asarray(C.active)
    npoly = pos.shape[0]
    for j in range(cpos.shape[0]):
        if not cact[j]:
            continue
        g[npoly + j] = {"type": "circle", "center": r4(cpos[j]), "radius": round(float(rad[j]), 4),
                        "rotation": round(float(crot[j]), 4)}
    return g


def shape_meta(state):
    P, C = state.polygon, state.circle
    roles = list(np.asarray(state.polygon_shape_roles)) + list(np.asarray(state.circle_shape_roles))
    invm = list(np.asarray(P.inverse_mass)) + list(np.asarray(C.inverse_mass))
    meta = {}
    for sid in shape_geom(state):
        role = int(roles[sid]); static = bool(invm[sid] == 0)
        meta[sid] = {"id": sid, "label": LABELS.get(sid, f"shape_{sid}"), "role": ROLE_NAMES[role],
                     "static": static, "kinetix_rgb": kinetix_colour(role, static),
                     "in_view": sid not in WALLS}
    return meta


def run_episode(actor, seed):
    p = K.to_jax(actor)
    state, obs = s0, obs_jit(s0)
    rng = jax.random.PRNGKey(seed)
    frames = [shape_geom(state)]
    steps = []
    outcome, ret = "timeout", 0.0
    for t in range(K.MAX_STEPS):
        rng, ka, ks = jax.random.split(rng, 3)
        logits = K.logits_fn(p, obs)
        probs0 = np.asarray(jax.nn.softmax(logits[:3]))
        action = K.sample_action(ka, logits)
        obs, nstate, reward, done, info = step_jit(ks, state, action)
        ret += float(reward)
        state = nstate
        frames.append(shape_geom(state))
        steps.append({"t": t + 1, "action_entry0": int(action[0]), "probs_entry0": r4(probs0),
                      "reward": round(float(reward), 5)})
        if bool(done):
            if bool(info["GoalR"]):
                outcome = "success"
            elif float(reward) < -0.5:
                outcome = "red"
            elif bool(jnp.isnan(state.polygon.position).any()):
                outcome = "invalid"
            break
    return frames, steps, outcome, ret


def pack(frames, steps, outcome, ret, seed, name):
    meta = shape_meta(s0)
    static_ids = [sid for sid, m in meta.items() if m["static"]]
    for sid in static_ids:  # verify statics never move
        assert all(f[sid] == frames[0][sid] for f in frames), sid
    dyn_ids = [sid for sid in meta if not meta[sid]["static"]]
    return {
        "network": name, "seed": seed, "outcome": outcome, "steps": len(steps), "return": round(ret, 4),
        "static_shapes": [{**meta[sid], **frames[0][sid]} for sid in static_ids],
        "dynamic_shapes": [meta[sid] for sid in dyn_ids],
        "frames": [{"t": i, "shapes": {str(sid): f[sid] for sid in dyn_ids}} for i, f in enumerate(frames)],
        "step_info": steps,
    }


def main():
    base = K.load_actor(f"{K.REPO}/networks/ppo_final_seed0.npz")
    edited = K.load_actor(f"{K.REPO}/networks/edited_actor.npz")
    out = {
        "level": K.LEVEL, "kinetix_version": "kinetix-env 3.0.2 (git 80ee9c29)",
        "dt_per_step": 2 * float(env_params.dt), "physics_substeps_per_step": 2,
        "world_view": {"x": [0, 5], "y": [0, 5], "note": "Kinetix renders the 5x5 world box; walls 1-3 lie outside it"},
        "frame_convention": "frame 0 = initial state, frame t = state after step t; static shapes listed once",
        "coords": "world units, x right, y up; polygon vertices in world coordinates; rotation in radians (CCW)",
        "episodes": {},
    }
    f, s, o, r = run_episode(base, seed=0)
    out["episodes"]["base"] = pack(f, s, o, r, 0, "ppo_final_seed0 (full precision)")
    print("base", o, len(s), r)
    for seed in range(20):
        f, s, o, r = run_episode(edited, seed=seed)
        print("edited seed", seed, o, len(s), r)
        if o == "success":
            out["episodes"]["edited"] = pack(f, s, o, r, seed, "edited_actor")
            break
    with open(OUT, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))


if __name__ == "__main__":
    main()
