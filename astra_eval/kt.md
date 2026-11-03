# Description length vs computation (rule-defined input permutations)

Each condition permutes the 500 inputs (row j of the shown W1 holds original input p(j)) and states the rule for p as a short procedure; P_sha_out also permutes the 5 logit columns by a stated SHA-256 rule. All are function-preserving (checked: bijection + forward pass). desc_bits = 16 per stated constant + 32 for the rule; SHA-256 of a short message counted as 2,296 word operations (breakdown in `kt.py`); kt_bits = desc_bits + log2(total_ops_all).

| Condition | k | desc bits | ops / index | total ops (all rows) | log2 total | kt bits | runs | accuracy | mean conf | reasoning tok mean (min–max) | output tok | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P_aff | 0 | 64 | 3.0 | 1,500 | 10.6 | 74.6 | 8 | 100% | 94.6 | 1,348 (799–2,070) | 2,470 | 81 |
| P_xs_1 | 1 | 64 | 6.1 | 3,072 | 11.6 | 75.6 | 8 | 100% | 92.2 | 2,425 (1,034–4,142) | 3,539 | 124 |
| P_xs_2 | 2 | 96 | 11.3 | 5,632 | 12.5 | 108.5 | 8 | 100% | 91.6 | 3,194 (2,070–5,178) | 4,330 | 142 |
| P_xs_4 | 4 | 160 | 21.5 | 10,752 | 13.4 | 173.4 | 8 | 100% | 89.9 | 2,982 (2,070–4,890) | 4,123 | 141 |
| P_xs_8 | 8 | 288 | 42.0 | 20,992 | 14.4 | 302.4 | 8 | 100% | 89.4 | 5,382 (3,624–8,804) | 6,560 | 224 |
| P_xs_16 | 16 | 544 | 82.9 | 41,472 | 15.3 | 559.3 | 8 | 75% | 77.9 | 7,001 (3,624–12,430) | 8,082 | 266 |
| P_xs_32 | 32 | 1056 | 164.9 | 82,432 | 16.3 | 1072.3 | 8 | 100% | 83.1 | 10,577 (7,250–15,020) | 11,713 | 349 |
| P_xs_64 | 64 | 2080 | 328.7 | 164,352 | 17.3 | 2097.3 | 8 | 75% | 64.4 | 12,464 (7,962–18,126) | 13,444 | 423 |
| P_xs_128 | 128 | 4128 | 655.1 | 327,551 | 18.3 | 4146.3 | 8 | 75% | 49.5 | 2,141 (228–13,226) | 2,959 | 108 |
| P_sha | – | 48 | 1,152,483.0 | 1,152,483 | 20.1 | 68.1 | 8 | 75% | 43.8 | 399 (208–516) | 1,200 | 49 |
| P_sha_out | – | 64 | 1,152,483.0 | 1,163,975 | 20.2 | 84.2 | 8 | 25% | 15.6 | 467 (304–865) | 1,204 | 49 |

### Reasoning tokens (median, IQR), declines

| Condition | k | median reasoning tok | IQR | declines | decline Game: lines |
|---|---|---|---|---|---|
| P_aff | 0 | 1,293 | 1,027–1,598 | 0/8 |  |
| P_xs_1 | 1 | 2,444 | 1,726–2,988 | 0/8 |  |
| P_xs_2 | 2 | 2,794 | 2,458–3,568 | 0/8 |  |
| P_xs_4 | 4 | 2,730 | 2,376–3,236 | 0/8 |  |
| P_xs_8 | 8 | 4,694 | 4,011–6,591 | 0/8 |  |
| P_xs_16 | 16 | 6,760 | 5,373–7,967 | 0/8 |  |
| P_xs_32 | 32 | 10,876 | 7,918–12,430 | 0/8 |  |
| P_xs_64 | 64 | 12,102 | 10,507–14,598 | 1/8 | "Best guess: a “Chase” or moving-target collection game. The exact game" |
| P_xs_128 | 128 | 506 | 455–698 | 2/8 | "Tentative guess: Snake. This is a low-confidence guess, not a decoded "; "Not reliably identified. The most specific defensible characterization" |
| P_sha | – | 432 | 330–506 | 2/8 | "Undetermined. My best-supported classification is a four-direction gri"; "Tentatively, a two-dimensional target-collection gridworld; the specif" |
| P_sha_out | – | 408 | 364–516 | 5/8 | "Undetermined—I cannot reliably identify the game from these permuted w"; "Undetermined from the analysis I can reliably perform under the no-too"; "A two-direction paddle-control game, plausibly Pong or Breakout. I can" |

A decline = the Game: line says the game is undetermined / not reliably identified / cannot be identified, or confidence <= 20.

## Power law: reasoning tokens vs ops_per_index

Feasible = P_aff plus every P_xs_k where at least half the answers wrote decoded p(j) values (P_aff, P_xs_1, P_xs_2, P_xs_4, P_xs_8, P_xs_16, P_xs_32, P_xs_64); `original` is included with ops counted as 1. OLS on log–log, bootstrap 95% CI of the exponent (1,000 resamples). The last column inverts the fit for 16,828 reasoning tokens (Experiment 5, writing the Breakout network) and converts ops/index to rounds k.

| Fit set | points | tokens ≈ A · ops^b | exponent 95% CI | R² (log) | ops/index for 16,828 tok | k |
|---|---|---|---|---|---|---|
| feasible, per run | 76 | 900 · ops^0.454 | [0.422, 0.490] | 0.87 | 633 | 123 |
| feasible, per-condition medians | 9 | 866 · ops^0.463 | [0.421, 0.518] | 0.97 | 607 | 118 |
| all P_aff + P_xs (incl. collapsed), per run | 84 | 1,382 · ops^0.229 | [0.109, 0.370] | 0.21 | 54,431 | 10,631 |

Previous fit (from the k <= 32 data): 892 · ops^0.459, predicting k ≈ 116.


P_xs cycle-walking (measured): k=1: 1.024 passes/index (max 2); k=2: 1.024 passes/index (max 2); k=4: 1.024 passes/index (max 2); k=8: 1.024 passes/index (max 2); k=16: 1.024 passes/index (max 2); k=32: 1.024 passes/index (max 2); k=64: 1.024 passes/index (max 2); k=128: 1.022 passes/index (max 2)

Per game (correct / runs):

| Condition | Breakout | Pong | Pac-Man | Freeway |
|---|---|---|---|---|
| P_aff | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_1 | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_2 | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_4 | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_8 | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_16 | 1/2 | 2/2 | 1/2 | 2/2 |
| P_xs_32 | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_64 | 2/2 | 2/2 | 0/2 | 2/2 |
| P_xs_128 | 2/2 | 2/2 | 0/2 | 2/2 |
| P_sha | 2/2 | 2/2 | 0/2 | 2/2 |
| P_sha_out | 1/2 | 1/2 | 0/2 | 0/2 |

## Spearman ρ of reasoning tokens (per run)

| Runs | n | vs desc_bits | vs log2(total_ops_all) | vs kt_bits |
|---|---|---|---|---|
| these runs (P_*) | 88 | 0.597 | -0.210 | 0.573 |
| all runs pooled | 244 | 0.400 | -0.074 | 0.382 |

Pooled runs use the earlier conditions' measures: desc_bits from complexity.py (permutation tables cost log2(500!)), total ops = V (ops to undo + table entries), so log2_total_ops = log2(1 + V).

## Logistic fit of correctness vs log2(total_ops_all) (all runs)

slope -0.831 per bit, C50 = 20.4, bootstrap 95% CI [19.5, 22.7] (14 failures / 244 runs). C50 beyond the largest value tested

P_* runs only: slope -0.562, C50 = 20, CI [18.8, 22.3].

## Wrong answers

- P_sha / pacman r1 -> `other` (conf 20.0): Game: "Undetermined. My best-supported classification is a four-direction grid-navigation or target-collection game, not a reliably identified named game."
- P_sha / pacman r2 -> `other` (conf 20.0): Game: "Tentatively, a two-dimensional target-collection gridworld; the specific game is not reliably identified."
- P_sha_out / freeway r1 -> `other` (conf 0.0): Game: "Undetermined—I cannot reliably identify the game from these permuted weights under the stated constraints."
- P_sha_out / freeway r2 -> `other` (conf 0.0): Game: "Undetermined from the analysis I can reliably perform under the no-tools constraint."
- P_sha_out / breakout r1 -> `pong` (conf 40.0): Game: "A two-direction paddle-control game, plausibly Pong or Breakout. I cannot reliably distinguish the specific game under the no-tools constraint."
- P_sha_out / pacman r1 -> `other` (conf 0.0): Game: "Not reliably identified from this manual inspection."
- P_sha_out / pacman r2 -> `other` (conf 0.0): Game: "Not reliably identified from my analysis of these weights."
- P_sha_out / pong r1 -> `breakout` (conf 30.0): Game: "Tentatively Breakout—a paddle-and-ball brick-breaking game. The stronger conclusion is merely “a one-axis paddle/control game.”"
- P_xs_128 / pacman r1 -> `other` (conf 20.0): Game: "Tentative guess: Snake. This is a low-confidence guess, not a decoded identification."
- P_xs_128 / pacman r2 -> `other` (conf 25.0): Game: "Not reliably identified. The most specific defensible characterization from my analysis is a likely four-direction grid-movement game, rather than a confidently identified named game."
- P_xs_16 / breakout r2 -> `other` (conf 82.0): Game: "Space Invaders-style, probably an automatically firing grid-based variant."
- P_xs_16 / pacman r2 -> `other` (conf 45.0): Game: "Best guess: Dodge — an open-grid moving-enemy avoidance/survival game."
- P_xs_64 / pacman r1 -> `other` (conf 30.0): Game: "Tentatively, “Dodge”: a full-grid moving-enemy avoidance/survival game."
- P_xs_64 / pacman r2 -> `other` (conf 25.0): Game: "Best guess: a “Chase” or moving-target collection game. The exact game remains undetermined."

## Did Astra compute p(j)? (every `p(j) = v` written in an answer, checked against the true p)

| Condition | answers with p(j) claims | claims correct | wrong answers among those runs |
|---|---|---|---|
| P_aff | 0/8 | 0/0 | 0 |
| P_xs_1 | 8/8 | 32/32 | 0 |
| P_xs_2 | 7/8 | 86/86 | 0 |
| P_xs_4 | 8/8 | 97/97 | 0 |
| P_xs_8 | 7/8 | 101/101 | 0 |
| P_xs_16 | 5/8 | 50/52 | 2 |
| P_xs_32 | 6/8 | 62/62 | 0 |
| P_xs_64 | 6/8 | 34/41 | 2 |
| P_xs_128 | 0/8 | 0/0 | 2 |
| P_sha | 0/8 | 0/0 | 2 |
| P_sha_out | 0/8 | 0/0 | 6 |

(P_aff answers decode rows without writing `p(j) = v`; P_sha answers never compute any hash.)

## Reasoning summaries (section titles, as returned by the gateway)

- **P_xs_32 / freeway r1** (12,430 reasoning tok, correct): Computing prominent row probabilities; Calculating p13 values; Checking row5col6ch4; Checking row-channel calculations; Mapping p39/p45 agent positions; Verifying border-channel decoding; Checking channel-one analog; Checking frame arithmetic; Comparing border patterns; Checking row 6 arithmetic; Computing channel 2 p0; Checking row 5, column 3; Correcting arithmetic mappings; Locating row2 col8 ch4 …
- **P_xs_32 / freeway r2** (11,912 reasoning tok, correct): Computing manual permutation samples; Computing hex XOR samples; Checking j13’s sparse region; Computing p8 values; Computing j10 channel; Mapping channel 2 target; Computing channel 3 j5; Computing game-channel samples; Sampling j0 channel; Checking p0 boundary position; Calculating XOR results; Checking channel 2; Checking forward index j4; Calculating XOR results …
- **P_xs_32 / breakout r1** (7,250 reasoning tok, correct): Decoding selected permutation rows; Computing the target mapping; Checking the arithmetic; Inverting channel 0 sample; Calculating table entries; Checking channel row candidates; Calculating XOR value; Decoding more sample mappings; Checking row10 reward; Computing p10; Checking p33 assignment; Decoding another reward row; Computing numeric checks; Estimating row 39 reward …
- **P_xs_32 / breakout r2** (7,968 reasoning tok, correct): Computing permutation samples; Checking p6 location; Locating the row index; Testing the first 40; Computing p13 value; Assessing p17 candidate; Computing adjusted values; Confirming p17 breakout; Recalculating p24; Sampling p10 and p33; Checking top-row targets; Calculating p10 movement; Calculating row entries; Considering p39 target …

- **P_sha / freeway r1** (222 reasoning tok, correct): Checking channel evidence; Checking border patterns
- **P_sha / freeway r2** (208 reasoning tok, correct): Inferring Frogger-like movement
- **P_sha / breakout r1** (366 reasoning tok, correct): Comparing breakout and catch; Estimating game type
- **P_sha / breakout r2** (516 reasoning tok, correct): Comparing game patterns; Narrowing game identity; Narrowing game identity

- **P_sha_out / freeway r1** (350 reasoning tok, wrong): Analyzing duplicated patterns; Comparing game patterns
- **P_sha_out / freeway r2** (414 reasoning tok, wrong): Comparing likely feature pairings; Checking feature mappings
- **P_sha_out / breakout r1** (516 reasoning tok, wrong): Comparing game patterns; Comparing paddle-game patterns; Examining paddle-ball layout
- **P_sha_out / breakout r2** (865 reasoning tok, correct): Inferring game from inputs; Inferring game from inputs; Inferring game inputs; Comparing channel weight patterns; Checking channel pattern evidence

![vs k](kt.png)

