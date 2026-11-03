import sys, numpy as np
sys.path.insert(0, sys.argv[2])
from search import Env, pol
W1,b1,W2,b2,W3,b3 = pol.p
best = dict(wall="reflect", catch="minatar", width=3, start_row=4, start_col="edge", pad0="4", prev0="zeros", order="paddle_first")
def run(mode, n, seed):
    rng = np.random.default_rng(seed); env = Env(rng, **best); R=[]; Lg=[]; acts=np.zeros(5)
    for _ in range(n):
        env.reset(); tot=0.
        while True:
            z = np.tanh(np.tanh(env.obs()@W1+b1)@W2+b2)@W3+b3
            if mode=="greedy": a=int(np.argmax(z))
            elif mode=="sample": p=np.exp(z-z.max()); a=rng.choice(5,p=p/p.sum())
            elif mode=="random": a=int(rng.integers(5))
            else: a=0
            acts[a]+=1; r,d=env.step(a); tot+=r
            if d: break
        R.append(tot); Lg.append(env.t)
    R=np.array(R)
    return R.mean(), R.std()/np.sqrt(n), np.mean(Lg), np.mean(np.array(Lg)<200), acts/acts.sum()
print("reference (meta json): sample 21.71, len 200, action use [.178 .183 .168 .237 .234]; random -0.40, len 7.84")
for mode, n in [("sample", 500), ("greedy", 500), ("random", 5000), ("noop", 500)]:
    m, se, L, lost, acts = run(mode, n, 7)
    print(f"{mode:7s} n={n:5d} return {m:6.2f} ± {se:.2f}  len {L:6.1f}  lost-ball rate {lost:.2f}  action use {np.round(acts,3)}")
