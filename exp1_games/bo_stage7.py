"""Stage 7: collision rules without horizontal/vertical-only ball steps (the policy mis-tracks those), scored by
the trained sampled policy's survival/return and the critic TD residual."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout"); rows = []
grid = dict(brick=["back", "bounce", "reflect", "reverse", "minatar"], top=["reflect", "stay"],
            catch=["flip_stay", "bounce", "back", "edge_stay", "edge_bounce"], hit=["landing", "either"])
for vals in itertools.product(*grid.values()):
    kw = dict(zip(grid, vals)); kw.update(wall="reflect", width=3, pad0=3, start_row=4, start_cols=(1, 8), start_dir="inward_down")
    s = evaluate(lambda rng: Env(rng, **kw), net, "sample", n_envs=16, n_steps=400, seed=5, td=True)
    rows.append((s["td_residual"], s["return"], s["len"], kw)); print("td %.3f sample %.2f len %.1f | %s" % rows[-1], flush=True)
rows.sort(key=lambda t: t[0]); print("-----")
for r in rows[:15]: print("td %.3f sample %.2f len %.1f | %s" % r)
