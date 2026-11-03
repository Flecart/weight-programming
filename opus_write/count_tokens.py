"""Token breakdown for each Opus reply.

If response.json's usage breaks out thinking tokens, that number is used ("usage"). Otherwise:
  answer_tokens   = count_tokens(user message = answer text) - count_tokens(user message = ".")
  thinking_tokens = usage.output_tokens - answer_tokens      ("output_minus_counted_answer")
Also recorded: thinking_summary_tokens = tokens of the returned (summarized) thinking text, counted the same way.
The summary is not the raw chain of thought, so it is a lower bound / reference only, not the reasoning count.

Usage: python -I count_tokens.py   -> runs/<game>/rep<k>/tokens.json
"""
import glob
import json
import os
import sys

import anthropic

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ask_opus import MODEL, api_key  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def find_thinking_field(u):
    """Return (key path, value) of a thinking/reasoning token count in the usage dict, if any."""
    def walk(d, path):
        for k, v in d.items():
            if isinstance(v, dict):
                r = walk(v, path + [k])
                if r:
                    return r
            elif isinstance(v, int) and ("thinking" in k or "reasoning" in k):
                return ".".join(path + [k]), v
        return None
    return walk(u or {}, [])


def main():
    client = anthropic.Anthropic(api_key=api_key(), max_retries=5)

    def count(text):
        return client.messages.count_tokens(model=MODEL, messages=[{"role": "user", "content": text}]).input_tokens

    base = count(".")
    for d in sorted(glob.glob(f"{HERE}/runs/*/*rep*")):
        if not os.path.exists(f"{d}/run.json"):
            continue
        run = json.load(open(f"{d}/run.json"))
        u = run.get("usage") or {}
        ans = open(f"{d}/answer.md").read()
        th = open(f"{d}/thinking.md").read()
        answer_tokens = count(ans) - base if ans else 0
        summary_tokens = count(th) - base if th else 0
        f = find_thinking_field(u)
        out = u.get("output_tokens")
        rec = {"input_tokens": u.get("input_tokens"), "cache_read_input_tokens": u.get("cache_read_input_tokens"),
               "cache_creation_input_tokens": u.get("cache_creation_input_tokens"), "output_tokens": out,
               "answer_tokens_counted": answer_tokens, "thinking_summary_tokens_counted": summary_tokens,
               "wall_s": run.get("wall_s"), "usage_raw": u}
        if f:
            rec.update(thinking_tokens=f[1], thinking_method=f"usage field {f[0]}")
        else:
            rec.update(thinking_tokens=out - answer_tokens if out is not None else None,
                       thinking_method="output_tokens minus count_tokens(answer text); usage has no thinking breakdown")
        json.dump(rec, open(f"{d}/tokens.json", "w"), indent=1)
        print(os.path.relpath(d, HERE), {k: rec[k] for k in ("input_tokens", "output_tokens", "thinking_tokens",
                                                              "answer_tokens_counted", "thinking_summary_tokens_counted",
                                                              "thinking_method", "wall_s")})


if __name__ == "__main__":
    main()
