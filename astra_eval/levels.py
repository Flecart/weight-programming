"""Graded obfuscation sweep (complexity levels L0s..L9).

Each Variant turns the original network into a shown network that computes exactly the same
function, states the transformation in the description and formula, prints all weights at
3 significant digits, and carries its complexity (d = number of composed transformations,
w = number of independent parameters to track), in the spirit of Dziri et al. 2023.

Input-side transformations are written as an affine map of the observation, x' = A x + c,
built from a list of steps applied in order. The shown first layer is W1' = A^-T W1 and
b1' = b1 - c @ W1', so x' @ W1' + b1' = x @ W1 + b1 for every x.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

import harness as H

N_IN = 500
SEED = 20261102
MIN_DECIMALS = 3   # never coarser than the 3-decimal original, so rescaling cannot lose information


# ----------------------------------------------------------------------------- formatting

def fmt_sig(v: float, sig: int = 3, min_dec: int | None = None) -> str:
    """Fixed-point with at least `sig` significant digits and at least MIN_DECIMALS decimals
    (0.0541, 4.066, 385.123, -0.000120); zero -> 0."""
    if v == 0 or not math.isfinite(v):
        return "0"
    e = math.floor(math.log10(abs(v)))
    dec = max(MIN_DECIMALS if min_dec is None else min_dec, sig - 1 - e)
    s = f"{v:.{dec}f}"
    if float(s) == 0:
        return "0"
    return s


def round_sig(a: np.ndarray, sig: int = 3, row_dec=None) -> np.ndarray:
    if row_dec is None or a.ndim == 1:
        return np.vectorize(lambda v: float(fmt_sig(v, sig)))(a)
    return np.array([[float(fmt_sig(v, sig, int(row_dec[j]))) for v in row] for j, row in enumerate(a)])


def render(shown: H.Network, forward_formula: str, sig: int = 3, transformed_input: bool = False,
           row_dec=None) -> str:
    extra = ""
    if row_dec is not None and max(row_dec) > MIN_DECIMALS:
        extra = (" Rows of W1 whose input x'_j is scaled up or offset get more decimals (up to "
                 f"{int(max(row_dec))}), so that no precision is lost relative to the original 3-decimal weights.")
    out = [f"Policy network weights. Forward pass: {forward_formula} Values rounded to {sig} significant digits "
           f"(and never to fewer than {MIN_DECIMALS} decimals).{extra}", ""]
    for k in H.TENSORS:
        a = shown.t[k]
        title = H.SECTION_TITLES[k].format(shape=" x ".join(map(str, a.shape)),
                                           cols=a.shape[1] if a.ndim == 2 else "")
        if transformed_input:
            title = title.replace("(row i = input i)", "(row j = position j of x')")
        out.append(title)
        rows = a if a.ndim == 2 else a[None, :]
        if k == "W1" and row_dec is not None:
            out.extend(" ".join(fmt_sig(v, sig, int(row_dec[j])) for v in row) for j, row in enumerate(rows))
        else:
            out.extend(" ".join(fmt_sig(v, sig) for v in row) for row in rows)
        out.append("")
    return "\n".join(out[:-1]) + "\n"


def _num(v: float) -> str:
    return f"{v:g}"


# ----------------------------------------------------------------------------- input steps

def obs_index(r, c, ch):
    return (r * 10 + c) * 5 + ch


def flip_index(j: int) -> int:
    cell, ch = divmod(j, 5)
    r, c = divmod(cell, 10)
    return obs_index(9 - r, c, ch)


@dataclass
class Step:
    kind: str                       # 'perm' | 'flip' | 'scale' | 'affine' | 'givens'
    w: int                          # independent parameters this step adds
    A: np.ndarray = None            # v_new = A v_old + c
    c: np.ndarray = None
    text: str = ""                  # how the step is stated
    table: str = ""                 # optional table printed after the steps
    # complexity of undoing this step for one affected W1 weight (Dziri et al.: graph size / depth)
    ops: int = 0                    # multiplies, adds, index-arithmetic steps, table lookups
    depth: int = 0                  # longest chain of dependent operations
    rows: int = N_IN                # W1 rows affected
    table_entries: int = 0          # numbers the reader must hold (table cells and stated constants)
    bits: float = 0.0               # description length of the step
    extra_ops: int = 0              # operations outside W1 (e.g. recovering b1 after an offset)


def step_perm(rng) -> Step:
    p = rng.permutation(N_IN)
    A = np.zeros((N_IN, N_IN))
    A[np.arange(N_IN), p] = 1
    lines = [f"  inputs {j}-{j + 9}: " + " ".join(str(v) for v in p[j:j + 10]) for j in range(0, N_IN, 10)]
    return Step("perm", N_IN, A, np.zeros(N_IN),
                "permutation: v'_j = v_{p[j]} for j = 0..499, where p is the PERMUTATION TABLE below "
                "(the value at position j after this step is the value at position p[j] before it)",
                "PERMUTATION TABLE p (each line lists p[j] for ten consecutive j)\n" + "\n".join(lines) + "\n",
                ops=OPS_PERM, depth=1, table_entries=N_IN, bits=log2_factorial(N_IN))


def step_flip() -> Step:
    f = np.array([flip_index(j) for j in range(N_IN)])
    A = np.zeros((N_IN, N_IN))
    A[np.arange(N_IN), f] = 1
    return Step("flip", 1, A, np.zeros(N_IN),
                "row flip: v'_j = v_{F(j)}, where for j = (r * 10 + c) * 5 + ch (r, c, ch read off the position j "
                "with the same formula as an observation index) F(j) = ((9 - r) * 10 + c) * 5 + ch",
                **FLIP_COST)


# ---- operation counts (derived from each step's undo rule; every multiply, add, index-arithmetic
# step and table lookup counts 1)
BITS_REAL = 16
OPS_PERM = 1        # W_orig[i] = W'[p^-1(i)]: one table lookup
# flip: cell = i // 5, ch = i % 5, r = cell // 10, c = cell % 10, 9 - r, *10, +c, *5, +ch
FLIP_OPS = ["//5", "%5", "//10", "%10", "9-r", "*10", "+c", "*5", "+ch"]
FLIP_DEPTH = 7      # (//5) -> (//10) -> (9-r) -> (*10) -> (+c) -> (*5) -> (+ch); %, // in parallel
FLIP_COST = dict(ops=len(FLIP_OPS), depth=FLIP_DEPTH, table_entries=0, bits=BITS_REAL)  # one constant (9)
OPS_SCALE = 3       # j mod 5, lookup k, multiply
OPS_GIVENS = 6      # lookup partner, lookup cos, lookup sin, 2 multiplies, 1 add  (depth 3)
BITS_RENAME = math.log2(math.factorial(5))


def log2_factorial(n: int) -> float:
    return math.lgamma(n + 1) / math.log(2)


K = [0.3, 7, -2, 0.05, 12]
M = [1, -0.5, 2, -3, 0.25]


def _kstr(name, vals):
    return ", ".join(f"{name}_{i} = {_num(v)}" for i, v in enumerate(vals))


def step_scale(channel_note: bool) -> Step:
    k = np.array([K[j % 5] for j in range(N_IN)])
    note = " (here j mod 5 is the channel of input j)" if channel_note else ""
    return Step("scale", 5, np.diag(k), np.zeros(N_IN),
                f"scale by position: v'_j = k_(j mod 5) · v_j{note}, with {_kstr('k', K)}",
                ops=OPS_SCALE, depth=3, table_entries=5, bits=5 * BITS_REAL)


def step_affine(channel_note: bool) -> Step:
    k = np.array([K[j % 5] for j in range(N_IN)])
    m = np.array([M[j % 5] for j in range(N_IN)])
    note = " (here j mod 5 is the channel of input j)" if channel_note else ""
    return Step("affine", 10, np.diag(k), m,
                f"affine by position: v'_j = k_(j mod 5) · v_j + m_(j mod 5){note}, with {_kstr('k', K)} "
                f"and {_kstr('m', M)}",
                ops=OPS_SCALE, depth=3, table_entries=10, bits=10 * BITS_REAL,
                # b1 = b1' + sum_j m_(j mod 5) * W1'[j]: per bias 500 x (mod, lookup, multiply, add)
                extra_ops=32 * N_IN * 4)


def step_givens(g: int, rng) -> Step:
    idx = rng.permutation(N_IN)[: 2 * g]
    pairs = [tuple(sorted((int(idx[2 * a]), int(idx[2 * a + 1])))) for a in range(g)]
    pairs.sort()
    angles = rng.integers(10, 171, size=g)  # whole degrees, 10..170
    A = np.eye(N_IN)
    lines = []
    for (i, j), deg in zip(pairs, angles):
        t = math.radians(int(deg))
        cs, sn = math.cos(t), math.sin(t)
        A[i, i], A[i, j], A[j, i], A[j, j] = cs, -sn, sn, cs
        lines.append(f"  ({i}, {j}): θ = {int(deg)}°  (cos θ ≈ {cs:.4f}, sin θ ≈ {sn:.4f})")
    return Step("givens", g, A, np.zeros(N_IN),
                f"rotations: {g} Givens rotations on disjoint pairs of positions (i, j), listed in the ROTATION TABLE "
                "below; for each pair, v'_i = cos θ · v_i − sin θ · v_j and v'_j = sin θ · v_i + cos θ · v_j; "
                "every position not in the table is unchanged (v'_k = v_k). G is orthogonal, so the shown "
                "W1 = G · W_orig and W_orig = Gᵀ · W1: rows i and j of the shown W1 are the rotation of the "
                "original rows i and j by the same angle",
                f"ROTATION TABLE ({g} pairs (i, j) with angle θ)\n" + "\n".join(lines) + "\n",
                ops=OPS_GIVENS, depth=3, rows=2 * g, table_entries=3 * g,
                bits=g * (math.log2(math.comb(N_IN, 2)) + BITS_REAL))


# ----------------------------------------------------------------------------- variants

DESC_FLATTEN = ("The observation is flattened to 500 numbers. Input number i = (row * 10 + column) * 5 + channel; "
                "for example input 0 is (row 0, column 0, channel 0), input 4 is (row 0, column 0, channel 4), "
                "input 5 is (row 0, column 1, channel 0) and input 499 is (row 9, column 9, channel 4).")
DESC_FLATTEN_FLIPPED = ("The observation is flattened to 500 numbers in bottom-to-top row order. Input number i = "
                        "((9 - row) * 10 + column) * 5 + channel; for example input 0 is (row 9, column 0, channel 0), "
                        "input 4 is (row 9, column 0, channel 4), input 5 is (row 9, column 1, channel 0), input 50 "
                        "is (row 8, column 0, channel 0) and input 499 is (row 0, column 9, channel 4).")
L1_LINE = "  h1 = tanh(x @ W1 + b1)          W1: 500 x 32, b1: 32\n"
ROW_SENT = "Row i of W1 holds the weights from input i to the 32 hidden units;"

def anonymise(desc: str) -> str:
    """Channel meanings and game hints removed (L8)."""
    old_grid = ("The network sees a 10 x 10 grid. Rows are numbered 0 (top) to 9 (bottom) and columns 0 (left) to 9 "
                "(right). The outer ring of cells (row 0, row 9, column 0 and column 9) is a wall border; the playable "
                "area is the inner 8 x 8 cells (rows 1-8, columns 1-8).\n")
    new_grid = ("The network sees a 10 x 10 grid. Rows are numbered 0 (top) to 9 (bottom) and columns 0 (left) to 9 "
                "(right).\n")
    start = desc.index("Each cell has 5 binary channels")
    end = desc.index("The observation is flattened")
    new_ch = ("Each cell has 5 binary channels (0 or 1), labelled A to E; what they represent is not given:\n"
              "  channel 0  channel A\n  channel 1  channel B\n  channel 2  channel C\n"
              "  channel 3  channel D\n  channel 4  channel E\n")
    desc = desc[:start] + new_ch + desc[end:]
    return H.apply_patch(desc, [(old_grid, new_grid)])


@dataclass
class Variant:
    name: str
    level: str
    d: int
    w: int
    axis: str = "arithmetic"            # 'arithmetic' | 'semantic' | 'control' | 'format'
    steps: list = field(default_factory=list)   # input pipeline (x' = A x + c)
    flatten_flipped: bool = False       # L4: restated index formula instead of a step
    anonymous: bool = False             # L8
    hidden_symmetry: bool = False       # L9 (not stated)
    sig: int = 3
    out_perm: object = None             # stated output-column permutation q: logit column m = action q(m)
    out_text: str = ""                  # its statement (added to THE ACTIONS)
    kt: dict = None                     # description-length / computation accounting (kt.py)

    # -- the map from the observation to the shown network's input
    def input_map(self):
        A, c = np.eye(N_IN), np.zeros(N_IN)
        if self.flatten_flipped:
            f = np.array([flip_index(j) for j in range(N_IN)])
            P = np.zeros((N_IN, N_IN))
            P[np.arange(N_IN), f] = 1
            A = P
        for s in self.steps:
            A, c = s.A @ A, s.A @ c + s.c
        return A, c

    def apply(self, net: H.Network) -> H.Network:
        t = dict(net.t)
        A, c = self.input_map()
        W1 = np.linalg.solve(A.T, t["W1"])           # A^-T W1
        t["W1"], t["b1"] = W1, t["b1"] - c @ W1
        if self.hidden_symmetry:
            rng = np.random.default_rng(SEED + 9)
            p1, p2 = rng.permutation(32), rng.permutation(32)
            s1, s2 = rng.choice([-1.0, 1.0], 32), rng.choice([-1.0, 1.0], 32)
            t["W1"], t["b1"] = t["W1"][:, p1] * s1, t["b1"][p1] * s1
            W2 = t["W2"][p1, :] * s1[:, None]
            t["W2"], t["b2"] = W2[:, p2] * s2, t["b2"][p2] * s2
            t["W3"] = t["W3"][p2, :] * s2[:, None]
        if self.out_perm is not None:
            q = np.asarray(self.out_perm)
            t["W3"], t["b3"] = t["W3"][:, q], t["b3"][q]
        return H.Network(net.id, t)

    def forward(self, shown: H.Network, x: np.ndarray) -> np.ndarray:
        """Shown network evaluated on an observation (x as in the original indexing), rows = samples."""
        A, c = self.input_map()
        out = shown.forward(x @ A.T + c)
        if self.out_perm is not None:  # undo the stated output permutation: action q(m) <- column m
            res = np.empty_like(out)
            res[:, np.asarray(self.out_perm)] = out
            out = res
        return out

    # -- prompt
    def has_input_steps(self):
        return bool(self.steps)

    def formula(self) -> str:
        xin = "x'" if self.steps else "x"
        return f"h1 = tanh({xin} @ W1 + b1); h2 = tanh(h1 @ W2 + b2); logits = h2 @ W3 + b3."

    def description(self, desc: str) -> str:
        if self.anonymous:
            desc = anonymise(desc)
        if self.flatten_flipped:
            desc = H.apply_patch(desc, [(DESC_FLATTEN, DESC_FLATTEN_FLIPPED)])
        if self.out_text:
            anchor = "  action 4  right (toward column 9)\n"
            desc = H.apply_patch(desc, [(anchor, anchor + self.out_text + "\n")])
        if not self.steps:
            return desc
        n = len(self.steps)
        desc = H.apply_patch(desc, [
            (L1_LINE, "  h1 = tanh(x' @ W1 + b1)         W1: 500 x 32, b1: 32\n"),
            (ROW_SENT, "Here x' is the transformed observation defined in THE INPUT TRANSFORMATION below, and row j "
                       "of W1 holds the weights from x'_j (position j of x') to the 32 hidden units;"),
        ])
        lines = ["", "THE INPUT TRANSFORMATION",
                 f"Before the first layer, the 500 observation numbers x (indexed as above) are transformed into x' "
                 f"in {n} step{'s' if n > 1 else ''}, applied in this order (v is the vector before a step, v' the "
                 f"vector after it; the first step starts from v = x and the last step gives x'). The network was "
                 f"rewritten so that it computes exactly the same function of x as before the transformation:"]
        for i, s in enumerate(self.steps, 1):
            lines.append(f"  step {i}, {s.text}.")
        tables = [s.table for s in self.steps if s.table]
        out = desc.rstrip("\n") + "\n" + "\n".join(lines) + "\n"
        if tables:
            out += "\n" + "\n".join(tables)
        return out

    def prompt(self, net: H.Network, description: str, question: str = H.QUESTION) -> str:
        shown = self.apply(net)
        return H.build_prompt(self.description(description), render(shown, self.formula(), self.sig, bool(self.steps),
                                                                        self.row_decimals()), question)

    def cost_steps(self):
        """Steps the reader has to undo (the restated flattening of L4 counts as a flip)."""
        st = list(self.steps)
        if self.flatten_flipped:
            st = [Step("flip", 1, **FLIP_COST)] + st
        return st

    def metrics(self) -> dict:
        st = self.cost_steps()
        n_aff = max([s.rows for s in st], default=0) * 32
        total = sum(s.ops * s.rows * 32 + s.extra_ops for s in st)
        table = sum(s.table_entries for s in st)
        bits = sum(s.bits for s in st) + (BITS_RENAME if self.anonymous else 0.0)
        return {"ops_per_weight": total / n_aff if n_aff else 0.0, "depth": sum(s.depth for s in st),
                "affected_weights": n_aff, "table_entries": table, "total_ops": total,
                "log10_V": math.log10(1 + total + table), "desc_bits": bits,
                "anonymised": self.anonymous}

    def row_decimals(self) -> np.ndarray:
        """Decimals per W1 row: x'_j = sum_i A[j,i] x_i + c_j can be up to s_j = sum_i |A[j,i]| + |c_j| in size,
        so a rounding error in W1'[j] is amplified by s_j; add ceil(log10 s_j) decimals (one more if offset),
        which keeps the printed network at least as precise as the 3-decimal original."""
        A, c = self.input_map()
        s = np.abs(A).sum(1) + np.abs(c)
        return MIN_DECIMALS + np.ceil(np.log10(np.maximum(s, 1.0)) - 1e-9).astype(int) + (np.abs(c) > 0)

    def rounded(self, net: H.Network) -> H.Network:
        shown = self.apply(net)
        rd = self.row_decimals()
        return H.Network(net.id, {k: round_sig(v, self.sig, rd if k == "W1" else None) for k, v in shown.t.items()})


def make_variants() -> dict:
    rng = lambda k: np.random.default_rng(SEED + k)
    perm5 = step_perm(rng(5))  # the same permutation table for L5 and L6
    V = [
        Variant("L0s_sig3", "L0s", 0, 0, axis="format"),
        Variant("L2_chscale", "L2", 1, 5, steps=[step_scale(True)]),
        Variant("L3_chaffine", "L3", 2, 10, steps=[step_affine(True)]),
        Variant("L4_flip", "L4", 1, 1, flatten_flipped=True),
        Variant("L5_perm", "L5", 1, 500, steps=[perm5]),
        Variant("L6a_flip_scale", "L6", 2, 6, steps=[step_flip(), step_scale(True)]),
        Variant("L6b_perm_flip_scale", "L6", 3, 506, steps=[perm5, step_flip(), step_scale(False)]),
        Variant("L6c_perm_flip_scale_affine", "L6", 4, 516,
                steps=[perm5, step_flip(), step_scale(False), step_affine(False)]),
        Variant("L7_givens10", "L7", 1, 10, steps=[step_givens(10, rng(7))]),
        Variant("L7_givens50", "L7", 1, 50, steps=[step_givens(50, rng(7))]),
        Variant("L7_givens250", "L7", 1, 250, steps=[step_givens(250, rng(7))]),
        Variant("L8_anon", "L8", 0, 0, axis="semantic", anonymous=True),
        Variant("L8_anon_flip", "L8", 1, 1, axis="semantic", anonymous=True, flatten_flipped=True),
        Variant("L9_hidden_perm_sign", "L9", 0, 0, axis="control", hidden_symmetry=True),
    ]
    return {v.name: v for v in V}


VARIANTS = make_variants()
