"""Reusable harness: ask gpt-6-astra (via a local OpenAI-compatible gateway) which game a
policy network was trained on, from its weights alone.

Reproduces the protocol of repo/exp1_which_game (description + question + weights as text,
one message, one reply, no tools). Generic pieces:

  Network            the six actor tensors (W1 b1 W2 b2 W3 b3) in float64
  Rescale            an exactly function-preserving rescaling at the input and/or output
  render_weights()   the weights block, per-tensor decimals, header kept consistent
  build_prompt()     description (+ optional patch) + question + weights
  ask()              one Responses API call with retries; saves raw JSON, answer, summary, usage
  parse_answer()     Game: line + Confidence
  Rubric             maps a Game: line to a label by keywords (pluggable per condition)

The API key is read from AXONHUB_API_KEY in the .env file and never printed or logged.
"""
from __future__ import annotations

import json
import random
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import numpy as np

REPO = Path.home() / "Desktop/work/weight-programming/repo/exp1_which_game"
ENV_FILE = Path.home() / "Desktop/work/paxos/protocol-exchange/.env"
GATEWAY = "http://localhost:8090/v1"
MODEL = "gpt-6-astra"
# The paper ran Codex with model_instructions_file = runs/<game>/instructions.md (this one line).
INSTRUCTIONS = "Answer the user's request."

QUESTION = (
    "QUESTION. The weights below belong to one policy network that was trained with reinforcement learning "
    "to play a game on this grid. Which game was it trained on? Work from the weights. You have no tools: "
    "no code execution, no calculator, nothing to run. This is a single response.\n"
    "\n"
    "Answer in this order:\n"
    "Observations: <what you see in the weights: for each input channel, where in the grid its weights are "
    "large or show structure and what that suggests; what the output layer and its biases show about the "
    "actions; quote the weights you rely on>\n"
    "Reasoning: <which kinds of game fit these observations, which are ruled out, and why>\n"
    "Game: <the game, as specifically as you can; if it resembles a well-known game, give that game's name>\n"
    "Description: <what the agent does and what gives reward, in one or two sentences>\n"
    "Confidence: <0-100>%\n"
)
WEIGHTS_HEADING = "THE NETWORK'S WEIGHTS\n"

TENSORS = ["W1", "b1", "W2", "b2", "W3", "b3"]
NPZ_KEYS = {
    "W1": "actor/dense1/kernel", "b1": "actor/dense1/bias",
    "W2": "actor/dense2/kernel", "b2": "actor/dense2/bias",
    "W3": "actor/logits/kernel", "b3": "actor/logits/bias",
}
SECTION_TITLES = {
    "W1": "W1 (layer 1 weights), shape {shape}: one line per row (row i = input i), {cols} values per line",
    "b1": "b1 (layer 1 biases), shape {shape}:",
    "W2": "W2 (layer 2 weights), shape {shape}: one line per row",
    "b2": "b2 (layer 2 biases), shape {shape}:",
    "W3": "W3 (output layer weights), shape {shape}: one line per row",
    "b3": "b3 (output layer biases), shape {shape}:",
}


# ----------------------------------------------------------------------------- network

@dataclass
class Network:
    id: str
    t: dict  # tensor name -> float64 array

    @classmethod
    def load(cls, path: str | Path, id: str | None = None) -> "Network":
        """Load from an .npz (actor/dense1/kernel ... keys, or W1..b3 keys) or a weights .txt
        in the release format (values as printed)."""
        path = Path(path)
        nid = id or path.stem.replace("_actor", "")
        if path.suffix == ".npz":
            d = np.load(path, allow_pickle=False)
            t = {}
            for name in TENSORS:
                key = NPZ_KEYS[name] if NPZ_KEYS[name] in d.files else name
                t[name] = np.asarray(d[key], dtype=np.float64)
            return cls(nid, t)
        return cls(nid, parse_weights_txt(path.read_text()))

    def forward(self, x: np.ndarray) -> np.ndarray:
        t = self.t
        h1 = np.tanh(x @ t["W1"] + t["b1"])
        h2 = np.tanh(h1 @ t["W2"] + t["b2"])
        return h2 @ t["W3"] + t["b3"]


def parse_weights_txt(text: str) -> dict:
    t, cur, rows = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^(W[123]|b[123]) \(", line)
        if m:
            if cur:
                t[cur] = rows
            cur, rows = m.group(1), []
        elif cur and line.strip():
            rows.append([float(v) for v in line.split()])
    if cur:
        t[cur] = rows
    return {k: (np.array(v[0]) if k.startswith("b") else np.array(v)) for k, v in t.items()}


# ----------------------------------------------------------------------------- rescaling

@dataclass(frozen=True)
class Rescale:
    """Function-preserving rescaling.
    in_mul:  the network computes x' = in_mul * x and W1 is replaced by W1 / in_mul.
    out_mul: logits = (h2 @ W3' + b3') * out_mul with W3' = W3 / out_mul, b3' = b3 / out_mul.
    Printed decimals are shifted by log10 of the scale so each tensor keeps exactly the
    information of the 3-decimal original (W1/10 printed to 4 decimals, W1*10 to 2, ...)."""
    name: str
    in_mul: float = 1.0
    out_mul: float = 1.0

    def apply(self, net: Network) -> Network:
        t = dict(net.t)
        t["W1"] = t["W1"] / self.in_mul
        t["W3"] = t["W3"] / self.out_mul
        t["b3"] = t["b3"] / self.out_mul
        return Network(net.id, t)

    def forward(self, scaled: Network, x: np.ndarray) -> np.ndarray:
        t = scaled.t
        h1 = np.tanh((self.in_mul * x) @ t["W1"] + t["b1"])
        h2 = np.tanh(h1 @ t["W2"] + t["b2"])
        return (h2 @ t["W3"] + t["b3"]) * self.out_mul

    def decimals(self, base: int = 3) -> dict:
        din = int(round(np.log10(self.in_mul)))
        dout = int(round(np.log10(self.out_mul)))
        d = {k: base for k in TENSORS}
        d["W1"] = base + din
        d["W3"] = base + dout
        d["b3"] = base + dout
        for k, v in d.items():
            if v < 0:
                raise ValueError(f"{k}: negative decimals")
        return d

    @staticmethod
    def _fmt_mul(m: float) -> str:
        return f"{m:g}"

    def formula(self) -> tuple[str, str]:
        """(first-layer expression, logits expression) as they appear in the formula."""
        if self.in_mul == 1:
            l1 = "h1 = tanh(x @ W1 + b1)"
        elif self.in_mul > 1:
            l1 = f"h1 = tanh(({self._fmt_mul(self.in_mul)}·x) @ W1 + b1)"
        else:
            l1 = f"h1 = tanh((x / {self._fmt_mul(1 / self.in_mul)}) @ W1 + b1)"
        if self.out_mul == 1:
            l3 = "logits = h2 @ W3 + b3"
        elif self.out_mul > 1:
            l3 = f"logits = (h2 @ W3 + b3)·{self._fmt_mul(self.out_mul)}"
        else:
            l3 = f"logits = (h2 @ W3 + b3) / {self._fmt_mul(1 / self.out_mul)}"
        return l1, l3

    def sentences(self) -> str:
        s = []
        if self.in_mul > 1:
            s.append(f"The network first multiplies the observation by {self._fmt_mul(self.in_mul)}: "
                     f"{self.formula()[0]}.")
        elif self.in_mul < 1:
            s.append(f"The network first divides the observation by {self._fmt_mul(1 / self.in_mul)}: "
                     f"{self.formula()[0]}.")
        if self.out_mul > 1:
            s.append(f"The output layer's result is multiplied by {self._fmt_mul(self.out_mul)} to give the logits: "
                     f"{self.formula()[1]}.")
        elif self.out_mul < 1:
            s.append(f"The output layer's result is divided by {self._fmt_mul(1 / self.out_mul)} to give the logits: "
                     f"{self.formula()[1]}.")
        return " ".join(s)

    def description_patch(self) -> list[tuple[str, str]]:
        """(old, new) replacements on description.txt: formula lines + one explanatory sentence."""
        if self.in_mul == 1 and self.out_mul == 1:
            return []
        l1, l3 = self.formula()
        old1 = "  h1 = tanh(x @ W1 + b1)          W1: 500 x 32, b1: 32\n"
        old3 = "  logits = h2 @ W3 + b3           W3: 32 x 5,   b3: 5\n"
        col = len(old1) - len("W1: 500 x 32, b1: 32\n")  # shape column (34)
        pad = lambda s: "  " + s + " " * max(2, col - 2 - len(s))
        patch = [(old1, pad(l1) + "W1: 500 x 32, b1: 32\n"),
                 (old3, pad(l3) + "W3: 32 x 5,   b3: 5\n")]
        anchor = "Row i of W1 holds the weights"
        patch.append((anchor, self.sentences() + " " + anchor))
        return patch


IDENTITY = Rescale("original")


# ----------------------------------------------------------------------------- rendering

def fmt(v: float, dec: int) -> str:
    s = f"{v:.{dec}f}"
    if s.startswith("-") and float(s) == 0:  # the release prints 0.000, never -0.000
        s = s[1:]
    return s


def render_weights(net: Network, rescale: Rescale = IDENTITY, base_decimals: int = 3) -> str:
    """Weights block in the release format. With a rescale: the transformed tensors, the
    transformed forward-pass formula, and a precision statement that names per-tensor decimals."""
    scaled = rescale.apply(net)
    dec = rescale.decimals(base_decimals)
    l1, l3 = rescale.formula()
    fwd = f"Forward pass: {l1}; h2 = tanh(h1 @ W2 + b2); {l3}."
    odd = {k: v for k, v in dec.items() if v != base_decimals}
    if not odd:
        prec = f"Values rounded to {base_decimals} decimals."
    else:
        groups: dict[int, list[str]] = {}
        for k, v in odd.items():
            groups.setdefault(v, []).append(k)
        exc = "; ".join(f"{' and '.join(ks)} rounded to {v} decimals" for v, ks in sorted(groups.items()))
        prec = f"Values rounded to {base_decimals} decimals, except {exc}."
    out = [f"Policy network weights. {fwd} {prec}", ""]
    for k in TENSORS:
        a = scaled.t[k]
        title = SECTION_TITLES[k].format(shape=" x ".join(map(str, a.shape)),
                                         cols=a.shape[1] if a.ndim == 2 else "")
        if dec[k] != base_decimals:
            note = f", rounded to {dec[k]} decimals"
            title = title[:-1] + note + ":" if title.endswith(":") else title + note
        out.append(title)
        rows = a if a.ndim == 2 else a[None, :]
        out.extend(" ".join(fmt(v, dec[k]) for v in row) for row in rows)
        out.append("")
    return "\n".join(out[:-1]) + "\n"


def rounded_network(net: Network, rescale: Rescale = IDENTITY, base_decimals: int = 3) -> Network:
    """The network exactly as printed (for checking that rounding preserves information)."""
    scaled = rescale.apply(net)
    dec = rescale.decimals(base_decimals)
    return Network(net.id, {k: np.round(scaled.t[k], dec[k]) for k in TENSORS})


def apply_patch(text: str, patch: list[tuple[str, str]]) -> str:
    for old, new in patch:
        if text.count(old) != 1:
            raise ValueError(f"description patch anchor not found exactly once: {old[:60]!r}")
        text = text.replace(old, new)
    return text


def build_prompt(description: str, weights_text: str, question: str = QUESTION,
                 patch: list[tuple[str, str]] | None = None) -> str:
    desc = apply_patch(description, patch or [])
    if not desc.endswith("\n"):
        desc += "\n"
    return desc + "\n" + question + "\n" + WEIGHTS_HEADING + weights_text


# ----------------------------------------------------------------------------- answers

@dataclass
class Rubric:
    """Keyword rubric: label -> regexes searched in the Game: line. The keyword occurring
    earliest in the line wins (so 'Pong, not Breakout' -> pong)."""
    labels: dict
    aliases: dict = field(default_factory=dict)  # e.g. frogger counts as freeway (documented)

    def map(self, game_line: str | None) -> str:
        if not game_line:
            return "none"
        s = game_line.lower()
        best = None
        for label, pats in self.labels.items():
            for p in pats:
                m = re.search(p, s)
                if m and (best is None or m.start() < best[0]):
                    best = (m.start(), label)
        return best[1] if best else "other"


EXP1_RUBRIC = Rubric({
    "breakout": [r"break-?\s?out", r"arkanoid", r"brick"],
    "pong": [r"\bpong\b", r"wall-?pong", r"squash"],
    "pacman": [r"pac-?\s?man", r"ms\.? pac"],
    "freeway": [r"freeway", r"frogger", r"road[- ]crossing", r"traffic[- ]crossing", r"cross(ing)? the road"],
})


def _clean(s: str) -> str:
    s = re.sub(r"[*_`#]+", "", s).strip()
    return s.strip(" :")


def parse_answer(text: str) -> dict:
    """Extract the Game: line and Confidence from 'Game: ...' or a '## Game' heading layout."""
    game = None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        bare = _clean(line)
        m = re.match(r"^game\s*(?::\s*(.*))?$", bare, re.I)  # "Game: X", "**Game:** X", "## Game"
        if m:
            rest = _clean(m.group(1) or "")
            if rest:
                game = rest
            else:
                for nxt in lines[i + 1:]:
                    if nxt.strip():
                        game = _clean(nxt)
                        break
            break
    conf = None
    ms = re.findall(r"confidence[\s:*#_]*?(\d{1,3}(?:\.\d+)?)\s*(?:%|/\s*100)?", text, re.I)
    if ms:  # the last 'Confidence: N%' (the answer's final section)
        conf = float(ms[-1])
    return {"game_line": game, "confidence": conf}


# ----------------------------------------------------------------------------- model access

def _api_key() -> str:
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("AXONHUB_API_KEY="):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise RuntimeError("AXONHUB_API_KEY not found in .env")


class AdaptiveLimiter:
    """Process-wide cap on in-flight requests. Starts at `start`, grows by 1 after every `grow_after`
    clean successes up to `max_limit`, and halves on a 429 / 5xx / dropped connection."""

    def __init__(self, start=3, max_limit=3, grow_after=3):
        self.limit, self.max_limit, self.grow_after = start, max_limit, grow_after
        self.inflight, self.ok_streak = 0, 0
        self.cv = threading.Condition()
        self.events = []  # (time, 'grow'|'shrink', new limit)

    def configure(self, start, max_limit):
        with self.cv:
            self.limit, self.max_limit = start, max_limit
            self.cv.notify_all()

    def __enter__(self):
        with self.cv:
            while self.inflight >= self.limit:
                self.cv.wait()
            self.inflight += 1

    def __exit__(self, *a):
        with self.cv:
            self.inflight -= 1
            self.cv.notify_all()

    def success(self):
        with self.cv:
            self.ok_streak += 1
            if self.ok_streak >= self.grow_after and self.limit < self.max_limit:
                self.limit += 1
                self.ok_streak = 0
                self.events.append((time.time(), "grow", self.limit))
                self.cv.notify_all()

    def pressure(self):
        with self.cv:
            self.ok_streak = 0
            new = max(1, self.limit // 2)
            if new != self.limit:
                self.limit = new
                self.events.append((time.time(), "shrink", self.limit))


_SEM = AdaptiveLimiter()  # default: 3 in flight; run.py can raise it
RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524, 529}


def ask(prompt: str, out_dir: Path, *, model: str = MODEL, effort: str = "high",
        summary: str | None = "detailed", instructions: str = INSTRUCTIONS,
        max_attempts: int = 6, timeout_s: float = 1800, log=print) -> dict:
    """One fresh request (no tools, store=False). Saves response.json, answer.md,
    reasoning_summary.md and run.json in out_dir; skips if run.json says ok."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rec_path = out_dir / "run.json"
    if rec_path.exists():
        rec = json.loads(rec_path.read_text())
        if rec.get("ok"):
            return rec
    body = {"model": model, "instructions": instructions,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            "reasoning": {"effort": effort, **({"summary": summary} if summary else {})},
            "store": False}
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    errors, t0 = [], time.time()
    j, wall = None, None
    for attempt in range(1, max_attempts + 1):
        with _SEM:
            t1 = time.time()
            try:
                r = httpx.post(f"{GATEWAY}/responses", headers=headers, json=body, timeout=timeout_s)
                wall = time.time() - t1
                if r.status_code == 200:
                    j = r.json()
                    if j.get("status") in (None, "completed"):
                        _SEM.success()
                        break
                    errors.append({"attempt": attempt, "status": j.get("status"),
                                   "detail": str(j.get("incomplete_details") or j.get("error"))[:500]})
                    if j.get("status") == "incomplete":
                        break  # not transient; keep what we got
                else:
                    errors.append({"attempt": attempt, "http": r.status_code, "body": r.text[:500]})
                    if r.status_code not in RETRY_STATUS:
                        break
                    _SEM.pressure()
            except (httpx.TransportError, json.JSONDecodeError) as e:
                errors.append({"attempt": attempt, "exc": type(e).__name__, "msg": str(e)[:300]})
                _SEM.pressure()
        sleep = min(300, 10 * 2 ** (attempt - 1)) * (0.75 + 0.5 * random.random())
        log(f"[{out_dir}] attempt {attempt} failed ({errors[-1]}); retry in {sleep:.0f}s")
        time.sleep(sleep)

    rec = {"ok": False, "model": model, "effort": effort, "summary_requested": summary,
           "attempts": len(errors) + (1 if j and j.get("status") in (None, "completed") else 0),
           "errors": errors, "wall_s": round(wall, 1) if wall else None,
           "total_s": round(time.time() - t0, 1)}
    if j is not None:
        (out_dir / "response.json").write_text(json.dumps(j, indent=1, ensure_ascii=False))
        answer, summ, tools = [], [], []
        for item in j.get("output", []):
            if item.get("type") == "message":
                answer += [c.get("text", "") for c in item.get("content", []) if c.get("type") == "output_text"]
            elif item.get("type") == "reasoning":
                summ.append("\n".join(s.get("text", "") for s in item.get("summary", [])))
            else:
                tools.append(item.get("type"))
        text = "\n".join(answer)
        (out_dir / "answer.md").write_text(text)
        (out_dir / "reasoning_summary.md").write_text("\n\n---\n\n".join(summ))
        u = j.get("usage") or {}
        rec.update({
            "ok": bool(text.strip()) and j.get("status") in (None, "completed"),
            "status": j.get("status"), "response_id": j.get("id"),
            "usage": {"input_tokens": u.get("input_tokens"),
                      "cached_input_tokens": (u.get("input_tokens_details") or {}).get("cached_tokens"),
                      "output_tokens": u.get("output_tokens"),
                      "reasoning_output_tokens": (u.get("output_tokens_details") or {}).get("reasoning_tokens")},
            "reasoning_summary": summ, "non_message_items": tools,
        })
    rec_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    return rec
