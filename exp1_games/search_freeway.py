"""Freeway variant search (network 0bbcc3ea).
Stage 0 (done interactively, see fw_diag.py): with random per-lane dir/speed and no collisions, per-lane hit rates of
the trained policy singled out lane2 (+1, every step), lane3 (-1, every 2), lane4 (+1, every 3), lane5 (-1, every 2),
lane6 (+1, every step); lane 7 only became clean with a shared global clock.
Stage 1: coordinate descent over each lane's (direction, move interval) on the critic TD residual.
Stage 2: discrete rule variants (clock, collision effect, start column, prev0, penalty).
Usage: python -I search_freeway.py <games dir>
"""
import sys, json, itertools
sys.path.insert(0, sys.argv[1])
from common import *
from freeway import Env

net = Net("freeway"); REF = reference("freeway")


def score(kw, prev0="same", n_envs=32, n_steps=400, seed=0):
    mk = lambda rng: Env(rng, **kw)
    s = evaluate(mk, net, "sample", n_envs, n_steps, seed, prev0, td=True)
    return s


def show(tag, kw, s, prev0="same"):
    print(f"{tag:10s} td {s['td_residual']:.4f} S {s['return']:6.2f} use {s['action_usage']} {json.dumps(kw)} prev0={prev0}",
          flush=True)


base = dict(speeds="fixed", dirs="fixed", fixed_dirs=[1, -1, 1, -1, 1, -1], fixed_speeds=[1, 2, 3, 2, 1, 3],
            timer="zero", collision="reset", start_col=4)

if __name__ == "__main__":
    # Stage 1: coordinate descent per lane
    cur = json.loads(json.dumps(base)); best_td = score(cur)["td_residual"]
    for sweep in range(2):
        changed = False
        for lane in range(6):
            for d, sp in itertools.product([-1, 1], [1, 2, 3, 4]):
                kw = json.loads(json.dumps(cur)); kw["fixed_dirs"][lane] = d; kw["fixed_speeds"][lane] = sp
                if kw == cur: continue
                s = score(kw)
                if s["td_residual"] < best_td - 0.003:
                    best_td, cur, changed = s["td_residual"], kw, True
                    show(f"lane{lane+2}", kw, s)
        if not changed: break
    print("stage1 best", json.dumps(cur), best_td, flush=True)
    # Stage 2: discrete variants around the best
    variants = {"base": {}, "timer=global_rand": dict(timer="global_rand"), "timer=random": dict(timer="random"),
                "collision=back1": dict(collision="back1"), "collision=reset_row": dict(collision="reset_row"),
                "collision=none": dict(collision="none"), "start_col=5": dict(start_col=5),
                "start_col=3": dict(start_col=3), "start_col=random": dict(start_col="random"),
                "swap_check": dict(swap_check=True), "goal keeps col": dict(goal_reset_col="keep"),
                "hit_penalty=1": dict(hit_penalty=1.0), "dirs all reversed": dict(fixed_dirs=[-d for d in cur["fixed_dirs"]])}
    rows = []
    for name, ch in variants.items():
        kw = {**cur, **ch}
        for prev0 in (["same", "zeros"] if name == "base" else ["same"]):
            s = score(kw, prev0, 48, 600, 1)
            show(name, kw, s, prev0); rows.append((name, prev0, kw, s))
    json.dump([{"name": n, "prev0": p, "params": k, "td_residual": s["td_residual"], "sample_return": s["return"],
                "action_usage": s["action_usage"]} for n, p, k, s in rows],
              open(sys.argv[1] + "/search_freeway_out.json", "w"), indent=1)
