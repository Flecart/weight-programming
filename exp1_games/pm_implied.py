"""Critic-implied reward per event type: E[V(s) - 0.99 V(s') (1-term)] grouped by what happened."""
import sys, json; sys.path.insert(0, '.')
import numpy as np
from common import *
import pacman
net = Net('pacman')
kw = json.loads(sys.argv[1]); rng = np.random.default_rng(0)
envs = [Wrapped(pacman.Env(np.random.default_rng(i), **kw)) for i in range(64)]
for e in envs: e.reset()
G = {}
O = np.stack([e.obs() for e in envs]); V = net.value(O)
for t in range(500):
    A = choose(net, O, "sample", rng)
    info = []
    for e, a in zip(envs, A):
        ate0, cl0 = e.env.ate, e.env.clears
        r, d = e.step(int(a))
        ev = 'death' if (d and e.env.died) else ('clear' if e.env.clears > cl0 else ('pellet' if e.env.ate > ate0 else ('trunc' if d else 'none')))
        info.append((ev, d and not e.env.truncated, d))
    O2 = np.stack([e.obs() for e in envs]); V2 = net.value(O2)
    for i, (ev, term, d) in enumerate(info):
        if ev == 'trunc': continue
        G.setdefault(ev, []).append(V[i] - GAMMA * V2[i] * (1 - term))
        if d: envs[i].reset(); O2[i] = envs[i].obs()
    O = O2; V = net.value(O)
for k, v in G.items(): print(k, 'n', len(v), 'implied reward mean %.3f sd %.3f' % (np.mean(v), np.std(v)))
