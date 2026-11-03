"""Implied reward r_hat = V(s) - 0.99 V(s') per event type, on-policy in a pong variant."""
import sys, json, numpy as np
sys.path.insert(0, '.')
import pong
from common import Net, Wrapped, choose
net = Net("pong")
def run(kw, n=150, seed=0):
    rng = np.random.default_rng(seed); ev = {}
    for ep in range(n):
        w = Wrapped(pong.Env(np.random.default_rng(1000 + ep), **kw), "zeros"); w.reset()
        while True:
            E = w.env; o = w.obs(); v = net.value(o[None])[0]
            bx, dx, by, dy = E.bx, E.dx, E.by, E.dy
            a = int(choose(net, o[None], "sample", rng)[0]); r, d = w.step(a)
            if r > 0: k = "opp_miss(+1)" + ("_terminal" if d else "")
            elif r < 0: k = "agent_miss(-1)"
            elif E.dx != dx and dx < 0: k = "agent_hit"
            elif E.dx != dx: k = "opp_hit"
            elif E.dy != dy: k = "wall"
            else: k = "free"
            v2 = 0.0 if (d and not E.truncated) else net.value(w.obs()[None])[0]
            ev.setdefault(k, []).append((v - 0.99 * v2, r))
            if d: break
    for k, l in sorted(ev.items()):
        l = np.array(l); print(f"  {k:15s} n={len(l):5d} implied r {l[:,0].mean():+.3f} (actual {l[:,1].mean():+.2f}) |err| {np.abs(l[:,0]-l[:,1]).mean():.3f}")
for line in sys.stdin:
    kw = json.loads(line); print(kw); run(kw)
