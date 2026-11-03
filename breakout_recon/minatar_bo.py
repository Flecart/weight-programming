"""MinAtar Breakout rules (Young & Tian 2019), shifted into the inner 8x8 of a walled 10x10 grid:
playable cols 1..8, top row 1, paddle row 8, bricks rows 1-3. Optional loss penalty.
Usage: python -I minatar_bo.py <a9f535cc.npz> <scratch dir>"""
import sys, numpy as np
sys.path.insert(0, sys.argv[2])
from breakout import Policy, run

L, R, TOP, PAD = 1, 8, 1, 8
class MinAtarBreakout:
    def __init__(self, rng, loss_penalty=1.0, start_row=3, prev_mode="movers", width=1, strike=True):
        self.rng, self.lp, self.start_row, self.prev_mode, self.w, self.use_strike = rng, loss_penalty, start_row, prev_mode, width, strike
    def reset(self):
        self.y = self.start_row
        self.x, self.dir = [(L, 2), (R, 3)][int(self.rng.integers(2))]
        self.pos = 4
        self.bricks = np.zeros((10, 10), bool); self.bricks[1:4, L:R+1] = True
        self.strike = False; self.t = 0
        self.prev = self._movers()
        return self.obs()
    def cols(self): return range(self.pos, self.pos + self.w)
    def _movers(self):
        m = np.zeros((10, 10), bool); m[PAD, list(self.cols())] = True
        if self.prev_mode == "movers": m[self.y, self.x] = True
        elif self.prev_mode == "ball": m[:] = False; m[self.y, self.x] = True
        return m
    def obs(self):
        o = np.zeros((10, 10, 5), np.float32)
        o[PAD, list(self.cols()), 0] = 1; o[self.y, self.x, 1] = 1; o[:, :, 2] = self.bricks
        o[0, :, 3] = o[9, :, 3] = o[:, 0, 3] = o[:, 9, 3] = 1
        o[:, :, 4] = self.prev
        return o.reshape(-1)
    def step(self, a):
        self.prev = self._movers(); self.t += 1
        if a == 3: self.pos = max(L, self.pos - 1)
        elif a == 4: self.pos = min(R - self.w + 1, self.pos + 1)
        r, done = 0.0, False
        lx, ly = self.x, self.y
        nx = self.x + (-1 if self.dir in (0, 3) else 1)
        ny = self.y + (-1 if self.dir in (0, 1) else 1)
        hit = False
        if nx < L or nx > R:
            nx = min(max(nx, L), R); self.dir = [1, 0, 3, 2][self.dir]
        if ny < TOP:
            ny = TOP; self.dir = [3, 2, 1, 0][self.dir]
        elif self.bricks[ny, nx]:
            hit = True
            if not (self.use_strike and self.strike):
                r += 1; self.strike = True; self.bricks[ny, nx] = False
                ny = ly; self.dir = [3, 2, 1, 0][self.dir]
        elif ny == PAD:
            if not self.bricks.any(): self.bricks[1:4, L:R+1] = True
            if lx in self.cols():
                self.dir = [3, 2, 1, 0][self.dir]; ny = ly
            elif nx in self.cols():
                self.dir = [2, 3, 0, 1][self.dir]; ny = ly
            else:
                done = True; r -= self.lp; ny = PAD - 1
        if not hit: self.strike = False
        self.x, self.y = nx, ny
        if self.t >= 200: done = True
        return self.obs(), r, done

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[0].endswith("minatar_bo.py"):
    pol = Policy(sys.argv[1]); rng = np.random.default_rng(0)
    def sample(o):
        z = pol.logits(o); p = np.exp(z - z.max()); return rng.choice(5, p=p / p.sum())
    greedy = lambda o: int(np.argmax(pol.logits(o)))
    rand = lambda o: int(rng.integers(5))
    print("reference: trained 21.71 ret / 200.0 len; random -0.40 ret / 7.84 len")
    for name, kw in {"minatar w1": {}, "minatar w1 prev=ball only": dict(prev_mode="ball"),
                     "minatar w1 no strike flag": dict(strike=False), "minatar w2": dict(width=2),
                     "minatar w3": dict(width=3)}.items():
        env = MinAtarBreakout(rng, **kw)
        s = run(env, sample, 300); g = run(env, greedy, 300); rr = run(env, rand, 3000)
        print(f"{name:28s} sample {s[0]:6.2f}±{s[1]:.2f} len {s[2]:5.1f} | greedy {g[0]:6.2f} len {g[2]:5.1f} | random {rr[0]:5.2f} len {rr[2]:4.1f}", flush=True)
