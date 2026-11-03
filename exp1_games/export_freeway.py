"""Write result_freeway.json and episodes_freeway.json. Usage: python -I export_freeway.py <games dir>"""
import sys, json
import numpy as np
sys.path.insert(0, sys.argv[1])
from common import *
from freeway import Env, BEST, PREV0
G = sys.argv[1]
fin = json.load(open(G + "/final_freeway_out.json"))
net = Net("freeway")


def big_random(kw, n=6000, seed=9):
    rng = np.random.default_rng(seed); rets = []
    for _ in range(n):
        e = Env(rng, **kw); e.reset(); R, d = 0.0, False
        while not d:
            r, d = e.step(int(rng.integers(5))); R += r
        rets.append(R)
    return float(np.mean(rets)), float(np.std(rets) / np.sqrt(n))


ours = dict(fin["best_clock0"]["report"])
ours["random_return"], ours["random_return_se"] = big_random(BEST)
ours["random_episodes"] = 6000
rej = []
for name in ["no_swap_check", "collision_back1", "clock_random_offset", "prev0_zeros", "independent_lane_timers",
             "lane7_speed1", "start_col5", "dirs_reversed", "random_lane_dynamics"]:
    f = fin[name]; rep = f["report"]
    rr = big_random(f["params"], 3000) if name in ("no_swap_check", "collision_back1") else (rep["random_return"], None)
    rej.append({"name": name, "params": f["params"], "prev0": f["prev0"], "td_residual": rep["td_residual"],
                "sample_return": rep["sample_return"], "greedy_return": rep["greedy_return"],
                "random_return": rr[0], "random_len": rep["random_len"], "critic_v0": rep["critic_v0"]})
res = {"id": IDS["freeway"], "game": "freeway",
       "rules": [
           "Wall ring; goal strip on row 1 (reward-target channel, always shown on cols 1-8); six one-way traffic lanes on rows 2-7; safe start strip on row 8.",
           "Agent is one cell; it starts at (8,4). Up/down/left/right move it one cell, clipped to rows 1-8 and cols 1-8; no-op stays.",
           "Each lane holds two cars 4 columns apart that wrap around cols 1-8, at a random phase each episode.",
           "Lane directions rows 2..7: right, left, right, left, right, left. A lane moves one cell every 1,2,3,2,1,3 steps respectively, all on one shared clock starting at t=0 (lane moves on steps where t is a multiple of its interval).",
           "Each step: agent moves, then cars move. Reaching row 1 gives +1 and puts the agent back at (8,4).",
           "Collision (agent on a car cell after the cars move, or agent and car swapping cells within a lane) sends the agent back to (8,4); no penalty, the episode continues.",
           "No terminal state: every episode lasts exactly 200 steps.",
           "Previous-frame channel at reset is a copy of the current agent+car cells (not zeros)."],
       "params": BEST, "prev0": PREV0,
       "verdict": "validated",
       "metrics": {"ours": ours, "reference": reference("freeway"), "rejected_variants": rej},
       "notes": ("Lane directions/speeds were identified per lane from the trained policy's hit rates and confirmed by the critic TD residual "
                 "(0.113 best vs 0.136-0.27 for alternatives). Critic V(s0)=7.2 vs empirical discounted return 10.1: expected, the critic cannot see "
                 "the step counter and PPO treated the 200-step cap as termination, so its value averages over the remaining horizon (~6.9 predicted for "
                 "0.12 reward/step); with prev0=zeros V(s0) drops to 1.6, which is why the start prev frame is taken to be a copy of the first frame. "
                 "Weakly constrained details: the clock offset (t=0 vs a random offset gives the same stats; TD 0.113 vs 0.117), the swap-collision rule "
                 "and reset-to-start vs reset-row-only (the trained policy almost never collides; only the random-policy return 0.010 vs ref 0.011 "
                 "favours swap collisions, without them 0.017-0.025; push-back-one-row gives 0.03-0.055 and is rejected), and the start column "
                 "(4 fits far better than 3, 5 or random). Collision penalty: none (ref random return is positive; -1 penalty would make it negative).")}
json.dump(res, open(G + "/result_freeway.json", "w"), indent=1)
eps = record(lambda rng: Env(rng, **BEST), net, n=2, seed=123, prev0=PREV0)
json.dump({"game": "freeway", "id": IDS["freeway"], "params": BEST, "episodes": eps}, open(G + "/episodes_freeway.json", "w"),
          separators=(",", ":"))
print(json.dumps(ours), [(e["return"], e["length"]) for e in eps])
