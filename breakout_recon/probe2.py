import sys, numpy as np
sys.path.insert(0, sys.argv[2])
from breakout import Policy
pol = Policy(sys.argv[1])
def obs(ball, prevball, pad):
    o = np.zeros((10,10,5), np.float32)
    o[8, pad, 0] = 1; o[ball[0], ball[1], 1] = 1
    o[1:4, 1:9, 2] = 1
    o[0,:,3]=o[9,:,3]=o[:,0,3]=o[:,9,3]=1
    o[8, pad, 4] = 1; o[prevball[0], prevball[1], 4] = 1
    return o.reshape(-1)
def land(r, c, dx):  # reflect off side walls at cols 1..8
    while r < 8:
        r += 1; c += dx
        if c < 1 or c > 8: dx = -dx; c += 2*dx
    return c
for dx in (1, -1):
    for r in (4, 5, 6, 7):
        for c in range(1, 9):
            pc = c - dx
            if not 1 <= pc <= 8: continue
            stay = [p for p in range(1, 9) for z in [pol.logits(obs((r,c),(r-1,pc),[p]))]
                    if np.argmax(z) < 3]
            print(f"ball ({r},{c}) dx {dx:+d}: my-landing col {land(r,c,dx)}  policy stays at {stay}")
