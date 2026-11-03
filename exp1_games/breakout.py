"""Reconstructed 10x10 Breakout. Paddle on row 8 (agent), ball (mover) in rows 1-7, bricks (targets)
rows 1-3, cols 1-8, inside the wall ring. Parameters cover the rule variants searched."""
import numpy as np
from common import wall_ring, MAX_STEPS

# Best reconstruction (stages 8-12 of the search; see bo_stage*.py and final_breakout.py)
BEST = dict(physics="axis", wall_stay=False, brick_stay=True, pad_stay=True, diag="dy", horiz=False,
            catch="edge_stay", hit="landing", width=3, pad0=3, start_row=6, start_cols=(1, 8),
            start_dir="inward_down", pause=1, order="paddle_first", miss_penalty=1.0, respawn="cleared")
PREV0 = "same"


def make_env(rng, **over):
    return Env(rng, **dict(BEST, **over))


class Env:
    def __init__(self, rng, width=3, pad0=4, start_row=4, start_cols=(1, 8), start_dir="inward_down",
                 wall="reflect", catch="flip", brick="minatar", top="reflect", miss_penalty=1.0,
                 respawn="cleared", order="paddle_first", brick_rows=(1, 2, 3), lives=1, hit="landing", physics="minatar", wall_stay=False, diag="dy", horiz=True, brick_stay=True, pad_stay=True, pause=0):
        self.rng = rng
        self.__dict__.update(dict(w=width, pad0=pad0, sr=start_row, scols=start_cols, sdir=start_dir, wall=wall,
                                  catch=catch, brick=brick, top=top, pen=miss_penalty, respawn=respawn, order=order,
                                  brows=brick_rows, lives0=lives, hit=hit, physics=physics, wall_stay=wall_stay, diag=diag, horiz=horiz, brick_stay=brick_stay, pad_stay=pad_stay, pause=pause))

    def _fill(self):
        self.bricks[:] = False
        for r in self.brows: self.bricks[r, 1:9] = True

    def reset(self):
        self.t, self.truncated, self.lives = 0, False, self.lives0
        self.bricks = np.zeros((10, 10), bool); self._fill()
        self.pos = (int(self.rng.integers(1, 10 - self.w)) if self.pad0 == "rand" else int(self.rng.choice(self.pad0)) if isinstance(self.pad0, (tuple, list)) else self.pad0)
        self._serve()

    def _serve(self):
        self.y = self.sr if not isinstance(self.sr, tuple) else int(self.rng.choice(self.sr))
        self.x = int(self.rng.choice(self.scols))
        if self.sdir == "inward_down":
            self.dx = 1 if self.x <= 4 else -1; self.dy = 1
        elif self.sdir == "rand_down":
            self.dx = int(self.rng.choice([-1, 1])); self.dy = 1
        elif self.sdir == "inward_up":
            self.dx = 1 if self.x <= 4 else -1; self.dy = -1
        elif self.sdir == "rand":
            self.dx = int(self.rng.choice([-1, 1])); self.dy = int(self.rng.choice([-1, 1]))

    def cols(self):
        return range(self.pos, self.pos + self.w)

    def layers(self):
        a = np.zeros((10, 10), bool); a[8, self.pos:self.pos + self.w] = True
        m = np.zeros((10, 10), bool); m[self.y, self.x] = True
        return {"agent": a, "movers": m, "targets": self.bricks.copy(), "obstacles": wall_ring()}

    def _move(self, a):
        if a == 3: self.pos = max(1, self.pos - 1)
        elif a == 4: self.pos = min(9 - self.w, self.pos + 1)

    def _axis(self):
        """Axis-separated collisions: walls flip the matching component; the brick straight ahead vertically
        (y+dy, x) and horizontally (y, x+dx) are checked before the diagonal one; on any brick/paddle
        contact the ball stays where it is this step (and on wall contact too if wall_stay)."""
        r, done, stay = 0.0, False, False
        x, y = self.x, self.y
        if not 1 <= x + self.dx <= 8: self.dx = -self.dx; stay |= self.wall_stay
        if y + self.dy < 1: self.dy = -self.dy; stay |= self.wall_stay
        hit = False
        if 1 <= y + self.dy <= 3 and self.bricks[y + self.dy, x]:
            self.bricks[y + self.dy, x] = False; r += 1; self.dy = -self.dy; hit = True
        if self.horiz and 1 <= y <= 3 and self.bricks[y, x + self.dx]:
            self.bricks[y, x + self.dx] = False; r += 1; self.dx = -self.dx; hit = True
        if not hit and 1 <= y + self.dy <= 3 and self.bricks[y + self.dy, x + self.dx]:
            self.bricks[y + self.dy, x + self.dx] = False; r += 1; hit = True
            self.dy = -self.dy
            if self.diag == "both": self.dx = -self.dx
        if hit:
            stay = self.brick_stay
            if self.respawn == "cleared" and not self.bricks.any(): self._fill()
        elif y + self.dy == 8:
            c = self.cols(); nx = x + self.dx
            ok = {"landing": nx in c, "below": x in c, "either": x in c or nx in c}[self.hit]
            if ok:
                self.dy = -self.dy; stay = self.pad_stay
                if self.catch == "edge_stay" and nx in c and x not in c: self.dx = -self.dx
            else:
                r -= self.pen; done = True; return r, done
        if not stay:
            self.x, self.y = x + self.dx, y + self.dy
        return r, done

    def step(self, a):
        if self.physics == "axis":
            self.t += 1
            if self.order == "paddle_first": self._move(a)
            r, done = self._axis() if self.t > self.pause else (0.0, False)   # ball held still for `pause` steps after reset
            if self.order == "ball_first": self._move(a)
            if self.t >= MAX_STEPS and not done: done = True; self.truncated = True
            return r, done
        self.t += 1
        if self.order == "paddle_first": self._move(a)
        r, done = 0.0, False
        x, y = self.x, self.y
        nx, ny = x + self.dx, y + self.dy
        if nx < 1 or nx > 8:
            self.dx = -self.dx
            if self.wall == "clip": nx = min(max(nx, 1), 8)
            elif self.wall == "back": self.dy = -self.dy; ny = y + self.dy; nx = x + self.dx
            elif self.wall == "stay": nx = x; ny = y
            else: nx = x + self.dx
        if ny < 1:
            self.dy = -self.dy
            if self.top == "clip": ny = 1
            elif self.top == "stay": ny, nx = y, x
            else: ny = y + self.dy
        if self.bricks[ny, nx]:
            self.bricks[ny, nx] = False; r += 1
            self.dy = -self.dy
            if self.brick == "minatar": ny = y            # slide sideways into (y, nx)
            elif self.brick == "reflect": ny, nx = y, x    # stay put, reverse vertical
            elif self.brick == "reverse": ny, nx = y, x; self.dx = -self.dx
            elif self.brick == "back": self.dx = -self.dx; ny, nx = y + self.dy, x + self.dx
            elif self.brick == "bounce": ny = y + self.dy   # proper reflection, keep dx, move now
            if self.respawn == "cleared" and not self.bricks.any(): self._fill()
        elif ny == 8:
            c = self.cols()
            hit = {"landing": nx in c, "below": x in c, "either": x in c or nx in c}[self.hit]
            if self.catch == "minatar":
                hit = x in c or nx in c
                if x in c: self.dy = -self.dy; ny = y
                elif nx in c: self.dy, self.dx = -self.dy, -self.dx; ny, nx = y, x
            elif self.catch in ("edge_stay", "edge_bounce"):
                corner = (nx in c) and (x not in c)
                if hit:
                    self.dy = -self.dy
                    if corner: self.dx = -self.dx
                    if self.catch == "edge_stay": ny, nx = y, x
                    else: ny, nx = y + self.dy, x + self.dx
            elif hit:
                self.dy = -self.dy; ny = y
                if self.catch == "flip_stay": nx = x
                elif self.catch == "bounce": ny = y + self.dy
                elif self.catch == "back": self.dx = -self.dx; ny, nx = y + self.dy, x + self.dx
            if not hit:
                r -= self.pen; self.lives -= 1
                if self.lives <= 0: done = True; ny = 7
                else: self._serve(); nx, ny = self.x, self.y
        self.x, self.y = nx, ny
        if self.order == "ball_first": self._move(a)
        if self.t >= MAX_STEPS and not done:
            done = True; self.truncated = True
        return r, done
