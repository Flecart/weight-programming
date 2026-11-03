"""Stage 11: small paddle-start / ball-start sets around the stage-9 winner."""
import sys, itertools, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout")
PHYS = dict(physics="axis", wall_stay=False, brick_stay=True, pad_stay=True, diag="dy", horiz=False, catch="edge_stay", width=3)
for sr, cols, sd, pad0, hit in itertools.product([5, 6], [(1, 8), (1, 2, 7, 8), (2, 7)], ["inward_down", "rand_down"], [3, (3, 4), (2, 3, 4)], ["either", "landing"]):
    kw = dict(PHYS, start_row=sr, start_cols=cols, start_dir=sd, pad0=pad0, hit=hit); mk = lambda rng: Env(rng, **kw)
    r = evaluate(mk, net, "random", n_envs=128, n_steps=300, seed=6, prev0="same")
    s = evaluate(mk, net, "sample", n_envs=32, n_steps=400, seed=5, prev0="same", td=True)
    print("td %.3f sample %.2f len %.1f | random %.2f len %.2f | sr %s cols %s %s pad0 %s hit %s" % (s["td_residual"], s["return"], s["len"], r["return"], r["len"], sr, cols, sd, pad0, hit), flush=True)
