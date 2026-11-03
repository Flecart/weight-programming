"""Per-event Bellman test of rule variants with the released critic.
For states s visited by the trained policy, the policy-expected one-step target
  T_v(s) = sum_a pi(a|s) [ r_v(s,a) + 0.99 V(s'_v(s,a)) (1-done) ]
is computed under each rule variant v (same state, different successor rule). The true rule should make
T_v(s) ~= V(s). Errors are grouped by the event the ball meets on that step."""
import sys, copy, json, itertools, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, Wrapped, choose
net = Net("breakout")
base = json.loads(sys.argv[2])
variants = json.loads(sys.argv[3])     # list of dicts overriding base
rng = np.random.default_rng(0)

def event(e):
    nx, ny = e.x + e.dx, e.y + e.dy
    if nx < 1 or nx > 8: return "side"
    if ny < 1: return "top"
    if e.bricks[ny, nx]: return "brick"
    if ny == 8: return "paddle_" + ("x" if e.x in e.cols() else "") + ("n" if nx in e.cols() else "") + ("miss" if e.x not in e.cols() and nx not in e.cols() else "")
    return "free"

states = []
for k in range(40):
    w = Wrapped(Env(np.random.default_rng(k), **base)); w.reset()
    while True:
        states.append(copy.deepcopy(w))
        a = int(choose(net, w.obs()[None], "sample", rng)[0])
        r, d = w.step(a)
        if d: break
print("states", len(states))
err = {}
for st in states:
    o = st.obs()[None]; v = net.value(o)[0]
    z = net.logits(o)[0]; p = np.exp(z - z.max()); p /= p.sum()
    ev = event(st.env)
    for vi, var in enumerate(variants):
        T = 0.0
        for a in range(5):
            s2 = copy.deepcopy(st); s2.env.__dict__.update(var)
            r, d = s2.step(a)
            T += p[a] * (r + (0 if (d and not s2.env.truncated) else 0.99 * net.value(s2.obs()[None])[0]))
        err.setdefault(ev, [[] for _ in variants])[vi].append(T - v)
for ev, L in sorted(err.items()):
    print(f"{ev:14s} n={len(L[0]):5d}  " + "  ".join(f"v{i}: |e| {np.mean(np.abs(x)):.3f} bias {np.mean(x):+.3f}" for i, x in enumerate(L)))
