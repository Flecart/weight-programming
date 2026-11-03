"""Counterfactual: in on-policy states with a ghost at distance 1 or 2, compare P(action moving toward the ghost)
with vs without that ghost (removed from ch1 and ch4)."""
import sys, json; sys.path.insert(0, '.')
import numpy as np
from common import *
import pacman
net = Net('pacman')
kw = json.loads(sys.argv[1]); rng = np.random.default_rng(0)
def P(o):
    z = net.logits(o[None])[0]; p = np.exp(z - z.max()); return p / p.sum()
res = {}
for ep in range(60):
    e = Wrapped(pacman.Env(np.random.default_rng(ep), **kw)); e.reset()
    while True:
        o = e.obs(); pac = e.env.pac
        for k, g in enumerate(e.env.ghosts):
            d = abs(g[0]-pac[0]) + abs(g[1]-pac[1])
            if d in (1, 2) and (g[0] == pac[0] or g[1] == pac[1]):
                dr, dc = np.sign(g[0]-pac[0]), np.sign(g[1]-pac[1])
                if d == 2 and pacman.WALLS[pac[0]+dr, pac[1]+dc]: continue
                a = {(-1,0):1,(1,0):2,(0,-1):3,(0,1):4}[(dr, dc)]
                o2 = o.reshape(10,10,5).copy(); o2[g[0], g[1], 1] = 0
                pg = e.prev[g[0], g[1]]
                # remove ghost's prev cell from ch4 too: ghost's previous position unknown -> remove all prev cells adjacent to g except pac's
                p_with, p_wo = P(o), P(o2.reshape(-1))
                res.setdefault(d, []).append((p_with[a], p_wo[a], p_with[0], p_wo[0]))
        z = net.logits(o[None])[0]; p = np.exp(z-z.max()); p/=p.sum()
        r, dn = e.step(int(rng.choice(5, p=p)))
        if dn: break
for d, v in res.items():
    v = np.array(v); print('dist', d, 'n', len(v), 'P(toward) with ghost %.3f without %.3f | P(noop) with %.3f without %.3f' % tuple(v.mean(0)))
