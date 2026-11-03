import sys, numpy as np
sys.path.insert(0, sys.argv[2])
from breakout import Breakout, Policy
pol = Policy(sys.argv[1]); rng = np.random.default_rng(int(sys.argv[4]))
env = Breakout(rng, width=int(sys.argv[3]))
o = env.reset(); names = "0^v<>"
for t in range(40):
    z = pol.logits(o); a = int(np.argmax(z))
    p = np.exp(z - z.max()); p /= p.sum()
    print(f"t{t:2d} ball{env.ball} d{env.d} paddle{list(env._paddle_cols())} act {names[a]} probs {np.round(p,2)}")
    o, r, done = env.step(a)
    if r: print("   reward", r)
    if done: print("DONE"); break
