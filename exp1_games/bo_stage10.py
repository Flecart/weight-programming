"""Stage 10: finer start-state / hit-rule search under the axis physics (random stats weigh heavily)."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout"); rows = []
PHYS = dict(physics="axis", wall_stay=False, brick_stay=True, pad_stay=True, diag="dy", horiz=False, catch="edge_stay", width=3)
colsets = {"edge": (1, 8), "any": tuple(range(1, 9)), "in2": (2, 7), "mid": (4, 5), "edge2": (1, 2, 7, 8)}
for sr, sc, sd, pad0, hit in itertools.product([5, 6, 7], colsets, ["inward_down", "rand_down", "inward_up", "rand"], [2, 3, 4], ["either", "landing", "below"]):
    kw = dict(PHYS, start_row=sr, start_cols=colsets[sc], start_dir=sd, pad0=pad0, hit=hit)
    mk = lambda rng: Env(rng, **kw)
    r = evaluate(mk, net, "random", n_envs=64, n_steps=300, seed=6, prev0="same")
    if abs(r["return"] + 0.40) > 0.12 or abs(r["len"] - 7.84) > 1.0: continue
    s = evaluate(mk, net, "sample", n_envs=32, n_steps=400, seed=5, prev0="same", td=True)
    sc_ = abs(s["return"] - 21.71) / 2 + abs(r["return"] + 0.40) * 3 + abs(r["len"] - 7.84) / 2 + s["td_residual"] * 10 + (200 - s["len"]) / 10
    rows.append((sc_, s["td_residual"], s["return"], s["len"], r["return"], r["len"], sr, sc, sd, pad0, hit))
    print("score %.2f td %.3f sample %.2f len %.1f | random %.2f len %.2f | sr %s cols %s dir %s pad0 %s hit %s" % rows[-1], flush=True)
rows.sort(key=lambda t: t[0]); print("-----")
for r in rows[:15]: print("score %.2f td %.3f sample %.2f len %.1f | random %.2f len %.2f | sr %s cols %s dir %s pad0 %s hit %s" % r)
