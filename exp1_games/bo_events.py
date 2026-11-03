"""Event probe: for each event type, which next ball cell (relative to incoming direction) best satisfies the
policy-expected Bellman equation of the released critic. Also tests 'terminal -1' for paddle approaches."""
import sys, copy, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, Wrapped, choose
net = Net("breakout"); rng = np.random.default_rng(0)
base = json.loads(sys.argv[2])
def event(e):
    nx, ny = e.x + e.dx, e.y + e.dy
    s = []
    if nx < 1 or nx > 8: s.append("side")
    if ny < 1: s.append("top")
    if 1 <= nx <= 8 and 1 <= ny and e.bricks[ny, nx]: s.append("brick")
    if ny == 8:
        s.append("pad_" + ("x" if e.x in e.cols() else "") + ("n" if 1 <= nx <= 8 and nx in e.cols() else ""))
    return "+".join(s) or "free"
states = []
for k in range(60):
    w = Wrapped(Env(np.random.default_rng(k), **base)); w.reset()
    while True:
        if event(w.env) != "free": states.append(copy.deepcopy(w))
        r, d = w.step(int(choose(net, w.obs()[None], "sample", rng)[0]))
        if d: break
res = {}
for st in states:
    o = st.obs()[None]; v = net.value(o)[0]
    z = net.logits(o)[0]; p = np.exp(z - z.max()); p /= p.sum()
    e = st.env; ev = event(e); nx, ny = e.x + e.dx, e.y + e.dy
    brick = "brick" in ev
    opts = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)] + ["terminal"]
    for opt in opts:
        T = 0
        for a in range(5):
            s2 = copy.deepcopy(st); E = s2.env; cur = s2._cur().copy(); E._move(a); rwd = 0.0
            if brick: E.bricks[ny, nx] = False; rwd = 1.0
            if opt == "terminal": T += p[a] * (rwd - 1.0); continue
            E.y = e.y + opt[0] * e.dy; E.x = e.x + opt[1] * e.dx
            if not (1 <= E.x <= 8 and 1 <= E.y <= 7) or E.bricks[E.y, E.x]: T = np.nan; break
            s2.prev = cur
            T += p[a] * (rwd + 0.99 * net.value(s2.obs()[None])[0])
        res.setdefault(ev, {}).setdefault(opt, []).append(T - v)
for ev, d in sorted(res.items(), key=lambda t: -len(next(iter(t[1].values())))):
    n = len(next(iter(d.values())))
    rows = sorted((np.nanmean(np.abs(x)), np.nanmean(x), np.mean(np.isfinite(x)), k) for k, x in d.items() if np.mean(np.isfinite(x)) > 0.5)
    print(f"{ev:18s} n={n:4d} " + " | ".join(f"{str(k):8s} {m:.2f}({b:+.2f},{f:.0%})" for m, b, f, k in rows[:5]))
