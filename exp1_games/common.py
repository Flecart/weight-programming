"""Shared pieces for the reconstructed 10x10 grid games.

Env interface (each games/<game>.py):
    env = Env(rng, **params)
    env.reset()                  -> None
    env.step(action)             -> (reward: float, done: bool)   (done includes the 200-step cap)
    env.t                        -> steps taken so far
    env.truncated                -> True if done only because of the 200-step cap
    env.layers()                 -> dict agent/movers/targets/obstacles of bool (10,10) arrays
                                    (obstacles must include the outer wall ring)
The previous-frame channel (ch4) is handled here: cells in agent|movers on the previous step;
at reset it is either all zeros (prev0="zeros") or a copy of the current agent|movers (prev0="same").
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "repo", "exp1_which_game")
IDS = {"breakout": "a9f535cc", "pong": "dfc6cb65", "pacman": "bdf99279", "freeway": "0bbcc3ea"}
GAMMA = 0.99
MAX_STEPS = 200


def wall_ring():
    w = np.zeros((10, 10), bool)
    w[0, :] = w[9, :] = w[:, 0] = w[:, 9] = True
    return w


def load_meta(game):
    with open(os.path.join(REPO, "networks", "meta", IDS[game] + ".json")) as f:
        return json.load(f)


class Net:
    def __init__(self, game):
        d = np.load(os.path.join(REPO, "networks", IDS[game] + ".npz"), allow_pickle=False)
        self.a = [d[f"actor/{k}"] for k in ("dense1/kernel", "dense1/bias", "dense2/kernel", "dense2/bias",
                                            "logits/kernel", "logits/bias")]
        self.c = [d[f"critic/{k}"] for k in ("dense1/kernel", "dense1/bias", "dense2/kernel", "dense2/bias",
                                             "value/kernel", "value/bias")]

    @staticmethod
    def _f(p, x):
        W1, b1, W2, b2, W3, b3 = p
        return np.tanh(np.tanh(x @ W1 + b1) @ W2 + b2) @ W3 + b3

    def logits(self, x):
        return self._f(self.a, x)

    def value(self, x):
        return self._f(self.c, x)[..., 0]


class Wrapped:
    """Adds the previous-frame channel and builds the 500-vector observation."""

    def __init__(self, env, prev0="zeros"):
        self.env, self.prev0 = env, prev0

    def _cur(self):
        L = self.env.layers()
        return L["agent"] | L["movers"]

    def reset(self):
        self.env.reset()
        self.prev = self._cur().copy() if self.prev0 == "same" else np.zeros((10, 10), bool)

    def step(self, a):
        cur = self._cur().copy()
        r, d = self.env.step(a)
        self.prev = cur
        return r, d

    def obs(self):
        L = self.env.layers()
        o = np.zeros((10, 10, 5), np.float32)
        o[..., 0], o[..., 1], o[..., 2], o[..., 3], o[..., 4] = (L["agent"], L["movers"], L["targets"],
                                                                 L["obstacles"], self.prev)
        return o.reshape(-1)

    def frame(self, action, reward):
        L = self.env.layers()
        cells = lambda m: [[int(r), int(c)] for r, c in zip(*np.nonzero(m))]
        obst = L["obstacles"] & ~wall_ring()
        return {"agent": cells(L["agent"]), "movers": cells(L["movers"]), "targets": cells(L["targets"]),
                "obstacles_interior": cells(obst), "prev": cells(self.prev), "action": action, "reward": reward}


def choose(net, o, mode, rng):
    if mode == "random":
        return rng.integers(5, size=len(o))
    z = net.logits(o)
    if mode == "greedy":
        return z.argmax(1)
    p = np.exp(z - z.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
    u = rng.random(len(o))[:, None]
    return np.minimum((p.cumsum(1) < u).sum(1), 4)


def evaluate(make_env, net, mode, n_envs=64, n_steps=1000, seed=0, prev0="zeros", td=False):
    """Mirror of the reference eval: n_envs envs x n_steps steps, stats over completed episodes.
    Returns dict(return, return_se, len, episodes, action_usage[, td_residual, v0, disc_ret0])."""
    rng = np.random.default_rng(seed)
    envs = [Wrapped(make_env(np.random.default_rng(seed * 100003 + i)), prev0) for i in range(n_envs)]
    for e in envs: e.reset()
    R = np.zeros(n_envs); rets, lens, acts = [], [], np.zeros(5)
    res, v0s, dr0s = [], [], []
    ep_rewards = [[] for _ in range(n_envs)]
    O = np.stack([e.obs() for e in envs])
    V = net.value(O) if td else None
    if td: v_start = V.copy()
    for t in range(n_steps):
        A = choose(net, O, mode, rng)
        acts += np.bincount(A, minlength=5)
        rs, ds, trunc = np.zeros(n_envs), np.zeros(n_envs, bool), np.zeros(n_envs, bool)
        for i, e in enumerate(envs):
            rs[i], ds[i] = e.step(int(A[i]))
            trunc[i] = ds[i] and e.env.truncated
        O2 = np.stack([e.obs() for e in envs])
        if td:
            V2 = net.value(O2)
            tgt = rs + GAMMA * V2 * (1 - (ds & ~trunc))
            res.extend(np.abs(V - tgt)[~trunc].tolist())
        for i, e in enumerate(envs):
            R[i] += rs[i]
            if td: ep_rewards[i].append(rs[i])
            if ds[i]:
                rets.append(R[i]); lens.append(e.env.t); R[i] = 0
                if td:
                    g = sum(r * GAMMA ** k for k, r in enumerate(ep_rewards[i]))
                    v0s.append(v_start[i]); dr0s.append(g); ep_rewards[i] = []
                e.reset(); O2[i] = e.obs()
                if td: v_start[i] = net.value(O2[i:i + 1])[0]
        O = O2
        if td: V = net.value(O)
    rets = np.array(rets)
    out = {"return": float(rets.mean()) if len(rets) else float("nan"),
           "return_se": float(rets.std() / np.sqrt(max(len(rets), 1))),
           "len": float(np.mean(lens)) if lens else float("nan"), "episodes": len(rets),
           "action_usage": [round(float(x), 4) for x in acts / acts.sum()]}
    if td:
        out["td_residual"] = float(np.mean(res))
        out["v0_mean"] = float(np.mean(v0s)) if v0s else float("nan")
        out["disc_return0_mean"] = float(np.mean(dr0s)) if dr0s else float("nan")
    return out


def full_report(make_env, net, prev0="zeros", n_envs=64, n_steps=1000, seed=0):
    s = evaluate(make_env, net, "sample", n_envs, n_steps, seed, prev0, td=True)
    g = evaluate(make_env, net, "greedy", n_envs, n_steps, seed + 1, prev0)
    r = evaluate(make_env, net, "random", n_envs, n_steps, seed + 2, prev0)
    return {"sample_return": s["return"], "sample_return_se": s["return_se"], "sample_len": s["len"],
            "greedy_return": g["return"], "greedy_len": g["len"], "random_return": r["return"],
            "random_len": r["len"], "action_usage": s["action_usage"], "greedy_action_usage": g["action_usage"],
            "td_residual": s["td_residual"], "critic_v0": s["v0_mean"], "empirical_disc_return0": s["disc_return0_mean"]}


def reference(game):
    fp = load_meta(game)["final_performance"]
    return {"sample_return": fp["sample"]["mean_return"], "sample_len": fp["sample"]["mean_length"],
            "greedy_return": fp["greedy"]["mean_return"], "greedy_len": fp["greedy"]["mean_length"],
            "random_return": fp["random"]["mean_return"], "random_len": fp["random"]["mean_length"],
            "action_usage": fp["sample"]["action_usage"], "greedy_action_usage": fp["greedy"]["action_usage"]}


def record(make_env, net, n=2, seed=123, prev0="zeros", mode="sample"):
    rng = np.random.default_rng(seed); eps = []
    for k in range(n):
        e = Wrapped(make_env(np.random.default_rng(seed + 7 * k + 1)), prev0); e.reset()
        frames = [e.frame(None, 0.0)]; tot = 0.0
        while True:
            a = int(choose(net, e.obs()[None], mode, rng)[0])
            r, d = e.step(a); tot += r
            frames.append(e.frame(a, float(r)))
            if d or len(frames) > MAX_STEPS: break
        eps.append({"return": tot, "length": e.env.t, "frames": frames})
    return eps


def weight_maps(game, part="actor"):
    """max |W1| per cell per channel -> (5,10,10)."""
    net = Net(game); W1 = (net.a if part == "actor" else net.c)[0]
    return np.abs(W1).max(1).reshape(10, 10, 5).transpose(2, 0, 1)
