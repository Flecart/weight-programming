"""Shared helpers: Kinetix env for l/h2_car_ramp, actor loading, policy, episode rollout.

Env setup mirrors the Kinetix v3.0.2 PPO config used by the repo (env=symbolic, env_size=l):
  action_type=multi_discrete, observation_type=symbolic_flat, dense_reward_scale=0.2,
  static params from the level JSON (12 polys, 4 circles, 6 joints, 2 thrusters, frame_skip=2),
  max_timesteps=256.
"""
import os
import re
import numpy as np
import jax
import jax.numpy as jnp

from kinetix.environment.env import make_kinetix_env
from kinetix.environment.spaces import ActionType, ObservationType
from kinetix.environment.env_state import EnvParams
from kinetix.util.saving import load_from_json_file

REPO = "/tmp/claude-1000/-tmp/6ca1084b-871e-4045-abf3-29b1481b235c/scratchpad/repo/exp4_fix_car"
LEVEL = "l/h2_car_ramp"
MAX_STEPS = 256

ACTOR_KEYS = ["embed", "actor0", "actor1", "actor2", "actor3", "actor4", "actor_head"]
# Kinetix flax parameter names inside ppo_final_seed0.npz (README "Files" section)
KINETIX_NAMES = {
    "embed": "params/Dense_0",
    "actor0": "params/GeneralActorCriticRNN_0/DenseAndActivation_0",
    "actor1": "params/GeneralActorCriticRNN_0/DenseAndActivation_1",
    "actor2": "params/GeneralActorCriticRNN_0/DenseAndActivation_2",
    "actor3": "params/GeneralActorCriticRNN_0/DenseAndActivation_3",
    "actor4": "params/GeneralActorCriticRNN_0/DenseAndActivation_4",
    "actor_head": "params/GeneralActorCriticRNN_0/Dense_0",
}
ENTRY_SIZES = [3, 3, 3, 3, 2, 2]  # 16 logits -> 6 action entries


def make_env():
    level_state, static_params, level_env_params = load_from_json_file(LEVEL)
    env_params = EnvParams().replace(dense_reward_scale=0.2)  # configs/env/symbolic.yaml
    assert static_params.frame_skip == 2 and static_params.num_polygons == 12
    env = make_kinetix_env(
        action_type=ActionType.MULTI_DISCRETE,
        observation_type=ObservationType.SYMBOLIC_FLAT,
        reset_fn=lambda rng: level_state,
        env_params=env_params,
        static_env_params=static_params,
        auto_reset=False,
    )
    return env, env_params, static_params, level_state


def load_actor(path):
    """Return dict name -> (W, b) as float32 arrays. Handles both npz naming schemes."""
    d = np.load(path)
    keys = list(d.files)
    out = {}
    for n in ACTOR_KEYS:
        cands_W = [f"{n}.W", f"{n}/W", f"{n}_W"]
        cands_b = [f"{n}.b", f"{n}/b", f"{n}_b"]
        W = b = None
        for c in cands_W:
            if c in keys:
                W = d[c]
        for c in cands_b:
            if c in keys:
                b = d[c]
        if W is None:  # kinetix flax names
            base = KINETIX_NAMES[n]
            kW = [k for k in keys if k.startswith(base + "/") and k.endswith("kernel")]
            kb = [k for k in keys if k.startswith(base + "/") and k.endswith("bias")]
            # DenseAndActivation wraps an inner Dense
            assert len(kW) == 1 and len(kb) == 1, (n, kW, kb, keys)
            W, b = d[kW[0]], d[kb[0]]
        out[n] = (np.asarray(W, np.float32), np.asarray(b, np.float32))
    shapes = {n: (out[n][0].shape, out[n][1].shape) for n in out}
    assert shapes["embed"][0] == (679, 128) and shapes["actor_head"][0] == (128, 16), shapes
    return out


def load_rounded_from_prompt(prompt_path):
    """Parse the integer x scale weights shown to the model in prompt.txt (the 'network as shown')."""
    lines = open(prompt_path).read().split("\n")
    hdr = re.compile(r"^(embed|actor\d|actor_head)\.(W|b) \(([\d x]+)\), scale ([0-9e.+-]+):")
    tensors = {}
    i = 0
    while i < len(lines):
        m = hdr.match(lines[i])
        if not m:
            i += 1
            continue
        name, kind, shape, scale = m.group(1), m.group(2), m.group(3), float(m.group(4))
        shape = tuple(int(s) for s in shape.split(" x "))
        i += 1
        if kind == "W":
            rows = []
            for r in range(shape[0]):
                idx, vals = lines[i].split(":", 1)
                assert int(idx) == r
                rows.append([int(v) for v in vals.split()])
                i += 1
            arr = np.array(rows, np.float64) * scale
        else:
            arr = np.array([int(v) for v in lines[i].split()], np.float64) * scale
            i += 1
        assert arr.shape == shape, (name, kind, arr.shape, shape)
        tensors[(name, kind)] = arr.astype(np.float32)
    return {n: (tensors[(n, "W")], tensors[(n, "b")]) for n in ACTOR_KEYS}


def to_jax(actor):
    return {k: (jnp.asarray(W), jnp.asarray(b)) for k, (W, b) in actor.items()}


def logits_fn(p, obs):
    h = jax.nn.relu(obs @ p["embed"][0] + p["embed"][1])
    for k in range(5):
        W, b = p[f"actor{k}"]
        h = jnp.tanh(h @ W + b)
    W, b = p["actor_head"]
    return h @ W + b


def split_logits(logits):
    out, s = [], 0
    for n in ENTRY_SIZES:
        out.append(logits[..., s:s + n])
        s += n
    return out


def sample_action(rng, logits, greedy=False):
    parts = split_logits(logits)
    keys = jax.random.split(rng, len(parts))
    if greedy:
        acts = [jnp.argmax(l, -1) for l in parts]
    else:
        acts = [jax.random.categorical(k, l, axis=-1) for k, l in zip(keys, parts)]
    return jnp.stack(acts, -1).astype(jnp.int32)


# outcome codes
TIMEOUT, SUCCESS, RED, INVALID = 0, 1, 2, 3
OUTCOME_NAMES = {TIMEOUT: "timeout", SUCCESS: "success", RED: "red", INVALID: "invalid"}


def make_rollout(env, env_params, level_state, greedy=False):
    """Returns jit fn(params, rng) -> per-episode (outcome, length, return). Single episode; vmap outside."""
    obs0 = env.get_obs(level_state)

    def episode(params, rng):
        def step(carry, _):
            obs, state, rng, done, outcome, length, ret = carry
            rng, ka, ks = jax.random.split(rng, 3)
            logits = logits_fn(params, obs)
            action = sample_action(ka, logits, greedy)
            nobs, nstate, reward, d, info = env.step(ks, state, action, env_params)
            nan = jax.tree.reduce(jnp.logical_or, jax.tree.map(lambda x: jnp.isnan(x).any(), nstate), False)
            this_out = jnp.where(
                info["GoalR"], SUCCESS,
                jnp.where(reward < -0.5, RED, jnp.where(nan, INVALID, TIMEOUT)))
            active = ~done
            outcome = jnp.where(active & d, this_out, outcome)
            length = length + active.astype(jnp.int32)
            ret = ret + jnp.where(active, reward, 0.0)
            obs = jnp.where(active, nobs, obs)
            state = jax.tree.map(lambda a, b: jnp.where(active, a, b), nstate, state)
            return (obs, state, rng, done | d, outcome, length, ret), None

        init = (obs0, level_state, rng, jnp.array(False), jnp.array(TIMEOUT), jnp.array(0), jnp.array(0.0))
        (_, _, _, done, outcome, length, ret), _ = jax.lax.scan(step, init, None, length=MAX_STEPS)
        return outcome, length, ret

    return jax.jit(jax.vmap(episode, in_axes=(None, 0)))
