"""Complexity measures per condition, the obfuscation-sweep checks, logistic fits and complexity.md / .png.

Measures (all derived from the transformation definitions in levels.py / harness.Rescale):
  d, w                 composed transformations / independent parameters (as assigned per level)
  ops_per_weight, depth, table_entries, log10_V
                       operations to recover one original W1/W3 weight from the shown ones
                       (multiply, add, index-arithmetic step, table lookup = 1 each);
                       V = total ops over affected weights (+ b1 recovery where offsets exist) + table entries;
                       log10_V = log10(1 + V) so the untransformed network sits at 0
  desc_bits            bits to state the transformation (real constant 16 bits, permutation log2(n!),
                       Givens rotation log2(C(500,2)) + 16, channel renaming log2(5!), unstated symmetry 0)
  surface_disruption   1 - Spearman rho between per-input (10x10x5) max|W1| of the shown network in displayed
                       positions (row j of the printed W1 placed at observation index j) and the original's
"""
from __future__ import annotations

import math

import numpy as np

import harness as H
import levels as LV

N_BOOT = 1000


# ----------------------------------------------------------------------------- measures

def _rescale_metrics(rs: H.Rescale) -> dict:
    total, table, bits, depth, n_aff = 0, 0, 0.0, 0, 0
    if rs.in_mul != 1:
        total += 1 * 500 * 32; table += 1; bits += LV.BITS_REAL; depth += 1; n_aff += 500 * 32
    if rs.out_mul != 1:
        total += 1 * (32 * 5 + 5); table += 1; bits += LV.BITS_REAL; depth = max(depth, 1); n_aff += 32 * 5 + 5
    return {"ops_per_weight": total / n_aff if n_aff else 0.0, "depth": depth, "affected_weights": n_aff,
            "table_entries": table, "total_ops": total, "log10_V": math.log10(1 + total + table),
            "desc_bits": bits, "anonymised": False}


def condition_metrics(cond) -> dict:
    return cond.variant.metrics() if cond.variant is not None else _rescale_metrics(cond.rescale)


def shown_network(cond, net: H.Network) -> H.Network:
    return cond.variant.apply(net) if cond.variant is not None else cond.rescale.apply(net)


def _ranks(a):
    order = np.argsort(a, kind="mergesort")
    r = np.empty(len(a))
    r[order] = np.arange(len(a))
    # average ties
    vals, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.bincount(inv, weights=r)
    return (sums / cnt)[inv]


def spearman(a, b) -> float:
    ra, rb = _ranks(np.asarray(a)), _ranks(np.asarray(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def surface_disruption(cond, net: H.Network) -> float:
    shown = shown_network(cond, net)
    return 1.0 - spearman(np.abs(shown.t["W1"]).max(1), np.abs(net.t["W1"]).max(1))


_CACHE: dict = {}


def run_metrics(cond, net_path, nid) -> dict:
    key = (cond.name, nid)
    if key not in _CACHE:
        m = dict(condition_metrics(cond))
        m["surface_disruption"] = surface_disruption(cond, H.Network.load(net_path, nid))
        _CACHE[key] = m
    return _CACHE[key]


# ----------------------------------------------------------------------------- sweep checks

def verify_sweep(conditions, networks, out_dir) -> bool:
    """Exactness at full precision and the effect of printing, on random observations."""
    rng = np.random.default_rng(1)
    xs = [(rng.random((2000, 500)) < 0.1).astype(float), rng.normal(size=(2000, 500))]
    ok = True
    print("== sweep: max |logit diff| vs the original network (2000 binary + 2000 gaussian inputs)")
    print("   'printed' = network as printed (>=3 sig. digits, >=3 decimals) vs full-precision original;")
    print("   reference: the paper's own 3-decimal print gives the 'L0 print' column")
    for cname, cond in conditions.items():
        v = cond.variant
        if v is None:
            continue
        for path, nid, game in networks:
            net = H.Network.load(path, nid)
            shown = v.apply(net)
            d_full = max(np.abs(v.forward(shown, x) - net.forward(x)).max() for x in xs)
            d_print = max(np.abs(v.forward(v.rounded(net), x) - net.forward(x)).max() for x in xs)
            d_ref = max(np.abs(H.rounded_network(net).forward(x) - net.forward(x)).max() for x in xs)
            good = d_full < 1e-8 and d_print <= 2 * d_ref + 1e-6
            ok &= good
            print(f"  {cname:28s} {game:9s} full {d_full:.1e}  printed {d_print:.1e}  L0 print {d_ref:.1e}  "
                  f"{'OK' if good else 'FAIL'}")
            (out_dir / f"{cname}_{nid}.txt").write_text(cond.prompt(net))
    return ok


# ----------------------------------------------------------------------------- logistic fits

def _fit(x, y, l2=1e-4, iters=100):
    """Logistic regression y ~ sigmoid(a + b x) by Newton/IRLS with a tiny ridge (handles separation)."""
    X = np.column_stack([np.ones_like(x), x])
    beta = np.zeros(2)
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X @ beta)))
        g = X.T @ (y - p) - l2 * np.r_[0, beta[1]]
        Hm = X.T @ (X * (p * (1 - p))[:, None]) + l2 * np.diag([1e-9, 1])
        step = np.linalg.solve(Hm, g)
        beta += step
        if np.abs(step).max() < 1e-9:
            break
    return beta


def logistic_report(rows, measure):
    x = np.array([r[measure] for r in rows], float)
    y = np.array([1.0 if r["correct"] else 0.0 for r in rows])
    xmax = float(x.max())
    res = {"measure": measure, "n": len(x), "failures": int((1 - y).sum()), "max_tested": xmax}
    if y.min() == 1:
        res.update(slope=None, c50=None, ci=None,
                   note=f"no failures: C50 lies beyond the largest value tested ({xmax:.3g})")
        return res
    sx = x.std() or 1.0
    a, b = _fit(x / sx, y)
    slope = b / sx
    c50 = -a / b * sx if b != 0 else math.inf
    rng = np.random.default_rng(0)
    boots = []
    for _ in range(N_BOOT):
        i = rng.integers(0, len(x), len(x))
        if y[i].min() == 1:
            boots.append(math.inf)
            continue
        if y[i].max() == 0:
            boots.append(-math.inf)
            continue
        ab, bb = _fit(x[i] / sx, y[i])
        boots.append(-ab / bb * sx if bb < 0 else math.inf)
    boots = np.sort(np.array(boots))  # may contain ±inf: take order statistics instead of interpolating
    lo, hi = boots[int(0.025 * (len(boots) - 1))], boots[int(math.ceil(0.975 * (len(boots) - 1)))]
    res["frac_boot_inf"] = float(np.isinf(boots).mean())
    res.update(slope=slope, c50=c50, ci=(lo, hi), intercept=a,
               note=("accuracy does not fall as this measure grows (failures sit at low values): no C50"
                     if slope >= 0 else "C50 beyond the largest value tested" if c50 > xmax else ""))
    return res


# ----------------------------------------------------------------------------- report

COLS = ["level", "d", "w", "ops_per_weight", "depth", "table_entries", "affected_weights", "log10_V",
        "desc_bits", "surface_disruption", "anonymised"]


def report(rows, order, root):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ok = [r for r in rows if r["ok"]]
    conds = []
    for c in order:
        rs = [r for r in ok if r["condition"] == c]
        if not rs:
            continue
        agg = {k: rs[0][k] for k in COLS}
        agg["surface_disruption"] = float(np.mean([r["surface_disruption"] for r in rs]))
        agg.update(condition=c, runs=len(rs), acc=np.mean([bool(r["correct"]) for r in rs]),
                   conf=np.mean([r["confidence"] for r in rs if r["confidence"] is not None]),
                   reas=np.mean([r["reasoning_tokens"] for r in rs if r["reasoning_tokens"] is not None]),
                   reas_min=min(r["reasoning_tokens"] for r in rs), reas_max=max(r["reasoning_tokens"] for r in rs),
                   inp=np.mean([r["input_tokens"] for r in rs]))
        conds.append(agg)

    L = ["# Complexity sweep: where does Astra stop recognising the game?", "",
         "Every condition computes exactly the same function as the original network (checked numerically, "
         "`python run.py verify`), states its transformation in the description and formula, and (sweep levels) "
         "prints weights at >= 3 significant digits and >= 3 decimals. Complexity measures follow Dziri et al. "
         "(2023): graph size |V|, depth, width; see `complexity.py` for the operation model.", "",
         "## Per-condition results", "",
         "| Condition | Level | d | w | ops/weight | depth | table | log10 V | desc bits | surface disr. | anon | runs | "
         "accuracy | mean conf | mean reasoning tok (min–max) | mean input tok |",
         "|" + "---|" * 16]
    for a in conds:
        L.append(f"| {a['condition']} | {a['level']} | {a['d']} | {a['w']} | {a['ops_per_weight']:.1f} | "
                 f"{a['depth']} | {a['table_entries']} | {a['log10_V']:.2f} | {a['desc_bits']:.0f} | "
                 f"{a['surface_disruption']:.3f} | {'yes' if a['anonymised'] else ''} | {a['runs']} | "
                 f"{a['acc']:.0%} | {a['conf']:.1f} | {a['reas']:,.0f} ({a['reas_min']:,}–{a['reas_max']:,}) | "
                 f"{a['inp']:,.0f} |")
    L += ["", "## Logistic fits of `correct` (all runs, including L0)", "",
          "| Measure | runs | failures | slope (per unit) | C50 | bootstrap 95% CI of C50 (1,000 resamples) | "
          "largest value tested | note |", "|---|---|---|---|---|---|---|---|"]
    fits = {}
    for m in ["log10_V", "desc_bits", "surface_disruption"]:
        f = logistic_report(ok, m)
        fits[m] = f
        fmt = lambda v: "∞" if v == math.inf else "-∞" if v == -math.inf else f"{v:.3g}"
        L.append(f"| {m} | {f['n']} | {f['failures']} | {fmt(f['slope']) if f['slope'] is not None else '–'} | "
                 f"{fmt(f['c50']) if f['c50'] is not None else '–'} | "
                 f"{('[' + fmt(f['ci'][0]) + ', ' + fmt(f['ci'][1]) + ']') if f['ci'] else '–'} | "
                 f"{f['max_tested']:.3g} | {f['note']} |")
    L += ["", "Bootstrap resamples with no failure count as C50 = ∞ (no break inside the resample).", ""]

    # complexity.png: 3 panels, accuracy + mean reasoning tokens vs each continuous measure
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    for ax, m, lab in zip(axes, ["log10_V", "desc_bits", "surface_disruption"],
                          ["log10 |V| (ops to undo + table entries)", "description bits",
                           "surface disruption (1 − Spearman ρ)"]):
        xs = np.array([a[m] for a in conds])
        acc = np.array([a["acc"] for a in conds])
        reas = np.array([a["reas"] for a in conds])
        anon = np.array([a["anonymised"] for a in conds])
        ax.scatter(xs[~anon], acc[~anon], c="#1f77b4", s=40, label="accuracy", zorder=3)
        ax.scatter(xs[anon], acc[anon], c="#1f77b4", marker="^", s=55, label="accuracy (anonymised)", zorder=3)
        f = fits[m]
        if f.get("slope") is not None:
            g = np.linspace(xs.min(), xs.max(), 200)
            ax.plot(g, 1 / (1 + np.exp(-(f["intercept"] + f["slope"] * g))), c="#1f77b4", lw=1, alpha=.6)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel(lab)
        ax.set_ylabel("accuracy", color="#1f77b4")
        ax2 = ax.twinx()
        ax2.scatter(xs, reas, c="#d62728", marker="x", s=40, label="mean reasoning tokens")
        ax2.set_ylabel("mean reasoning tokens", color="#d62728")
        ax2.set_ylim(0, max(reas) * 1.15)
        for a in conds:
            ax.annotate(a["level"], (a[m], a["acc"]), fontsize=6, alpha=.6, xytext=(2, -8),
                        textcoords="offset points")
    axes[0].legend(loc="lower left", fontsize=7)
    fig.suptitle("gpt-6-astra: which game? accuracy and reasoning effort vs transformation complexity")
    fig.tight_layout()
    fig.savefig(root / "complexity.png", dpi=130)
    plt.close(fig)

    # complexity_dw.png: accuracy, confidence, reasoning vs d and w
    fig, axes = plt.subplots(3, 2, figsize=(11, 9), sharex="col")
    for col, key in enumerate(["d", "w"]):
        xs = np.array([a[key] for a in conds], float)
        xp = np.log10(1 + xs) if key == "w" else xs
        for row, (k, lab) in enumerate([("acc", "accuracy"), ("conf", "mean confidence"),
                                        ("reas", "mean reasoning tokens")]):
            ax = axes[row, col]
            ys = np.array([a[k] for a in conds])
            anon = np.array([a["anonymised"] for a in conds])
            ax.scatter(xp[~anon], ys[~anon], s=35)
            ax.scatter(xp[anon], ys[anon], marker="^", s=50, label="anonymised channels")
            for a, xv, yv in zip(conds, xp, ys):
                ax.annotate(a["level"], (xv, yv), fontsize=6, alpha=.6, xytext=(2, 2), textcoords="offset points")
            ax.set_ylabel(lab)
            if row == 2:
                ax.set_xlabel("d (composed transformations)" if key == "d" else "log10(1 + w)  (w = parameters)")
    axes[0, 0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(root / "complexity_dw.png", dpi=130)
    plt.close(fig)

    L += ["## Notes", "",
          "- Only the input side is obfuscated in L2–L8. W2, b2, W3 and b3 are printed unchanged (at 3 significant "
          "digits), so the output layer's action usage (e.g. left/right dominant) stays readable and is a cue that no "
          "level removes.",
          "- Spot check (L6c, Breakout, r1): Astra claimed 10 decoded positions -> (row, col, channel); all 10 match "
          "p[F(j)] exactly, and it applied the composed factor k² correctly. It really undoes the depth-4 pipeline "
          "and is not just guessing from surface cues.",
          "- surface_disruption can exceed 1 (negative Spearman ρ, e.g. under per-channel scaling that inverts "
          "channel magnitude order).",
          "- log10_V uses log10(1 + V) so that untransformed conditions sit at 0. For L3/L6c, V includes recovering "
          "b1 from the offsets (32 × 500 × 4 ops), and ops/weight averages that in.",
          ""]
    L += ["![accuracy and reasoning vs complexity](complexity.png)", "",
          "![accuracy, confidence and reasoning vs d and w](complexity_dw.png)", ""]
    return L, conds, fits
