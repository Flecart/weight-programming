import sys, numpy as np
sys.path.insert(0, sys.argv[2])
from breakout import Breakout, Policy
pol = Policy(sys.argv[1]); rng = np.random.default_rng(3)
env = Breakout(rng, width=int(sys.argv[3]))
shown = 0
for ep in range(100):
    o = env.reset(); hist = []
    while True:
        a = int(np.argmax(pol.logits(o)))
        hist.append((env.t, list(env.ball), list(env.d), env.paddle, "0^v<>"[a], int(env.bricks.sum())))
        o, r, done = env.step(a)
        if done: break
    if env.t < 200 and shown < 3:
        shown += 1; print("episode", ep, "lost at t", env.t)
        for h in hist[-6:]: print("  t%d ball%s d%s paddle_left %d act %s bricks %d" % h)
