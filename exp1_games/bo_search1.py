"""Stage 1 of the Breakout search: the trained policy never loses and its sampled and greedy returns are
identical in the reference (21.71, se .031 -> sd 1.11), so with a flip-only catch the ball path is policy
independent. Score each geometry variant by the return of an always-catching paddle (n starts)."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
def perfect(kw, n=128):
    R = []
    for s in range(n):
        e = Env(np.random.default_rng(s), **kw); e.width = 8; e.reset(); e.w = 8; e.pos = 1; tot = 0
        while True:
            r, d = e.step(0); tot += r
            if d: break
        R.append(tot)
    return float(np.mean(R)), float(np.std(R))
out = []
for sr, sc, sd, wall, brick, top, catch in itertools.product([2,3,4,5,6,7], ["edge","any","mid"], ["inward_down","rand_down","rand","inward_up"],
        ["reflect","clip"], ["minatar","reflect","reverse"], ["reflect","clip"], ["flip","flip_stay"]):
    cols = {"edge": (1, 8), "any": tuple(range(1, 9)), "mid": (4, 5)}[sc]
    kw = dict(start_row=sr, start_cols=cols, start_dir=sd, wall=wall, brick=brick, top=top, catch=catch)
    m, s = perfect(kw)
    out.append((abs(m - 21.71) + abs(s - 1.11), m, s, kw))
out.sort(key=lambda t: t[0])
for o in out[:25]: print(f"{o[1]:6.2f} sd {o[2]:4.2f}  {o[3]}")
json.dump([[o[1], o[2], o[3]] for o in out[:60]], open(sys.argv[1] + "/bo_stage1.json", "w"))
