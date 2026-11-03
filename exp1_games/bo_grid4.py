"""Stage 4: trained greedy+sampled policy over the collision-rule grid suggested by the critic event probe."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout")
rows = []
grid = dict(brick=["minatar", "back", "bounce", "reflect"], top=["reflect", "clip", "stay"], wall=["reflect", "clip", "back"],
            catch=["flip_stay", "flip", "bounce"], hit=["either", "landing"])
for vals in itertools.product(*grid.values()):
    kw = dict(zip(grid, vals)); kw.update(width=3, pad0=3, start_row=4, start_cols=(1, 8), start_dir="inward_down")
    g = evaluate(lambda rng: Env(rng, **kw), net, "greedy", n_envs=8, n_steps=400, seed=1)
    s = evaluate(lambda rng: Env(rng, **kw), net, "sample", n_envs=16, n_steps=400, seed=2)
    rows.append((s["return"], s["len"], g["return"], g["len"], kw)); print("sample %.2f len %.1f | greedy %.2f len %.1f | %s" % rows[-1], flush=True)
rows.sort(key=lambda t: -t[1] - t[0] / 10)
print("-----")
for r in rows[:15]: print("sample %.2f len %.1f | greedy %.2f len %.1f | %s" % r)
