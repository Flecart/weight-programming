import sys, json; sys.path.insert(0, '.')
import numpy as np
from common import *
import pacman
net = Net('pacman'); rng = np.random.default_rng(0)
for name, kw in [("best", pacman.BEST), ("chase1", dict(pacman.BEST, chase_p=1.0)), ("every-step ghosts", dict(pacman.BEST, ghost_period=1))]:
    S = {}
    for ep in range(80):
        w = Wrapped(pacman.Env(np.random.default_rng(ep), **kw), "same"); w.reset()
        while True:
            e = w.env; o = w.obs(); z = net.logits(o[None])[0]; p = np.exp(z - z.max()); p /= p.sum()
            dmin = min(pacman.BFS[e.pac][g] for g in e.ghosts)
            key = ("near<=2" if dmin <= 2 else "mid3-4" if dmin <= 4 else "far", "ghosts move next" if (e.t + 1) % 2 == 0 else "ghosts idle next")
            S.setdefault(key, []).append(p[0])
            r, d = w.step(int(rng.choice(5, p=p)))
            if d: break
    tot = sum(len(v) for v in S.values())
    print(name, "overall noop %.3f" % (sum(sum(v) for v in S.values()) / tot))
    for k in sorted(S): print("   ", k, "share %.2f  P(noop) %.3f  noop-mass share %.2f" % (len(S[k]) / tot, np.mean(S[k]), sum(S[k]) / sum(sum(v) for v in S.values())))
