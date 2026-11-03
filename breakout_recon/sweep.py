import sys, itertools, numpy as np
sys.path.insert(0, sys.argv[2])
from breakout import Breakout, Policy, run
pol = Policy(sys.argv[1]); rng = np.random.default_rng(1)
def sample(o):
    z = pol.logits(o); p = np.exp(z - z.max()); return rng.choice(5, p=p / p.sum())
rand = lambda o: int(rng.integers(5))
rows = []
for w, sr, sc, ed in itertools.product([2, 3, 4], [2, 3, 4, 5], ["edge", "any"], [True, False]):
    env = Breakout(rng, start_row=sr, start_cols=sc, width=w, edge_deflect=ed)
    s = run(env, sample, 60); rr = run(env, rand, 600)
    rows.append((s[0], w, sr, sc, ed, s[2], rr[0], rr[2]))
for r in sorted(rows, reverse=True)[:12]:
    print("ret %6.2f  width %d start_row %d cols %-4s deflect %-5s len %5.1f | random ret %5.2f len %4.1f" % r)
