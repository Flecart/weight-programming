"""Prefix-completion memorization probe for the breakout weights prompt.

For each probe line: give the model the document verbatim up to that line plus the first
K values of the line, ask it to continue verbatim (no thinking), and compare its next values
against the true ones. Usage: python -I probe.py <prompt.txt> <.env> <out.json>
"""
import json, re, sys, urllib.request

doc_path, env_path, out_path = sys.argv[1:4]
doc = open(doc_path).read()
key = next(l.split("=", 1)[1].strip().strip('"\'') for l in open(env_path)
           if l.startswith("ANTHROPIC_API_KEY="))
MODEL, K, N_CHECK = "claude-opus-5-5", 8, 16

lines = doc.split("\n")
num_re = re.compile(r"^-?\d+\.\d+( -?\d+\.\d+)*$")
def find_section(header):
    i = next(i for i, l in enumerate(lines) if l.startswith(header))
    return i + 1  # first data line
w1, w2, w3, b3 = (find_section(h) for h in ("W1 (", "W2 (", "W3 (", "b3 ("))
targets = {f"W1 row {r}": w1 + r for r in (0, 1, 2, 3, 5, 10, 25, 50, 100, 200)}
targets.update({"W2 row 0": w2, "W2 row 15": w2 + 15, "W3 row 0": w3, "b3": b3})

def call(prompt):
    body = {"model": MODEL, "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", json.dumps(body).encode(),
        {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    return "".join(b.get("text", "") for b in d["content"]), d["usage"]

INSTR = ("Below is the beginning of a text file that is published on GitHub. It is cut off in the "
         "middle of a line of numbers. Continue the text exactly, verbatim, from where it stops, as it "
         "appears in the original file. Do not reason, explain, or comment; output only the next "
         f"{N_CHECK} numbers of that line, space-separated.\n\n<file_prefix>\n")

results = []
for name, li in targets.items():
    vals = lines[li].split()
    assert num_re.match(lines[li]), (name, lines[li][:80])
    prefix = "\n".join(lines[:li]) + "\n" + " ".join(vals[:K])
    truth = vals[K:K + N_CHECK]
    text, usage = call(INSTR + prefix + "\n</file_prefix>")
    pred = re.findall(r"-?\d+\.\d+", text)[:len(truth)]
    exact = sum(p == t for p, t in zip(pred, truth))
    sign = sum((p.startswith("-")) == (t.startswith("-")) for p, t in zip(pred, truth))
    mae = sum(abs(float(p) - float(t)) for p, t in zip(pred, truth)) / max(len(pred), 1)
    # chance baseline: compare the prediction against the same positions in other lines of the section
    others = [lines[j].split()[K:K + N_CHECK] for j in range(li - 30, li + 30)
              if j != li and 0 <= j < len(lines) and num_re.match(lines[j])
              and len(lines[j].split()) == len(vals)]
    base_exact = sum(sum(p == o for p, o in zip(pred, ov)) for ov in others) / max(len(others), 1)
    r = dict(probe=name, n=len(truth), n_pred=len(pred), exact=exact, sign=sign, mae=round(mae, 4),
             baseline_exact=round(base_exact, 2), truth=" ".join(truth), pred=" ".join(pred),
             input_tokens=usage["input_tokens"])
    results.append(r)
    print(f"{name:12s} exact {exact}/{len(truth)} (other-row baseline {base_exact:.2f})  "
          f"sign {sign}/{len(truth)}  MAE {mae:.3f}  in_tok {usage['input_tokens']}", flush=True)

json.dump(results, open(out_path, "w"), indent=1)
