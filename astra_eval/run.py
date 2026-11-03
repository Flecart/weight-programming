"""Conditions, prompt checks, runs and summary for the 'which game' evaluation.

  python run.py verify                  # prompt byte-identity + forward-pass checks, writes prompts/
  python run.py run [--only COND ...]   # ask Astra (<=3 concurrent), resumable (skips finished runs)
  python run.py summarize               # results.csv / results.json / summary.md
  python run.py ask NETWORK [--description F] [--patch F.json] [--rescale NAME] [--rubric F.json]
                    [--truth LABEL] [--replicas N] [--condition NAME]
                                        # any network file (.npz or weights .txt) through the same harness

A condition = (name, list of (network path, id, truth), rescale, description, patch, rubric, replicas).
Novel-game networks plug in as new Condition entries (own description file and rubric).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import harness as H
import levels as LV
import complexity as CX
import kt as KT

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
NETS = H.REPO / "networks"
PAPER = {"a9f535cc": "breakout", "dfc6cb65": "pong", "bdf99279": "pacman", "0bbcc3ea": "freeway"}

RESCALES = {
    "original": H.IDENTITY,
    "x10_input": H.Rescale("x10_input", in_mul=10),
    "div10_input": H.Rescale("div10_input", in_mul=0.1),
    "x10_output": H.Rescale("x10_output", out_mul=10),
    "div10_output": H.Rescale("div10_output", out_mul=0.1),
}


@dataclass
class Condition:
    name: str
    networks: list            # [(path, id, truth)]
    rescale: H.Rescale = H.IDENTITY
    replicas: int = 1
    description_file: Path = NETS / "description.txt"
    patch: list = field(default_factory=list)   # extra (old, new) replacements on the description
    rubric: H.Rubric = field(default_factory=lambda: H.EXP1_RUBRIC)
    question: str = H.QUESTION
    variant: object = None                      # a levels.Variant (complexity sweep), overrides rescale
    level: str = ""
    d: int = 0
    w: int = 0
    axis: str = "arithmetic"

    def prompt(self, net: H.Network) -> str:
        desc = self.description_file.read_text()
        if self.variant is not None:
            return self.variant.prompt(net, desc, self.question)
        return H.build_prompt(desc, H.render_weights(net, self.rescale), self.question,
                              patch=self.rescale.description_patch() + list(self.patch))


def paper_networks():
    return [(NETS / f"{i}.npz", i, g) for i, g in PAPER.items()]


CONDITIONS = {
    "original": Condition("original", paper_networks(), H.IDENTITY, replicas=3, level="L0", d=0, w=0, axis="baseline"),
    **{n: Condition(n, paper_networks(), RESCALES[n], replicas=2, level="L1" if n == "x10_input" else "L1'",
                    d=1, w=1)
       for n in ["x10_input", "div10_input", "x10_output", "div10_output"]},
    **{v.name: Condition(v.name, paper_networks(), replicas=2, variant=v, level=v.level, d=v.d, w=v.w, axis=v.axis)
       for v in LV.VARIANTS.values()},
    **{v.name: Condition(v.name, paper_networks(), replicas=2, variant=v, level=v.level, d=v.d, w=v.w, axis=v.axis)
       for v in KT.VARIANTS.values()},
    # Hook: novel networks, e.g.
    # "novel_snake": Condition("novel_snake", [(Path(".../snake.npz"), "abcd1234", "snake")],
    #                          description_file=Path(".../snake_description.txt"),
    #                          rubric=H.Rubric({"snake": [r"snake", r"nibbles"]}), replicas=2),
}


# ----------------------------------------------------------------------------- verify

def verify(only=None) -> bool:
    ok = True
    pdir = ROOT / "prompts"
    pdir.mkdir(exist_ok=True)
    rng = np.random.default_rng(0)
    xb = (rng.random((2000, 500)) < 0.1).astype(np.float64)    # binary observations like the env
    xg = rng.normal(size=(2000, 500))                             # and arbitrary real inputs
    print("== prompt byte-identity (original condition vs repo runs/<game>/prompt.txt)")
    for path, nid, game in paper_networks():
        net = H.Network.load(path, nid)
        w = H.render_weights(net)
        ref_w = (NETS / f"{nid}_actor.txt").read_text()
        p = CONDITIONS["original"].prompt(net)
        ref = (H.REPO / "runs" / game / "prompt.txt").read_text()
        same_w, same_p = w == ref_w, p == ref
        ok &= same_w and same_p
        print(f"  {game:9s} {nid}: weights.txt identical={same_w}  prompt.txt identical={same_p}")
        if not same_p:
            a, b = p.splitlines(), ref.splitlines()
            for k, (la, lb) in enumerate(zip(a, b)):
                if la != lb:
                    print(f"    first diff line {k+1}:\n     ours: {la[:150]}\n     repo: {lb[:150]}")
                    break
            print(f"    lengths ours={len(p)} repo={len(ref)}")
    print("== function preservation (max |logit diff| vs original over 2000 binary + 2000 gaussian inputs)")
    for name, rs in RESCALES.items():
        if name == "original":
            continue
        for path, nid, game in paper_networks():
            net = H.Network.load(path, nid)
            sc = rs.apply(net)
            d_full = max(np.abs(rs.forward(sc, x) - net.forward(x)).max() for x in (xb, xg))
            # printed (rounded) variant vs printed (rounded) original
            r0 = H.rounded_network(net)
            rv = H.rounded_network(net, rs)
            d_print = max(np.abs(rs.forward(rv, x) - r0.forward(x)).max() for x in (xb, xg))
            # every printed value of the variant equals the printed original value rescaled
            same_info = all(np.allclose(rv.t[k] * (rs.in_mul if k == "W1" else rs.out_mul if k in ("W3", "b3") else 1),
                                        r0.t[k], atol=1e-9, rtol=0) for k in H.TENSORS)
            good = d_full < 1e-9 and d_print < 1e-6
            ok &= good
            print(f"  {name:12s} {game:9s} full-precision {d_full:.1e}  printed {d_print:.1e}  "
                  f"printed values == original*scale: {same_info}  {'OK' if good else 'FAIL'}")
            (pdir / f"{name}_{nid}.txt").write_text(CONDITIONS[name].prompt(net))
    for path, nid, game in paper_networks():
        (pdir / f"original_{nid}.txt").write_text(CONDITIONS["original"].prompt(H.Network.load(path, nid)))
    ok &= CX.verify_sweep({k: c for k, c in CONDITIONS.items() if not only or k in only}, paper_networks(), pdir)
    print("verify:", "ALL OK" if ok else "PROBLEMS")
    return ok


# ----------------------------------------------------------------------------- run

def jobs_for(cond: Condition, replicas: int | None = None):
    for path, nid, truth in cond.networks:
        net = H.Network.load(path, nid)
        prompt = cond.prompt(net)
        d = RUNS / cond.name / nid
        d.mkdir(parents=True, exist_ok=True)
        (d / "prompt.txt").write_text(prompt)
        (d / "truth.json").write_text(json.dumps({"id": nid, "truth": truth, "network": str(path)}))
        for r in range(1, (replicas or cond.replicas) + 1):
            yield cond, nid, truth, r, prompt, d / f"r{r}"


def run(names, start=3, max_inflight=3, first=None):
    jobs = [j for n in names for j in jobs_for(CONDITIONS[n])]
    if first:  # e.g. Breakout across all levels first
        jobs.sort(key=lambda j: (j[1] != first, j[3]))
    jobs = [j for j in jobs if not done(j[5])]
    H._SEM.configure(start, max_inflight)
    print(f"{len(jobs)} jobs to do; in-flight start {start}, max {max_inflight} (halves on 429/5xx/drops)",
          flush=True)

    def one(j):
        cond, nid, truth, r, prompt, out = j
        rec = H.ask(prompt, out)
        ans = (out / "answer.md").read_text() if (out / "answer.md").exists() else ""
        pa = H.parse_answer(ans)
        print(f"{cond.name:12s} {nid} r{r}: ok={rec.get('ok')} game={cond.rubric.map(pa['game_line'])} "
              f"conf={pa['confidence']} wall={rec.get('wall_s')}s errors={len(rec.get('errors', []))} "
              f"limit={H._SEM.limit}", flush=True)

    with ThreadPoolExecutor(max(1, max_inflight)) as ex:  # H._SEM caps what is actually in flight
        list(ex.map(one, jobs))
    print("limiter events:", H._SEM.events, flush=True)


def done(out: Path) -> bool:
    p = out / "run.json"
    return p.exists() and json.loads(p.read_text()).get("ok")


# ----------------------------------------------------------------------------- summarize

def collect():
    rows = []
    for cdir in sorted(RUNS.iterdir()) if RUNS.exists() else []:
        cond = CONDITIONS.get(cdir.name)
        rubric = cond.rubric if cond else H.EXP1_RUBRIC
        for ndir in sorted(p for p in cdir.iterdir() if p.is_dir()):
            tj = json.loads((ndir / "truth.json").read_text())
            truth = tj["truth"]
            cm = CX.run_metrics(cond, Path(tj["network"]), ndir.name) if cond else {}
            for rdir in sorted(p for p in ndir.iterdir() if p.is_dir()):
                rec = json.loads((rdir / "run.json").read_text()) if (rdir / "run.json").exists() else {}
                ans = (rdir / "answer.md").read_text() if (rdir / "answer.md").exists() else ""
                pa = H.parse_answer(ans)
                guess = rubric.map(pa["game_line"])
                u = rec.get("usage") or {}
                rows.append({
                    "condition": cdir.name, "level": cond.level if cond else "", "d": cond.d if cond else None,
                    "w": cond.w if cond else None, "axis": cond.axis if cond else "", "network": ndir.name, "truth": truth, "replica": rdir.name,
                    "ok": rec.get("ok", False), "game_line": pa["game_line"], "guess": guess,
                    "correct": guess == truth if rec.get("ok") else None,
                    "confidence": pa["confidence"],
                    "input_tokens": u.get("input_tokens"),
                    "cached_input_tokens": u.get("cached_input_tokens"),
                    "output_tokens": u.get("output_tokens"),
                    "reasoning_tokens": u.get("reasoning_output_tokens"),
                    "wall_s": rec.get("wall_s"), "attempts": rec.get("attempts"),
                    "errors": len(rec.get("errors", [])),
                    "has_reasoning_summary": any(s.strip() for s in rec.get("reasoning_summary", [])),
                    **{k: cm.get(k) for k in ["ops_per_weight", "depth", "table_entries", "affected_weights",
                                              "total_ops", "log10_V", "desc_bits", "surface_disruption",
                                              "anonymised"]},
                    **{f"kt_{k}" if k in ("desc_bits",) else k: v for k, v in (KT.row_kt(cond) if cond else {}).items()},
                })
    return rows


TOKEN_FIELDS = [("input_tokens", "input_tokens", "Input"), ("cached_input_tokens", "cached_input_tokens", "Cached input"),
                ("output_tokens", "output_tokens", "Output"), ("reasoning_tokens", "reasoning_output_tokens", "Reasoning"),
                ("wall_s", None, "Wall s")]


def paper_usage():
    """The paper's per-run usage and wall time from repo runs/<game>/run.json (audit.usage, wall_s)."""
    out = []
    for nid, game in PAPER.items():
        rj = json.loads((H.REPO / "runs" / game / "run.json").read_text())
        u = rj.get("audit", {}).get("usage", {})
        out.append({"game": game, "network": nid, **{k: u.get(src) for k, src, _ in TOKEN_FIELDS if src},
                    "wall_s": rj.get("wall_s")})
    return out


def _mmm(vals, wall=False):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "n/a"
    f = (lambda v: f"{v:.1f}") if wall else (lambda v: f"{v:,.0f}")
    return f"{f(np.mean(vals))} ({f(min(vals))}–{f(max(vals))})"


def token_table(rows, order):
    paper = paper_usage()
    L = ["## Tokens and wall time per condition", "",
         "Mean (min–max) per run. Ours: Responses API `usage` (input_tokens, input_tokens_details.cached_tokens, "
         "output_tokens, output_tokens_details.reasoning_tokens); wall time = the HTTP request. Paper: "
         "`exp1_which_game/runs/<game>/run.json` -> `audit.usage` and `wall_s` (Codex CLI, one run per game).", "",
         "| Condition | Runs | " + " | ".join(t for _, _, t in TOKEN_FIELDS) + " |",
         "|---|---|" + "---|" * len(TOKEN_FIELDS)]
    L.append("| **paper (Codex CLI)** | 4 | " + " | ".join(
        _mmm([p[k] for p in paper], k == "wall_s") for k, _, _ in TOKEN_FIELDS) + " |")
    for c in order:
        okr = [r for r in rows if r["condition"] == c and r["ok"]]
        L.append(f"| {c} | {len(okr)} | " + " | ".join(
            _mmm([r[k] for r in okr], k == "wall_s") for k, _, _ in TOKEN_FIELDS) + " |")
    L += ["", "Per game, paper vs our original condition (mean of 3):", "",
          "| Game | Paper in / cached / out / reasoning / wall s | Ours (original) in / cached / out / reasoning / wall s |",
          "|---|---|---|"]
    for p in paper:
        okr = [r for r in rows if r["condition"] == "original" and r["network"] == p["network"] and r["ok"]]
        ours = " / ".join(_mmm([r[k] for r in okr], k == "wall_s").split(" (")[0] for k, _, _ in TOKEN_FIELDS)
        pap = " / ".join((f"{p[k]:.1f}" if k == "wall_s" else f"{p[k]:,}") for k, _, _ in TOKEN_FIELDS)
        L.append(f"| {p['game']} | {pap} | {ours} |")
    return L


def summarize():
    rows = collect()
    (ROOT / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    with open(ROOT / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    order = [c for c in CONDITIONS if any(r["condition"] == c for r in rows)]
    games = ["breakout", "pong", "pacman", "freeway"]
    L = ["# gpt-6-astra: which game? (weights only)", "",
         "Protocol: repo/exp1_which_game (description + question + weights, one message, no tools, "
         "reasoning effort high, summary detailed). Rescaled variants are exactly function-preserving; "
         "the rescaling is stated in the description and formula, and each rescaled tensor is printed with "
         "decimals shifted by one (W/10 to 4 decimals, W*10 to 2), so it carries exactly the information "
         "of the 3-decimal original.", "",
         "## Accuracy per condition", "",
         "| Condition | Runs | Correct | Accuracy | Mean confidence | Mean conf. (wrong) | " +
         " | ".join(g.capitalize() for g in games) + " |",
         "|---|---|---|---|---|---|" + "---|" * len(games)]
    for c in order:
        rs = [r for r in rows if r["condition"] == c]
        okr = [r for r in rs if r["ok"]]
        cor = sum(1 for r in okr if r["correct"])
        confs = [r["confidence"] for r in okr if r["confidence"] is not None]
        wc = [r["confidence"] for r in okr if not r["correct"] and r["confidence"] is not None]
        per = []
        for g in games:
            gr = [r for r in okr if r["truth"] == g]
            per.append(f"{sum(r['correct'] for r in gr)}/{len(gr)}")
        mi = np.mean([r["input_tokens"] for r in okr if r["input_tokens"]]) if okr else float("nan")
        mo = np.mean([r["output_tokens"] for r in okr if r["output_tokens"]]) if okr else float("nan")
        mw = np.mean([r["wall_s"] for r in okr if r["wall_s"]]) if okr else float("nan")
        L.append(f"| {c} | {len(okr)}/{len(rs)} | {cor} | {cor/len(okr):.0%} | "
                 f"{np.mean(confs):.1f} | {f"{np.mean(wc):.1f}" if wc else "–"} | " + " | ".join(per) + " |")
    L += ["", "Per-game cells: correct / runs. Paper (1 run each): 4/4, confidences 99/96/96/97.", ""]
    L += token_table(rows, order)
    L += ["", "## Wrong or unmapped answers", ""]
    bad = [r for r in rows if r["ok"] and not r["correct"]]
    if not bad:
        L.append("None.")
    for r in bad:
        L.append(f"- **{r['condition']} / {r['truth']} ({r['network']}) {r['replica']}** -> `{r['guess']}`, "
                 f"confidence {r['confidence']}: Game: \"{r['game_line']}\"")
    L += ["", "## All Game: lines", "", "| Condition | Truth | Replica | Guess | Conf | Game: line |",
          "|---|---|---|---|---|---|"]
    for r in rows:
        gl = (r["game_line"] or "").replace("|", "\\|")
        L.append(f"| {r['condition']} | {r['truth']} | {r['replica']} | {r['guess']} | {r['confidence']} | {gl} |")
    probs = [r for r in rows if not r["ok"] or r["errors"] or r["confidence"] is None
             or r["game_line"] is None or not r["has_reasoning_summary"]]
    L += ["", "## Run problems (failed runs, retries, format breaks, missing reasoning summary)", ""]
    L += [f"- {r['condition']}/{r['network']}/{r['replica']}: ok={r['ok']} errors={r['errors']} "
          f"game_line={'missing' if r['game_line'] is None else 'ok'} "
          f"confidence={'missing' if r['confidence'] is None else 'ok'} "
          f"reasoning_summary={'yes' if r['has_reasoning_summary'] else 'no'}" for r in probs] or ["None."]
    (ROOT / "summary.md").write_text("\n".join(L) + "\n")
    CL, _, _ = CX.report(rows, order, ROOT)
    (ROOT / "complexity.md").write_text("\n".join(CL) + "\n")
    (ROOT / "kt.md").write_text("\n".join(KT.report(rows, ROOT)) + "\n")
    print("\n".join(L[:20 + len(order)]))


# ----------------------------------------------------------------------------- generic single network

def ask_cli(a):
    patch = [tuple(p) for p in json.loads(Path(a.patch).read_text())] if a.patch else []
    rubric = H.Rubric(json.loads(Path(a.rubric).read_text())) if a.rubric else H.EXP1_RUBRIC
    path = Path(a.network)
    nid = a.id or path.stem.replace("_actor", "")
    cond = Condition(a.condition, [(path, nid, a.truth or "unknown")], RESCALES[a.rescale],
                     replicas=a.replicas, description_file=Path(a.description) if a.description
                     else NETS / "description.txt", patch=patch, rubric=rubric)
    CONDITIONS[cond.name] = cond
    if a.dry_run:
        print(cond.prompt(H.Network.load(path, nid))[:4000])
        return
    run([cond.name])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("verify")
    pv.add_argument("--only", nargs="*")
    pr = sub.add_parser("run")
    pr.add_argument("--only", nargs="*", default=list(CONDITIONS))
    pr.add_argument("--start", type=int, default=3, help="initial requests in flight")
    pr.add_argument("--max-inflight", type=int, default=3, help="cap for the adaptive limiter")
    pr.add_argument("--first", help="network id to run first across all conditions")
    sub.add_parser("summarize")
    pa = sub.add_parser("ask")
    pa.add_argument("network")
    pa.add_argument("--id")
    pa.add_argument("--description", help="description file (default: the paper's description.txt)")
    pa.add_argument("--patch", help="JSON list of [old, new] replacements applied to the description")
    pa.add_argument("--rescale", default="original", choices=list(RESCALES))
    pa.add_argument("--rubric", help="JSON {label: [regex, ...]} for mapping the Game: line")
    pa.add_argument("--truth")
    pa.add_argument("--replicas", type=int, default=1)
    pa.add_argument("--condition", default="adhoc")
    pa.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.cmd == "verify":
        sys.exit(0 if verify(a.only) else 1)
    elif a.cmd == "run":
        run(a.only, a.start, a.max_inflight, a.first)
    elif a.cmd == "summarize":
        summarize()
    else:
        ask_cli(a)
