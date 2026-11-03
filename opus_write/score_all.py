"""Apply every Opus reply with apply_edits.py, score it with eval_minatar.py --net (1,000 episodes), and collect
results.json. Controller descriptions (written after reading the replies) are read from controllers.json if present.

Usage: <minatar python> -I score_all.py [--episodes 1000] [--workers 18] [--skip-eval]
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from apply_edits import apply_text, save_npz, summarize  # noqa: E402

WP = os.path.expanduser("~/Desktop/work/weight-programming")
REPO = f"{WP}/repo/exp5_write_from_scratch"
EVAL = f"{WP}/minatar/eval_minatar.py"
GAMES = ["breakout", "seaquest", "asterix"]
RUNS = ["rep1", "rep2", "xhigh_rep1", "xhigh_rep2"]  # rep<k>: effort max (primary); xhigh_rep<k>: supplementary
PPO_KEYS = {"breakout": ("ppo100_s2", "ppo500_s0"), "seaquest": ("ppo100_s2", "ppo500_s2"),
            "asterix": ("ppo100_s6", "ppo500_s1")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=18)
    ap.add_argument("--skip-eval", action="store_true")
    a = ap.parse_args()
    ref = json.load(open(f"{REPO}/eval/minatar_eval.json"))
    val = json.load(open(f"{WP}/minatar/validation.json"))
    ctrl = json.load(open(f"{HERE}/controllers.json")) if os.path.exists(f"{HERE}/controllers.json") else {}
    results = {"protocol": {"minatar": "1.0.15", "episodes": a.episodes, "sticky_action_prob": 0.1, "max_steps": 10000,
                            "action_selection": "sample softmax(logits)", "evaluator": EVAL + " --net",
                            "seeds": "same per-game seeds as validation.json (env seed = 1e6*(game_index+1)+i)"},
               "games": {}}
    for g in GAMES:
        astra_run = json.load(open(f"{REPO}/runs/{g}/apply.json"))
        astra_rr = json.load(open(f"{REPO}/runs/{g}/reply/run.json"))
        au = astra_rr["audit"]["usage"]
        r1, r5 = PPO_KEYS[g]
        G = {"astra": {"paper": {"mean": ref[g]["hand"]["mean"], "se": ref[g]["hand"]["se"]},
                       "reproduced": {"mean": val[g]["ours"]["mean"], "se": val[g]["ours"]["se"]},
                       "statements": astra_run["edit_report"]["statements"],
                       "nonzero_total": astra_run["nonzero_total"],
                       "input_tokens": au["input_tokens"], "cached_input_tokens": au["cached_input_tokens"],
                       "output_tokens": au["output_tokens"],
                       "reasoning_output_tokens": au["reasoning_output_tokens"],
                       "reasoning_method": "reply/run.json audit.usage.reasoning_output_tokens (Codex usage)",
                       "wall_s": astra_rr["wall_s"]},
             "ppo100": {"key": r1, "mean": ref[g][r1]["mean"], "se": ref[g][r1]["se"]},
             "ppo500": {"key": r5, "mean": ref[g][r5]["mean"], "se": ref[g][r5]["se"]},
             "random": {"mean": val[g]["random"]["mean"], "se": val[g]["random"]["se"]},
             "noop": {"mean": val[g]["noop"]["mean"], "se": val[g]["noop"]["se"]},
             "opus": {}}
        for key in RUNS:
            d = f"{HERE}/runs/{g}/{key}"
            if not os.path.exists(f"{d}/run.json"):
                G["opus"][key] = {"missing": True}
                continue
            run = json.load(open(f"{d}/run.json"))
            net, er = apply_text(open(f"{d}/answer.md").read())
            npz = f"{d}/net.npz"
            save_npz(net, npz)
            s = summarize(net)
            apply_rec = {"edit_report": er, **s, "tool_free": run.get("tool_free"), "usage": run.get("usage"),
                         "stop_reason": run.get("stop_reason"), "wall_s": run.get("wall_s")}
            json.dump(apply_rec, open(f"{d}/apply.json", "w"), indent=1)
            ev_dir = f"{d}/eval"
            os.makedirs(ev_dir, exist_ok=True)
            if not a.skip_eval:
                if os.path.exists(f"{ev_dir}/validation.json"):
                    os.remove(f"{ev_dir}/validation.json")
                subprocess.run([sys.executable, "-I", EVAL, "--repo", REPO, "--out", ev_dir, "--games", g, "--net",
                                npz, "--no-frames", "--episodes", str(a.episodes), "--workers", str(a.workers)],
                               check=True)
            ev = json.load(open(f"{ev_dir}/validation.json"))[g]["ours"]
            u = run.get("usage") or {}
            tk = json.load(open(f"{d}/tokens.json")) if os.path.exists(f"{d}/tokens.json") else {}
            G["opus"][key] = {"effort": run.get("effort"),
                "mean": ev["mean"], "se": ev["se"], "episodes": ev["episodes"], "max": ev["max"],
                "mean_len": ev["mean_len"], "truncated_at_10000": ev["truncated_at_10000"],
                "statements": er["statements"], "applied": er["applied"], "errors": er["errors"],
                "cut_off": er["cut_off"], "block": er["block"], "lenient": er["lenient"],
                "entries_written": er["entries_written"], "nonzero_total": s["nonzero_total"],
                "max_abs": s["max_abs"], "output_tokens": u.get("output_tokens"), "input_tokens": u.get("input_tokens"),
                "thinking_tokens": tk.get("thinking_tokens"), "thinking_method": tk.get("thinking_method"),
                "answer_tokens_counted": tk.get("answer_tokens_counted"),
                "thinking_summary_tokens_counted": tk.get("thinking_summary_tokens_counted"), "usage": u,
                "stop_reason": run.get("stop_reason"), "wall_s": run.get("wall_s"), "tool_free": run.get("tool_free"),
                "model": run.get("model"), "controller": ctrl.get(g, {}).get(key)}
            print(g, key, G["opus"][key]["mean"], er["statements"], len(er["errors"]), flush=True)
        results["games"][g] = G
    json.dump(results, open(f"{HERE}/results.json", "w"), indent=1)

    f = lambda mean, se: f"{mean:.2f} ± {se:.2f}" if abs(mean) < 10 else f"{mean:.1f} ± {se:.1f}"
    lab = {"rep1": "Opus 5.5, effort max, reply 1", "rep2": "Opus 5.5, effort max, reply 2",
           "xhigh_rep1": "Opus 5.5, effort xhigh, reply 1 (supplementary)",
           "xhigh_rep2": "Opus 5.5, effort xhigh, reply 2 (supplementary)"}
    L = ["# Exp 5 repeated with Claude Opus 5.5: one-shot, tool-free MinAtar networks", "",
         f"Scoring: official MinAtar 1.0.15, {a.episodes} episodes, sticky actions 0.1, sampled actions, 10,000-step cap "
         "(eval_minatar.py --net: the same evaluator and per-game seeds that reproduced the paper's Astra numbers). "
         "Mean ± SE. Opus output tokens include thinking; the thinking count is usage.output_tokens_details."
         "thinking_tokens from the API. Astra's numbers are reply/run.json audit.usage (output / reasoning_output).", ""]
    for g, G in results["games"].items():
        L += [f"## {g}", "", "| Policy | Score | Input tok | Output tok | of which thinking | Wall | Stop | "
              "Statements applied / read | Errors | Cut off | Nonzero weights |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for k in RUNS:
            x = G["opus"][k]
            if "mean" not in x:
                continue
            th = f"{x['thinking_tokens']:,}" if x.get("thinking_tokens") is not None else "?"
            blk = f"{x['applied']} / {x['statements']}" if x["block"] else "no edits block"
            L.append(f"| {lab[k]} | {f(x['mean'], x['se'])} | {x['input_tokens']:,} | {x['output_tokens']:,} | {th} | "
                     f"{x['wall_s']:.0f} s | {x['stop_reason']} | {blk} | {len(x['errors'])} | "
                     f"{'yes' if x['cut_off'] else 'no'} | {x['nonzero_total']} |")
        A = G["astra"]
        L.append(f"| Astra, paper | {f(**A['paper'])} | {A['input_tokens']:,} | {A['output_tokens']:,} | "
                 f"{A['reasoning_output_tokens']:,} | {A['wall_s']:.0f} s | – | {A['statements']} / {A['statements']} | 0 | "
                 f"no | {A['nonzero_total']} |")
        L.append(f"| Astra, our re-evaluation | {f(**A['reproduced'])} | | | | | | | | | |")
        L.append(f"| PPO 100M ({G['ppo100']['key']}) | {f(G['ppo100']['mean'], G['ppo100']['se'])} | | | | | | | | | |")
        L.append(f"| PPO 500M ({G['ppo500']['key']}) | {f(G['ppo500']['mean'], G['ppo500']['se'])} | | | | | | | | | |")
        L.append(f"| Random (uniform) | {f(**G['random'])} | | | | | | | | | |")
        L.append("")
    L += ["## What each Opus reply says it implemented", ""]
    for g, G in results["games"].items():
        for k in RUNS:
            c = G["opus"][k].get("controller")
            if c:
                L.append(f"- **{g}, {lab[k]}**: {c}")
    notes = f"{HERE}/notes.md"
    if os.path.exists(notes):
        L += ["", open(notes).read().strip()]
    open(f"{HERE}/summary.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
