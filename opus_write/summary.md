# Exp 5 repeated with Claude Opus 5.5: one-shot, tool-free MinAtar networks

Scoring: official MinAtar 1.0.15, 1000 episodes, sticky actions 0.1, sampled actions, 10,000-step cap (eval_minatar.py --net: the same evaluator and per-game seeds that reproduced the paper's Astra numbers). Mean ± SE. Opus output tokens include thinking; the thinking count is usage.output_tokens_details.thinking_tokens from the API. Astra's numbers are reply/run.json audit.usage (output / reasoning_output).

## breakout

| Policy | Score | Input tok | Output tok | of which thinking | Wall | Stop | Statements applied / read | Errors | Cut off | Nonzero weights |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5, effort max, reply 1 | 0.52 ± 0.02 | 3,745 | 128,000 | 128,000 | 1167 s | max_tokens | no edits block | 0 | no | 0 |
| Opus 5.5, effort max, reply 2 | 0.52 ± 0.02 | 3,745 | 128,000 | 128,000 | 1136 s | max_tokens | no edits block | 0 | no | 0 |
| Opus 5.5, effort xhigh, reply 1 (supplementary) | 0.52 ± 0.02 | 3,745 | 128,000 | 128,000 | 1206 s | max_tokens | no edits block | 0 | no | 0 |
| Opus 5.5, effort xhigh, reply 2 (supplementary) | 0.52 ± 0.02 | 3,745 | 128,000 | 128,000 | 1164 s | max_tokens | no edits block | 0 | no | 0 |
| Astra, paper | 517.4 ± 7.4 | 6,119 | 20,567 | 16,828 | 501 s | – | 92 / 92 | 0 | no | 815 |
| Astra, our re-evaluation | 501.2 ± 7.8 | | | | | | | | | |
| PPO 100M (ppo100_s2) | 15.8 ± 0.1 | | | | | | | | | |
| PPO 500M (ppo500_s0) | 25.3 ± 0.1 | | | | | | | | | |
| Random (uniform) | 0.51 ± 0.02 | | | | | | | | | |

## seaquest

| Policy | Score | Input tok | Output tok | of which thinking | Wall | Stop | Statements applied / read | Errors | Cut off | Nonzero weights |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5, effort max, reply 1 | 0.12 ± 0.01 | 6,822 | 128,000 | 128,000 | 1236 s | max_tokens | no edits block | 0 | no | 0 |
| Opus 5.5, effort max, reply 2 | 0.12 ± 0.01 | 6,822 | 128,000 | 128,000 | 1260 s | max_tokens | no edits block | 0 | no | 0 |
| Opus 5.5, effort xhigh, reply 1 (supplementary) | 13.0 ± 0.4 | 6,822 | 119,242 | 113,105 | 1142 s | end_turn | 255 / 255 | 0 | no | 1973 |
| Opus 5.5, effort xhigh, reply 2 (supplementary) | 0.12 ± 0.01 | 6,822 | 128,000 | 128,000 | 1249 s | max_tokens | no edits block | 0 | no | 0 |
| Astra, paper | 53.1 ± 1.4 | 8,112 | 23,894 | 19,803 | 545 s | – | 122 / 122 | 0 | no | 803 |
| Astra, our re-evaluation | 51.9 ± 1.3 | | | | | | | | | |
| PPO 100M (ppo100_s2) | 5.62 ± 0.05 | | | | | | | | | |
| PPO 500M (ppo500_s2) | 88.9 ± 1.6 | | | | | | | | | |
| Random (uniform) | 0.07 ± 0.01 | | | | | | | | | |

## asterix

| Policy | Score | Input tok | Output tok | of which thinking | Wall | Stop | Statements applied / read | Errors | Cut off | Nonzero weights |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5, effort max, reply 1 | 0.51 ± 0.03 | 3,924 | 128,000 | 128,000 | 1180 s | max_tokens | no edits block | 0 | no | 0 |
| Opus 5.5, effort max, reply 2 | 0.51 ± 0.03 | 3,924 | 128,000 | 128,000 | 1222 s | max_tokens | no edits block | 0 | no | 0 |
| Opus 5.5, effort xhigh, reply 1 (supplementary) | 47.0 ± 0.9 | 3,924 | 59,034 | 54,113 | 545 s | end_turn | 170 / 170 | 0 | no | 526 |
| Opus 5.5, effort xhigh, reply 2 (supplementary) | 60.9 ± 1.1 | 3,924 | 98,785 | 92,514 | 892 s | end_turn | 104 / 104 | 0 | no | 739 |
| Astra, paper | 53.2 ± 1.0 | 6,199 | 28,993 | 25,694 | 583 s | – | 55 / 55 | 0 | no | 637 |
| Astra, our re-evaluation | 55.2 ± 1.1 | | | | | | | | | |
| PPO 100M (ppo100_s6) | 25.8 ± 0.4 | | | | | | | | | |
| PPO 500M (ppo500_s1) | 55.2 ± 0.6 | | | | | | | | | |
| Random (uniform) | 0.49 ± 0.03 | | | | | | | | | |

## What each Opus reply says it implemented

- **breakout, Opus 5.5, effort max, reply 1**: No answer: 128,000 thinking tokens, no text, no edits block (all weights 0, so a uniform-random policy).
- **breakout, Opus 5.5, effort max, reply 2**: No answer: 128,000 thinking tokens, no text, no edits block (all weights 0). The thinking summary shows it was still filling per-row landing-offset lookup tables for falling and rising balls, gated by direction, when the budget ran out.
- **breakout, Opus 5.5, effort xhigh, reply 1 (supplementary)**: No answer: 128,000 thinking tokens, no text, no edits block (all weights 0).
- **breakout, Opus 5.5, effort xhigh, reply 2 (supplementary)**: No answer: 128,000 thinking tokens, no text, no edits block (all weights 0).
- **seaquest, Opus 5.5, effort max, reply 1**: No answer: 128,000 thinking tokens, no text, no edits block (all weights 0).
- **seaquest, Opus 5.5, effort max, reply 2**: No answer: 128,000 thinking tokens, no text, no edits block (all weights 0).
- **seaquest, Opus 5.5, effort xhigh, reply 1 (supplementary)**: The sub stays in the two centre columns. It changes row to line up with targets, turns and fires along its row, and dodges bullets by changing row. It surfaces when oxygen < 60 and it carries a diver. Layer 1: row-gated features (vertical preference, target side, own-row bullet threat), a parity/XOR facing-direction detector, and surfacing/top-row/row-8 flags. Layer 2: ANDs of target side and facing that drive fire/turn, plus move blockers, with fixed output priorities (blocked < bullet escape > surface > fire/turn > drift > no-op).
- **seaquest, Opus 5.5, effort xhigh, reply 2 (supplementary)**: No answer: 128,000 thinking tokens, no text, no edits block (all weights 0).
- **asterix, Opus 5.5, effort max, reply 1**: No answer: 128,000 thinking tokens, no text, no edits block (all weights 0).
- **asterix, Opus 5.5, effort max, reply 2**: No answer: 128,000 thinking tokens, no text, no edits block (all weights 0).
- **asterix, Opus 5.5, effort xhigh, reply 1 (supplementary)**: Stays in column 5 and moves only up and down: each row is a lane with at most one entity. Layer 1 computes per-row danger (enemy distance and approach, read from the trail) at 4 levels, per-row approaching treasure, and a one-hot player row. Layer 2 builds row-gated ANDs for flee up/down (current row more dangerous than its neighbour), seek treasure 1–2 rows away, and drift away from the edge rows. Otherwise it takes a strong no-op.
- **asterix, Opus 5.5, effort xhigh, reply 2 (supplementary)**: Stays in column 5 and dodges only vertically, hopping between rows with approaching gold. Layer 1 computes per-row imminent danger, a graded approaching enemy, graded approaching gold, and the player row as 3 binary bits. Layer 2 has one gated unit per (player row, up/stay/down) holding a value for the destination row: death −10, enemy and gold terms, a centrality term, a look-ahead for gold 2–4 rows away, and a sticky-move guard. Output is 40·tanh(value); left/right/fire are fixed at −50.

## Fairness notes

- **Primary protocol (effort `max`, max_tokens 128,000, the model's ceiling): 0 of 6 replies produced an answer.** Every reply ended with `stop_reason=max_tokens` after 128,000 thinking tokens (`usage.output_tokens_details.thinking_tokens`) and no text block, after about 19–21 min. Under the paper's rules (only the last `edits` block is read; every weight starts at 0), each network is all zeros. Uniform logits make it a uniform-random policy, so the scores equal the random baseline within noise. Opus 5.5 has no larger output budget to give it, so this is the result of the protocol as specified, not an applier problem.
- **Supplementary (effort `xhigh`, the same level name as Astra's Codex setting; everything else identical):** 3 of 6 replies answered (Asterix ×2, Seaquest ×1). Both Breakout replies and one Seaquest reply again used all 128k tokens on thinking. I ran this set on my own initiative so the comparison isn't degenerate; it is labelled supplementary and was not in the brief.
- **Budget asymmetry:** Astra used 20.6k–29.0k output tokens (16.8k–25.7k reasoning) and finished every game. The Opus replies that answered used 59k–119k output tokens. Effort labels are not comparable across vendors: Codex `xhigh` on gpt-6-astra and Anthropic `xhigh`/`max` on Opus 5.5 are different knobs. Input tokens also differ (Codex adds its own wrapper and uses another tokenizer: Astra 6,119–8,112, Opus 3,745–6,822 for the same prompt plus the system line).
- **System prompt:** the paper's Codex `model_instructions_file` was "Answer the user's request.", and that was sent as `system`. The user message was `message.txt` verbatim. No tools; every reply is tool-free. No `temperature`. No server-side refusal fallback, since it would change the model. There were no refusals and no transient errors (0 retries).
- **Applies:** every Opus edits block that was written applied fully (Seaquest xhigh 255/255, Asterix xhigh 170/170 and 104/104, 0 errors, none cut off). No lenient reader rule was needed.
- **Thinking-token method:** taken from the API usage field `output_tokens_details.thinking_tokens`. As a check, output − thinking agrees with `count_tokens` on the answer text to within 3–5 tokens. The returned thinking is a *summary* (`display: "summarized"`): about 30–35% of the thinking tokens, stored in `thinking.md`, and not the raw chain of thought.
- **Astra reproduced:** our evaluator gives 501.2 / 51.9 / 55.2 against the paper's 517.4 / 53.1 / 53.2. Opus networks are scored with the same evaluator and seeds (`--net`), so comparing Opus with the reproduced Astra column is like for like.
