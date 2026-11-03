"""Stage 12: start-set refinement with hit=landing and a 1-step serve pause (return spread: ref sd 1.11)."""
import sys, itertools, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout")
PHYS = dict(physics="axis", wall_stay=False, brick_stay=True, pad_stay=True, diag="dy", horiz=False, catch="edge_stay", width=3, hit="landing", start_row=6)
for cols, sd, pad0, pause in itertools.product([(1, 8), tuple(range(1, 9)), (1, 2, 7, 8)], ["inward_down", "rand_down"], [3, (3, 4), (2, 3, 4)], [1]):
    kw = dict(PHYS, start_cols=cols, start_dir=sd, pad0=pad0, pause=pause); mk = lambda rng: Env(rng, **kw)
    r = evaluate(mk, net, "random", 256, 400, 6, "same"); s = evaluate(mk, net, "sample", 64, 400, 5, "same", td=True)
    print("td %.3f sample %.2f se %.3f len %.1f | random %.3f len %.2f | cols %s %s pad0 %s" % (s["td_residual"], s["return"], s["return_se"], s["len"], r["return"], r["len"], cols, sd, pad0), flush=True)
