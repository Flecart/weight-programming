# Weight Programming

Replication and stress tests of *Sparks of Weight Space Programming: LLMs can understand and write neural
network weights* ([post](https://rikiyat.github.io/blog/weight-space-programming/),
[logs](https://github.com/RikiyaT/lm_understand-logs)), plus the companion blog post
[`blog/companion_post.md`](blog/companion_post.md), *A Limit of Weight Programming: A Trip to Task Complexity*.

The question: when GPT-6 Astra reads or writes network weights with no tools, what is it actually doing, and where does it
stop working?

## Results at a glance

| Question | Answer | Where |
|---|---|---|
| Do the paper's results reproduce? | Yes. Experiment 5's hand-written MinAtar networks match the published scores within noise; Experiment 4's car fix succeeds in 1,024/1,024 real Kinetix episodes. | [`minatar/`](minatar), [`exp4_kinetix/`](exp4_kinetix) |
| What did Astra write for Breakout? | A ~10-line "simulate the ball, wait where it lands" program compiled into 6 + 8 units of AND/OR logic. A 10-line Python script with the same algorithm scores 534; the network 517 (ceiling ≈ 823). | [`critique/`](critique), post Appendix D |
| Does it break under obfuscation? | Not under anything cheap to undo: 156/156 correct across rescaling, flips, a 500-entry shuffle table, 250 rotations, stacked compositions and anonymous channels. | [`astra_eval/summary.md`](astra_eval/summary.md), [`astra_eval/complexity.md`](astra_eval/complexity.md) |
| Where does it break? | When undoing the shuffle needs about 2^18 operations: reasoning peaks at 64 rounds of multiply-add + XOR-shift and collapses at 128; with SHA-256 it declines instead of computing. | [`astra_eval/kt.md`](astra_eval/kt.md) |
| How does effort scale? | Subexponentially: roughly the square root of the work when decoding (tokens ≈ 900 · ops^0.45), linear in the computation graph for arithmetic. | [`astra_eval/kt.md`](astra_eval/kt.md), [`faith_fate_probe/`](faith_fate_probe) |
| Is Faith and Fate still right? | Astra is exact at 120×120-digit multiplication and on 2,560-element DP sums, about 1,000× larger graphs than GPT-4 managed; past its limit it declines rather than guessing. 44% of its arithmetic reasoning steps are modular checksums. | [`faith_fate_probe/`](faith_fate_probe) |
| Is it just Astra? | Claude Opus 5.5 can write working networks too (Asterix 60.9 vs Astra's 55.2), but needs 2–5× more reasoning and often runs out of its output budget. | [`opus_write/`](opus_write) |

## Repository map

| Folder | What it holds |
|---|---|
| [`blog/`](blog) | The companion post and its figures (`image/blog/weight-programming/`). |
| [`minatar/`](minatar) | Experiment 5 validation on official MinAtar 1.0.15: scores, baselines, replay episodes. |
| [`exp4_kinetix/`](exp4_kinetix) | Experiment 4 validation in Kinetix 3.0.2 (`l/h2_car_ramp`), with episode traces. |
| [`exp1_games/`](exp1_games) | Rebuilt Experiment 1 games: Breakout and Freeway validated against the paper's numbers and the released critic; Pong and Pac-Man approximate. |
| [`astra_eval/`](astra_eval) | Which-game harness for gpt-6-astra: original networks, rescaling, graded obfuscation (`levels.py`, `complexity.py`) and rule-defined shuffles (`kt.py`). Every raw reply is in `runs/`. |
| [`faith_fate_probe/`](faith_fate_probe) | Faith-and-Fate tasks (multiplication, DP sum): probe, limit run, binary search, parallel grid, verification counts. |
| [`opus_write/`](opus_write) | Experiment 5 repeated with Claude Opus 5.5, with an edits applier verified bit-for-bit against Astra's networks. |
| [`critique/`](critique) | Scripted Breakout players (`scripted_breakout.py`) and the never-lose-the-ball ceiling (`max_score.py`). |
| [`prefix_probe/`](prefix_probe) | Prefix-completion test: does a model reproduce the released weights from memory? (No.) |
| [`site/`](site) | Figure scripts: operations-vs-tokens chart, Faith-and-Fate charts, obfuscation GIF, MinAtar replay page. |
| [`breakout_recon/`](breakout_recon) | First attempts at reconstructing the Experiment 1 Breakout (superseded by `exp1_games/`). |
| [`novel_games/`](novel_games) | Designs for three unseen games (Corner Push, Mirror Twin, Charge Pad); training was stopped, so no results. |

## Reproducing

1. **Paper data.** Clone the paper's log repo into `repo/`; it holds the released networks and prompts.
   ```
   git clone https://github.com/RikiyaT/lm_understand-logs repo
   ```
2. **Python.** Python 3.12+ with `numpy`, `matplotlib` and `pillow`. Add `minatar==1.0.15` for the MinAtar scripts, and `kinetix-env==3.0.2` with `jax==0.4.38` (CPU) for Kinetix. Run scripts with `python -I`.
3. **API keys.** Scripts read keys from local `.env` files at run time; none are stored here.
   - **gpt-6-astra:** `AXONHUB_API_KEY`, through an OpenAI-compatible gateway at `http://localhost:8090/v1` (Responses API).
   - **Claude Opus 5.5:** `ANTHROPIC_API_KEY`.

   Pass the `.env` path as the first argument where a script asks for it.

| Experiment | Command |
|---|---|
| MinAtar scores | `python -I minatar/eval_minatar.py --repo repo/exp5_write_from_scratch --out minatar/ --episodes 1000` |
| Scripted players, ceiling | `python -I critique/scripted_breakout.py 200` · `python -I critique/max_score.py 400` |
| Which-game harness | `cd astra_eval && python run.py verify && python run.py run && python run.py summarize` (resumable; finished runs are skipped) |
| Rule-defined shuffles | conditions are defined in `astra_eval/kt.py` and run through the same harness; results in `kt.md` |
| Faith-and-Fate probes | `python -I faith_fate_probe/{probe,limit,grid,verification}.py <.env> <out.json>` |
| Opus 5.5 weight writing | `python -I opus_write/ask_opus.py <game> <rep> [effort]`, then `python -I opus_write/score_all.py` |
| Kinetix | `python exp4_kinetix/evaluate.py 1024` |
| Figures | `python -I site/make_ops_tokens_chart.py astra_eval blog/image/blog/weight-programming/ops_vs_reasoning_tokens.png` · `python -I site/make_ff_charts.py faith_fate_probe blog/image/blog/weight-programming` · `python -I site/make_obfuscation_gif.py astra_eval blog/image/blog/weight-programming/breakout_obfuscation.gif` |

The full experimental protocol (prompts, transformations, sizes, seeds, scoring and statistics) is in the post's
Appendix C.

## Notes and caveats

- **Sampling.** gpt-6-astra does not expose a temperature setting, so every result is from independent replies (2–4 per condition). Small conditions are noisy.
- **Reasoning summaries.** The saved summaries are condensed versions of the hidden reasoning, so the verification share is a proxy.
- **Effort settings.** Codex `xhigh` (Astra in the paper) and Anthropic `xhigh` / `max` (Opus) are not equivalent; compare tokens, not labels.
- **Gateway failures.** Requests that failed at the gateway are excluded, never counted as wrong.

## Licences

- **The paper's logs, data and networks** are CC BY 4.0. The MinAtar source quoted in its prompts is GPL-3.0. Neither is redistributed here beyond the derived results; clone the original repo instead.
- **The code in this repository** is by the author of the companion post.
