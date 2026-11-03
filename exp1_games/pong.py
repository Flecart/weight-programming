"""Reconstructed 10x10 Pong (network dfc6cb65). Parametrised; BEST holds the chosen rules.

Agent: vertical paddle (length L) in column 1, actions up/down (others are no-ops).
Opponent (opp=True): CPU paddle (length Lo) in column 8, drawn in the moving-objects channel; it follows
the ball's row, moving one cell on a step with probability opp_p.
Ball: one cell, moves diagonally (dy, dx in +-1) and reflects off the top/bottom walls.
A point is scored when a paddle fails to return the ball: +1 if the opponent misses, -1 if the agent misses;
then the ball is re-served. The episode ends after `points` points (or 200 steps).
Column 9 (rows 1-8) is drawn in the reward-target channel (the agent's goal line)."""
import numpy as np
from common import wall_ring, MAX_STEPS


class Env:
    def __init__(self, rng, L=3, opp=True, Lo=3, opp_p=0.5, opp_mode="prob", opp_track="center",
                 serve_col="center", serve_dir="random", serve_dy="pm1", serve_row="random",
                 points=5, hit="landing_or_current", opp_hit=None, pad0="center", pad_reset=False,
                 opp_reset=False, target_col=True, english=False, serve_wait=0, contact_stay=False):
        self.rng = rng
        for k, v in dict(L=L, opp=opp, Lo=Lo, opp_p=opp_p, opp_mode=opp_mode, opp_track=opp_track,
                         serve_col=serve_col, serve_dir=serve_dir, serve_dy=serve_dy, serve_row=serve_row,
                         points=points, hit=hit, opp_hit=opp_hit or hit, pad0=pad0, pad_reset=pad_reset,
                         opp_reset=opp_reset, english=english, serve_wait=serve_wait, contact_stay=contact_stay).items():
            setattr(self, k, v)
        self.right_col = 7 if opp else 8   # last column the ball can occupy
        self.walls = wall_ring()
        self.tg = np.zeros((10, 10), bool)
        if target_col: self.tg[1:9, 9] = True

    def _serve(self):
        r = self.rng
        if self.serve_row == "random": self.by = int(r.integers(1, 9))
        elif self.serve_row == "edge": self.by = int(r.choice([1, 8]))
        else: self.by = int(self.serve_row)
        sc = self.serve_col
        if sc == "center": self.bx = int(r.integers(4, 6))
        elif sc == "random": self.bx = int(r.integers(2, self.right_col + 1))
        else: self.bx = int(sc)
        last = getattr(self, "last", 0)  # +1: agent won last point, -1: agent lost it, 0: none yet
        if self.serve_dir == "left": self.dx = -1
        elif self.serve_dir == "right": self.dx = 1
        elif self.serve_dir in ("loser", "winner") and last != 0:
            to_agent = (last < 0) == (self.serve_dir == "loser")
            self.dx = -1 if to_agent else 1
        else: self.dx = int(r.choice([-1, 1]))
        self.dy = int(r.choice([-1, 1]))
        if self.serve_row == "edge": self.dy = 1 if self.by == 1 else -1
        self.wait = self.serve_wait
        if self.pad_reset: self._pad_start()
        if self.opp_reset: self.oy = (9 - self.Lo) // 2 + 1

    def _pad_start(self):
        self.py = (9 - self.L) // 2 + 1 if self.pad0 == "center" else int(self.rng.integers(1, 10 - self.L))

    def reset(self):
        self.t, self.n_points, self.truncated, self.last = 0, 0, False, 0
        self._pad_start(); self.oy = (9 - self.Lo) // 2 + 1
        self._serve()

    def layers(self):
        a = np.zeros((10, 10), bool); a[self.py:self.py + self.L, 1] = True
        m = np.zeros((10, 10), bool); m[self.by, self.bx] = True
        if self.opp: m[self.oy:self.oy + self.Lo, 8] = True
        return {"agent": a, "movers": m, "targets": self.tg, "obstacles": self.walls}

    def _covers(self, top, Lp, y, ny, rule):
        pad = range(top, top + Lp)
        return (ny in pad) if rule == "landing" else (y in pad) if rule == "current" else (ny in pad or y in pad)

    def _move_opp(self):
        if not self.opp: return
        if self.opp_mode == "prob" and self.rng.random() >= self.opp_p: return
        if self.opp_mode == "when_coming" and (self.dx < 0 or self.rng.random() >= self.opp_p): return
        if self.opp_mode == "alternate" and self.t % 2: return
        c = self.oy + (self.Lo - 1) / 2
        if self.by < c - 0.5 * (self.opp_track == "cover"): self.oy = max(1, self.oy - 1)
        elif self.by > c + 0.5 * (self.opp_track == "cover"): self.oy = min(9 - self.Lo, self.oy + 1)

    def step(self, a):
        self.t += 1
        if a == 1: self.py = max(1, self.py - 1)
        elif a == 2: self.py = min(9 - self.L, self.py + 1)
        self._move_opp()
        r = self._ball()
        if r != 0: self.n_points += 1
        done = bool(self.points and self.n_points >= self.points)
        self.truncated = False
        if not done and self.t >= MAX_STEPS: done, self.truncated = True, True
        return r, done

    def _ball(self):
        if self.wait > 0:
            self.wait -= 1; return 0.0
        y, x = self.by, self.bx
        ny, nx = y + self.dy, x + self.dx
        if ny < 1 or ny > 8:
            self.dy = -self.dy; ny = y + self.dy
        if nx < 2:
            if not self._covers(self.py, self.L, y, ny, self.hit):
                self.last = -1; self._serve(); return -1.0
            self.dx = 1; nx = x + 1
            if self.contact_stay: nx, ny = x, y
            if self.english:
                off = y - self.py - (self.L - 1) / 2
                if off != 0: self.dy = int(np.sign(off))
                ny = y + self.dy
                if ny < 1 or ny > 8: self.dy = -self.dy; ny = y + self.dy
        elif nx > self.right_col:
            if self.opp and not self._covers(self.oy, self.Lo, y, ny, self.opp_hit):
                self.last = 1; self._serve(); return 1.0
            self.dx = -1; nx = x - 1
            if self.contact_stay: nx, ny = x, y
        self.by, self.bx = ny, nx
        return 0.0


BEST = dict(L=3, opp=True, Lo=2, opp_mode="prob", opp_p=0.7, opp_track="center", opp_reset=True,
            hit="landing_or_current", opp_hit="landing", serve_col=5, serve_row="random", serve_dir="left",
            points=5, pad0="center", pad_reset=False, target_col=True)
PREV0 = "zeros"
