"""One simple chart: work needed to decode one input row (x, log scale) vs Astra's reasoning tokens (y).
Each dot is one reply (4 networks x 2 replies per rule; original has 3 per network). Filled = right game, hollow = wrong.
Palette validated with the dataviz validator (#086ddd, #d98a00 on white; orange gets direct labels for contrast).
Usage: python -I make_ops_tokens_chart.py <astra_eval dir> <out.png>
"""
import csv, collections, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches

ev, out = sys.argv[1], sys.argv[2]
BLUE, ORANGE, INK, MUTED, GRID = "#086ddd", "#d98a00", "#1e1e1e", "#6c6c6c", "#eeeeee"
FEASIBLE = [("original", "no shuffle"), ("P_aff", "affine rule"), ("P_xs_1", "XOR ×1"), ("P_xs_2", "×2"),
            ("P_xs_4", "×4"), ("P_xs_8", "×8"), ("P_xs_16", "×16"), ("P_xs_32", "×32")]
SHA = [("P_sha", "SHA-256 on inputs"), ("P_sha_out", "SHA-256 on inputs + outputs")]

rows = collections.defaultdict(list)
for r in csv.DictReader(open(f"{ev}/results.csv")):
    rows[r["condition"]].append(r)


def pts(cond):
    xs = np.array([max(1.0, float(r["ops_per_index"] or 0)) for r in rows[cond]])
    ys = np.array([float(r["reasoning_tokens"]) for r in rows[cond]])
    ok = np.array([r["correct"] == "True" for r in rows[cond]])
    return xs, ys, ok


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150, facecolor="white")
ax.set_facecolor("white")
rng = np.random.default_rng(0)
med_x, med_y, q25, q75 = [], [], [], []
for group, color in ((FEASIBLE, BLUE), (SHA, ORANGE)):
    for cond, label in group:
        xs, ys, ok = pts(cond)
        jit = xs * np.exp(rng.normal(0, 0.18 if group is SHA else 0.06, len(xs)))  # small horizontal jitter so replies don't overlap
        ax.scatter(jit[ok], ys[ok], s=46, color=color, edgecolor="white", linewidth=1.5, zorder=3)
        ax.scatter(jit[~ok], ys[~ok], s=46, facecolor="white", edgecolor=color, linewidth=2, zorder=3)
        if group is FEASIBLE:
            med_x.append(xs[0]); med_y.append(np.median(ys)); q25.append(np.percentile(ys, 25)); q75.append(np.percentile(ys, 75))
ax.fill_between(med_x, q25, q75, color=BLUE, alpha=0.12, lw=0, zorder=1)
ax.plot(med_x, med_y, color=BLUE, lw=2, zorder=2, alpha=0.6)
sx_all = [max(1.0, float(r['ops_per_index'])) for c, _ in SHA for r in rows[c]]
sy_all = [float(r['reasoning_tokens']) for c, _ in SHA for r in rows[c]]
ax.errorbar([np.median(sx_all)], [np.median(sy_all)], yerr=[[np.median(sy_all) - np.percentile(sy_all, 25)], [np.percentile(sy_all, 75) - np.median(sy_all)]],
            fmt='none', ecolor=ORANGE, elinewidth=2, capsize=6, zorder=4)
for (cond, label), x, y in zip(FEASIBLE, med_x, med_y):
    off = {"XOR ×1": (-8, 12), "×8": (-10, 8), "×32": (10, -2)}
    if label in off:
        ax.annotate(label, (x, y), xytext=off[label], textcoords="offset points", ha="left" if off[label][0] > 0 else "right", color=INK, fontsize=10)
sx = max(1.0, float(rows["P_sha"][0]["ops_per_index"]))
ax.annotate("SHA-256", (1.2e6, 900), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=10)
ax.set_xscale("log")
ax.set_xlim(0.6, 5e6); ax.set_ylim(0, 16500)
ax.set_xticks([1, 10, 100, 1e3, 1e4, 1e5, 1e6]); ax.set_xticklabels(["≤1", "10", "100", "1k", "10k", "100k", "1M"])
ax.set_xlabel("Operations to decode one input row (log scale)", color=MUTED)
ax.set_ylabel("Reasoning tokens per reply", color=MUTED)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k" if v else "0"))
ax.grid(True, axis="y", color=GRID, lw=1); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
for s in ("left", "bottom"): ax.spines[s].set_color("#d6d6d6")
ax.tick_params(colors=MUTED)
# legend: what filled / hollow means (identity is also carried by the direct labels)
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], marker="o", ls="", color=BLUE, markeredgecolor="white", ms=8, label="right game"),
                   Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor=BLUE, mew=2, ms=8, label="wrong game"),
                   Line2D([], [], marker="o", ls="", color=ORANGE, markeredgecolor="white", ms=8, label="SHA-256 rules"),
                   matplotlib.patches.Patch(color=BLUE, alpha=0.18, label="middle 50% of replies")],
          loc="upper right", frameon=False, fontsize=10, labelcolor=INK)
fig.tight_layout()
fig.savefig(out, facecolor="white")
print(out)
