"""Ball-visitation fingerprint. Because the reference ball path is policy independent, the set of cells the ball
ever occupies is a property of the rules. Cells the ball never visits keep init-scale weights in the moving-object
channel (max|W1| ~0.1-0.2). Compare each variant's visitation (always-catching paddle, all starts) with the
ch1 weight map, plus the always-catch return (ref 21.71, sd 1.11)."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import weight_maps
W = weight_maps("breakout")[1]
vis_ref = W[1:8, 1:9] > 0.5          # cells with clearly trained weights
def perfect(kw, n=64):
    R = []; V = np.zeros((10, 10))
    for s in range(n):
        e = Env(np.random.default_rng(s), **kw); e.reset(); e.w = 8; e.pos = 1; tot = 0
        V[e.y, e.x] += 1
        while True:
            r, d = e.step(0); tot += r; V[e.y, e.x] += 1
            if d: break
        R.append(tot)
    return float(np.mean(R)), float(np.std(R)), V
if __name__ == "__main__":
    rows = []
    grid = dict(brick=["minatar", "back", "bounce", "reflect", "reverse"], top=["clip", "reflect", "stay"], wall=["reflect", "clip", "stay"],
                catch=["flip_stay", "flip", "bounce"], start_row=[3, 4, 5, 6, 7], start_cols=["edge", "any"], start_dir=["inward_down", "rand", "rand_down"])
    for vals in itertools.product(*grid.values()):
        kw = dict(zip(grid, vals)); kw["start_cols"] = (1, 8) if kw["start_cols"] == "edge" else tuple(range(1, 9))
        try: m, s, V = perfect(kw, 48)
        except IndexError: continue
        v = V[1:8, 1:9] > 0
        mism = int((v != vis_ref).sum())
        rows.append((mism + abs(m - 21.71) + abs(s - 1.11), mism, m, s, kw))
    rows.sort(key=lambda t: t[0])
    for r in rows[:25]: print("score %.2f mismatched cells %d | perfect %.2f sd %.2f | %s" % r)
    json.dump([r[-1] for r in rows[:40]], open(sys.argv[1] + "/bo_fp.json", "w"))
