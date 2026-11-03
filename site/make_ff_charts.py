"""Two charts for the Faith and Fate probe, from every arithmetic run so far:
  ff_accuracy.png  share of exact answers per size vs the paper's computation-graph size |V| (log), per task
  ff_tokens.png    reasoning tokens per reply vs |V|; filled = correct, hollow = wrong number, x = declined
Gateway failures are excluded. bsearch replies without an ANSWER line count as declined: the one such reply whose text
was saved (check_240.json) is an explicit decline, and every grid reply without one was too.
Palette validated with the dataviz validator (#086ddd, #d98a00 on white). Usage: python -I make_ff_charts.py <faith_fate_probe dir> <out dir>
"""
import collections, json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

src_dir, out_dir = sys.argv[1], sys.argv[2]
src = open(os.path.join(src_dir, "limit.py")).read().split("def ask(")[0]
ns = {}
exec(src.replace("env_path, out_path = sys.argv[1:3]", "env_path = None").replace("KEY = next", "KEY = None  #"), ns)
mult_graph, dp_graph = ns["mult_graph"], ns["dp_graph"]
V = lambda task, n: (mult_graph(n, n) if task == "multiplication" else dp_graph(n))["V"]
BLUE, ORANGE, INK, MUTED, GRID, EDGE = "#086ddd", "#d98a00", "#1e1e1e", "#6c6c6c", "#eeeeee", "#d6d6d6"
COL = {"multiplication": BLUE, "dp_nonadjacent": ORANGE}
NAME = {"multiplication": "n×n-digit multiplication", "dp_nonadjacent": "best non-adjacent sum (DP)"}

runs = []  # (task, size, outcome, reasoning_tokens)
for f in ("results.json", "limit_results.json"):
    for r in json.load(open(os.path.join(src_dir, f))):
        if str(r.get("raw_tail", "")).startswith("ERROR") or (r.get("answer") is None and r.get("reasoning_tokens") is None):
            continue
        runs.append((r["task"], r["size"], "correct" if r["correct"] else ("wrong" if r.get("answer") else "declined"), r["reasoning_tokens"]))
b = json.load(open(os.path.join(src_dir, "bsearch_results.json")))
for p in (b["probes"] if isinstance(b, dict) else b):
    for r in p["runs"]:
        if r.get("error"): continue
        runs.append((r["task"], r["size"], "correct" if r["correct"] else ("wrong" if r["answer"] else "declined"), r["reasoning_tokens"]))
for r in json.load(open(os.path.join(src_dir, "grid_results.json"))):
    if r["outcome"] == "error": continue
    runs.append((r["task"], r["size"], "declined" if r["outcome"] in ("declined", "no_answer") else r["outcome"], r["reasoning_tokens"]))
c240 = json.load(open(os.path.join(src_dir, "check_240.json")))
runs.append(("multiplication", 240, "declined", c240["usage"]["output_tokens_details"]["reasoning_tokens"]))

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})


def style(ax, ylabel):
    ax.set_xscale("log"); ax.set_facecolor("white")
    ax.grid(True, axis="y", color=GRID, lw=1); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(EDGE)
    ax.tick_params(colors=MUTED)
    ax.set_xlabel("Computation-graph size |V| (Faith and Fate's measure, log scale)", color=MUTED)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))


# chart 1: accuracy per size
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=150, facecolor="white")
for task, col in COL.items():
    by = collections.defaultdict(list)
    for t, n, o, _ in runs:
        if t == task: by[n].append(o == "correct")
    sizes = sorted(by)
    xs = [V(task, n) for n in sizes]; acc = [np.mean(by[n]) for n in sizes]
    ax.plot(xs, acc, color=col, lw=2, alpha=0.7, zorder=2)
    ax.scatter(xs, acc, s=[30 + 12 * len(by[n]) for n in sizes], color=col, edgecolor="white", linewidth=1.5, zorder=3)
    if task == "multiplication":  # label at its last exact size, just before the drop
        i = max(k for k, a in enumerate(acc) if a == 1.0)
        ax.annotate("multiplication", (xs[i], acc[i]), xytext=(8, 8), textcoords="offset points", ha="left", color=INK, fontsize=10)
    else:  # label at its 50% point
        i = min(range(len(acc)), key=lambda k: abs(acc[k] - 0.5))
        ax.annotate("DP (non-adjacent sum)", (xs[i], acc[i]), xytext=(10, -4), textcoords="offset points", ha="left", va="top", color=INK, fontsize=10)
ax.axhline(0.5, color=MUTED, lw=1, ls=(0, (4, 3)))
ax.annotate("50%", (12, 0.5), xytext=(0, 4), textcoords="offset points", color=MUTED, fontsize=9)
style(ax, "Share of exact answers")
ax.set_ylim(-0.04, 1.08); ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
fig.tight_layout(); fig.savefig(os.path.join(out_dir, "ff_accuracy.png"), facecolor="white"); plt.close(fig)

# chart 2: reasoning tokens per reply, by outcome
fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150, facecolor="white")
rng = np.random.default_rng(0)
for task, col in COL.items():
    for o in ("correct", "wrong", "declined"):
        pts = [(V(t, n) * np.exp(rng.normal(0, 0.05)), rt) for t, n, oo, rt in runs if t == task and oo == o and rt]
        if not pts: continue
        x, y = zip(*pts)
        if o == "correct":
            ax.scatter(x, y, s=40, color=col, edgecolor="white", linewidth=1.4, zorder=3)
        elif o == "wrong":
            ax.scatter(x, y, s=46, facecolor="white", edgecolor=col, linewidth=2, zorder=4)
        else:
            ax.scatter(x, y, s=48, marker="x", color=col, linewidth=2, zorder=4)
style(ax, "Reasoning tokens per reply")
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k" if v else "0"))
ax.legend(handles=[Line2D([], [], marker="o", ls="", color=BLUE, mec="white", ms=8, label="multiplication"),
                   Line2D([], [], marker="o", ls="", color=ORANGE, mec="white", ms=8, label="DP (non-adjacent sum)"),
                   Line2D([], [], marker="o", ls="", color=MUTED, mec="white", ms=8, label="exact answer"),
                   Line2D([], [], marker="o", ls="", mfc="white", mec=MUTED, mew=2, ms=8, label="wrong number"),
                   Line2D([], [], marker="x", ls="", color=MUTED, mew=2, ms=8, label="declined")],
          loc="upper left", frameon=False, fontsize=10, labelcolor=INK)
fig.tight_layout(); fig.savefig(os.path.join(out_dir, "ff_tokens.png"), facecolor="white"); plt.close(fig)
print("runs used:", len(runs), collections.Counter((t, o) for t, _, o, _ in runs))
