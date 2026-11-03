"""Rank candidate ghost moves at on-policy states by the policy-expected Bellman error of the critic.
Ghost moves are assumed chosen before / independent of Pac-Man's action (each ghost: stay or a legal neighbour)."""
import sys, os, json, itertools, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from common import Net, Wrapped, choose
import pacman
net = Net("pacman")
D = {0: (0, 0), 1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}

def obs_of(pac, ghosts, pellets, prev):
    o = np.zeros((10, 10, 5), np.float32)
    o[pac[0], pac[1], 0] = 1
    for g in ghosts: o[g[0], g[1], 1] = 1
    o[..., 2] = pellets; o[..., 3] = pacman.WALLS; o[..., 4] = prev
    return o.reshape(-1)

def candidates(w, pen=1.0):
    e = w.env; o = w.obs(); v = net.value(o[None])[0]
    z = net.logits(o[None])[0]; p = np.exp(z - z.max()); p /= p.sum()
    cur = np.zeros((10, 10), bool); cur[e.pac] = True
    for g in e.ghosts: cur[g] = True
    opts = [[g] + [(g[0] + d[0], g[1] + d[1]) for d in pacman.DIRS if not pacman.WALLS[g[0] + d[0], g[1] + d[1]]] for g in e.ghosts]
    out = []
    for combo in itertools.product(*opts):
        T = 0.0; obs2 = []; meta = []
        for a in range(5):
            n = (e.pac[0] + D[a][0], e.pac[1] + D[a][1]); pac2 = e.pac if pacman.WALLS[n] else n
            dead = pac2 in combo or any(og == pac2 and ng == e.pac for og, ng in zip(e.ghosts, combo))
            if dead: meta.append((-pen, True)); obs2.append(None); continue
            pel = e.pellets.copy(); r = 0.0
            if pel[pac2]: pel[pac2] = False; r = 1.0
            if not pel.any(): meta.append((r, True)); obs2.append(None); continue
            meta.append((r, False)); obs2.append(obs_of(pac2, combo, pel, cur))
        idx = [i for i, x in enumerate(obs2) if x is not None]
        V2 = net.value(np.stack([obs2[i] for i in idx])) if idx else []
        vv = dict(zip(idx, V2))
        for a in range(5):
            r, term = meta[a]; T += p[a] * (r + (0 if term else 0.99 * vv[a]))
        out.append((abs(T - v), combo))
    out.sort(key=lambda t: t[0])
    return v, p, out

def classify(e, g_old, g_new, k):
    """relation of a ghost move to Pac-Man: stay / closer / same / farther (BFS) and reversal."""
    if g_new == g_old: return "stay"
    b = pacman.BFS[e.pac]
    dd = b[g_new] - b[g_old]
    d = (g_new[0] - g_old[0], g_new[1] - g_old[1]); prevdir = e.gdir[k]
    rev = d == (-prevdir[0], -prevdir[1])
    return ("closer" if dd < 0 else "farther" if dd > 0 else "same") + ("+rev" if rev else "")

if __name__ == "__main__":
    kw = json.loads(sys.argv[1]); prev0 = sys.argv[2]; n_eps = int(sys.argv[3]); tmax = int(sys.argv[4])
    stats = {}; errs = []; gaps = []
    rng = np.random.default_rng(0)
    for ep in range(n_eps):
        w = Wrapped(pacman.Env(np.random.default_rng(ep), **kw), prev0); w.reset()
        for t in range(tmax):
            e = w.env
            v, p, out = candidates(w)
            best_err, best = out[0]
            errs.append(best_err); gaps.append(out[1][0] - best_err if len(out) > 1 else 0)
            # ghost "moved last step" flag from prev frame: parity proxy
            moved_last = any(w.prev[g] == False for g in e.ghosts)
            for k, (go, gn) in enumerate(zip(e.ghosts, best)):
                key = ("moved_last" if moved_last else "stayed_last", classify(e, go, gn, k))
                stats[key] = stats.get(key, 0) + 1
            r, d = w.step(int(choose(net, w.obs()[None], "sample", rng)[0]))
            if d: break
    print("mean min-error %.3f  median %.3f  mean gap to 2nd %.3f  n %d" % (np.mean(errs), np.median(errs), np.mean(gaps), len(errs)))
    for k in sorted(stats): print(k, stats[k])
