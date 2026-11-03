"""Full reports for the Freeway finalists and rejected variants. Usage: python -I final_freeway.py <games dir>"""
import sys, json
sys.path.insert(0, sys.argv[1])
from common import *
from freeway import Env
net = Net("freeway")
B = dict(speeds="fixed", dirs="fixed", fixed_dirs=[1, -1, 1, -1, 1, -1], fixed_speeds=[1, 2, 3, 2, 1, 3],
         timer="zero", collision="reset", start_col=4, swap_check=True)
cands = {"best_clock0": (B, "same"),
         "clock_random_offset": ({**B, "timer": "global_rand"}, "same"),
         "no_swap_check": ({**B, "swap_check": False}, "same"),
         "prev0_zeros": (B, "zeros"),
         "independent_lane_timers": ({**B, "timer": "random"}, "same"),
         "collision_back1": ({**B, "collision": "back1"}, "same"),
         "start_col5": ({**B, "start_col": 5}, "same"),
         "lane7_speed1": ({**B, "fixed_speeds": [1, 2, 3, 2, 1, 1]}, "same"),
         "dirs_reversed": ({**B, "fixed_dirs": [-1, 1, -1, 1, -1, 1]}, "same"),
         "random_lane_dynamics": ({**B, "speeds": "random", "dirs": "random", "timer": "random"}, "same")}
out = {}
for name, (kw, p0) in cands.items():
    rep = full_report(lambda rng: Env(rng, **kw), net, prev0=p0, n_envs=64, n_steps=1000, seed=0)
    out[name] = {"params": kw, "prev0": p0, "report": rep}
    print(name, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rep.items()}), flush=True)
json.dump(out, open(sys.argv[1] + "/final_freeway_out.json", "w"), indent=1)
