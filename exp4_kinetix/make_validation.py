"""Combine raw_eval.json with the repo's reference eval JSONs into validation.json."""
import json, math
import kcommon as K

raw = json.load(open("raw_eval.json"))
base_ref = json.load(open(f"{K.REPO}/eval/base_result.json"))
one = json.load(open(f"{K.REPO}/eval/oneshot_result.json"))
ppo = json.load(open(f"{K.REPO}/eval/ppo_training_result.json"))


def ours(r):
    return {"success": r["success"], "fail": r["fail"], "timeout": r["timeout"], "invalid": r["invalid"],
            "episodes": r["episodes"], "counts": r["counts"], "mean_return": round(r["mean_return"], 4),
            "mean_length": round(r["mean_length"], 2), "argmax_outcome": r["argmax_outcome"]}


def ref(d, n, src):
    return {"success": d["success"], "fail": d["red"], "timeout": d["timeout"], "invalid": d["invalid"],
            "episodes": n, "mean_return": round(d["return"], 4), "mean_length": d["length"],
            "argmax_outcome": d.get("argmax_outcome"), "source": src}


def consistent(o, r):
    """Two-proportion check on success/fail/timeout; allow 3 sigma (pooled), exact match needed if both 0/1."""
    for k in ("success", "fail", "timeout"):
        p1, n1, p2, n2 = o[k], o["episodes"], r[k], r["episodes"]
        p = (p1 * n1 + p2 * n2) / (n1 + n2)
        se = math.sqrt(max(p * (1 - p), 1e-12) * (1 / n1 + 1 / n2))
        if abs(p1 - p2) > max(3 * se, 1e-9) and p * (1 - p) > 0 or (p * (1 - p) == 0 and p1 != p2):
            return False
    return True


out = {}
spec = [
    ("ppo_final_seed0", "base_full_precision",
     ref(ppo["last_search"], 256, "eval/ppo_training_result.json -> last_search (full-precision final network, 256 search episodes)")),
    ("ppo_final_seed0_as_shown_rounded", "base_as_shown_rounded",
     ref(base_ref, 256, "eval/base_result.json (network as shown in prompt, 256 search episodes)")),
    ("edited_actor", "edited",
     {**ref(one["test"], one["test"]["episodes"], "eval/oneshot_result.json -> test (1,024 test episodes)"),
      "search_256": ref(one["search"], 256, "eval/oneshot_result.json -> search")}),
]
for name, key, r in spec:
    o = ours(raw[key])
    v = consistent(o, r) and (o["argmax_outcome"] == r["argmax_outcome"] or r["argmax_outcome"] is None)
    out[name] = {"ours": o, "reference": r, "verdict": "validated" if v else "not validated"}
    print(name, out[name]["verdict"], o["counts"])
out["_notes"] = {
    "env": "kinetix-env 3.0.2 (== FLAIROx/Kinetix tag v3.0.2, commit 80ee9c29 recorded in ppo_training_result.json), "
           "jax/jaxlib 0.4.38 CPU, Python 3.12; level l/h2_car_ramp, symbolic_flat obs (679), multi_discrete actions, "
           "frame_skip 2, dense_reward_scale 0.2, max 256 steps",
    "sampling": "each of the 6 action entries sampled independently from softmax of its logits; our RNG streams differ "
                "from the harness's 'search'/'test' streams, so per-episode identity is not reproduced, only rates",
    "outcome_rule": "success = GoalR (green touches blue); fail = red contact (step reward < -0.5); invalid = NaN state; "
                    "timeout = 256 steps otherwise",
}
json.dump(out, open("validation.json", "w"), indent=1)
