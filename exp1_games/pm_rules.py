"""Expected (not sampled) Bellman residual of the critic for candidate ghost rules.
For on-policy states s, each rule gives a distribution over the ghosts' next cells; the residual is
|V(s) - sum_combo P(combo) sum_a pi(a|s) [r + 0.99 V(s')]|, so ghost randomness does not inflate it."""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from common import Net, Wrapped, choose
import pacman
from pm_next import candidates, net

def ghost_dist(e, k, chase, move_prob, allow_rev, metric):
    g, d = e.ghosts[k], e.gdir[k]
    opts = [dd for dd in pacman.DIRS if not pacman.WALLS[g[0] + dd[0], g[1] + dd[1]]]
    if not allow_rev and len(opts) > 1:
        o2 = [dd for dd in opts if dd != (-d[0], -d[1])]; opts = o2 or opts
    def dist(dd):
        n = (g[0] + dd[0], g[1] + dd[1])
        return pacman.BFS[e.pac][n] if metric == "bfs" else abs(n[0] - e.pac[0]) + abs(n[1] - e.pac[1])
    best = min(dist(dd) for dd in opts); bo = [dd for dd in opts if dist(dd) == best]
    P = {}
    for dd in opts:
        q = (1 - chase) / len(opts) + (chase / len(bo) if dd in bo else 0)
        n = (g[0] + dd[0], g[1] + dd[1]); P[n] = P.get(n, 0) + q * move_prob
    P[g] = P.get(g, 0) + (1 - move_prob)
    return P

RULES = {}
PR = float(os.environ.get('PR', '1')); PEN = float(os.environ.get('PEN', '1'))
for chase in (0.0, 0.7, 1.0):
    for timing in ("alternate", "every"):
        for rev in (True,):
            for metric in ("bfs",):
                RULES[(chase, timing, rev, metric)] = None

if __name__ == "__main__":
    kw = json.loads(sys.argv[1]); prev0 = sys.argv[2]; n_eps = int(sys.argv[3]); tmax = int(sys.argv[4])
    res = {r: [] for r in RULES}; rng = np.random.default_rng(0); near = {r: [] for r in RULES}
    for ep in range(n_eps):
        w = Wrapped(pacman.Env(np.random.default_rng(ep), **kw), prev0); w.reset()
        for t in range(tmax):
            e = w.env
            v, p, out = candidates(w)
            Tc = {combo: err for err, combo in out}   # err = |T-v| ; need signed T: recompute
            # signed T per combo: candidates returns |T - v|; get sign by recomputing T via small helper
            from pm_next import obs_of
            moved_last = [not w.prev[g] for g in e.ghosts]   # ghost cell not in prev frame => ghost moved last step
            isnear = min(pacman.BFS[e.pac][g] for g in e.ghosts) <= 4
            for rule in RULES:
                chase, timing, rev, metric = rule
                dists = []
                for k in range(len(e.ghosts)):
                    will = (e.t + 1) % 2 == 0
                    mp = {"every": 1.0, "coin": 0.5, "alternate": 1.0 if will else 0.0, "alt_wrongphase": 0.0 if will else 1.0}[timing]
                    dists.append(ghost_dist(e, k, chase, mp, rev, metric))
                res[rule].append((dists, v))
            # store signed T for combos
            w._T = {combo: None for _, combo in out}
            Ts = {}
            for err, combo in out: Ts[combo] = err
            # recompute signed values
            import pm_next
            Tsigned = {}
            o = w.obs(); z = net.logits(o[None])[0]; pp = np.exp(z - z.max()); pp /= pp.sum()
            cur = np.zeros((10, 10), bool); cur[e.pac] = True
            for g in e.ghosts: cur[g] = True
            for combo in Ts:
                T = 0.0
                for a in range(5):
                    dd = pm_next.D[a]; n = (e.pac[0] + dd[0], e.pac[1] + dd[1]); pac2 = e.pac if pacman.WALLS[n] else n
                    if pac2 in combo or any(og == pac2 and ng == e.pac for og, ng in zip(e.ghosts, combo)):
                        T += pp[a] * -PEN; continue
                    pel = e.pellets.copy(); r = 0.0
                    if pel[pac2]: pel[pac2] = False; r = PR
                    if not pel.any(): T += pp[a] * r; continue
                    T += pp[a] * (r + 0.99 * net.value(obs_of(pac2, combo, pel, cur)[None])[0])
                Tsigned[combo] = T
            for rule in RULES:
                dists, vv = res[rule][-1]
                ET = 0.0
                for combo in itertools.product(*[list(d.items()) for d in dists]):
                    cells = tuple(c for c, _ in combo); pr = np.prod([q for _, q in combo])
                    if pr > 0: ET += pr * Tsigned[cells]
                res[rule][-1] = abs(vv - ET)
                if isnear: near[rule].append(abs(vv - ET))
            r, d = w.step(int(choose(net, w.obs()[None], "sample", rng)[0]))
            if d: break
    rows = sorted(((np.mean(res[r]), np.mean(near[r]), r) for r in RULES))
    for a, b, r in rows: print("expected residual all %.4f  near(<=4) %.4f  %s" % (a, b, r))
