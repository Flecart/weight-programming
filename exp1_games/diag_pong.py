import sys, json; sys.path.insert(0,'.')
from common import *; import pong
net=Net('pong')
def diag(kw, mode, n=300, seed=0):
    rng=np.random.default_rng(seed); st=dict(ahit=0,amiss=0,ohit=0,omiss=0); T=[];R=[]
    for ep in range(n):
        e=Wrapped(pong.Env(np.random.default_rng(seed*1000+ep),**kw)); e.reset(); tot=0
        while True:
            E=e.env; dx=E.dx; bx=E.bx
            a=int(choose(net,e.obs()[None],mode,rng)[0]); r,d=e.step(a); tot+=r
            if r<0: st['amiss']+=1
            elif r>0: st['omiss']+=1
            elif dx<0 and bx==2: st['ahit']+=1
            elif dx>0 and bx==E.right_col: st['ohit']+=1
            if d: break
        T.append(E.t); R.append(tot)
    p=st['ahit']/max(1,st['ahit']+st['amiss']); q=st['ohit']/max(1,st['ohit']+st['omiss'])
    return dict(ret=np.mean(R), len=np.mean(T), p_agent=round(p,3), q_opp=round(q,3))
if __name__=="__main__":
    kw=json.loads(sys.argv[1])
    for m in ('sample','random'): print(m, diag(kw,m))
