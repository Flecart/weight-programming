"""For a given state, rank candidate next states (ball cell, brick removed or not, reward) by the
policy-expected Bellman error of the critic."""
import sys, copy, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, Wrapped, choose
net = Net("breakout")
def rank(st, top=8, removable=None):
    o = st.obs()[None]; v = net.value(o)[0]; z = net.logits(o)[0]; p = np.exp(z - z.max()); p /= p.sum()
    e = st.env; out = []
    cand_bricks = [None] + [(r, c) for r in range(1, 4) for c in range(1, 9) if e.bricks[r, c] and abs(r - e.y) <= 1 and abs(c - e.x) <= 1]
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for b in cand_bricks:
                T = 0
                for a in range(5):
                    s2 = copy.deepcopy(st); E = s2.env; cur = s2._cur().copy(); E._move(a)
                    E.y, E.x = e.y + dy, e.x + dx
                    if not (1 <= E.x <= 8 and 1 <= E.y <= 7): T = None; break
                    rw = 0
                    if b: E.bricks[b] = False; rw = 1
                    if E.bricks[E.y, E.x]: T = None; break
                    s2.prev = cur
                    T += p[a] * (rw + 0.99 * net.value(s2.obs()[None])[0])
                if T is not None: out.append((abs(T - v), (dy, dx), b))
    out.sort(key=lambda t: t[0])
    return v, out[:top]
if __name__ == "__main__":
    kw = json.loads(sys.argv[2]); steps = [int(x) for x in sys.argv[3].split(",")]
    w = Wrapped(Env(np.random.default_rng(int(sys.argv[4]) if len(sys.argv) > 4 else 1), **kw), sys.argv[5] if len(sys.argv) > 5 else "zeros"); w.reset()
    rng = np.random.default_rng(0)
    for t in range(max(steps) + 1):
        if t in steps:
            v, out = rank(w)
            print(f"t{t} ball({w.env.y},{w.env.x}) d({w.env.dy:+d},{w.env.dx:+d}) V={v:.2f}: " + "; ".join(f"{d} brick{b} err{e:.2f}" for e, d, b in out))
        w.step(int(choose(net, w.obs()[None], "greedy", rng)[0]))
