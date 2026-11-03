"""How much of Astra's multiplication reasoning is checking its own work?
12 multiplications (20..120 digits, 2 each) with reasoning summaries on. Counts reasoning-summary section headings that
are verification steps (check / verify / recount / recheck / correct / confirm / recompute). Retries dropped streams;
one failure no longer loses the batch. Usage: python -I verification.py <env file> <out.json>
"""
import json, random, re, sys, time, urllib.request, concurrent.futures as cf

env_path, out_path = sys.argv[1:3]
KEY = next(l.split("=", 1)[1].strip().strip('"\'') for l in open(env_path) if l.startswith("AXONHUB_API_KEY="))
VER = re.compile(r"\b(check|verif|recount|recheck|correct|confirm|re-?comput|cross-check|double-check)", re.I)
rng = random.Random(11)
cases = [(n, rng.randrange(10**(n-1), 10**n), rng.randrange(10**(n-1), 10**n)) for n in (20, 40, 60, 80, 100, 120) for _ in range(2)]


def call(body):
    err = ""
    for attempt in range(5):
        try:
            req = urllib.request.Request("http://localhost:8090/v1/responses", json.dumps(body).encode(),
                                         {"Authorization": f"Bearer {KEY}", "content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=1800) as r:
                return json.load(r), None
        except Exception as e:
            err = repr(e); time.sleep(15 * (attempt + 1))
    return None, err


def one(c):
    n, a, b = c
    d, err = call({"model": "gpt-6-astra", "reasoning": {"effort": "high", "summary": "detailed"},
                   "input": f"What is {a} * {b}? You have no tools: no calculator, no code. "
                            "Give the exact product on the last line in the form 'ANSWER: <number>' with no commas."})
    if d is None:
        return {"n": n, "error": err}
    txt = "".join(x.get("text", "") for o in d["output"] for x in (o.get("content") or []))
    summ = " ".join(s.get("text", "") for o in d["output"] if o.get("type") == "reasoning" for s in o.get("summary", []))
    heads = re.findall(r"\*\*([^*]+)\*\*", summ)
    m = re.findall(r"ANSWER:\s*(\d+)", txt)
    r = {"n": n, "correct": bool(m) and m[-1] == str(a * b), "reasoning_tokens": d["usage"]["output_tokens_details"]["reasoning_tokens"],
         "headings": heads, "verification_headings": [h for h in heads if VER.search(h)], "summary": summ}
    print(n, r["correct"], r["reasoning_tokens"], f'{len(r["verification_headings"])}/{len(heads)}', r["verification_headings"][:4], flush=True)
    return r


with cf.ThreadPoolExecutor(6) as ex:
    res = list(ex.map(one, cases))
json.dump(res, open(out_path, "w"), indent=1)
ok = [r for r in res if "error" not in r]
v = sum(len(r["verification_headings"]) for r in ok); h = sum(len(r["headings"]) for r in ok)
print(f"runs {len(ok)}/{len(res)}; verification headings {v}/{h} ({100*v/max(h,1):.0f}%); "
      f"runs with at least one check: {sum(bool(r['verification_headings']) for r in ok)}/{len(ok)}")
