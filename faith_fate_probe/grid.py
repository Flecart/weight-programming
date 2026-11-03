"""Parallel replacement for bsearch.py: probe every remaining size at once instead of bisecting one size at a time.

Multiplication: n in 130..170 (between the last success at 120 and the first failure at 180).
DP max-sum non-adjacent: 5,120 / 10,240 / 20,480 elements (last success at 2,560).
K problems per size, all requests in flight together. Each run saves the reply text, so a decline ("I can't
reliably compute...") can be told apart from a wrong number, plus reasoning tokens and the computation graph.
Scoring is unchanged: correct = the last 'ANSWER: <number>' line matches Python's exact answer.
Usage: python -I grid.py <env file> <out.json>
"""
import json, os, random, re, sys, concurrent.futures as cf

env_path, out_path = sys.argv[1:3]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "limit.py")).read()
ns = {"__file__": "limit.py"}
exec(src.split("cases = []")[0].replace("env_path, out_path = sys.argv[1:3]", f"env_path = {env_path!r}"), ns)
mult_graph, dp_graph, ask, dp_best = ns["mult_graph"], ns["dp_graph"], ns["ask"], ns["dp_best"]
K = 4
rng = random.Random(3)
DECLINE = re.compile(r"can['’]?t reliably|cannot reliably|not able to|unable to|won['’]?t (?:give|provide)|fabricat", re.I)

cases = []
for n in (130, 140, 150, 160, 170):
    for _ in range(K):
        a, b = rng.randrange(10**(n-1), 10**n), rng.randrange(10**(n-1), 10**n)
        cases.append({"task": "multiplication", "size": n, "graph": mult_graph(n, n), "truth": str(a * b),
                      "prompt": f"What is {a} * {b}? You have no tools: no calculator, no code. "
                                "Give the exact product on the last line in the form 'ANSWER: <number>' with no commas."})
for n in (5120, 10240, 20480):
    for _ in range(K):
        xs = [rng.randint(-5, 5) for _ in range(n)]
        cases.append({"task": "dp_nonadjacent", "size": n, "graph": dp_graph(n), "truth": str(dp_best(xs)),
                      "prompt": "Given the sequence of integers " + json.dumps(xs) + ", find a subsequence with the highest "
                                "possible sum such that no two chosen numbers are adjacent in the original sequence (the empty "
                                "subsequence, sum 0, is allowed). You have no tools. Give the maximum sum on the last line as "
                                "'ANSWER: <number>'."})


def run(c):
    text, rt, ot, wall, tools = ask(c["prompt"])
    m = re.findall(r"ANSWER:\s*(-?[\d,]+)", text)
    ans = m[-1].replace(",", "") if m else None
    err = text.startswith("ERROR")
    outcome = "error" if err else ("correct" if ans == c["truth"] else ("wrong" if ans else ("declined" if DECLINE.search(text) else "no_answer")))
    digits = None
    if ans and c["task"] == "multiplication" and len(ans) == len(c["truth"]):
        digits = sum(x == y for x, y in zip(ans, c["truth"])) / len(c["truth"])
    r = {**{k: v for k, v in c.items() if k != "prompt"}, "answer": ans, "correct": ans == c["truth"], "outcome": outcome,
         "digit_accuracy": digits, "reasoning_tokens": rt, "output_tokens": ot, "wall_s": wall,
         "non_reasoning_items": tools, "reply_text": text[-1500:]}
    print(f"{c['task']:15s} n={c['size']:6d} |V|={c['graph']['V']:7d} {outcome:9s} reasoning={rt}", flush=True)
    return r


with cf.ThreadPoolExecutor(len(cases)) as ex:
    res = list(ex.map(run, cases))
json.dump(res, open(out_path, "w"), indent=1)
summary = {}
for r in res:
    summary.setdefault((r["task"], r["size"]), []).append(r["outcome"])
for k, v in sorted(summary.items()):
    print(k, {o: v.count(o) for o in set(v)})
