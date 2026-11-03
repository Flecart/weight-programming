"""Stage 3: trained-policy check (sampled actions) + critic TD residual for stage-2 finalists and prev0 variants."""
import sys, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout")
cands = json.load(open(sys.argv[1] + "/bo_stage2.json"))
extra = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
rows = []
for kw in cands + extra:
    kw["start_cols"] = tuple(kw["start_cols"])
    for prev0 in ("zeros", "same"):
        s = evaluate(lambda rng: Env(rng, **kw), net, "sample", n_envs=32, n_steps=400, seed=5, prev0=prev0, td=True)
        rows.append((s["td_residual"], s["return"], s["len"], prev0, kw))
        print("td %.3f  sample ret %6.2f len %5.1f prev0 %s  %s" % rows[-1], flush=True)
rows.sort(key=lambda t: t[0])
print("---- sorted by td residual")
for r in rows[:15]: print("td %.3f  sample ret %6.2f len %5.1f prev0 %s  %s" % r)
json.dump([[r[0], r[1], r[2], r[3], r[4]] for r in rows], open(sys.argv[1] + "/bo_stage3.json", "w"))
