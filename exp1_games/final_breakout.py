"""Final Breakout validation: full_report for BEST and rejected variants; writes result_breakout.json and
episodes_breakout.json."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from breakout import Env, BEST, PREV0, make_env
from common import Net, full_report, reference, record, evaluate
net = Net("breakout")
ours = full_report(make_env, net, PREV0, n_envs=128, n_steps=1000)
rej = {
    "earlier best (MinAtar-style: ball slides on brick/paddle contact, corner catch reverses, start row 4, prev0 zeros)":
        (dict(width=3, pad0=4, start_row=4, start_cols=(1, 8), start_dir="inward_down", wall="reflect", catch="minatar",
              brick="minatar", top="reflect"), "zeros"),
    "MinAtar brick rule (diagonal brick, ball slides sideways) with otherwise best rules":
        (dict(BEST, physics="minatar", brick="minatar", catch="flip_stay", hit="landing"), PREV0),
    "best but ball keeps moving after brick contact": (dict(BEST, brick_stay=False), PREV0),
    "best but ball keeps moving after paddle contact": (dict(BEST, pad_stay=False), PREV0),
    "best but horizontal brick check too": (dict(BEST, horiz=True), PREV0),
    "best but ball pauses on wall contact": (dict(BEST, wall_stay=True), PREV0),
    "best but catch if paddle under ball OR landing cell (either)": (dict(BEST, hit="either"), PREV0),
    "best but no 1-step serve pause": (dict(BEST, pause=0), PREV0),
    "best but ball moves before paddle": (dict(BEST, order="ball_first"), PREV0),
    "best but ball serves from row 5": (dict(BEST, start_row=5), PREV0),
}
rv = []
for name, (kw, p0) in rej.items():
    mk = lambda rng: Env(rng, **kw)
    s = evaluate(mk, net, "sample", 64, 600, 11, p0, td=True); r = evaluate(mk, net, "random", 256, 500, 12, p0)
    kw2 = {k: (list(v) if isinstance(v, tuple) else v) for k, v in kw.items()}
    rv.append({"name": name, "params": kw2, "prev0": p0, "td_residual": s["td_residual"], "sample_return": s["return"],
               "sample_len": s["len"], "random_return": r["return"], "random_len": r["len"]})
    print(rv[-1], flush=True)
params = {k: (list(v) if isinstance(v, tuple) else v) for k, v in BEST.items()}
res = {"id": "a9f535cc", "game": "breakout", "rules": [
    "Wall ring; paddle (agent) is 3 cells wide on row 8 and starts at cols 3-5; left/right move it one cell (clipped to cols 1-8); no-op/up/down do nothing.",
    "Bricks (reward targets) fill rows 1-3, cols 1-8 (24 bricks); +1 per brick; the full wall of bricks respawns when the last one is broken.",
    "Ball (moving object) starts at (6,1) heading down-right or (6,8) heading down-left (50/50), and is held still on the first step.",
    "Ball moves one cell diagonally per step. Each step: paddle moves first, then the ball.",
    "Side/top walls: the matching direction component flips and the ball moves on in the new direction the same step.",
    "Bricks: the brick straight ahead vertically (row y+dy, same column) is checked first, otherwise the diagonal brick (y+dy, x+dx); the hit brick is removed, dy flips, and the ball stays in its cell for that step (no horizontal brick check).",
    "Paddle: when the ball is on row 7 heading down, it is caught if the paddle covers its landing column (x+dx after any wall flip). The ball stays in its cell that step with dy flipped; if only the landing cell (not the ball's own column) is covered, dx also flips.",
    "Miss: -1 and the episode ends immediately (the ball is never shown on row 8). 200-step cap.",
    "Previous-frame channel at reset = copy of the current paddle+ball cells."],
    "params": params, "prev0": PREV0,
    "metrics": {"ours": ours, "reference": reference("breakout"), "rejected_variants": rv}}
ref = res["metrics"]["reference"]
ok = abs(ours["sample_return"] - ref["sample_return"]) / ref["sample_return"] < 0.1 and abs(ours["random_return"] - ref["random_return"]) < 0.1 \
     and abs(ours["random_len"] - ref["random_len"]) < 1.0 and ours["td_residual"] < 0.5 * min(v["td_residual"] for v in rv)
res["verdict"] = "validated" if ok else "approximate"
res["notes"] = ("Return spread differs: ours is almost deterministic (2 mirror-image starts), reference sd ~1.11 over 1280 episodes, "
                "so the true start set (or paddle start) likely has a bit more variety that we could not pin down without breaking "
                "the trained policy's survival or the random stats. The 1-step serve pause is indistinguishable from the reference "
                "counting one extra step per episode. The corner-catch dx flip is almost never exercised by the trained policy.")
json.dump(res, open("result_breakout.json", "w"), indent=1)
json.dump(record(make_env, net, n=2, prev0=PREV0), open("episodes_breakout.json", "w"))
print(json.dumps({k: res[k] for k in ("verdict",)}), json.dumps(ours, indent=1))
