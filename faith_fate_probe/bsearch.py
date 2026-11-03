"""Binary search for GPT-6 Astra's breaking size on the two Faith-and-Fate tasks.

The reliability threshold is 50% exact-match accuracy (the C50 used elsewhere in the report), estimated from K samples
per probed size.
1. Bracket: start from limit_results.json (waits for it). lo = largest size with accuracy >= 0.5, hi = smallest larger
   size with accuracy < 0.5. If nothing failed, grow by doubling (exponential search) until a size fails.
2. Bisect between lo and hi until hi - lo <= tolerance, sampling K fresh problems at each midpoint.
Every probe logs |V|, depth and width of the paper-style computation graph, so the break can be stated in |V|.
Usage: python -I bsearch.py <env file> <limit_results.json> <out.json>
"""
import json, os, random, re, sys, time, urllib.request, concurrent.futures as cf

env_path, limit_path, out_path = sys.argv[1:4]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "limit.py")).read()
ns = {"__file__": "limit.py"}
exec(src.split("cases = []")[0].replace("env_path, out_path = sys.argv[1:3]", f"env_path = {env_path!r}"), ns)
mult_graph, dp_graph, ask, dp_best = ns["mult_graph"], ns["dp_graph"], ns["ask"], ns["dp_best"]
K = 4
rng = random.Random(2)
TASKS = {
    "multiplication": {"tol": 2, "max": 400},
    "dp_nonadjacent": {"tol_frac": 0.1, "max": 20000},
}


def make_case(task, n):
    if task == "multiplication":
        a, b = rng.randrange(10**(n-1), 10**n), rng.randrange(10**(n-1), 10**n)
        return {"task": task, "size": n, "graph": mult_graph(n, n), "truth": str(a * b),
                "prompt": f"What is {a} * {b}? You have no tools: no calculator, no code. "
                          "Give the exact product on the last line in the form 'ANSWER: <number>' with no commas."}
    xs = [rng.randint(-5, 5) for _ in range(n)]
    return {"task": task, "size": n, "graph": dp_graph(n), "truth": str(dp_best(xs)),
            "prompt": "Given the sequence of integers " + json.dumps(xs) + ", find a subsequence with the highest possible "
                      "sum such that no two chosen numbers are adjacent in the original sequence (the empty subsequence, "
                      "sum 0, is allowed). You have no tools. Give the maximum sum on the last line as 'ANSWER: <number>'."}


def probe(task, n, log):
    cases = [make_case(task, n) for _ in range(K)]
    def one(c):
        text, rt, ot, wall, tools = ask(c["prompt"])
        m = re.findall(r"ANSWER:\s*(-?[\d,]+)", text)
        ans = m[-1].replace(",", "") if m else None
        return {**{k: v for k, v in c.items() if k != "prompt"}, "answer": ans, "correct": ans == c["truth"],
                "error": text.startswith("ERROR"), "reasoning_tokens": rt, "output_tokens": ot, "wall_s": wall,
                "non_reasoning_items": tools}
    with cf.ThreadPoolExecutor(K) as ex:
        res = list(ex.map(one, cases))
    valid = [r for r in res if not r["error"]]
    acc = sum(r["correct"] for r in valid) / len(valid) if valid else None
    log.append({"task": task, "size": n, "acc": acc, "runs": res, "graph": cases[0]["graph"]})
    json.dump(log, open(out_path, "w"), indent=1)
    print(f"{task:15s} n={n:6d} |V|={cases[0]['graph']['V']:8d} acc={acc} "
          f"reasoning={[r['reasoning_tokens'] for r in res]}", flush=True)
    return acc


def search(task, prior, log):
    cfg = TASKS[task]
    sizes = sorted(prior)
    ok = [n for n in sizes if prior[n] >= 0.5]
    lo = max(ok) if ok else 1
    fails = [n for n in sizes if n > lo and prior[n] < 0.5]
    hi = min(fails) if fails else None
    while hi is None:  # exponential search upward
        n = lo * 2
        if n > cfg["max"]:
            print(f"{task}: still reliable at the cap {lo}; no break found", flush=True)
            return {"task": task, "lo": lo, "hi": None}
        acc = probe(task, n, log)
        if acc is not None and acc >= 0.5: lo = n
        else: hi = n
    tol = cfg.get("tol") or max(1, int(cfg["tol_frac"] * lo))
    while hi - lo > tol:
        mid = (lo + hi) // 2
        acc = probe(task, mid, log)
        if acc is not None and acc >= 0.5: lo = mid
        else: hi = mid
        tol = cfg.get("tol") or max(1, int(cfg["tol_frac"] * lo))
    return {"task": task, "lo": lo, "hi": hi, "V_lo": (mult_graph(lo, lo) if task == "multiplication" else dp_graph(lo))["V"],
            "V_hi": (mult_graph(hi, hi) if task == "multiplication" else dp_graph(hi))["V"]}


while not os.path.exists(limit_path):
    time.sleep(30)
time.sleep(5)
prior_runs = json.load(open(limit_path))
log = []
results = []
for task in TASKS:
    by = {}
    for r in prior_runs:
        if r["task"] == task and not str(r.get("raw_tail", "")).startswith("ERROR"):
            by.setdefault(r["size"], []).append(r["correct"])
    prior = {n: sum(v) / len(v) for n, v in by.items()}
    print(task, "prior accuracy by size:", dict(sorted(prior.items())), flush=True)
    results.append(search(task, prior, log))
json.dump({"breakpoints": results, "probes": log}, open(out_path, "w"), indent=1)
print(json.dumps(results, indent=1))
