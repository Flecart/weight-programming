"""Animated explainer: what Astra sees as the Breakout network is hidden behind harder and harder (stated,
function-preserving) shuffles, what it has to compute to undo them, and how it did.

Left: the network exactly as shown in the prompt, drawn as a picture. Each W1 row is one input; its largest |weight|
is plotted at the grid cell the standard index formula assigns to that row position. Unshuffled, this picture IS the
game board (paddle row, ball area, brick rows), because inputs that never fire keep their tiny initial weights.
Right: the picture after decoding. The largest rows (the ones Astra decodes) fly to their true cell, recovered by
matching each shown row to the original network's rows.
Numbers are the real Breakout results (2-3 replies per condition) from astra_eval/results.csv.

Usage: python -I make_obfuscation_gif.py <astra_eval dir> <out.gif>
"""
import csv, collections, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch, Rectangle
from PIL import Image

ev, out = sys.argv[1], sys.argv[2]
NET = "a9f535cc"
CH = [(0, "agent"), (1, "moving objects"), (2, "reward targets")]
CONDS = [
    ("original", "No obfuscation", "the weights as trained", "0"),
    ("L4_flip", "Board flipped upside down", "stated: row r is shown as row 9 − r", "≈9"),
    ("L5_perm", "Random shuffle of all 500 inputs", "stated: the full 500-entry table", "1 table lookup"),
    ("P_aff", "Shuffle by a rule", "p(j) = (337·j + 141) mod 500", "3"),
    ("P_xs_1", "Rule: multiply-add, then XOR-shift", "1 round", "≈6"),
    ("P_xs_8", "Rule: multiply-add, then XOR-shift", "8 rounds", "≈42"),
    ("P_xs_32", "Rule: multiply-add, then XOR-shift", "32 rounds", "≈165"),
    ("P_sha", "Rule: order rows by SHA-256", "one short sentence to state it", "≈1,150,000"),
    ("P_sha_out", "SHA-256 on the rows AND the output columns", "even which output is which action is hidden", "≈1,150,000"),
]
BG, FG, MUTED, AMBER, BLUE, RED, GREEN = "#ffffff", "#1e1e1e", "#6c6c6c", "#d98a00", "#086ddd", "#e93147", "#16a34a"
TRACK, EDGE = "#eeeeee", "#d6d6d6"
K = 20  # rows decoded in the animation (Astra decodes a small sample)


def w1(path):
    lines = open(path).read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("W1 ("))
    return np.array([[float(x) for x in l.split()] for l in lines[i + 1:i + 501]])


orig = w1(f"{ev}/prompts/original_{NET}.txt")
res = collections.defaultdict(list)
for r in csv.DictReader(open(f"{ev}/results.csv")):
    if r["network"] == NET:
        res[r["condition"]].append(r)


def picture(rows_max, index_of_row):
    img = np.zeros((10, 10, 5))
    for j, v in enumerate(rows_max):
        q = index_of_row[j]
        img[(q // 5) // 10, (q // 5) % 10, q % 5] = v
    return img


def frame_images():
    om = np.abs(orig).max(1)
    vmax = [0.75 * om[c::5].max() for c in range(5)]
    for cond, title, sub, ops in CONDS:
        shown = w1(f"{ev}/prompts/{cond}_{NET}.txt")
        mags = np.abs(shown).max(1)
        # true original input of each shown row: nearest original row (shuffles only move rows; flip/perm keep values)
        d = ((shown[:, None, :] - orig[None, :, :]) ** 2).sum(-1)
        truth = d.argmin(1)
        shown_pic = picture(mags, np.arange(500))
        # Astra decodes a sample near the top of the listing: take the first K shown rows that carry real weight
        order = np.array([j for j in range(500) if mags[j] > 0.5][:K])
        runs = res[cond]
        acc = sum(r["correct"] == "True" for r in runs)
        conf = np.mean([float(r["confidence"]) for r in runs])
        toks = np.mean([float(r["reasoning_tokens"]) for r in runs])
        guesses = sorted({r["guess"] for r in runs})
        infeasible = cond.startswith("P_sha")
        n_frames = 30
        for f in range(n_frames):
            prog = min(1.0, max(0.0, (f - 4) / 18))  # decoding progress 0..1 over frames 4..22
            k_done = 0 if infeasible else int(round(prog * K))
            yield draw(cond, title, sub, ops, shown_pic, mags, truth, order[:k_done], vmax, prog, infeasible,
                       acc, len(runs), conf, toks, guesses, cond == "original"), (1600 if f == n_frames - 1 else 110)


def draw(cond, title, sub, ops, shown_pic, mags, truth, decoded, vmax, prog, infeasible, acc, n, conf, toks, guesses, ident):
    fig = plt.figure(figsize=(12, 5.6), dpi=80, facecolor=BG)
    fig.text(0.03, 0.93, title, color=FG, fontsize=20, fontweight="bold", family="DejaVu Sans")
    fig.text(0.03, 0.875, sub, color=MUTED, fontsize=13)
    fig.text(0.03, 0.78, "What Astra is shown", color=FG, fontsize=13, fontweight="bold")
    fig.text(0.53, 0.78, "What decoding recovers", color=FG, fontsize=13, fontweight="bold")
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("w", ["#f5f5f5", "#9cc3f2", BLUE, "#063f80"])
    axl, axr = [], []
    for i, (c, name) in enumerate(CH):
        for side, xs, store in ((0, 0.03, axl), (1, 0.53, axr)):
            ax = fig.add_axes([xs + i * 0.152, 0.30, 0.135, 0.42])
            ax.set_facecolor(BG); ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values(): s.set_color(EDGE)
            ax.set_title(name, color=MUTED, fontsize=10)
            if side == 0:
                ax.imshow(shown_pic[:, :, c], cmap=cmap, vmin=0, vmax=vmax[c])
            else:
                rec = np.zeros((10, 10))
                if ident and prog > 0:
                    rec = shown_pic[:, :, c] * min(1, prog * 1.5)
                for j in decoded:
                    q = truth[j]
                    if q % 5 == c:
                        rec[(q // 5) // 10, (q // 5) % 10] = mags[j]
                ax.imshow(rec, cmap=cmap, vmin=0, vmax=vmax[c])
                if infeasible and prog > 0.3:
                    ax.add_patch(Rectangle((-0.5, -0.5), 10, 10, color=BG, alpha=0.75))
                    ax.text(4.5, 4.5, "?", color=RED, fontsize=40, ha="center", va="center", fontweight="bold")
            if side == 1 and (prog >= 1 or (ident and prog > 0.6)) and not infeasible:
                lab = {0: ("paddle row", 6.6), 1: ("where the ball flies", 0.2), 2: ("bricks", 4.6)}[c]
                ax.text(4.5, lab[1], lab[0], color=FG, fontsize=9.5, ha="center", va="center",
                        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=EDGE, alpha=0.92))
            store.append(ax)
    # arrows from shown cell to true cell for the most recently decoded rows
    if not infeasible and not ident:
        for j in decoded[-4:]:
            cs, ct = j % 5, truth[j] % 5
            if cs > 2 or ct > 2:
                continue
            ps = ((j // 5) % 10, (j // 5) // 10)
            pt = ((truth[j] // 5) % 10, (truth[j] // 5) // 10)
            fig.add_artist(ConnectionPatch(ps, pt, "data", "data", axesA=axl[cs], axesB=axr[ct],
                                           color=BLUE, lw=1.6, alpha=0.9, arrowstyle="->"))
    # bottom band: cost, effort, verdict
    fig.text(0.03, 0.17, "Work to decode one row", color=MUTED, fontsize=11)
    fig.text(0.03, 0.105, ops if "lookup" in ops else f"{ops} operations", color=FG, fontsize=17, fontweight="bold")
    fig.text(0.34, 0.17, "Astra's reasoning tokens (mean)", color=MUTED, fontsize=11)
    bar = fig.add_axes([0.34, 0.095, 0.30, 0.05]); bar.set_xlim(0, 11000); bar.set_ylim(0, 1); bar.axis("off")
    bar.add_patch(Rectangle((0, 0), 11000, 1, color=TRACK))
    shown_toks = toks * min(1, prog * 1.3) if not infeasible else toks * min(1, prog * 3)
    bar.add_patch(Rectangle((0, 0), shown_toks, 1, color=RED if infeasible else BLUE))
    fig.text(0.65, 0.105, f"{shown_toks:,.0f}", color=FG, fontsize=15, fontweight="bold")
    fig.text(0.76, 0.17, "Answer (Breakout network)", color=MUTED, fontsize=11)
    if prog >= 1:
        ok = acc == n
        col = GREEN if ok else (AMBER if acc else RED)
        fig.text(0.76, 0.105, f"{acc}/{n} correct · {conf:.0f}%", color=col, fontsize=15, fontweight="bold")
        note = {"P_sha": "never hashes; falls back on the output layer",
                "P_sha_out": "\"I cannot reliably assign\nthe displayed W1 rows\""}.get(cond, "decoded a sample of rows by hand")
        if ident: note = "reads the board straight off the weights"
        fig.text(0.76, 0.075, note, color=MUTED, fontsize=10, va="top")
    fig.canvas.draw()
    im = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB")
    plt.close(fig)
    return im


frames, durations = [], []
for im, dur in frame_images():
    frames.append(im.quantize(colors=160, method=Image.Quantize.MEDIANCUT)); durations.append(dur)
frames[0].save(out, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True, disposal=2)
print(out, len(frames), "frames")
