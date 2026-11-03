"""Pack minatar/episodes.json + validation.json into site/data.js (6 network channels, one b64 char per cell)."""
import json, sys
root = sys.argv[1]
ep = json.load(open(f"{root}/minatar/episodes.json"))["games"]
val = json.load(open(f"{root}/minatar/validation.json"))
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
CH = ["player", "danger", "reward", "projectile", "trail", "gauge"]  # the networks' 6 input channels
MAP = {  # from each prompt's "How the 6 channels are built" line
    "breakout": {"player": ["paddle"], "reward": ["brick"], "projectile": ["ball"], "trail": ["trail"]},
    "seaquest": {"player": ["sub_front", "sub_back"], "danger": ["enemy_fish", "enemy_sub", "enemy_bullet"],
                 "reward": ["enemy_fish", "enemy_sub", "diver"], "projectile": ["friendly_bullet"],
                 "trail": ["trail", "sub_back"], "gauge": ["oxygen_guage", "diver_guage"]},
    "asterix": {"player": ["player"], "danger": ["enemy"], "reward": ["gold"], "trail": ["trail"]},
}
out = {"channels": CH, "games": {}}
for g, v in ep.items():
    eps = {}
    for kind in ("network", "random"):
        e = v[kind]; frames = []
        for f in e["frames"]:
            m = [0] * 100
            for bit, ch in enumerate(CH):
                for src in MAP[g].get(ch, []):
                    for r, c in f["channels"].get(src, []):
                        m[(r % 10) * 10 + (c % 10)] |= 1 << bit
            frames.append("".join(B64[x] for x in m))
        eps[kind] = {"frames": frames, "rewards": [f["reward"] for f in e["frames"]],
                     "actions": [f["action"] for f in e["frames"]], "executed": [f["executed"] for f in e["frames"]],
                     "score": e["score"], "steps": e["steps"], "ended": e["terminated"]}
    vv = val[g]
    out["games"][g] = {"episodes": eps, "map": MAP[g], "val": {
        "ours": vv["ours"], "reference": vv["reference"], "random": vv["random"], "noop": vv["noop"],
        "z": vv["z_diff"], "verdict": vv["verdict"], "extra": vv.get("extra_check")}}
open(f"{root}/site/data.js", "w").write("window.MINATAR=" + json.dumps(out, separators=(",", ":")) + ";")
print("bytes", len(json.dumps(out)))
