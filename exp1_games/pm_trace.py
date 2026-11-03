import sys, json; sys.path.insert(0, '.')
import numpy as np
from common import *
import pacman
net = Net('pacman')
kw = json.loads(sys.argv[1]); rng = np.random.default_rng(int(sys.argv[2]))
e = Wrapped(pacman.Env(np.random.default_rng(int(sys.argv[2])), **kw)); e.reset()
def show():
    g = [['#' if pacman.WALLS[r,c] else ('.' if e.env.pellets[r,c] else ' ') for c in range(10)] for r in range(10)]
    for gg in e.env.ghosts: g[gg[0]][gg[1]] = 'G'
    g[e.env.pac[0]][e.env.pac[1]] = 'P'
    return [''.join(x) for x in g]
hist=[]
while True:
    z = net.logits(e.obs()[None])[0]; p=np.exp(z-z.max()); p/=p.sum()
    a = int(rng.choice(5, p=p)); v = net.value(e.obs()[None])[0]
    hist.append((show(), a, np.round(p,2), v))
    r, d = e.step(a)
    if d: break
print('len', e.env.t, 'pellets left', e.env.pellets.sum())
for s,a,p,v in hist[-5:]:
    print('act', '0^v<>'[a], p, 'V %.1f'%v)
    print('\n'.join(s[1:9]))
print('\n'.join(show()))
