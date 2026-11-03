"""Find where GPT-6 Astra breaks on two Faith-and-Fate tasks (Dziri et al., NeurIPS 2023), measuring each problem by
its computation graph like the paper: |V| nodes, depth (longest path), width (max nodes at one depth).

Graphs (one node per elementary step, as in the paper's long-multiplication and DP graphs):
- multiplication a (n digits) x b (m digits): one node per digit product a_i*b_j, one per carry-add when forming each
  partial product, and one per digit-add (with carry) when summing the m partial products column by column.
- DP max-sum non-adjacent: per element i, nodes take_i = skip_{i-1} + x_i, skip_i = max(take_{i-1}, skip_{i-1}),
  plus the final max; depth grows linearly with the length.

Usage: python -I limit.py <env file> <out.json>
"""
import json, math, random, re, sys, time, urllib.request, concurrent.futures as cf
from collections import defaultdict

env_path, out_path = sys.argv[1:3]
KEY = next(l.split("=", 1)[1].strip().strip('"\'') for l in open(env_path) if l.startswith("AXONHUB_API_KEY="))
URL, MODEL, EFFORT = "http://localhost:8090/v1/responses", "gpt-6-astra", "high"
rng = random.Random(1)


class Graph:
    def __init__(self): self.depth = {}
    def node(self, name, *parents):
        self.depth[name] = 1 + max((self.depth[p] for p in parents), default=0)
        return name
    def stats(self):
        per = defaultdict(int)
        for d in self.depth.values(): per[d] += 1
        return {"V": len(self.depth), "depth": max(self.depth.values()), "width": max(per.values())}


def mult_graph(n, m):
    g = Graph()
    a = [g.node(f"a{i}") for i in range(n)]; b = [g.node(f"b{j}") for j in range(m)]
    partial_digits = []
    for j in range(m):  # partial product of a by digit b_j, digit by digit with carry
        carry, digits = None, []
        for i in range(n):
            p = g.node(f"p{i},{j}", a[i], b[j])
            s = g.node(f"pc{i},{j}", p, *( [carry] if carry else [] ))
            digits.append(s); carry = s
        partial_digits.append(digits)
    carry = None  # column sums of shifted partials
    for col in range(n + m):
        terms = [partial_digits[j][col - j] for j in range(m) if 0 <= col - j < n]
        if carry: terms.append(carry)
        if terms:
            carry = g.node(f"col{col}", *terms)
    return g.stats()


def dp_graph(n):
    g = Graph()
    take = skip = g.node("zero")
    for i in range(n):
        x = g.node(f"x{i}")
        t = g.node(f"take{i}", skip, x)
        s = g.node(f"skip{i}", take, skip)
        take, skip = t, s
    g.node("ans", take, skip)
    return g.stats()


def ask(prompt):
    body = {"model": MODEL, "input": prompt, "reasoning": {"effort": EFFORT}}
    err = ""
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(),
                                         {"Authorization": f"Bearer {KEY}", "content-type": "application/json"})
            t = time.time()
            with urllib.request.urlopen(req, timeout=1800) as r:
                d = json.load(r)
            tools = [o.get("type") for o in d.get("output", []) if o.get("type") not in ("reasoning", "message")]
            text = "".join(c.get("text", "") for o in d.get("output", []) for c in (o.get("content") or []))
            u = d.get("usage", {})
            return text, u.get("output_tokens_details", {}).get("reasoning_tokens"), u.get("output_tokens"), time.time() - t, tools
        except Exception as e:
            err = repr(e); time.sleep(10 * (attempt + 1))
    return "ERROR " + err, None, None, None, []


def dp_best(xs):
    take, skip = 0, 0
    for x in xs:
        take, skip = skip + x, max(take, skip)
    return max(take, skip, 0)


cases = []
for n in (20, 30, 40, 60, 80, 120):
    for _ in range(3):
        a, b = rng.randrange(10**(n-1), 10**n), rng.randrange(10**(n-1), 10**n)
        cases.append({"task": "multiplication", "size": n, "graph": mult_graph(n, n), "truth": str(a * b),
                      "prompt": f"What is {a} * {b}? You have no tools: no calculator, no code. "
                                "Give the exact product on the last line in the form 'ANSWER: <number>' with no commas."})
for n in (160, 320, 640, 1280, 2560):
    for _ in range(3):
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
    digits_ok = None
    if ans and c["task"] == "multiplication" and len(ans) == len(c["truth"]):
        digits_ok = sum(x == y for x, y in zip(ans, c["truth"])) / len(c["truth"])
    return {**{k: v for k, v in c.items() if k != "prompt"}, "answer": ans, "correct": ans == c["truth"],
            "digit_accuracy": digits_ok, "reasoning_tokens": rt, "output_tokens": ot, "wall_s": wall,
            "non_reasoning_items": tools, "raw_tail": text[-300:]}


with cf.ThreadPoolExecutor(len(cases)) as ex:
    res = list(ex.map(run, cases))
json.dump(res, open(out_path, "w"), indent=1)
for r in res:
    g = r["graph"]
    print(f"{r['task']:15s} size {r['size']:5d}  |V| {g['V']:7d} depth {g['depth']:5d} width {g['width']:4d}  "
          f"correct {str(r['correct']):5s} digits {r['digit_accuracy']}  reasoning {r['reasoning_tokens']}  tools {r['non_reasoning_items']}",
          flush=True)
