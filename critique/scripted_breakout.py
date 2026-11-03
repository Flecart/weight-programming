"""Hand-coded Breakout players on official MinAtar 1.0.15, same protocol as the paper's Exp 5
(sticky actions 0.1, 10,000-step cap). Shows how hard 'writing a Breakout controller' is.
Usage: python -I scripted_breakout.py [episodes]"""
import sys, numpy as np
from multiprocessing import Pool
from minatar import Environment

L, R, NOOP = 1, 3, 0  # MinAtar action indices: n l u r d f

def track_ball(env, s):
    """3 lines: move toward the ball's column."""
    pc = np.argwhere(s[:, :, 0])[0][1]; bc = np.argwhere(s[:, :, 1])[0][1]
    return L if bc < pc else R if bc > pc else NOOP

def predict_landing(env, s):
    """Simulate the ball forward with the rules from the source file (ignoring bricks) and wait at the landing column."""
    e = env.env
    pos, x, y, d = e.pos, e.ball_x, e.ball_y, e.ball_dir
    for _ in range(40):
        if y == 8 and d in (2, 3):
            break
        nx = x + (-1 if d in (0, 3) else 1); ny = y + (-1 if d in (0, 1) else 1)
        if nx < 0 or nx > 9:
            nx = min(max(nx, 0), 9); d = [1, 0, 3, 2][d]
        if ny < 0:
            ny = 0; d = [3, 2, 1, 0][d]
        x, y = nx, ny
    target = x
    return L if target < pos else R if target > pos else NOOP

import copy
def simulate_landing(env, s):
    """Copy the game (rules exactly as in the source file the prompt gave) and step it until the ball is about to land."""
    g = copy.deepcopy(env.env); g.terminal = False
    for _ in range(60):
        if g.ball_y == 8 and g.ball_dir in (2, 3):
            break
        g.pos = g.ball_x  # keep the simulated paddle under the ball so the copy never ends
        g.act(0)
    target = g.ball_x if g.ball_y == 8 else env.env.ball_x
    pos = env.env.pos
    return L if target < pos else R if target > pos else NOOP

def episode(args):
    name, seed = args
    pol = {"track_ball": track_ball, "predict_landing": predict_landing, "simulate_landing": simulate_landing}[name]
    env = Environment("breakout", sticky_action_prob=0.1)
    env.seed(seed)
    env.reset(); G = 0.0
    for t in range(10000):
        r, done = env.act(pol(env, env.state())); G += r
        if done: break
    return G, t + 1

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    with Pool(16) as p:
        for name in ("track_ball", "predict_landing", "simulate_landing"):
            res = np.array(p.map(episode, [(name, s) for s in range(n)]))
            print(f"{name:16s} mean {res[:,0].mean():7.1f} ± {res[:,0].std()/np.sqrt(n):5.1f}  "
                  f"len {res[:,1].mean():7.0f}  hit 10k cap {np.mean(res[:,1]>=10000):.0%}  (n={n})", flush=True)
