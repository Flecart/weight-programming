"""Apply an `edits` block (the weight-writing language of exp5 prompts) to an all-zero 600-32-32-6 network.

Language (from runs/<game>/message.txt, "HOW TO WRITE THE WEIGHTS"):
  - only the LAST code block whose opening line is ```edits is read
  - one statement per line, '#' starts a comment, a long list may continue over the next lines
  - tensors W1 (600x32), b1 (32), W2 (32x32), b2 (32), W3 (32x6), b3 (6); every weight starts at 0
  - TENSOR[idx] = v | += v | -= v | *= v ; idx per axis is an int or a:b / a:b:s (half-open; ':' = whole axis)
  - v is a number, a list (as many values as entries) or a 2-D list for a 2-D block
  - statements apply in order; a statement that cannot be read is skipped, the others still apply
  - values are plain decimal numbers with |v| <= 1e6

Reader rules where the prompt is silent (recorded in the report under "lenient" when they fire):
  - a 2-D list may be written '[ [' with spaces/newlines anywhere (the paper's final reader accepts this)
  - a flat list whose length equals the size of a 2-D block is filled row-major ("flat_into_2d")
  - an integer index out of range, an empty selection, a shape mismatch, a non-number or |v| > 1e6 is an error
  - if the last ```edits block has no closing fence, cut_off = True and the statements present are read; a final
    statement with unbalanced brackets is an error (skipped)

Usage: python -I apply_edits.py <answer.md> <out.npz> [<report.json>]
"""
import json
import re
import sys

import numpy as np

SHAPES = {"W1": (600, 32), "b1": (32,), "W2": (32, 32), "b2": (32,), "W3": (32, 6), "b3": (6,)}
NPZ_KEYS = {"W1": "actor/dense1/kernel", "b1": "actor/dense1/bias", "W2": "actor/dense2/kernel",
            "b2": "actor/dense2/bias", "W3": "actor/logits/kernel", "b3": "actor/logits/bias"}
VMAX = 1e6
NUM = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
STMT = re.compile(r"^\s*(W1|b1|W2|b2|W3|b3)\s*\[([^\[\]]*)\]\s*(=|\+=|-=|\*=)\s*(.*?)\s*$", re.S)


class EditError(Exception):
    pass


def extract_block(text):
    """Return (lines of the last ```edits block, closed?) or (None, False) if there is none."""
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if re.match(r"^\s*```edits\s*$", l)]
    if not starts:
        return None, False
    s = starts[-1]
    for j in range(s + 1, len(lines)):
        if re.match(r"^\s*```\s*$", lines[j]):
            return lines[s + 1:j], True
    return lines[s + 1:], False


def split_statements(lines):
    """Join continuation lines (open brackets) into statements. Returns list of (first_line_no, text, complete)."""
    out, buf, start, depth = [], [], None, 0
    for n, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0]
        if not buf and not line.strip():
            continue
        if not buf:
            start = n
        buf.append(line)
        depth += line.count("[") - line.count("]")
        if depth <= 0:
            out.append((start, " ".join(x.strip() for x in buf), depth == 0))
            buf, depth = [], 0
    if buf:
        out.append((start, " ".join(x.strip() for x in buf), False))
    return out


def parse_index(s, shape):
    parts = [p.strip() for p in s.split(",")]
    if len(parts) != len(shape):
        raise EditError(f"{len(parts)} indices for a {len(shape)}-D tensor")
    idx = []
    for p, dim in zip(parts, shape):
        if ":" in p:
            f = p.split(":")
            if len(f) > 3:
                raise EditError(f"bad slice {p!r}")
            vals = []
            for x in f:
                x = x.strip()
                if x == "":
                    vals.append(None)
                elif re.fullmatch(r"[+-]?\d+", x):
                    vals.append(int(x))
                else:
                    raise EditError(f"bad slice {p!r}")
            if len(vals) == 3 and vals[2] is not None and vals[2] <= 0:
                raise EditError(f"bad step in {p!r}")
            idx.append(slice(*vals))
        else:
            if not re.fullmatch(r"[+-]?\d+", p):
                raise EditError(f"bad index {p!r}")
            i = int(p)
            if not -dim <= i < dim:
                raise EditError(f"index {i} out of range for axis of size {dim}")
            idx.append(i)
    return tuple(idx)


def parse_value(s):
    """Number or nested list of numbers. Returns float or list."""
    pos = 0
    s = s.strip()

    def ws():
        nonlocal pos
        while pos < len(s) and s[pos].isspace():
            pos += 1

    def val():
        nonlocal pos
        ws()
        if pos < len(s) and s[pos] == "[":
            pos += 1
            items = []
            ws()
            if pos < len(s) and s[pos] == "]":
                pos += 1
                return items
            while True:
                items.append(val())
                ws()
                if pos < len(s) and s[pos] == ",":
                    pos += 1
                    ws()
                    if pos < len(s) and s[pos] == "]":  # trailing comma
                        pos += 1
                        return items
                    continue
                if pos < len(s) and s[pos] == "]":
                    pos += 1
                    return items
                raise EditError(f"bad list near {s[pos:pos + 20]!r}")
        m = NUM.match(s, pos)
        if not m:
            raise EditError(f"not a number near {s[pos:pos + 20]!r}")
        pos = m.end()
        return float(m.group())

    v = val()
    ws()
    if pos != len(s):
        raise EditError(f"trailing text {s[pos:pos + 20]!r}")
    return v


def apply_text(text):
    net = {k: np.zeros(v, dtype=np.float64) for k, v in SHAPES.items()}
    lines, closed = extract_block(text)
    rep = {"block": lines is not None, "statements": 0, "applied": 0, "entries_written": 0, "errors": [],
           "cut_off": bool(lines is not None and not closed), "tensors_touched": [], "lenient": []}
    if lines is None:
        return net, rep
    touched = set()
    for ln, st, complete in split_statements(lines):
        rep["statements"] += 1
        try:
            if not complete:
                raise EditError("unbalanced brackets (statement incomplete)")
            m = STMT.match(st)
            if not m:
                raise EditError("not a statement")
            name, idxs, op, vs = m.groups()
            idx = parse_index(idxs, SHAPES[name])
            target = net[name][idx]
            if target.size == 0:
                raise EditError("empty selection")
            v = parse_value(vs)
            arr = np.array(v, dtype=np.float64)
            if arr.dtype == object or (isinstance(v, list) and arr.ndim == 0):
                raise EditError("ragged list")
            if not np.all(np.isfinite(arr)) or np.any(np.abs(arr) > VMAX):
                raise EditError("value out of range")
            if arr.ndim > 0 and arr.shape != target.shape:
                if arr.ndim == 1 and target.ndim == 2 and arr.size == target.size:
                    arr = arr.reshape(target.shape)
                    rep["lenient"].append({"line": ln, "rule": "flat_into_2d"})
                else:
                    raise EditError(f"value shape {arr.shape} != selection shape {target.shape}")
            if op == "=":
                net[name][idx] = arr
            elif op == "+=":
                net[name][idx] = target + arr
            elif op == "-=":
                net[name][idx] = target - arr
            else:
                net[name][idx] = target * arr
            rep["applied"] += 1
            rep["entries_written"] += int(target.size)
            touched.add(name)
        except EditError as e:
            rep["errors"].append({"line": ln, "statement": st[:200], "error": str(e)})
    rep["tensors_touched"] = sorted(touched)
    return net, rep


def summarize(net):
    nz = {k: int(np.count_nonzero(v.astype(np.float32))) for k, v in net.items()}
    return {"nonzero": nz, "nonzero_total": sum(nz.values()), "parameters": int(sum(v.size for v in net.values())),
            "max_abs": {k: float(np.abs(v).max()) for k, v in net.items()}}


def save_npz(net, path):
    np.savez(path, **{NPZ_KEYS[k]: v.astype(np.float32) for k, v in net.items()})


def main():
    text = open(sys.argv[1]).read()
    net, rep = apply_text(text)
    save_npz(net, sys.argv[2])
    out = {"edit_report": rep, **summarize(net)}
    if len(sys.argv) > 3:
        json.dump(out, open(sys.argv[3], "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("statements", "applied", "entries_written", "cut_off")}),
          "errors", len(rep["errors"]), "nonzero", out["nonzero_total"])


if __name__ == "__main__":
    main()
