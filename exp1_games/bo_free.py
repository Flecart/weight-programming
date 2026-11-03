"""Free-flight probe: for states where the ball is in open space, which ball displacement (and paddle timing)
makes the policy-expected critic target match V(s)?"""
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
        if 1 <= nx <= 8 and 1 <= ny <= 7 and not e.bricks[ny, nx] and 2 <= e.y <= 6: states.append(copy.deepcopy(w))
        r, d = w.step(int(choose(net, w.obs()[None], "sample", rng)[0]))
        if d: break
print(len(states), "free states")
res = {}
for st in states[:600]:
    o = st.obs()[None]; v = net.value(o)[0]
    z = net.logits(o)[0]; p = np.exp(z - z.max()); p /= p.sum()
    e = st.env
    for mdy in (-2, -1, 0, 1, 2):
        for mdx in (-2, -1, 0, 1, 2):
            for prevmode in ("movers", "none", "ball_only"):
                T = 0
                for a in range(5):
                    s2 = copy.deepcopy(st); E = s2.env
                    cur = (s2._cur()).copy()
                    E._move(a)
                    E.x = min(max(e.x + mdx, 1), 8); E.y = min(max(e.y + mdy, 1), 7)
                    if prevmode == "movers": s2.prev = cur
                    elif prevmode == "none": s2.prev = np.zeros((10, 10), bool)
                    else: s2.prev = np.zeros((10, 10), bool); s2.prev[e.y, e.x] = True
                    T += p[a] * 0.99 * net.value(s2.obs()[None])[0]
                key = (mdy * e.dy, mdx * e.dx, prevmode)   # displacement relative to the ball's direction
                res.setdefault(key, []).append(T - v)
rows = sorted(((np.mean(np.abs(x)), np.mean(x), k) for k, x in res.items()))
for r in rows[:12]: print("|e| %.3f bias %+.3f  rel-displacement(dy,dx),prev=%s" % (r[0], r[1], r[2]))
