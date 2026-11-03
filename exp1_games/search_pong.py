"""Pong rule-variant search. Stage 1: coarse grid scored jointly on trained-sampled and random stats.
Usage: python -I search_pong.py [stage]"""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from common import Net, evaluate, full_report, reference
from pong import Env

net = Net("pong")
REF = dict(s=4.96, sl=73.7, r=-1.02, rl=39.5)


def score(kw, n_envs=32, n_steps=300, seed=0):
    mk = lambda rng: Env(rng, **kw)
    s = evaluate(mk, net, "sample", n_envs, n_steps, seed, td=True)
    r = evaluate(mk, net, "random", n_envs, n_steps, seed + 1)
    d = (abs(s["return"] - REF["s"]) / 0.5 + abs(s["len"] - REF["sl"]) / 7 + abs(r["return"] - REF["r"]) / 0.3
         + abs(r["len"] - REF["rl"]) / 4)
    return d, s, r


def grid(space, base=None, top=15, **ev):
    keys = list(space); rows = []
    for vals in itertools.product(*space.values()):
        kw = dict(base or {}); kw.update(zip(keys, vals))
        d, s, r = score(kw, **ev)
        rows.append((d, kw, s, r))
    rows.sort(key=lambda t: t[0])
    for d, kw, s, r in rows[:top]:
        print(f"d {d:5.2f} td {s['td_residual']:.3f} S {s['return']:5.2f} len {s['len']:5.1f} | R {r['return']:5.2f} len {r['len']:5.1f} | {s['action_usage']} {kw}", flush=True)
    return rows


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "1"
    if stage == "1":
        grid(dict(hit=["landing", "current", "landing_or_current"], wall_bounce=["through", "stay"],
                  pad_bounce=["through", "stay"], right_bounce=["through", "stay"],
                  serve_col=[3, 5, 8, "random"], serve_dir=["left", "random"]))
    if stage == "2":
        grid(dict(Lo=[1, 2, 3], opp_p=[0.3, 0.5, 0.7, 1.0], hit=["landing", "landing_or_current"],
                  serve_col=["center", "random", 3], serve_dir=["left", "random"]))
    if stage == "3":
        grid(dict(Lo=[1, 2, 3], opp_p=[0.4, 0.5, 0.6], opp_track=["center", "cover"],
                  hit=["landing_or_current", "landing"], serve_col=["center", "random"],
                  serve_dir=["left", "random"], opp_reset=[False, True]), top=30)
    if stage == "4":
        grid(dict(Lo=[1, 2, 3], opp_mode=["prob", "when_coming"], opp_p=[0.3, 0.5, 0.7, 0.85],
                  serve_col=["center", "random"], serve_dir=["left", "random"], opp_reset=[False, True]),
             base=dict(hit="landing_or_current"), top=25)
        grid(dict(Lo=[1, 2, 3], opp_mode=["alternate"], serve_col=["center", "random"], serve_dir=["left", "random"],
                  opp_reset=[False, True]), base=dict(hit="landing_or_current"), top=6)
    if stage == "5":
        grid(dict(opp_mode=["alternate", "prob"], pad_reset=[False, True], english=[False, True],
                  hit=["landing_or_current", "landing"], serve_wait=[0, 2], Lo=[2, 3]),
             base=dict(opp_p=0.5, serve_col="center", serve_dir="random", opp_reset=True), top=20)
    if stage == "6":
        grid(dict(serve_dir=["random", "loser", "winner", "left"], opp_mode=["alternate", "prob"], english=[False, True],
                  Lo=[2, 3], serve_col=["center", "random"]),
             base=dict(opp_p=0.5, opp_reset=True, hit="landing_or_current"), top=20)
    if stage == "7":
        grid(dict(serve_col=[3, 4, 5, 6, "center", "random"], serve_dir=["loser", "random", "left"],
                  opp_mode=["alternate", "prob"], english=[False, True]),
             base=dict(Lo=2, opp_p=0.5, opp_reset=True, hit="landing_or_current"), top=20, n_envs=48, n_steps=400)
    if stage == "8":
        grid(dict(serve_col=[4, 5, "center"], serve_dir=["loser", "random", "left", "winner"],
                  opp_mode=["alternate", "prob"], Lo=[2, 3], hit=["landing_or_current", "landing"]),
             base=dict(opp_p=0.5, opp_reset=True, serve_row="edge"), top=20, n_envs=48, n_steps=400)
    if stage == "9":
        rows = []
        for om, op in [("alternate", 0.5), ("prob", 0.5), ("prob", 0.7), ("prob", 1.0)]:
            rows += grid(dict(opp_hit=["landing", "current", "landing_or_current"], serve_dir=["random", "loser", "left"],
                              serve_col=[5, "center"], Lo=[2, 3]),
                         base=dict(opp_mode=om, opp_p=op, opp_reset=True, hit="landing_or_current"), top=0)
        rows.sort(key=lambda t: t[0])
        for d, kw, s, r in rows[:25]:
            print(f"d {d:5.2f} td {s['td_residual']:.3f} S {s['return']:5.2f} len {s['len']:5.1f} | R {r['return']:5.2f} len {r['len']:5.1f} | {kw}", flush=True)
    if stage == "10":
        grid(dict(opp_p=[0.6, 0.7, 0.8, 0.9], opp_reset=[False, True], pad_reset=[False, True], serve_col=[4, 5, 6]),
             base=dict(opp_mode="prob", hit="landing_or_current", opp_hit="landing", serve_dir="left", Lo=2),
             top=12, n_envs=64, n_steps=400)
    if stage == "final":
        from common import record
        from pong import BEST, PREV0
        HERE = os.path.dirname(os.path.abspath(__file__))
        rep = lambda kw: full_report(lambda rng: Env(rng, **kw), net, prev0=PREV0, n_envs=128, n_steps=1000, seed=11)
        ours = rep(BEST); print("best", ours, flush=True)
        rejected_kw = [
            dict(opp=False, L=3, hit="landing_or_current", serve_col=8, serve_dir="left", points=5),  # no opponent: ball bounces off right wall, only misses score
            dict(BEST, Lo=1, opp_mode="prob", opp_p=0.5, opp_hit="landing_or_current"),
            dict(BEST, Lo=3),
            dict(BEST, opp_mode="alternate", opp_hit="landing_or_current", serve_dir="random"),
            dict(BEST, hit="landing"),
        ]
        rejected = []
        for kw in rejected_kw:
            m = rep(kw); print("rej", kw, m, flush=True)
            rejected.append({"params": kw, "td_residual": m["td_residual"], "sample_return": m["sample_return"],
                             "sample_len": m["sample_len"], "random_return": m["random_return"], "random_len": m["random_len"]})
        rules = [
            "Agent: vertical paddle 3 cells tall in column 1 (rows 1-8), starts centred (rows 4-6); up/down move it one cell, no-op/left/right do nothing.",
            "Opponent: CPU paddle 2 cells tall in column 8, drawn in the moving-objects channel; each step with probability 0.7 it moves one cell toward the ball's row; it is re-centred at every serve.",
            "Ball: one cell moving diagonally (one row and one column per step) between columns 2 and 7; reflects off the top/bottom walls.",
            "Agent return: when the ball would move into column 1, it is returned if the paddle covers the ball's current row or its landing row; otherwise the agent loses the point (-1).",
            "Opponent return: when the ball would move into column 8, the opponent returns it only if it covers the landing row; otherwise the agent wins the point (+1).",
            "After every point the ball is re-served from column 5 at a random row, moving toward the agent with random vertical direction.",
            "Episode ends after 5 points (or 200 steps). Column 9 (rows 1-8) is permanently shown in the reward-target channel; the wall ring is in the obstacle channel.",
        ]
        out = {"id": "dfc6cb65", "game": "pong", "rules": rules, "params": BEST, "prev0": PREV0, "verdict": None,
               "metrics": {"ours": ours, "reference": reference("pong"), "rejected_variants": rejected}}
        json.dump(out, open(os.path.join(HERE, "result_pong.json"), "w"), indent=1)
        eps = record(lambda rng: Env(rng, **BEST), net, n=2, prev0=PREV0)
        json.dump(eps, open(os.path.join(HERE, "episodes_pong.json"), "w"), separators=(",", ":"))
