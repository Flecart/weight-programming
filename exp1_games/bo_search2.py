"""Stage 2: for the stage-1 geometries, random-policy length/return (ref len 7.84, return -0.40)."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
geo = json.load(open(sys.argv[1] + "/bo_stage1.json"))[:40]
def rand_stats(kw, n=1500):
    rng = np.random.default_rng(1); R = []; L = []
    e = Env(rng, **kw)
    for _ in range(n):
        e.reset(); tot = 0
        while True:
            r, d = e.step(int(rng.integers(5))); tot += r
            if d: break
        R.append(tot); L.append(e.t)
    return np.mean(R), np.mean(L)
out = []
for (m, s, g), w, pad0, hit, order in itertools.product(geo, [1, 2, 3], ["center", "rand"], ["landing", "below", "either"], ["paddle_first", "ball_first"]):
    kw = dict(g); kw["start_cols"] = tuple(kw["start_cols"])
    kw.update(width=w, pad0=(9 - w) // 2 if pad0 == "center" else "rand", hit=hit, order=order)
    R, L = rand_stats(kw)
    out.append((abs(R + 0.40) * 3 + abs(L - 7.84) / 2 + abs(m - 21.71) + abs(s - 1.11), m, s, R, L, kw))
out.sort(key=lambda t: t[0])
for o in out[:30]: print("score %.2f perfect %.2f sd %.2f | random ret %.2f len %.2f | %s" % o)
json.dump([o[-1] for o in out[:40]], open(sys.argv[1] + "/bo_stage2.json", "w"))
