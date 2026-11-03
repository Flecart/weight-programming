import sys, numpy as np
sys.path.insert(0, sys.argv[2])
from breakout import Policy
pol = Policy(sys.argv[1])
def obs(ball, prevball, pad, prevpad, bricks=True):
    o = np.zeros((10,10,5), np.float32)
    o[8, pad, 0] = 1; o[ball[0], ball[1], 1] = 1
    if bricks: o[1:4, 1:9, 2] = 1
    o[0,:,3]=o[9,:,3]=o[:,0,3]=o[:,9,3]=1
    o[8, prevpad, 4] = 1; o[prevball[0], prevball[1], 4] = 1
    return o.reshape(-1)
names = "0^v<>"
for w in (1, 2, 3, 4):
    print(f"--- paddle width {w}; ball at (6,4) moving down-right -> would land at (8,6)")
    for left in range(1, 10 - w):
        pad = list(range(left, left + w))
        z = pol.logits(obs((6,4), (5,3), pad, pad)); p = np.exp(z-z.max()); p/=p.sum()
        print(f"  paddle cols {pad}: greedy {names[int(np.argmax(z))]}  P(stay)={p[:3].sum():.2f} P(<)={p[3]:.2f} P(>)={p[4]:.2f}")
