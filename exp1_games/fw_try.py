import sys, json; sys.path.insert(0, sys.argv[1])
from common import *
from freeway import Env
net = Net("freeway")
variants = json.loads(sys.argv[2])
for kw in variants:
    mk = lambda rng: Env(rng, **kw)
    s = evaluate(mk, net, "sample", 32, 400, 0, td=True)
    r = evaluate(mk, net, "random", 32, 400, 2)
    print(f"{json.dumps(kw):90s} S {s['return']:6.2f} td {s['td_residual']:.3f} v0 {s['v0_mean']:.2f}/{s['disc_return0_mean']:.2f} R {r['return']:.3f} use {s['action_usage']}", flush=True)
