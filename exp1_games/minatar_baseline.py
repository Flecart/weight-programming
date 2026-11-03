"""Ground-truth baseline: one episode of the official MinAtar Breakout (pip `minatar`, GPL-3.0, Young & Tian 2019),
played by a scripted paddle that tracks the ball's predicted landing column. Default MinAtar settings
(sticky_action_prob=0.1). MinAtar's own 10x10 grid has no wall ring; frames use the same compact format as
episodes.json (agent=paddle on row 9, movers=ball, targets=bricks, prev=paddle+ball cells of the previous step).
Writes games/minatar_episode.json."""
import json, os, sys
import numpy as np
from minatar import Environment

def predict_landing(x, y, dx, dy):
    # roll the ball forward ignoring bricks until it reaches row 8 (the row above the paddle)
    for _ in range(40):
        if dy > 0 and y == 8: return x
        nx, ny = x + dx, y + dy
        if nx < 0 or nx > 9: dx = -dx; nx = min(max(nx, 0), 9)
        if ny < 0: dy = -dy; ny = 0
        x, y = nx, ny
    return x

def run(seed=0, max_steps=200):
    env = Environment("breakout"); env.seed(seed)
    env.reset(); g = env.env
    A = env.minimal_action_set()  # [n, l, r] as indices of the full action set
    frames, tot = [], 0.0
    cells = lambda m: [[int(r), int(c)] for r, c in zip(*np.nonzero(m))]
    def frame(prev, a, r):
        s = env.state()
        return {"agent": cells(s[..., 0]), "movers": cells(s[..., 1]), "targets": cells(s[..., 3]),
                "obstacles_interior": [], "prev": prev, "action": a, "reward": r}
    prev = []
    frames.append(frame(prev, None, 0.0))
    t = 0
    while t < max_steps:
        dx = 1 if g.ball_dir in (1, 2) else -1; dy = 1 if g.ball_dir in (2, 3) else -1
        target = predict_landing(g.ball_x, g.ball_y, dx, dy) if dy > 0 else g.ball_x
        a = 0 if g.pos == target else (3 if g.pos > target else 4)   # our action ids: 0 noop, 3 left, 4 right
        s = env.state(); prev = cells(s[..., 0] | s[..., 1])
        r, done = env.act({0: A[0], 3: A[1], 4: A[2]}[a]); t += 1; tot += r
        frames.append(frame(prev, a, float(r)))
        if done: break
    return {"source": "official MinAtar Breakout (pip minatar 1.0.15), scripted landing-tracking paddle, sticky actions 0.1",
            "grid": "MinAtar native 10x10, no wall ring, paddle row 9", "return": tot, "length": t, "frames": frames}

if __name__ == "__main__":
    ep = run(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    json.dump(ep, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "minatar_episode.json"), "w"))
    print("return", ep["return"], "length", ep["length"])
