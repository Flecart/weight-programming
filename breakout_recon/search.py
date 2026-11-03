"""Search Breakout rule variants; score = trained policy's greedy return/length (true env -> ~21.7, never loses)."""
import sys, itertools, numpy as np
sys.path.insert(0, sys.argv[2])
from breakout import Policy
pol = Policy(sys.argv[1])
W1,b1,W2,b2,W3,b3 = pol.p

class Env:
    def __init__(s, rng, wall="clip", catch="minatar", width=1, start_row=3, start_col="edge", pad0="4",
                 prev0="same", order="paddle_first"):
        s.rng=rng; s.wall=wall; s.catch=catch; s.w=width; s.sr=start_row; s.sc=start_col; s.pad0=pad0; s.prev0=prev0; s.order=order
    def cols(s): return range(s.pos, s.pos+s.w)
    def movers(s):
        m=np.zeros((10,10),bool); m[8,list(s.cols())]=True; m[s.y,s.x]=True; return m
    def reset(s):
        s.y=s.sr
        if s.sc=="edge":
            s.x=[1,8][int(s.rng.integers(2))]; s.dx=1 if s.x==1 else -1
        else:
            s.x=int(s.rng.integers(1,9)); s.dx=int(s.rng.choice([-1,1]))
        s.dy=1
        s.pos={"4":4,"center":(9-s.w)//2,"rand":int(s.rng.integers(1,10-s.w))}[s.pad0]
        s.bricks=np.zeros((10,10),bool); s.bricks[1:4,1:9]=True
        s.prev=s.movers() if s.prev0=="same" else np.zeros((10,10),bool); s.t=0
    def obs(s):
        o=np.zeros((10,10,5),np.float32); o[8,list(s.cols()),0]=1; o[s.y,s.x,1]=1; o[:,:,2]=s.bricks
        o[0,:,3]=o[9,:,3]=o[:,0,3]=o[:,9,3]=1; o[:,:,4]=s.prev; return o.reshape(-1)
    def move_paddle(s,a):
        if a==3: s.pos=max(1,s.pos-1)
        elif a==4: s.pos=min(9-s.w,s.pos+1)
    def step(s,a):
        s.prev=s.movers(); s.t+=1
        if s.order=="paddle_first": s.move_paddle(a)
        r=0.; done=False; x,y=s.x,s.y; nx,ny=x+s.dx,y+s.dy
        if nx<1 or nx>8:
            s.dx=-s.dx; nx = min(max(nx,1),8) if s.wall=="clip" else x+s.dx
        if ny<1:
            s.dy=-s.dy; ny = 1 if s.wall=="clip" else y+s.dy
        if s.bricks[ny,nx]:
            s.bricks[ny,nx]=False; r+=1; s.dy=-s.dy; ny=y
            if not s.bricks.any(): s.bricks[1:4,1:9]=True
        elif ny==8:
            c=s.cols()
            if s.catch=="minatar":
                if x in c: s.dy=-s.dy; ny=y
                elif nx in c: s.dy=-s.dy; s.dx=-s.dx; ny=y
                else: done=True
            elif s.catch=="landing":   # only the landing cell counts
                if nx in c: s.dy=-s.dy; ny=y
                else: done=True
            elif s.catch=="landing_reflect":  # landing cell counts, ball reflects (ny=y, nx=x)
                if nx in c: s.dy=-s.dy; ny=y; nx=x
                else: done=True
            elif s.catch=="below":     # paddle must be under the ball's current column
                if x in c: s.dy=-s.dy; ny=y; nx=x
                else: done=True
            if done: r-=1; ny=7
        s.x,s.y=nx,ny
        if s.order=="ball_first": s.move_paddle(a)
        if s.t>=200: done=True
        return r,done

def evaluate(kw, n=24, seed=0):
    rng=np.random.default_rng(seed); env=Env(rng,**kw); R=[];Lg=[]
    for _ in range(n):
        env.reset(); tot=0.
        while True:
            o=env.obs(); a=int(np.argmax(np.tanh(np.tanh(o@W1+b1)@W2+b2)@W3+b3))
            r,d=env.step(a); tot+=r
            if d: break
        R.append(tot); Lg.append(env.t)
    return np.mean(R), np.mean(Lg)

if __name__=="__main__":
    grid=dict(wall=["clip","reflect"], catch=["minatar","landing","landing_reflect","below"], width=[1,2,3],
              start_row=[3,4,5], start_col=["edge","any"], pad0=["4","center","rand"], prev0=["same","zeros"],
              order=["paddle_first","ball_first"])
    keys=list(grid); res=[]
    for vals in itertools.product(*grid.values()):
        kw=dict(zip(keys,vals)); res.append((*evaluate(kw, n=12), kw))
    res.sort(key=lambda t:(-t[1],-t[0]))
    for R,Lg,kw in res[:15]: print(f"ret {R:6.2f} len {Lg:6.1f}  {kw}")
