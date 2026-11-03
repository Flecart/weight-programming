"""Ask Claude Opus 5.5 for one exp5 reply: message.txt verbatim as the only user message, no tools.

System prompt = runs/<game>/instructions.md (the Codex model-instructions file the paper used: "Answer the user's
request."). Adaptive thinking (always on for Opus 5.5) with effort "max", summarized thinking returned, streaming,
max_tokens 128000 (model maximum). No temperature (rejected by Opus 5.5). No server-side fallbacks (a fallback would
swap the model). The API key is read from ~/Desktop/work/thesis/.env and never printed.

Usage: python -I ask_opus.py <game> <rep> [effort]   -> runs/<game>/rep<rep>/... (effort max, the default)
                                                       or runs/<game>/<effort>_rep<rep>/... (other effort)
       files: request.json, response.json, thinking.md, answer.md, run.json
"""
import json
import os
import random
import sys
import time

import anthropic

MODEL = "claude-opus-5-5"
EFFORT = "max"
MAX_TOKENS = 128000
REPO = os.path.expanduser("~/Desktop/work/weight-programming/repo/exp5_write_from_scratch")
HERE = os.path.dirname(os.path.abspath(__file__))


def api_key():
    for line in open(os.path.expanduser("~/Desktop/work/thesis/.env")):
        line = line.strip()
        if line.startswith("export "):
            line = line[7:]
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ANTHROPIC_API_KEY not found in .env")


def main():
    game, rep = sys.argv[1], int(sys.argv[2])
    effort = sys.argv[3] if len(sys.argv) > 3 else EFFORT
    out = os.path.join(HERE, "runs", game, f"rep{rep}" if effort == EFFORT else f"{effort}_rep{rep}")
    os.makedirs(out, exist_ok=True)
    if os.path.exists(os.path.join(out, "run.json")) and json.load(open(os.path.join(out, "run.json"))).get("ok"):
        print(game, rep, "already done")
        return
    prompt = open(f"{REPO}/runs/{game}/message.txt").read()
    system = open(f"{REPO}/runs/{game}/instructions.md").read().strip()
    req = dict(model=MODEL, max_tokens=MAX_TOKENS, system=system,
               thinking={"type": "adaptive", "display": "summarized"},
               output_config={"effort": effort},
               messages=[{"role": "user", "content": prompt}])
    json.dump({**req, "messages": [{"role": "user", "content": f"<runs/{game}/message.txt, {len(prompt)} chars>"}]},
              open(os.path.join(out, "request.json"), "w"), indent=1)
    client = anthropic.Anthropic(api_key=api_key(), timeout=3600.0, max_retries=0)
    attempts = []
    for attempt in range(1, 9):
        t0 = time.time()
        try:
            with client.messages.stream(**req) as stream:
                msg = stream.get_final_message()
            wall = time.time() - t0
            break
        except (anthropic.RateLimitError, anthropic.InternalServerError, anthropic.APIConnectionError,
                anthropic.APITimeoutError) as e:
            err = f"{type(e).__name__}: {getattr(e, 'message', str(e))[:300]}"
        except anthropic.APIStatusError as e:
            if e.status_code in (408, 409, 429, 500, 502, 503, 504, 529):
                err = f"APIStatusError {e.status_code}: {e.message[:300]}"
            else:
                raise
        attempts.append({"attempt": attempt, "error": err, "after_s": round(time.time() - t0, 1)})
        print(game, rep, "retry", attempt, err, flush=True)
        time.sleep(min(30 * 2 ** (attempt - 1), 600) + random.uniform(0, 10))
    else:
        json.dump({"ok": False, "attempts": attempts}, open(os.path.join(out, "run.json"), "w"), indent=1)
        raise SystemExit(f"{game} rep{rep}: gave up")

    d = msg.to_dict()
    json.dump(d, open(os.path.join(out, "response.json"), "w"), indent=1)
    thinking = "\n\n---\n\n".join(b.thinking for b in msg.content if b.type == "thinking")
    answer = "".join(b.text for b in msg.content if b.type == "text")
    open(os.path.join(out, "thinking.md"), "w").write(thinking)
    open(os.path.join(out, "answer.md"), "w").write(answer)
    types = [b.type for b in msg.content]
    run = {"ok": True, "model": msg.model, "effort": effort, "max_tokens": MAX_TOKENS, "stop_reason": msg.stop_reason,
           "stop_details": d.get("stop_details"), "usage": d.get("usage"), "wall_s": round(wall, 1),
           "content_block_types": {t: types.count(t) for t in set(types)}, "tool_free": not any(
               t in ("tool_use", "server_tool_use") for t in types), "attempts_failed": attempts,
           "request_id": getattr(msg, "_request_id", None), "answer_chars": len(answer),
           "thinking_summary_chars": len(thinking)}
    json.dump(run, open(os.path.join(out, "run.json"), "w"), indent=1)
    print(game, rep, "done", msg.stop_reason, d.get("usage", {}).get("output_tokens"), f"{wall:.0f}s", flush=True)


if __name__ == "__main__":
    main()
