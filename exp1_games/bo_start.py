"""Start-state probe: for each candidate start (ball row/col/direction, paddle position, prev=copy), the
critic's V(s0) vs the empirical discounted return from it (trained sampled policy, axis physics), plus the
one-step policy-expected Bellman error. In-distribution starts should agree on both."""
import sys, itertools, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, Wrapped, choose
net = Net("breakout"); rng = np.random.default_rng(0)
PHYS = dict(physics="axis", wall_stay=False, brick_stay=True, pad_stay=True, diag="dy", horiz=False, catch="edge_stay", width=3, hit="either")
rows = []
for y, x, dy, dx, pos in itertools.product([4, 5, 6, 7], range(1, 9), [1, -1], [1, -1], [3, 4]):
    G = []; V0 = None
    for k in range(6):
        e = Env(np.random.default_rng(k), **PHYS); w = Wrapped(e, "same"); e.reset()
        e.y, e.x, e.dy, e.dx, e.pos = y, x, dy, dx, pos; w.prev = w._cur().copy()
        if V0 is None: V0 = net.value(w.obs()[None])[0]
        g = 0; t = 0
        while True:
            r, d = w.step(int(choose(net, w.obs()[None], "sample", rng)[0])); g += 0.99 ** t * r; t += 1
            if d: break
        G.append(g)
    rows.append((abs(V0 - np.mean(G)), V0, np.mean(G), y, x, dy, dx, pos))
rows.sort()
for r in rows[:30]: print("|V-G| %.2f V0 %.2f G %.2f  ball(%d,%d) d(%+d,%+d) pad%d" % r)
