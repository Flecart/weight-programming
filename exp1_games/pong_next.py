"""Rank candidate next states for Pong by policy-expected Bellman error of the critic."""
import sys, copy, json, numpy as np
sys.path.insert(0, '.')
import pong
from common import Net, Wrapped, choose
net = Net("pong")
def rank(st, top=6):
    o = st.obs()[None]; v = net.value(o)[0]; z = net.logits(o)[0]; p = np.exp(z - z.max()); p /= p.sum()
    e = st.env; out = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for do in (-1, 0, 1):
                for rw in (0.0,):
                    T = 0; ok = True
                    for a in range(5):
                        s2 = copy.deepcopy(st); E = s2.env; cur = s2._cur().copy()
                        if a == 1: E.py = max(1, E.py - 1)
                        elif a == 2: E.py = min(9 - E.L, E.py + 1)
                        E.by, E.bx = e.by + dy, e.bx + dx; E.oy = e.oy + do
                        if not (1 <= E.by <= 8 and 2 <= E.bx <= E.right_col and 1 <= E.oy <= 9 - E.Lo): ok = False; break
                        s2.prev = cur
                        T += p[a] * (rw + 0.99 * net.value(s2.obs()[None])[0])
                    if ok: out.append((abs(T - v), (dy, dx), do))
    out.sort(key=lambda t: t[0])
    return v, out[:top]
if __name__ == "__main__":
    kw = json.loads(sys.argv[1]); n = int(sys.argv[2])
    w = Wrapped(pong.Env(np.random.default_rng(int(sys.argv[3])), **kw), "zeros"); w.reset()
    rng = np.random.default_rng(0)
    for t in range(n):
        v, out = rank(w); E = w.env
        print(f"t{t} ball({E.by},{E.bx}) d({E.dy:+d},{E.dx:+d}) pad{E.py} opp{E.oy} V={v:.2f}: " + "; ".join(f"{d} o{o:+d} {er:.3f}" for er, d, o in out))
        r, d = w.step(int(choose(net, w.obs()[None], "sample", rng)[0]))
        if r: print("   reward", r)
        if d: break
