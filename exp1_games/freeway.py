"""Reconstructed 10x10 Freeway (road crossing) for network 0bbcc3ea.

Layout: wall ring; goal strip row 1 (reward-target channel, constant); six traffic lanes rows 2-7, each with
two cars 4 columns apart that wrap around cols 1-8; safe start strip row 8.  The agent (one cell) starts on
row 8; reaching row 1 gives +1 and sends the agent back to the start.  Episodes only end at the 200-step cap.
"""
import numpy as np

LANES = range(2, 8)


class Env:
    def __init__(self, rng, speeds="random", speed_set=(1, 2, 3, 4), dirs="random", fixed_speeds=None,
                 fixed_dirs=None, collision="reset", start_col=4, order="agent_first", swap_check=False,
                 goal_reset_col="start", hit_penalty=0.0, lr_moves=True, rand_phase=True, timer="random", check="after"):
        self.rng = rng
        self.p = dict(speeds=speeds, speed_set=tuple(speed_set), dirs=dirs, fixed_speeds=fixed_speeds,
                      fixed_dirs=fixed_dirs, collision=collision, start_col=start_col, order=order,
                      swap_check=swap_check, goal_reset_col=goal_reset_col, hit_penalty=hit_penalty,
                      lr_moves=lr_moves, rand_phase=rand_phase, timer=timer, check=check)

    def _start_col(self):
        sc = self.p["start_col"]
        return int(self.rng.integers(1, 9)) if sc == "random" else sc

    def reset(self):
        p, rng = self.p, self.rng
        self.t, self.truncated = 0, False
        self.ay, self.ax = 8, self._start_col()
        n = 6
        if p["speeds"] == "random":
            self.spd = rng.choice(p["speed_set"], size=n)
        else:
            self.spd = np.array(p["fixed_speeds"])
        if p["dirs"] == "random":
            self.dir = rng.choice([-1, 1], size=n)
        elif p["dirs"] == "alternate_random":
            s = rng.choice([-1, 1]); self.dir = np.array([s * (-1) ** i for i in range(n)])
        else:
            self.dir = np.array(p["fixed_dirs"])
        self.phase = rng.integers(0, 8, size=n) if p["rand_phase"] else np.zeros(n, int)  # car col-1 of car A
        if p["timer"] == "random":  # independent random timer per lane
            self.timer = np.array([rng.integers(0, s) for s in self.spd])
        elif p["timer"] == "global_rand":  # one shared clock with a random offset
            off = int(rng.integers(0, 12)); self.timer = np.array([off % s for s in self.spd])
        else:  # shared clock starting at 0
            self.timer = np.zeros(n, int)

    def cars(self):
        m = np.zeros((10, 10), bool)
        for i, r in enumerate(LANES):
            for k in (0, 4):
                m[r, (self.phase[i] + k) % 8 + 1] = True
        return m

    def layers(self):
        ag = np.zeros((10, 10), bool); ag[self.ay, self.ax] = True
        tg = np.zeros((10, 10), bool); tg[1, 1:9] = True
        ob = np.zeros((10, 10), bool); ob[0, :] = ob[9, :] = ob[:, 0] = ob[:, 9] = True
        return {"agent": ag, "movers": self.cars(), "targets": tg, "obstacles": ob}

    def _move_agent(self, a):
        y, x = self.ay, self.ax
        if a == 1: y -= 1
        elif a == 2: y += 1
        elif a == 3 and self.p["lr_moves"]: x -= 1
        elif a == 4 and self.p["lr_moves"]: x += 1
        self.ay, self.ax = min(max(y, 1), 8), min(max(x, 1), 8)

    def _move_cars(self):
        self.old_cars = self.cars()
        self.timer += 1
        mv = self.timer >= self.spd
        self.timer[mv] = 0
        self.phase = (self.phase + self.dir * mv) % 8

    def _hit(self, prev_agent):
        cars = self.cars()
        if cars[self.ay, self.ax]:
            return True
        if self.p["swap_check"]:  # agent and a car swapped cells within one lane (passed through each other)
            py, px = prev_agent
            if py == self.ay and px != self.ax and self.old_cars[self.ay, self.ax] and cars[py, px]:
                return True
        return False

    def step(self, a):
        self.t += 1
        r = 0.0
        prev_agent = (self.ay, self.ax)
        if self.p["order"] == "agent_first":
            self._move_agent(a)
            pre_hit = self.p["check"] == "both" and 2 <= self.ay <= 7 and self.cars()[self.ay, self.ax]
            self._move_cars()
        else:
            self._move_cars(); self._move_agent(a); pre_hit = False
        if self.ay == 1:
            r += 1.0
            self.ay = 8
            if self.p["goal_reset_col"] == "start":
                self.ax = self._start_col()
        elif pre_hit or self._hit(prev_agent):
            r -= self.p["hit_penalty"]
            if self.p["collision"] == "reset":
                self.ay, self.ax = 8, self._start_col()
            elif self.p["collision"] == "reset_row":
                self.ay = 8
            elif self.p["collision"] == "back1":
                self.ay = min(self.ay + 1, 8)
        done = self.t >= 200
        self.truncated = done
        return r, done


# Best fit (see search_freeway.py / final_freeway.py): lanes rows 2..7 move +1,-1,+1,-1,+1,-1 (right/left) once
# every 1,2,3,2,1,3 steps on one shared clock starting at t=0; collisions send the agent back to the start cell.
BEST = dict(speeds="fixed", dirs="fixed", fixed_dirs=[1, -1, 1, -1, 1, -1], fixed_speeds=[1, 2, 3, 2, 1, 3],
            timer="zero", collision="reset", start_col=4, swap_check=True)
PREV0 = "same"
