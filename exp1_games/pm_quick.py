import sys, json, itertools, time; sys.path.insert(0, '.')
import numpy as np
from common import *
import pacman
net = Net('pacman')
def q(kw, modes=("sample","random"), n_envs=32, n_steps=400, td=False):
    out = {}
    for m in modes:
        nn = n_envs*4 if m=="random" else n_envs
        e = evaluate(lambda rng: pacman.Env(rng, **kw), net, m, nn, n_steps if m!="random" else 150, seed=1, td=(td and m=="sample"))
        out[m] = e
    return out
if __name__ == "__main__":
    kws = json.loads(sys.argv[1])
    for kw in kws:
        t=time.time(); o = q(kw, td=True)
        s,r=o["sample"],o["random"]
        print(f"S {s['return']:6.2f} L {s['len']:5.1f} td {s['td_residual']:.3f} v0 {s['v0_mean']:.2f}/{s['disc_return0_mean']:.2f} | R {r['return']:5.2f} L {r['len']:5.1f} | act {s['action_usage']} {kw} ({time.time()-t:.0f}s)", flush=True)
