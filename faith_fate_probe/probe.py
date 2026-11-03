"""Tiny probe of GPT-6 Astra on two Faith-and-Fate tasks (Dziri et al., NeurIPS 2023): n x n digit multiplication
and the max-sum non-adjacent subsequence DP. Zero-shot, no tools, one reply. Usage: python -I probe.py <env file> <out.json>"""
import json, random, re, sys, time, urllib.request, concurrent.futures as cf

env_path, out_path = sys.argv[1:3]
KEY = next(l.split("=", 1)[1].strip().strip('"\'') for l in open(env_path) if l.startswith("AXONHUB_API_KEY="))
URL, MODEL, EFFORT = "http://localhost:8090/v1/responses", "gpt-6-astra", "high"
rng = random.Random(0)

def ask(prompt):
    body = {"model": MODEL, "input": prompt, "reasoning": {"effort": EFFORT}}
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(),
                                         {"Authorization": f"Bearer {KEY}", "content-type": "application/json"})
            t = time.time()
            with urllib.request.urlopen(req, timeout=900) as r:
                d = json.load(r)
            text = "".join(c.get("text", "") for o in d.get("output", []) for c in (o.get("content") or []))
            u = d.get("usage", {})
            return text, u.get("output_tokens_details", {}).get("reasoning_tokens"), u.get("output_tokens"), time.time() - t
        except Exception as e:
            err = repr(e); time.sleep(5 * (attempt + 1))
    return "ERROR " + err, None, None, None

def mult_case(n):
    a, b = rng.randrange(10**(n-1), 10**n), rng.randrange(10**(n-1), 10**n)
    p = (f"What is {a} * {b}? You have no tools: no calculator, no code. "
         "Give the exact product on the last line in the form 'ANSWER: <number>' with no commas.")
    return {"task": "multiplication", "size": n, "prompt": p, "truth": str(a * b)}

def dp_best(xs):
    take, skip = 0, 0
    for x in xs:
        take, skip = skip + x, max(take, skip)
    return max(take, skip, 0)

def dp_case(n):
    xs = [rng.randint(-5, 5) for _ in range(n)]
    p = ("Given the sequence of integers " + json.dumps(xs) + ", find a subsequence with the highest possible sum such that "
         "no two chosen numbers are adjacent in the original sequence (the empty subsequence, sum 0, is allowed). "
         "You have no tools. Give the maximum sum on the last line as 'ANSWER: <number>'.")
    return {"task": "dp_nonadjacent", "size": n, "prompt": p, "truth": str(dp_best(xs))}

cases = [mult_case(n) for n in (2, 3, 4, 5, 6, 8, 10, 15) for _ in range(2)] + \
        [dp_case(n) for n in (5, 10, 20, 40, 80) for _ in range(2)]

def run(c):
    text, rt, ot, wall = ask(c["prompt"])
    m = re.findall(r"ANSWER:\s*(-?[\d,]+)", text)
    ans = m[-1].replace(",", "") if m else None
    return {**{k: v for k, v in c.items() if k != "prompt"}, "answer": ans, "correct": ans == c["truth"],
            "reasoning_tokens": rt, "output_tokens": ot, "wall_s": wall, "raw_tail": text[-300:]}

with cf.ThreadPoolExecutor(len(cases)) as ex:
    res = list(ex.map(run, cases))
json.dump(res, open(out_path, "w"), indent=1)
for r in res:
    print(f"{r['task']:15s} size {r['size']:3d}  correct {str(r['correct']):5s}  reasoning {r['reasoning_tokens']}  "
          f"answer {str(r['answer'])[:40]:40s} truth {r['truth'][:40]}")
