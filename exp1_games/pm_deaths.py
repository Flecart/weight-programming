import sys, json; sys.path.insert(0, '.')
import numpy as np
from common import *
import pacman
net = Net('pacman')
kw = json.loads(sys.argv[1]); rng = np.random.default_rng(0)
cnt = {}; Vs = {}
for ep in range(300):
    e = Wrapped(pacman.Env(np.random.default_rng(ep), **kw)); e.reset()
    while True:
        o = e.obs(); z = net.logits(o[None])[0]; p = np.exp(z-z.max()); p/=p.sum()
        a = int(rng.choice(5, p=p)); pac0 = e.env.pac; g0 = list(e.env.ghosts)
        r, dn = e.step(a)
        if dn:
            if e.env.died:
                pac1 = e.env.pac; g1 = e.env.ghosts
                if pac1 in g0: kind = 'pac moved onto ghost cell' if pac1 != pac0 else 'stayed, ghost there?'
                elif pac1 == pac0: kind = 'pac stayed/blocked, ghost moved in'
                else:
                    dmin = min(abs(g[0]-pac0[0])+abs(g[1]-pac0[1]) for g in g0)
                    kind = 'pac moved, ghost moved onto it (pre-dist %d)' % dmin
                cnt[kind] = cnt.get(kind, 0) + 1; Vs.setdefault(kind, []).append(net.value(o[None])[0]); 
                Vs.setdefault(kind+' pA', []).append(p[a])
            break
for k, v in cnt.items(): print(k, v, 'V before %.2f' % np.mean(Vs[k]), 'p(chosen act) %.2f' % np.mean(Vs[k+' pA']))
