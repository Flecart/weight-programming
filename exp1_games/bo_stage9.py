"""Stage 9: start-state variants under the axis physics found in stage 8."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout"); rows = []
PHYS = dict(physics="axis", wall_stay=False, brick_stay=True, pad_stay=True, diag="dy", horiz=False, catch="edge_stay", hit="either", width=3)
for sr, sc, sd, pad0 in itertools.product([3, 4, 5, 6], ["edge", "any"], ["inward_down", "rand_down", "rand"], [3, 4, "rand"]):
    kw = dict(PHYS, start_row=sr, start_cols=(1, 8) if sc == "edge" else tuple(range(1, 9)), start_dir=sd, pad0=pad0)
    mk = lambda rng: Env(rng, **kw)
    s = evaluate(mk, net, "sample", n_envs=32, n_steps=400, seed=5, prev0="same", td=True)
    r = evaluate(mk, net, "random", n_envs=64, n_steps=400, seed=6, prev0="same")
    sc_ = abs(s["return"] - 21.71) / 2 + abs(r["return"] + 0.40) * 3 + abs(r["len"] - 7.84) / 2 + s["td_residual"] * 10
    rows.append((sc_, s["td_residual"], s["return"], s["len"], r["return"], r["len"], kw))
rows.sort(key=lambda t: t[0])
for r in rows[:15]: print("score %.2f td %.3f sample %.2f len %.1f | random %.2f len %.2f | sr %s cols %s dir %s pad0 %s" % (r[:6] + (r[6]["start_row"], len(r[6]["start_cols"]), r[6]["start_dir"], r[6]["pad0"])))
