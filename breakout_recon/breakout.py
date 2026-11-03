"""Reconstructed 10x10 Breakout (MinAtar-style, inside a wall border) + the released PPO policy.

The training env was not published, so the rules here are a reconstruction; a few variants are
exposed as parameters and scored against the reference numbers in networks/meta/a9f535cc.json
(trained policy 21.71 return / 200 steps; uniform random -0.40 return / 7.84 steps).
Usage: python -I breakout.py <a9f535cc.npz>
"""
import sys
import numpy as np

PADDLE_ROW, MAX_STEPS = 8, 200


class Breakout:
    def __init__(self, rng, start_row=3, start_cols="edge", width=1, loss_penalty=1.0,
                 respawn=True, edge_deflect=True):
        self.rng, self.start_row, self.start_cols = rng, start_row, start_cols
        self.width, self.loss_penalty, self.respawn, self.edge_deflect = width, loss_penalty, respawn, edge_deflect

    def reset(self):
        self.bricks = np.zeros((10, 10), bool)
        self.bricks[1:4, 1:9] = True
        self.paddle = 4  # leftmost paddle column
        if self.start_cols == "edge":
            c = self.rng.choice([1, 8])
            dx = 1 if c == 1 else -1
        else:
            c = int(self.rng.integers(1, 9))
            dx = int(self.rng.choice([-1, 1]))
        self.ball = [self.start_row, c]
        self.d = [1, dx]  # moving down
        self.prev = self._movers()
        self.t = 0
        return self.obs()

    def _paddle_cols(self):
        return range(self.paddle, self.paddle + self.width)

    def _movers(self):
        m = np.zeros((10, 10), bool)
        m[PADDLE_ROW, list(self._paddle_cols())] = True
        m[self.ball[0], self.ball[1]] = True
        return m

    def obs(self):
        o = np.zeros((10, 10, 5), np.float32)
        o[PADDLE_ROW, list(self._paddle_cols()), 0] = 1
        o[self.ball[0], self.ball[1], 1] = 1
        o[:, :, 2] = self.bricks
        o[0, :, 3] = o[9, :, 3] = o[:, 0, 3] = o[:, 9, 3] = 1
        o[:, :, 4] = self.prev
        return o.reshape(-1)

    def step(self, a):
        self.prev = self._movers()
        self.t += 1
        if a == 3:
            self.paddle = max(1, self.paddle - 1)
        elif a == 4:
            self.paddle = min(9 - self.width, self.paddle + 1)
        r, done = 0.0, False
        (y, x), (dy, dx) = self.ball, self.d
        ny, nx = y + dy, x + dx
        if nx < 1 or nx > 8:  # side walls
            dx = -dx; nx = x + dx
        if ny < 1:  # top wall
            dy = -dy; ny = y + dy
        if self.bricks[ny, nx]:
            self.bricks[ny, nx] = False
            r += 1
            dy = -dy; ny = y
            if self.respawn and not self.bricks.any():
                self.bricks[1:4, 1:9] = True
        elif ny == PADDLE_ROW:
            cols = self._paddle_cols()
            if x in cols:  # directly under the ball: straight bounce
                dy = -dy; ny = y
            elif nx in cols and self.edge_deflect:  # caught on the corner: bounce back the way it came
                dy, dx = -dy, -dx; ny, nx = y, x
            elif nx in cols:
                dy = -dy; ny = y
            else:
                r -= self.loss_penalty; done = True
                ny = min(ny, PADDLE_ROW)
        self.ball, self.d = [ny, nx], [dy, dx]
        if self.t >= MAX_STEPS:
            done = True
        return self.obs(), r, done


class Policy:
    def __init__(self, path):
        d = np.load(path, allow_pickle=False)
        self.p = [d[f"actor/{k}"] for k in ("dense1/kernel", "dense1/bias", "dense2/kernel",
                                            "dense2/bias", "logits/kernel", "logits/bias")]

    def logits(self, x):
        W1, b1, W2, b2, W3, b3 = self.p
        return np.tanh(np.tanh(x @ W1 + b1) @ W2 + b2) @ W3 + b3


def run(env, act, episodes):
    rets, lens = [], []
    for _ in range(episodes):
        o, R, done = env.reset(), 0.0, False
        while not done:
            o, r, done = env.step(act(o))
            R += r
        rets.append(R); lens.append(env.t)
    return np.mean(rets), np.std(rets) / np.sqrt(episodes), np.mean(lens)


if __name__ == "__main__":
    pol = Policy(sys.argv[1])
    rng = np.random.default_rng(0)

    def sample(o):
        z = pol.logits(o); p = np.exp(z - z.max()); return rng.choice(5, p=p / p.sum())

    greedy = lambda o: int(np.argmax(pol.logits(o)))
    rand = lambda o: int(rng.integers(5))
    variants = {
        "row3 edge w1 (MinAtar-like)": {},
        "row3 anycol w1": dict(start_cols="any"),
        "row4 edge w1": dict(start_row=4),
        "row3 edge w1 no-deflect": dict(edge_deflect=False),
        "row3 edge w2": dict(width=2),
        "row3 edge w1 no-respawn": dict(respawn=False),
    }
    print("reference: trained 21.71 ret / 200.0 len; random -0.40 ret / 7.84 len")
    for name, kw in variants.items():
        env = Breakout(rng, **kw)
        s = run(env, sample, 200); g = run(env, greedy, 200); rr = run(env, rand, 2000)
        print(f"{name:30s} sample {s[0]:6.2f}±{s[1]:.2f} len {s[2]:5.1f} | greedy {g[0]:6.2f} len {g[2]:5.1f}"
              f" | random {rr[0]:5.2f} len {rr[2]:4.1f}", flush=True)
