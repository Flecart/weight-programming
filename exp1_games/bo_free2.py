"""Free-flight probe 2: paddle step size / action mapping, using the policy-expected Bellman target."""
import sys, copy, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, Wrapped, choose
net = Net("breakout"); rng = np.random.default_rng(0)
base = json.loads(sys.argv[2])
states = []
for k in range(30):
    w = Wrapped(Env(np.random.default_rng(k), **base)); w.reset()
    while True:
        e = w.env; nx, ny = e.x + e.dx, e.y + e.dy
        if 1 <= nx <= 8 and 1 <= ny <= 7 and not e.bricks[ny, nx]: states.append(copy.deepcopy(w))
        r, d = w.step(int(choose(net, w.obs()[None], "sample", rng)[0]))
        if d: break
states = states[:500]
maps = {"step1": {3: -1, 4: 1}, "step2": {3: -2, 4: 2}, "swapLR": {3: 1, 4: -1}, "updown_too": {3: -1, 4: 1, 1: -1, 2: 1}, "nomove": {}}
for name, mp in maps.items():
    errs = []
    for st in states:
        o = st.obs()[None]; v = net.value(o)[0]; z = net.logits(o)[0]; p = np.exp(z - z.max()); p /= p.sum()
        T = 0
        for a in range(5):
            s2 = copy.deepcopy(st); E = s2.env; cur = s2._cur().copy()
            E.pos = min(max(E.pos + mp.get(a, 0), 1), 9 - E.w)
            E.x += E.dx; E.y += E.dy; s2.prev = cur
            T += p[a] * 0.99 * net.value(s2.obs()[None])[0]
        errs.append(T - v)
    print(f"{name:12s} |e| {np.mean(np.abs(errs)):.3f} bias {np.mean(errs):+.3f} median|e| {np.median(np.abs(errs)):.3f}")
