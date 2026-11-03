"""Stage 6: fingerprint finalists x paddle details -> trained sampled return/len, TD residual, random stats."""
import sys, itertools, json, numpy as np
sys.path.insert(0, sys.argv[1])
from breakout import Env
from common import Net, evaluate
net = Net("breakout")
cands = json.load(open(sys.argv[1] + "/" + sys.argv[2]))
rows = []
for kw0 in cands:
    for hit, pad0 in itertools.product(["either", "landing", "below"], [3, 4]):
        kw = dict(kw0, start_cols=tuple(kw0["start_cols"]), hit=hit, pad0=pad0, width=3)
        mk = lambda rng: Env(rng, **kw)
        s = evaluate(mk, net, "sample", n_envs=16, n_steps=400, seed=5, td=True)
        if s["len"] < 150: continue
        r = evaluate(mk, net, "random", n_envs=64, n_steps=300, seed=6)
        rows.append((s["td_residual"], s["return"], s["len"], r["return"], r["len"], kw))
        print("td %.3f sample %.2f len %.1f | random %.2f len %.2f | %s" % rows[-1], flush=True)
rows.sort(key=lambda t: t[0])
print("-----")
for r in rows[:15]: print("td %.3f sample %.2f len %.1f | random %.2f len %.2f | %s" % r)
json.dump([r[-1] for r in rows[:15]], open(sys.argv[1] + "/bo_stage6.json", "w"))
