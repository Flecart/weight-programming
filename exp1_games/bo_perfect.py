"""Policy-independent part: return over 200 steps with a paddle that always catches (catch=flip-type rules)."""
import sys, itertools, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
def perfect(kw, n=64):
    R = []
    for s in range(n):
        e = Env(np.random.default_rng(s), **kw); e.reset(); tot = 0
        while True:
            # cheat: put paddle under landing column
            lx = e.x + e.dx
            if lx < 1 or lx > 8: lx = e.x - e.dx
            e.pos = min(max(lx - e.w // 2, 1), 9 - e.w)
            r, d = e.step(0); tot += r
            if d: break
        R.append(tot)
    return np.mean(R), np.std(R), len(set(R))
for sr, sc, sd, wall, brick, top in itertools.product([2,3,4,5,6], [(1,8), tuple(range(1,9))], ["inward_down","rand_down","rand"],
                                               ["reflect","clip"], ["minatar","reflect","reverse"], ["reflect","clip"]):
    kw = dict(start_row=sr, start_cols=sc, start_dir=sd, wall=wall, brick=brick, top=top, catch="flip")
    m, s, k = perfect(kw)
    if abs(m - 21.71) < 2.5: print(f"{m:6.2f} sd {s:4.2f} nvals {k}  sr{sr} cols{'edge' if len(sc)==2 else 'any'} {sd} wall {wall} brick {brick} top {top}")
