import sys, json; sys.path.insert(0, '.')
import numpy as np
from common import *
import pacman
net = Net('pacman')
kw = json.loads(sys.argv[1]) if len(sys.argv)>1 else {}
res=[]
for s in pacman.OPEN:
    e = evaluate(lambda rng: pacman.Env(rng, pac_start=list(s), **kw), net, "sample", 16, 300, seed=2)
    res.append((e['return'], e['len'], s))
    full=np.zeros((10,10),bool)
grid=np.full((10,10),np.nan)
for R,L,s in res: grid[s]=R
np.set_printoptions(precision=0, suppress=True, linewidth=150)
print(grid[1:9,1:9])
for R,L,s in sorted(res,reverse=True)[:6]: print(s, round(R,1), round(L,1))
