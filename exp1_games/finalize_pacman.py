"""Final validation + export for Pac-Man: writes result_pacman.json and episodes_pacman.json."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from common import Net, full_report, reference, record, IDS
import pacman

net = Net("pacman")
def rep(kw, prev0):
    r = full_report(lambda rng: pacman.Env(rng, **kw), net, prev0, n_envs=128, n_steps=1000, seed=11)
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}

best = rep(pacman.BEST, pacman.PREV0); print("best", best, flush=True)
B = pacman.BEST
rejected_specs = [
    ("deterministic chasers (chase_p=1.0): lowest TD but too easy (return 47, random dies too fast)", dict(B, chase_p=1.0), "same"),
    ("purely random ghosts (chase_p=0), same starts", dict(B, chase_p=0.0), "same"),
    ("random ghosts moving every step, same starts", dict(B, chase_p=0.0, ghost_period=1), "same"),
    ("random Pac-Man start, ghosts random >=3 cells away, random ghosts every step", dict(B, pac_start="random", ghost_start="random_far", chase_p=0.0, ghost_period=1), "same"),
    ("best rules but previous-frame channel zero at reset", dict(B), "zeros"),
    ("ghosts start at (3,4),(3,5)", dict(B, ghost_start=[[3, 4], [3, 5]]), "same"),
]
rejected = []
for name, kw, p0 in rejected_specs:
    r = rep(kw, p0); print(name, r, flush=True)
    rejected.append({"name": name, "params": kw, "prev0": p0, "td_residual": r["td_residual"],
                     "sample_return": r["sample_return"], "sample_len": r["sample_len"], "random_return": r["random_return"],
                     "random_len": r["random_len"], "critic_v0": r["critic_v0"], "empirical_disc_return0": r["empirical_disc_return0"]})
ref = reference("pacman")
res = {"id": IDS["pacman"], "game": "pacman", "rules": pacman.RULES, "params": pacman.BEST, "prev0": pacman.PREV0,
       "verdict": "validated",
       "metrics": {"ours": best, "reference": ref, "rejected_variants": rejected},
       "notes": ("Structure (maze, fixed starts, 2 half-speed ghosts that mostly chase, +1 pellet / -1 death / end on clear, "
                 "prev-frame at reset = current cells) is well supported: TD residual drops from ~1.4 (random starts) and ~0.6 "
                 "(random ghosts) to ~0.27, and critic V(s0) matches the empirical discounted return only with these starts and "
                 "prev0='same'. Not pinned down: the ghosts' chase probability (0.6-1.0 all plausible; 1.0 gives a lower TD residual "
                 "but return 47 and random length 16, so 0.7 was chosen on the joint fit), tie-breaking and exact ghost targeting "
                 "rule (BFS vs Manhattan nearly indistinguishable), initial ghost headings. Our trained policy uses no-op ~2x more "
                 "often than the reference (0.065 vs 0.034); sampled return is ~5% above the reference.")}
json.dump(res, open(os.path.join(HERE, "result_pacman.json"), "w"), indent=1)
eps = record(lambda rng: pacman.Env(rng, **pacman.BEST), net, n=2, seed=123, prev0=pacman.PREV0)
json.dump({"game": "pacman", "id": IDS["pacman"], "params": pacman.BEST, "prev0": pacman.PREV0, "episodes": eps},
          open(os.path.join(HERE, "episodes_pacman.json"), "w"), separators=(",", ":"))
print("episodes", [(e["return"], e["length"]) for e in eps])
