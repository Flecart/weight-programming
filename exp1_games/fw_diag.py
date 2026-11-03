import sys; sys.path.insert(0,'.')
from common import *
from freeway import Env
import numpy as np, collections
net=Net('freeway'); rng=np.random.default_rng(0)
e=Wrapped(Env(rng, collision="none"),'zeros'); e.reset()
hits=collections.Counter(); exp=collections.Counter()
for t in range(40000):
    o=e.obs(); a=int(choose(net,o[None],'sample',rng)[0]); r,d=e.step(a)
    env=e.env
    if 2<=env.ay<=7:
        i=env.ay-2; key=(env.ay,int(env.dir[i]),int(env.spd[i]))
        exp[key]+=1
        if env.cars()[env.ay,env.ax]: hits[key]+=1
    if d: e.reset()
for k in sorted(exp): print(k, exp[k], round(hits[k]/exp[k],3))
