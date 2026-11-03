import sys, json; sys.path.insert(0,'.')
from common import *; import pong
net=Net('pong')
def calib(kw, n=200, seed=0):
    rng=np.random.default_rng(seed); Vs=[];Gs=[]
    for ep in range(n):
        e=Wrapped(pong.Env(np.random.default_rng(seed*1000+ep),**kw)); e.reset(); obs=[];rs=[]
        while True:
            o=e.obs(); obs.append(o); a=int(choose(net,o[None],'sample',rng)[0]); r,d=e.step(a); rs.append(r)
            if d: break
        G=0; g=[]
        for r in rs[::-1]: G=r+0.99*G; g.append(G)
        Gs+=g[::-1]; Vs+=list(net.value(np.stack(obs)))
    Vs=np.array(Vs); Gs=np.array(Gs)
    return dict(meanV=Vs.mean(), meanG=Gs.mean(), mae=np.abs(Vs-Gs).mean())
for line in sys.stdin:
    kw=json.loads(line); print({k:round(float(v),3) for k,v in calib(kw).items()}, kw, flush=True)
