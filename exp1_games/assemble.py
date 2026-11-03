"""Merge per-game results into validation.json and episodes.json (+ MinAtar baseline)."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
L = lambda f: json.load(open(os.path.join(H, f)))
val, eps = {}, {}
for g in ["breakout", "pong", "pacman", "freeway"]:
    r = L(f"result_{g}.json"); r.setdefault("game", g); val[g] = r
    e = L(f"episodes_{g}.json"); e = e["episodes"] if isinstance(e, dict) else e
    eps[g] = {"id": r["id"], "source": "reconstructed env, trained network, sampled actions", "verdict": r["verdict"],
              "episodes": [{"return": x["return"], "length": x["length"], "frames": x["frames"][:201]} for x in e]}
m = L("minatar_episode.json")
eps["minatar_breakout_baseline"] = {"source": m["source"], "grid": m["grid"], "verdict": "ground truth (official MinAtar)",
                                    "episodes": [{"return": m["return"], "length": m["length"], "frames": m["frames"][:201]}]}
val["minatar_breakout_baseline"] = {"source": m["source"], "return": m["return"], "length": m["length"],
                                    "note": "Not a reconstruction: official MinAtar Breakout (pip minatar 1.0.15, GPL-3.0) on its native 10x10 grid (no wall ring, paddle row 9, 1-cell paddle), played by a scripted landing-tracking paddle (games/minatar_baseline.py, seed 0)."}
json.dump(val, open(os.path.join(H, "validation.json"), "w"), indent=1)
json.dump(eps, open(os.path.join(H, "episodes.json"), "w"), separators=(",", ":"))
print({k: (v["episodes"][0]["return"], [x["length"] for x in v["episodes"]]) for k, v in eps.items()})
