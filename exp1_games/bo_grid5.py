"""Stage 5: with brick=back / wall=reflect, scan start states and top/catch rules: always-catch return
(target 21.71, sd 1.11), random-policy stats (target -0.40 / 7.84), then trained sampled policy."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout")
def perfect(kw, n=96):
    R = []
    for s in range(n):
        e = Env(np.random.default_rng(s), **kw); e.reset(); e.w = 8; e.pos = 1; tot = 0
        while True:
            r, d = e.step(0); tot += r
            if d: break
        R.append(tot)
    return float(np.mean(R)), float(np.std(R))
def rand_stats(kw, n=1500):
    rng = np.random.default_rng(1); R = []; L = []; e = Env(rng, **kw)
    for _ in range(n):
        e.reset(); tot = 0
        while True:
            r, d = e.step(int(rng.integers(5))); tot += r
            if d: break
        R.append(tot); L.append(e.t)
    return float(np.mean(R)), float(np.mean(L))
rows = []
for sr, sc, sd, top, catch in itertools.product([3, 4, 5, 6, 7], ["edge", "any", "mid"], ["inward_down", "rand_down", "rand", "inward_up"],
                                               ["clip", "reflect", "stay"], ["flip_stay", "bounce"]):
    cols = {"edge": (1, 8), "any": tuple(range(1, 9)), "mid": (4, 5)}[sc]
    kw = dict(brick="back", wall="reflect", top=top, catch=catch, hit="either", width=3, pad0=3, start_row=sr, start_cols=cols, start_dir=sd)
    if sr <= 3 and sd != "inward_up" and False: continue
    m, s = perfect(kw)
    if abs(m - 21.71) > 1.5: continue
    for pad0, hit in itertools.product([3, 4, "rand"], ["either", "landing", "below"]):
        k2 = dict(kw, pad0=pad0, hit=hit)
        R, L = rand_stats(k2)
        sc_ = abs(m - 21.71) + abs(s - 1.11) + 3 * abs(R + 0.40) + abs(L - 7.84) / 2
        rows.append((sc_, m, s, R, L, k2))
rows.sort(key=lambda t: t[0])
for r in rows[:25]: print("score %.2f perfect %.2f sd %.2f | random %.2f len %.2f | %s" % r, flush=True)
json.dump([r[-1] for r in rows[:25]], open(sys.argv[1] + "/bo_stage5.json", "w"))
