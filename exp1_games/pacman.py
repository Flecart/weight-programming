"""Reconstructed 10x10 Pac-Man (network bdf99279). Fixed symmetric maze inside the wall ring,
pellets on open cells, ghosts that kill on contact. Rule variants are parameters; BEST/PREV0/RULES are the chosen
reconstruction (see search_pacman.py and result_pacman.json)."""
import numpy as np
from common import wall_ring, MAX_STEPS

MAZE = ["........",
        ".##..##.",
        ".#....#.",
        "...##...",
        "...##...",
        ".#....#.",
        ".##..##.",
        "........"]
WALLS = wall_ring()
for _r, _row in enumerate(MAZE):
    for _c, _ch in enumerate(_row):
        if _ch == "#": WALLS[_r + 1, _c + 1] = True
OPEN = [(r, c) for r in range(1, 9) for c in range(1, 9) if not WALLS[r, c]]
def _bfs(src):
    d = np.full((10, 10), 99); d[src] = 0; q = [src]
    while q:
        p = q.pop(0)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            n = (p[0] + dr, p[1] + dc)
            if not WALLS[n] and d[n] == 99: d[n] = d[p] + 1; q.append(n)
    return d
BFS = {p: _bfs(p) for p in OPEN}
D = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Env:
    def __init__(self, rng, n_ghosts=2, pac_start="random", ghost_start="random_far", ghost_move="random",
                 ghost_period=1, chase_p=0.0, death_penalty=0.0, clear="end", clear_bonus=0.0,
                 pellet_reward=1.0, min_dist=3, swap_kills=True, ghost_reverse=False, pellet_under_ghost=True, order="pac_first", check_after_ghost=True, chase_metric="manhattan"):
        self.rng = rng
        self.__dict__.update(dict(n_ghosts=n_ghosts, pac_start=pac_start, ghost_start=ghost_start,
                                  ghost_move=ghost_move, ghost_period=ghost_period, chase_p=chase_p,
                                  death_penalty=death_penalty, clear=clear, clear_bonus=clear_bonus,
                                  pellet_reward=pellet_reward, min_dist=min_dist, swap_kills=swap_kills,
                                  ghost_reverse=ghost_reverse, pellet_under_ghost=pellet_under_ghost, order=order,
                                  check_after_ghost=check_after_ghost, chase_metric=chase_metric))

    def _rand_open(self, exclude=(), far_from=None):
        cand = [p for p in OPEN if p not in exclude and
                (far_from is None or abs(p[0] - far_from[0]) + abs(p[1] - far_from[1]) >= self.min_dist)]
        return cand[int(self.rng.integers(len(cand)))]

    def reset(self):
        self.t, self.truncated = 0, False
        if self.pac_start == "random":
            self.pac = self._rand_open()
        else:
            self.pac = tuple(self.pac_start)
        self.pellets = np.zeros((10, 10), bool)
        for p in OPEN: self.pellets[p] = True
        self.pellets[self.pac] = False
        self.ghosts, self.gdir = [], []
        if self.ghost_start != "random_far": self.n_ghosts = len(self.ghost_start)
        for k in range(self.n_ghosts):
            if self.ghost_start == "random_far":
                g = self._rand_open(exclude=[self.pac] + self.ghosts, far_from=self.pac)
            else:
                g = tuple(self.ghost_start[k])
            self.ghosts.append(g); self.gdir.append(DIRS[int(self.rng.integers(4))])
        if not self.pellet_under_ghost:
            for g in self.ghosts: self.pellets[g] = False
        self.ate, self.died, self.clears = 0, False, 0

    def _free(self, p):
        return not WALLS[p]

    def _move_ghost(self, k):
        g, d = self.ghosts[k], self.gdir[k]
        opts = [dd for dd in DIRS if self._free((g[0] + dd[0], g[1] + dd[1]))]
        if self.ghost_reverse is False and len(opts) > 1:
            back = (-d[0], -d[1])
            opts2 = [dd for dd in opts if dd != back]
            if opts2: opts = opts2
        cp = self.chase_p[k] if isinstance(self.chase_p, (list, tuple)) else self.chase_p
        if self.ghost_move == "chase" or (cp > 0 and self.rng.random() < cp):
            if self.chase_metric == "bfs":
                dist = lambda dd: BFS[self.pac][g[0] + dd[0], g[1] + dd[1]]
            else:
                dist = lambda dd: abs(g[0] + dd[0] - self.pac[0]) + abs(g[1] + dd[1] - self.pac[1])
            best = min(dist(dd) for dd in opts)
            opts = [dd for dd in opts if dist(dd) == best]
        elif self.ghost_move == "straight":
            if d in opts and self.rng.random() < 0.7: opts = [d]
        dd = opts[int(self.rng.integers(len(opts)))]
        self.gdir[k] = dd
        self.ghosts[k] = (g[0] + dd[0], g[1] + dd[1])

    def step(self, a):
        self.t += 1
        r, done = 0.0, False
        old = self.pac
        oldg = list(self.ghosts)
        gmove = int(self.t / self.ghost_period) != int((self.t - 1) / self.ghost_period)
        if self.order == "ghost_first" and gmove:
            for k in range(self.n_ghosts): self._move_ghost(k)
        if a in D:
            n = (old[0] + D[a][0], old[1] + D[a][1])
            if self._free(n): self.pac = n
        dead = self.pac in self.ghosts
        if self.order == "pac_first_nocheck":
            dead = False
        if self.order != "ghost_first" and not dead and gmove:
            for k in range(self.n_ghosts): self._move_ghost(k)
            dead = self.check_after_ghost and self.pac in self.ghosts
        if gmove and self.swap_kills and any(og == self.pac and ng == old for og, ng in zip(oldg, self.ghosts)):
            dead = True
        if self.pellets[self.pac] and not (dead and self.order != "eat_then"):
            self.pellets[self.pac] = False; r += self.pellet_reward
        self.ate += r > 0
        if dead:
            r -= self.death_penalty; done = True; self.died = True
        elif not self.pellets.any():
            r += self.clear_bonus
            self.clears += 1
            if self.clear == "end":
                done = True
            else:
                for p in OPEN: self.pellets[p] = True
                self.pellets[self.pac] = False
        if self.t >= MAX_STEPS and not done:
            done, self.truncated = True, True
        return r, done

    def layers(self):
        ag = np.zeros((10, 10), bool); ag[self.pac] = True
        mv = np.zeros((10, 10), bool)
        for g in self.ghosts: mv[g] = True
        return {"agent": ag, "movers": mv, "targets": self.pellets.copy(), "obstacles": WALLS.copy()}


BEST = dict(n_ghosts=2, pac_start=[7, 4], ghost_start=[[2, 4], [2, 5]], order="ghost_first", swap_kills=True,
            ghost_period=2, chase_p=0.7, chase_metric="bfs", ghost_reverse=False, death_penalty=1.0,
            clear="end", clear_bonus=0.0, pellet_reward=1.0, pellet_under_ghost=True)
PREV0 = "same"   # previous-frame channel at reset = current agent+ghost cells (critic V(s0) only matches with this)
RULES = [
    "Fixed symmetric maze: inner walls at (2,2),(2,3),(2,6),(2,7),(3,2),(3,7),(4,4),(4,5),(5,4),(5,5),(6,2),(6,7),(7,2),(7,3),(7,6),(7,7); 48 open cells.",
    "Pac-Man starts at (7,4) every episode; a pellet (+1) on every other open cell (47 pellets, including under the ghosts).",
    "Two ghosts start at (2,4) and (2,5) with a random initial heading.",
    "Ghosts move one cell every second step (half Pac-Man's speed), never reversing unless forced; on each move a ghost takes the step that minimises maze (BFS) distance to Pac-Man with prob 0.7, otherwise a random legal non-reversing step.",
    "Step order: ghosts move (on their steps), then Pac-Man moves (moves into walls leave him in place, no-op stays); Pac-Man dies if he ends on a ghost cell or swaps cells with a ghost.",
    "Eating a pellet gives +1; death gives -1 and ends the episode; eating the last pellet ends the episode (no clear bonus); 200-step cap.",
    "Observation: ch0 Pac-Man, ch1 ghosts, ch2 pellets, ch3 walls (ring + maze), ch4 previous Pac-Man+ghost cells (at reset = the current cells).",
]
