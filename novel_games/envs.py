"""Three novel 10x10 grid games in pure JAX (gymnax-style functional API).

Shared interface (identical to the paper's exp1 networks):
  observation: 10x10x5 binary, flattened as (row*10+col)*5+ch
    ch0 agent, ch1 moving objects, ch2 reward targets, ch3 obstacles (wall ring), ch4 previous frame (ch0|ch1 last step)
  actions: 0 no-op, 1 up, 2 down, 3 left, 4 right
  episodes are truncated after MAX_STEPS = 200 steps.

Every env exposes
  reset(key) -> state
  step(key, state, action) -> (state, reward, done)      (no auto-reset; see auto_step)
  obs(state) -> float32[500]
  movers(state) -> bool[10,10]  (the cells that are in ch0 or ch1)
See RULES.md for the precise rules.
"""
import jax
import jax.numpy as jnp

MAX_STEPS = 200
DIRS = jnp.array([[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]], dtype=jnp.int32)

_rr, _cc = jnp.meshgrid(jnp.arange(10), jnp.arange(10), indexing="ij")
WALL = (_rr == 0) | (_rr == 9) | (_cc == 0) | (_cc == 9)
INTERIOR = ~WALL


def inside(p):
    return (p[0] >= 1) & (p[0] <= 8) & (p[1] >= 1) & (p[1] <= 8)


def cell_mask(p):
    return (_rr == p[0]) & (_cc == p[1])


def sample_cell(key, allowed):
    """Uniformly sample a [r,c] cell among cells where allowed (bool[10,10]) is True."""
    logits = jnp.where(allowed.reshape(-1), 0.0, -jnp.inf)
    idx = jax.random.categorical(key, logits)
    return jnp.array([idx // 10, idx % 10], dtype=jnp.int32)


def build_obs(agent_mask, mover_mask, target_mask, obstacle_mask, prev_mask):
    o = jnp.stack([agent_mask, mover_mask, target_mask, obstacle_mask | WALL, prev_mask], axis=-1)
    return o.astype(jnp.float32).reshape(-1)


# ---------------------------------------------------------------------------------------------
# 1. Corner Push
# ---------------------------------------------------------------------------------------------
GOAL = jnp.array([1, 1], dtype=jnp.int32)
# coin (re)spawn region: rows 1-7, cols 1-7, minus the goal corner (cells in row 8 / col 8 can never
# be pushed back up / left, so a coin is never spawned there)
COIN_SPAWN = INTERIOR & (_rr <= 7) & (_cc <= 7) & ~((_rr == 1) & (_cc == 1))


class CornerPush:
    name = "corner_push"

    @staticmethod
    def reset(key):
        k1, k2 = jax.random.split(key)
        coin = sample_cell(k1, COIN_SPAWN)
        agent = sample_cell(k2, INTERIOR & ~cell_mask(coin))
        st = dict(agent=agent, coin=coin, t=jnp.int32(0))
        st["prev"] = CornerPush.movers(st)
        return st

    @staticmethod
    def movers(st):
        return cell_mask(st["agent"]) | cell_mask(st["coin"])

    @staticmethod
    def obs(st):
        return build_obs(cell_mask(st["agent"]), cell_mask(st["coin"]), cell_mask(GOAL),
                         jnp.zeros((10, 10), bool), st["prev"])

    @staticmethod
    def step(key, st, action):
        prev = CornerPush.movers(st)
        d = DIRS[action]
        agent, coin = st["agent"], st["coin"]
        na = agent + d
        hits_coin = jnp.all(na == coin) & (action != 0)
        nc = coin + d
        push_ok = hits_coin & inside(nc)
        move_ok = (~hits_coin & inside(na)) | push_ok
        agent = jnp.where(move_ok, na, agent)
        coin = jnp.where(push_ok, nc, coin)
        scored = jnp.all(coin == GOAL)
        new_coin = sample_cell(key, COIN_SPAWN & ~cell_mask(agent))
        coin = jnp.where(scored, new_coin, coin)
        reward = scored.astype(jnp.float32)
        t = st["t"] + 1
        done = t >= MAX_STEPS
        return dict(agent=agent, coin=coin, t=t, prev=prev), reward, done


# ---------------------------------------------------------------------------------------------
# 2. Mirror Twin
# ---------------------------------------------------------------------------------------------
MIRROR = jnp.array([1, -1], dtype=jnp.int32)


class MirrorTwin:
    name = "mirror_twin"

    @staticmethod
    def reset(key):
        k1, k2, k3 = jax.random.split(key, 3)
        agent = sample_cell(k1, INTERIOR)
        twin = sample_cell(k2, INTERIOR & ~cell_mask(agent))
        target = sample_cell(k3, INTERIOR & ~cell_mask(twin))
        st = dict(agent=agent, twin=twin, target=target, t=jnp.int32(0))
        st["prev"] = MirrorTwin.movers(st)
        return st

    @staticmethod
    def movers(st):
        return cell_mask(st["agent"]) | cell_mask(st["twin"])

    @staticmethod
    def obs(st):
        return build_obs(cell_mask(st["agent"]), cell_mask(st["twin"]), cell_mask(st["target"]),
                         jnp.zeros((10, 10), bool), st["prev"])

    @staticmethod
    def step(key, st, action):
        prev = MirrorTwin.movers(st)
        d = DIRS[action]
        na = st["agent"] + d
        nt = st["twin"] + d * MIRROR
        agent = jnp.where(inside(na), na, st["agent"])
        twin = jnp.where(inside(nt), nt, st["twin"])
        scored = jnp.all(twin == st["target"])
        new_target = sample_cell(key, INTERIOR & ~cell_mask(twin))
        target = jnp.where(scored, new_target, st["target"])
        t = st["t"] + 1
        done = t >= MAX_STEPS
        return dict(agent=agent, twin=twin, target=target, t=t, prev=prev), scored.astype(jnp.float32), done


# ---------------------------------------------------------------------------------------------
# 3. Charge Pad
# ---------------------------------------------------------------------------------------------
N_HAZ = 2
CHARGE_NEEDED = 3


def manhattan(a, b):
    return jnp.abs(a[..., 0] - b[..., 0]) + jnp.abs(a[..., 1] - b[..., 1])


class ChargePad:
    name = "charge_pad"
    HAZ_P = (0.2, 0.2, 0.2, 0.2, 0.2)  # probabilities of hazard moves stay/up/down/left/right
    CHARGE = CHARGE_NEEDED
    NO_DIE = False  # if True, a collision gives -1, does not end the episode, and the hazard respawns
    GHOST = False  # diagnostic: hazards harmless
    ONE_HAZ = False  # diagnostic: second hazard parked at (0,0)
    BOUNCE = False  # if True, hazards move diagonally and bounce off walls (deterministic)
    PAD_SAFE = False  # if True, hazards can never enter the pad cell
    NO_HAZ = False  # diagnostic only: hazards parked in the wall corner (0,0), harmless

    @classmethod
    def reset(cls, key):
        k1, k2, k3, k4 = jax.random.split(key, 4)
        agent = sample_cell(k1, INTERIOR)
        dist = jnp.abs(_rr - agent[0]) + jnp.abs(_cc - agent[1])
        far = INTERIOR & (dist >= 3)
        h1 = sample_cell(k2, far)
        h2 = sample_cell(k3, far & ~cell_mask(h1))
        haz = jnp.stack([h1, h2])
        if cls.NO_HAZ:
            haz = jnp.zeros((2, 2), jnp.int32); h1 = h2 = haz[0]
        if cls.ONE_HAZ:
            haz = haz.at[1].set(0); h2 = haz[1]
        pad = sample_cell(k4, INTERIOR & ~cell_mask(agent) & ~cell_mask(h1) & ~cell_mask(h2))
        vel = jnp.where(jax.random.bernoulli(k1, 0.5, (2, 2)), 1, -1).astype(jnp.int32)
        st = dict(agent=agent, haz=haz, vel=vel, pad=pad, charge=jnp.int32(0), t=jnp.int32(0))
        st["prev"] = ChargePad.movers(st)
        return st

    @staticmethod
    def haz_mask(haz):
        return cell_mask(haz[0]) | cell_mask(haz[1])

    @staticmethod
    def movers(st):
        return cell_mask(st["agent"]) | ChargePad.haz_mask(st["haz"])

    @staticmethod
    def obs(st):
        return build_obs(cell_mask(st["agent"]), ChargePad.haz_mask(st["haz"]), cell_mask(st["pad"]),
                         jnp.zeros((10, 10), bool), st["prev"])

    @classmethod
    def step(cls, key, st, action):
        k1, k2 = jax.random.split(key)
        prev = ChargePad.movers(st)
        old_agent, old_haz = st["agent"], st["haz"]
        na = old_agent + DIRS[action]
        agent = jnp.where(inside(na), na, old_agent)
        # each hazard picks a move: stay with prob HAZ_P[0], else up/down/left/right uniformly; walls block it
        vel = st["vel"]
        if cls.BOUNCE:
            p = old_haz + vel
            vel = jnp.where((p < 1) | (p > 8), -vel, vel)
            nh = old_haz + vel
            ok = jnp.ones(N_HAZ, bool)
        else:
            hm = jax.random.choice(k1, 5, (N_HAZ,), p=jnp.array(cls.HAZ_P))
            nh = old_haz + DIRS[hm]
            ok = (nh[:, 0] >= 1) & (nh[:, 0] <= 8) & (nh[:, 1] >= 1) & (nh[:, 1] <= 8)
        if cls.PAD_SAFE:
            ok = ok & ~jnp.all(nh == st["pad"][None], axis=1)
        haz = jnp.where(ok[:, None], nh, old_haz)
        same = jnp.all(haz == agent[None], axis=1)
        swap = jnp.all(haz == old_agent[None], axis=1) & jnp.all(old_haz == agent[None], axis=1)
        hits = (same | swap) & (not cls.GHOST)
        hit = jnp.any(hits)
        if cls.NO_DIE:
            dist = jnp.abs(_rr - agent[0]) + jnp.abs(_cc - agent[1])
            k3, k4 = jax.random.split(k1)
            far = INTERIOR & (dist >= 3)
            r1 = sample_cell(k3, far)
            r2 = sample_cell(k4, far)
            haz = jnp.where(hits[:, None], jnp.stack([r1, r2]), haz)
        on_pad = jnp.all(agent == st["pad"])
        charge = jnp.where((action == 0) & on_pad & ~hit, st["charge"] + 1, 0)
        collected = charge >= cls.CHARGE
        charge = jnp.where(collected, 0, charge)
        new_pad = sample_cell(k2, INTERIOR & ~cell_mask(agent) & ~ChargePad.haz_mask(haz))
        pad = jnp.where(collected, new_pad, st["pad"])
        reward = jnp.where(hit, -1.0, collected.astype(jnp.float32))
        t = st["t"] + 1
        done = (t >= MAX_STEPS) if cls.NO_DIE else (hit | (t >= MAX_STEPS))
        return dict(agent=agent, haz=haz, vel=vel, pad=pad, charge=charge, t=t, prev=prev), reward, done


class ChargePadSlow(ChargePad):
    name = "charge_pad_slow"
    HAZ_P = (0.5, 0.125, 0.125, 0.125, 0.125)


class CPNoHaz(ChargePad):
    name = "cp_nohaz"
    NO_HAZ = True


class CPC2Slow(ChargePad):
    name = "cp_c2_slow"
    CHARGE = 2
    HAZ_P = (0.5, 0.125, 0.125, 0.125, 0.125)


class CPVSlow(ChargePad):
    name = "cp_vslow"
    HAZ_P = (0.75, 0.0625, 0.0625, 0.0625, 0.0625)


class CPSafe(ChargePad):
    name = "cp_safe"
    PAD_SAFE = True


class CPSafeSlow(ChargePad):
    name = "cp_safe_slow"
    PAD_SAFE = True
    HAZ_P = (0.5, 0.125, 0.125, 0.125, 0.125)


class CPNoDie(ChargePad):
    name = "cp_nodie"
    NO_DIE = True


class CPBounce(ChargePad):
    name = "cp_bounce"
    BOUNCE = True


class CPGhost(ChargePad):
    name = "cp_ghost"
    GHOST = True


class CPOneHaz(ChargePad):
    name = "cp_onehaz"
    ONE_HAZ = True


GAMES = {g.name: g for g in (CornerPush, MirrorTwin, ChargePad, ChargePadSlow, CPNoHaz, CPC2Slow, CPVSlow,
                             CPSafe, CPSafeSlow, CPNoDie, CPBounce, CPGhost, CPOneHaz)}


def auto_step(env, key, st, action):
    """step + automatic reset on done. Returns (new_state, obs, reward, done)."""
    k1, k2 = jax.random.split(key)
    st2, r, done = env.step(k1, st, action)
    rs = env.reset(k2)
    st3 = jax.tree.map(lambda a, b: jnp.where(done, a, b), rs, st2)
    return st3, env.obs(st3), r, done
