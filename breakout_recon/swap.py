import sys, numpy as np
sys.path.insert(0, sys.argv[2])
from breakout import Policy, run, Breakout
from minatar_bo import MinAtarBreakout
pol = Policy(sys.argv[1]); rng = np.random.default_rng(0)
perm = {"as described": [0,1,2,3,4], "left<->right": [0,1,2,4,3], "up/down=left/right": [0,3,4,1,2], "up/down=right/left": [0,4,3,1,2]}
for pname, P in perm.items():
    g = lambda o: P[int(np.argmax(pol.logits(o)))]
    for ename, env in {"minatar w1": MinAtarBreakout(rng), "minatar w3": MinAtarBreakout(rng, width=3), "mine w1": Breakout(rng)}.items():
        res = run(env, g, 100)
        print(f"{pname:20s} {ename:12s} greedy ret {res[0]:6.2f} len {res[2]:5.1f}")
