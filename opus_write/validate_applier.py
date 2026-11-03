"""Validate apply_edits.py on Astra's replies: networks and counts must match the paper's hand.npz / apply.json."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_edits import NPZ_KEYS, apply_text, summarize  # noqa: E402

REPO = os.path.expanduser("~/Desktop/work/weight-programming/repo/exp5_write_from_scratch")
ok_all = True
res = {}
for g in ["breakout", "seaquest", "asterix"]:
    net, rep = apply_text(open(f"{REPO}/runs/{g}/reply/answer.md").read())
    s = summarize(net)
    ref = json.load(open(f"{REPO}/runs/{g}/apply.json"))
    d = np.load(f"{REPO}/networks/{g}/hand.npz", allow_pickle=False)
    exact = all(d[NPZ_KEYS[k]].dtype == np.float32 and d[NPZ_KEYS[k]].shape == net[k].shape
                and np.array_equal(d[NPZ_KEYS[k]], net[k].astype(np.float32)) for k in net)
    er = ref["edit_report"]
    checks = {
        "weights_exact": exact,
        "npz_keys": sorted(d.files) == sorted(NPZ_KEYS.values()),
        "statements": (rep["statements"], er["statements"]),
        "applied": (rep["applied"], er["applied"]),
        "entries_written": (rep["entries_written"], er["entries_written"]),
        "errors": (len(rep["errors"]), len(er["errors"])),
        "cut_off": (rep["cut_off"], er["cut_off"]),
        "tensors_touched": (rep["tensors_touched"], sorted(er["tensors_touched"])),
        "nonzero": (s["nonzero"], ref["nonzero"]),
        "nonzero_total": (s["nonzero_total"], ref["nonzero_total"]),
        "max_abs": (s["max_abs"], ref["max_abs"]),
    }
    ok = all(v if isinstance(v, bool) else v[0] == v[1] for v in checks.values()) and not rep["lenient"]
    ok_all &= ok
    res[g] = {"ok": ok, "checks": checks, "lenient": rep["lenient"]}
    print(g, "OK" if ok else "MISMATCH", {k: v for k, v in checks.items()})
json.dump({"all_ok": ok_all, "games": res}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "applier_validation.json"), "w"), indent=1)
print("ALL OK" if ok_all else "FAILED")
