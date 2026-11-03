"""Stage 8: axis-separated physics variants: trained sampled policy + TD residual (prev0=same)."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout"); rows = []
grid = dict(wall_stay=[False, True], brick_stay=[True, False], pad_stay=[True, False], diag=["dy", "both"], horiz=[True, False],
            catch=["flip_stay", "edge_stay"], hit=["either", "landing"])
for vals in itertools.product(*grid.values()):
    kw = dict(zip(grid, vals)); kw.update(physics="axis", width=3, pad0=3, start_row=4, start_cols=(1, 8), start_dir="inward_down")
    s = evaluate(lambda rng: Env(rng, **kw), net, "sample", n_envs=16, n_steps=400, seed=5, prev0="same", td=True)
    rows.append((s["td_residual"], s["return"], s["len"], kw))
rows.sort(key=lambda t: t[0])
for r in rows[:20]: print("td %.3f sample %.2f len %.1f | %s" % r)
