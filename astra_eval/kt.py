"""Description length vs computation: rule-defined input permutations (P_aff, P_xs_k, P_sha, P_sha_out).

Each condition permutes the 500 inputs (row j of the shown W1 holds original input p(j)) and states the
rule for p as a short procedure instead of a table. Logged per condition:
  desc_bits        16 bits per stated constant + 32 bits flat for the rule text
  ops_per_index    operations to compute p(j) for one j (mean over j; cycle-walking measured)
  total_ops_all    operations to decode every row (sum over j; for SHA the hashing and the sort are shared
                   by all rows, so this is the amortised cost; naive_total_ops = ops_per_index * 500 is logged too)
  kt_bits          desc_bits + log2(total_ops_all)   (Levin-Kt style)
"""
from __future__ import annotations

import hashlib
import math

import numpy as np

import complexity as CX
import harness as H
import levels as LV

N = 500
BITS_CONST, BITS_RULE = 16, 32
OPS_AFF = 3                     # multiply, add, mod
OPS_XS_ROUND = 5                # multiply, add, mod 512, shift, xor
OPS_CMP = 1                     # the ">= 500 ?" test after each pass
# SHA-256 of a short (one-block) message, counted in 32-bit word operations
SHA_BREAKDOWN = {
    "message schedule (48 words: sigma0 5 + sigma1 5 + 3 adds)": 48 * 13,
    "64 rounds x (Sigma1 5 + Ch 4 + T1 4 adds + Sigma0 5 + Maj 5 + T2 1 add + 2 adds)": 64 * 26,
    "final 8 additions": 8,
}
SHA_OPS = sum(SHA_BREAKDOWN.values())
SEED = 20261103


def sha_order(prefix: str, n: int) -> list:
    return sorted(range(n), key=lambda i: hashlib.sha256(f"{prefix}{i}".encode("ascii")).hexdigest())


def sort_ops(n: int) -> int:
    return math.ceil(n * math.log2(n)) if n > 1 else 0


def perm_matrix(p) -> np.ndarray:
    A = np.zeros((N, N))
    A[np.arange(N), p] = 1
    return A


def _check_bijection(p, n=N):
    assert sorted(int(v) for v in p) == list(range(n)), "not a bijection"


def _step(p, text, ops_per_index, total, n_consts, extra_note=""):
    _check_bijection(p)
    desc = BITS_CONST * n_consts + BITS_RULE
    st = LV.Step("rule_perm", N, perm_matrix(p), np.zeros(N), text,
                 ops=ops_per_index, depth=ops_per_index, table_entries=n_consts, bits=desc)
    return st, {"desc_bits": desc, "ops_per_index": ops_per_index, "total_ops_all": total,
                "naive_total_ops": ops_per_index * N, "n_consts": n_consts, "note": extra_note}


def make_aff(a=337, c=141):
    assert math.gcd(a, N) == 1
    p = [(a * j + c) % N for j in range(N)]
    text = (f"permutation by rule: v'_j = v_{{p(j)}} for j = 0..499, where p(j) = ({a} · j + {c}) mod 500 "
            f"(gcd({a}, 500) = 1, so p is a permutation of 0..499). So row j of W1 holds the weights of original "
            f"input p(j)")
    return _step(p, text, OPS_AFF, OPS_AFF * N, 2)


def xs_rounds(k):
    rng = np.random.default_rng(SEED + k)
    return [(int(2 * rng.integers(1, 256) + 1), int(rng.integers(0, 512))) for _ in range(k)]


def xs_pass(x, rounds):
    for a, c in rounds:
        x = (a * x + c) % 512
        x = x ^ (x >> 3)
    return x


def make_xs(k):
    rounds = xs_rounds(k)
    p, passes = [], []
    for j in range(N):
        x, n = xs_pass(j, rounds), 1
        while x >= N:
            x, n = xs_pass(x, rounds), n + 1
        p.append(x)
        passes.append(n)
    per_pass = OPS_XS_ROUND * k + OPS_CMP
    total = per_pass * sum(passes)
    listing = "; ".join(f"round {r}: a = {a}, c = {c}" for r, (a, c) in enumerate(rounds, 1))
    text = ("permutation by rule: v'_j = v_{p(j)} for j = 0..499 (row j of W1 holds the weights of original input "
            "p(j)), where p(j) is computed as follows. Start with x = j. Apply the "
            f"{k} round{'s' if k > 1 else ''} listed below in order; round r does x ← (a_r · x + c_r) mod 512 and "
            "then x ← x XOR (x >> 3) (bitwise exclusive-or of x with x shifted right by 3 bits, i.e. with "
            f"floor(x / 8)). If the result after all {k} round{'s' if k > 1 else ''} is 500 or more, apply all "
            f"{k} round{'s' if k > 1 else ''} again to that result, and repeat until the result is less than 500; "
            "that result is p(j). Every round is a bijection of 0..511, so p is a permutation of 0..499. "
            f"The rounds (a_r odd): {listing}")
    st, kt = _step(p, text, total / N, total, 2 * k,
                   f"cycle-walk passes: mean {np.mean(passes):.3f}, max {max(passes)}")
    kt["passes_mean"], kt["passes_max"] = float(np.mean(passes)), int(max(passes))
    return st, kt


def make_sha():
    p = sha_order("wp-", N)
    text = ("permutation by rule: v'_j = v_{p(j)} for j = 0..499 (row j of W1 holds the weights of original input "
            "p(j)), where p is defined by sorting: for every integer n = 0..499 compute the SHA-256 hex digest "
            "(lowercase) of the ASCII string \"wp-\" followed by n in decimal (for example \"wp-0\", \"wp-17\", "
            "\"wp-499\"); sort the 500 integers by their digests in ascending order; p(j) is the integer at position "
            "j (counting from 0) of this sorted list")
    per_index = N * SHA_OPS + sort_ops(N)          # one row from scratch needs all 500 hashes and the sort
    total = N * SHA_OPS + sort_ops(N)              # all rows: hashes and sort shared (amortised)
    return _step(p, text, per_index, total, 1, "SHA: total_ops_all amortised (hash once, sort once)")


def make_sha_out_perm():
    q = sha_order("wp-act-", 5)
    text = ("In the network shown below the 5 logit columns are reordered: logit column m (column m of W3 and entry "
            "m of b3) belongs to action q(m), where q is defined by sorting: compute the SHA-256 hex digest "
            "(lowercase) of the ASCII string \"wp-act-\" followed by the action number (\"wp-act-0\" ... "
            "\"wp-act-4\"), sort the actions 0..4 by their digests in ascending order, and q(m) is the action at "
            "position m (counting from 0). The action is sampled from the softmax of the logits after putting "
            "each logit back at its action.")
    ops = 5 * SHA_OPS + sort_ops(5)
    return q, text, {"out_desc_bits": BITS_CONST, "out_ops": ops}


def make_variants() -> dict:
    V = {}
    st, kt = make_aff()
    V["P_aff"] = LV.Variant("P_aff", "P", 1, 2, axis="kt", steps=[st], kt={**kt, "k": 0, "family": "aff"})
    for k in [1, 2, 4, 8, 16, 32]:
        st, kt = make_xs(k)
        V[f"P_xs_{k}"] = LV.Variant(f"P_xs_{k}", "P", k, 2 * k, axis="kt", steps=[st],
                                   kt={**kt, "k": k, "family": "xs"})
    st, kt = make_sha()
    V["P_sha"] = LV.Variant("P_sha", "P", 1, 1, axis="kt", steps=[st], kt={**kt, "k": None, "family": "sha"})
    st2, kt2 = make_sha()
    q, qtext, qk = make_sha_out_perm()
    kt2 = dict(kt2)
    kt2["desc_bits"] += qk["out_desc_bits"]
    kt2["total_ops_all"] += qk["out_ops"]
    kt2["naive_total_ops"] += qk["out_ops"]
    st2.bits += qk["out_desc_bits"]
    V["P_sha_out"] = LV.Variant("P_sha_out", "P", 2, 2, axis="kt", steps=[st2], out_perm=q, out_text=qtext,
                                kt={**kt2, "k": None, "family": "sha_out", "q": q})
    for v in V.values():
        v.kt["kt_bits"] = v.kt["desc_bits"] + math.log2(v.kt["total_ops_all"])
        v.kt["log2_total_ops"] = math.log2(v.kt["total_ops_all"])
    return V


VARIANTS = make_variants()
KT_COLS = ["family", "k", "desc_bits", "ops_per_index", "total_ops_all", "naive_total_ops", "log2_total_ops",
           "kt_bits"]


def row_kt(cond) -> dict:
    """KT columns for any condition. Earlier conditions: desc_bits as in complexity.py, total ops = V."""
    v = getattr(cond, "variant", None)
    if v is not None and v.kt:
        return {k: v.kt.get(k) for k in KT_COLS}
    m = CX.condition_metrics(cond)
    tot = m["total_ops"] + m["table_entries"]
    return {"family": "", "k": None, "desc_bits": m["desc_bits"], "ops_per_index": m["ops_per_weight"],
            "total_ops_all": tot, "naive_total_ops": None, "log2_total_ops": math.log2(1 + tot),
            "kt_bits": m["desc_bits"] + math.log2(1 + tot)}


# ----------------------------------------------------------------------------- report

def report(rows, root):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = list(VARIANTS)
    ok = [r for r in rows if r["ok"]]
    kr = [r for r in ok if r["condition"] in VARIANTS]
    L = ["# Description length vs computation (rule-defined input permutations)", "",
         "Each condition permutes the 500 inputs (row j of the shown W1 holds original input p(j)) and states the "
         "rule for p as a short procedure; P_sha_out also permutes the 5 logit columns by a stated SHA-256 rule. "
         "All are function-preserving (checked: bijection + forward pass). desc_bits = 16 per stated constant + "
         f"32 for the rule; SHA-256 of a short message counted as {SHA_OPS:,} word operations "
         "(breakdown in `kt.py`); kt_bits = desc_bits + log2(total_ops_all).", "",
         "| Condition | k | desc bits | ops / index | total ops (all rows) | log2 total | kt bits | runs | accuracy | "
         "mean conf | reasoning tok mean (min–max) | output tok | wall s |", "|" + "---|" * 13]
    agg = []
    for n in names:
        rs = [r for r in kr if r["condition"] == n]
        if not rs:
            continue
        kt = VARIANTS[n].kt
        a = dict(cond=n, acc=np.mean([bool(r["correct"]) for r in rs]),
                 conf=np.mean([r["confidence"] for r in rs if r["confidence"] is not None]),
                 reas=np.mean([r["reasoning_tokens"] for r in rs]), runs=len(rs), **kt)
        agg.append(a)
        L.append(f"| {n} | {kt['k'] if kt['k'] is not None else '–'} | {kt['desc_bits']:.0f} | "
                 f"{kt['ops_per_index']:,.1f} | {kt['total_ops_all']:,.0f} | {kt['log2_total_ops']:.1f} | "
                 f"{kt['kt_bits']:.1f} | {len(rs)} | {a['acc']:.0%} | {a['conf']:.1f} | {a['reas']:,.0f} "
                 f"({min(r['reasoning_tokens'] for r in rs):,}–{max(r['reasoning_tokens'] for r in rs):,}) | "
                 f"{np.mean([r['output_tokens'] for r in rs]):,.0f} | {np.mean([r['wall_s'] for r in rs]):.0f} |")
    L += ["", "P_xs cycle-walking (measured): " + "; ".join(
        f"k={VARIANTS[n].kt['k']}: {VARIANTS[n].kt['passes_mean']:.3f} passes/index (max "
        f"{VARIANTS[n].kt['passes_max']})" for n in names if VARIANTS[n].kt["family"] == "xs"), ""]

    # per-game accuracy
    L += ["Per game (correct / runs):", "", "| Condition | Breakout | Pong | Pac-Man | Freeway |", "|---|---|---|---|---|"]
    for n in names:
        cells = []
        for g in ["breakout", "pong", "pacman", "freeway"]:
            gr = [r for r in kr if r["condition"] == n and r["truth"] == g]
            cells.append(f"{sum(bool(r['correct']) for r in gr)}/{len(gr)}")
        L.append(f"| {n} | " + " | ".join(cells) + " |")

    # Spearman correlations
    def rho(rs, key):
        x = [r[key] for r in rs]
        y = [r["reasoning_tokens"] for r in rs]
        return CX.spearman(x, y) if len(set(x)) > 1 else float("nan")

    L += ["", "## Spearman ρ of reasoning tokens (per run)", "",
          "| Runs | n | vs desc_bits | vs log2(total_ops_all) | vs kt_bits |", "|---|---|---|---|---|"]
    for lab, rs in [("these runs (P_*)", kr), ("all runs pooled", ok)]:
        L.append(f"| {lab} | {len(rs)} | {rho(rs, 'desc_bits'):.3f} | {rho(rs, 'log2_total_ops'):.3f} | "
                 f"{rho(rs, 'kt_bits'):.3f} |")
    L += ["", "Pooled runs use the earlier conditions' measures: desc_bits from complexity.py (permutation tables "
          "cost log2(500!)), total ops = V (ops to undo + table entries), so log2_total_ops = log2(1 + V).", ""]

    # logistic fit
    f = CX.logistic_report(ok, "log2_total_ops")
    L += ["## Logistic fit of correctness vs log2(total_ops_all) (all runs)", ""]
    if f["slope"] is None:
        L.append(f"{f['failures']} failures in {f['n']} runs: {f['note']}.")
    else:
        L.append(f"slope {f['slope']:.3g} per bit, C50 = {f['c50']:.3g}, bootstrap 95% CI "
                 f"[{f['ci'][0]:.3g}, {f['ci'][1]:.3g}] ({f['failures']} failures / {f['n']} runs). {f['note']}")
    fk = CX.logistic_report(kr, "log2_total_ops") if kr else None
    if fk and fk["slope"] is not None:
        L.append(f"\nP_* runs only: slope {fk['slope']:.3g}, C50 = {fk['c50']:.3g}, CI [{fk['ci'][0]:.3g}, "
                 f"{fk['ci'][1]:.3g}].")
    L.append("")

    # wrong answers
    bad = [r for r in kr if not r["correct"]]
    L += ["## Wrong answers", ""] + ([f"- {r['condition']} / {r['truth']} {r['replica']} -> `{r['guess']}` "
                                       f"(conf {r['confidence']}): Game: \"{r['game_line']}\"" for r in bad]
                                      or ["None."]) + [""]

    # did Astra actually compute p(j)?  check every "p(j) = v" it wrote against the true permutation
    import re
    L += ["## Did Astra compute p(j)? (every `p(j) = v` written in an answer, checked against the true p)", "",
          "| Condition | answers with p(j) claims | claims correct | wrong answers among those runs |",
          "|---|---|---|---|"]
    for n in names:
        p = VARIANTS[n].steps[0].A.argmax(1)
        files = tot = good = 0
        for r in [r for r in kr if r["condition"] == n]:
            txt = (root / "runs" / n / r["network"] / r["replica"] / "answer.md").read_text()
            claims = {(int(j), int(v)) for j, v in re.findall(r"p\((\d+)\)\s*=\s*(\d+)", txt) if int(j) < N}
            files += bool(claims)
            tot += len(claims)
            good += sum(p[j] == v for j, v in claims)
        nbad = sum(1 for r in kr if r["condition"] == n and not r["correct"])
        L.append(f"| {n} | {files}/{sum(1 for r in kr if r['condition'] == n)} | {good}/{tot} | {nbad} |")
    L += ["", "(P_aff answers decode rows without writing `p(j) = v`; P_sha answers never compute any hash.)", ""]

    # reasoning summaries
    L += ["## Reasoning summaries (section titles, as returned by the gateway)", ""]
    for n in ["P_xs_32", "P_sha", "P_sha_out"]:
        for r in [r for r in kr if r["condition"] == n][:4]:
            sm = (root / "runs" / n / r["network"] / r["replica"] / "reasoning_summary.md").read_text()
            heads = [h.strip("* ") for h in re.findall(r"\*\*[^*]+\*\*", sm)]
            L.append(f"- **{n} / {r['truth']} {r['replica']}** ({r['reasoning_tokens']:,} reasoning tok, "
                     f"{'correct' if r['correct'] else 'wrong'}): " + "; ".join(heads[:14]) +
                     (" …" if len(heads) > 14 else ""))
        L.append("")

    # plot vs k
    xs = [a for a in agg if a["family"] == "xs"]
    if xs:
        fig, ax = plt.subplots(1, 3, figsize=(14, 4))
        ks = [a["k"] for a in xs]
        for i, (key, lab) in enumerate([("acc", "accuracy"), ("conf", "mean confidence"),
                                        ("reas", "mean reasoning tokens")]):
            ax[i].plot(ks, [a[key] for a in xs], "o-", label="P_xs_k")
            for a in agg:
                if a["family"] != "xs":
                    ax[i].axhline(a[key], ls="--", lw=.8, alpha=.7, label=a["cond"],
                                  color={"aff": "gray", "sha": "red", "sha_out": "purple"}[a["family"]])
            ax[i].set_xscale("log", base=2)
            ax[i].set_xlabel("k (rounds)")
            ax[i].set_ylabel(lab)
        ax[0].set_ylim(-.05, 1.05)
        ax[2].legend(fontsize=7)
        fig.suptitle("Rule-defined permutations: accuracy, confidence, reasoning vs rounds k")
        fig.tight_layout()
        fig.savefig(root / "kt.png", dpi=130)
        plt.close(fig)
        L += ["![vs k](kt.png)", ""]
    return L
