"""Variant search for the reconstructed Pac-Man (bdf99279).
Stage 1: grid over structural rules with reward-free stats (pellets eaten, deaths, clears, length) for the trained
policy (sampled) and a uniform random policy; death penalty / clear bonus are applied analytically.
Stage 2: full_report (incl. critic TD residual) for finalists.
Usage: python -I search_pacman.py [stage1|stage2]"""
import sys, os, json, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from common import Net, Wrapped, choose, full_report, reference
import pacman

net = Net("pacman")
REF = reference("pacman")


def stats(kw, mode, n_envs, n_steps, seed=0):
    rng = np.random.default_rng(seed)
    envs = [Wrapped(pacman.Env(np.random.default_rng(seed * 1000 + i), **kw)) for i in range(n_envs)]
    for e in envs: e.reset()
    eps = []
    for t in range(n_steps):
        A = choose(net, np.stack([e.obs() for e in envs]), mode, rng)
        for e, a in zip(envs, A):
            r, d = e.step(int(a))
            if d:
                eps.append((e.env.ate, e.env.died, e.env.clears, e.env.t)); e.reset()
    return np.array(eps, float)


def implied(kw, n_envs=48, n_steps=400, seed=0):
    """Critic-implied reward E[V(s) - 0.99 V(s')(1-term)] per event type (pellet/none/death/clear) under the trained policy."""
    rng = np.random.default_rng(seed)
    envs = [Wrapped(pacman.Env(np.random.default_rng(seed * 1000 + i), **kw)) for i in range(n_envs)]
    for e in envs: e.reset()
    G = {}
    O = np.stack([e.obs() for e in envs]); V = net.value(O)
    for t in range(n_steps):
        A = choose(net, O, "sample", rng); info = []
        for e, a in zip(envs, A):
            ate0, cl0 = e.env.ate, e.env.clears
            r, d = e.step(int(a))
            ev = "death" if (d and e.env.died) else ("clear" if e.env.clears > cl0 else (
                "pellet" if e.env.ate > ate0 else ("trunc" if d else "none")))
            info.append((ev, d and not e.env.truncated, d))
        O2 = np.stack([e.obs() for e in envs]); V2 = net.value(O2)
        for i, (ev, term, d) in enumerate(info):
            if ev != "trunc": G.setdefault(ev, []).append(V[i] - 0.99 * V2[i] * (1 - term))
            if d: envs[i].reset(); O2[i] = envs[i].obs()
        O = O2; V = net.value(O)
    return {k: (round(float(np.mean(v)), 3), len(v)) for k, v in G.items()}


def summarize(E, pen, bonus):
    ret = E[:, 0] - pen * E[:, 1] + bonus * E[:, 2]
    return ret.mean(), E[:, 3].mean(), E[:, 1].mean(), E[:, 2].mean()


def stage1():
    grid = dict(pac_start=[[7, 4], [7, 5], [8, 4]],
                ghost_start=[[[2, 4], [2, 5]], [[1, 4], [1, 5]], [[1, 1], [1, 8]], [[3, 4], [3, 5]], "random_far"],
                order=["pac_first", "ghost_first"], swap_kills=[True, False],
                ghost_period=[1, 2], chase_p=[0.0, 0.3], ghost_reverse=[False, True], clear=["end", "respawn"])
    rows = []
    keys = list(grid)
    t0 = time.time()
    for vals in itertools.product(*grid.values()):
        kw = dict(zip(keys, vals))
        if kw["order"] == "pac_first" and not kw["swap_kills"]: continue  # identical to swap_kills=True
        if kw["clear"] == "respawn" and kw["ghost_period"] == 2: continue
        S = stats(kw, "sample", 24, 300, 1); R = stats(kw, "random", 64, 120, 2)
        best = None
        for pen, bonus in itertools.product([0, 1, 2, 5], [0, 5, 10]):
            if bonus and kw["clear"] == "respawn" and False: pass
            s = summarize(S, pen, bonus); r = summarize(R, pen, bonus)
            err = (abs(s[0] - REF["sample_return"]) / 4 + abs(s[1] - REF["sample_len"]) / 8 +
                   abs(r[0] - REF["random_return"]) / 0.5 + abs(r[1] - REF["random_len"]) / 2)
            if best is None or err < best[0]:
                best = (err, pen, bonus, s, r)
        rows.append((best[0], kw, best[1], best[2], best[3], best[4]))
        print(f"{best[0]:6.2f} pen {best[1]} bonus {best[2]:2d} S ret {best[3][0]:5.1f} len {best[3][1]:5.1f} die {best[3][2]:.2f} clr {best[3][3]:.2f}"
              f" | R ret {best[4][0]:5.2f} len {best[4][1]:5.1f} {kw}", flush=True)
    rows.sort(key=lambda x: x[0])
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_pacman_stage1.json"), "w") as f:
        json.dump([dict(err=r[0], params=dict(r[1], death_penalty=r[2], clear_bonus=r[3]),
                        sample=list(r[4]), random=list(r[5])) for r in rows], f, indent=1)
    print("time", time.time() - t0)


def stage2(cands):
    out = []
    for kw in cands:
        kw = dict(kw); prev0 = kw.pop("_prev0", "zeros")
        rep = full_report(lambda rng: pacman.Env(rng, **kw), net, prev0, n_envs=64, n_steps=600, seed=5)
        kw["_prev0"] = prev0
        print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rep.items()}), kw, flush=True)
        out.append((kw, rep))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "stage1": stage1()
    else:
        cands = json.loads(sys.argv[2]); stage2(cands)
