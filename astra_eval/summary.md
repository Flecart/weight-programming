# gpt-6-astra: which game? (weights only)

Protocol: repo/exp1_which_game (description + question + weights, one message, no tools, reasoning effort high, summary detailed). Rescaled variants are exactly function-preserving; the rescaling is stated in the description and formula, and each rescaled tensor is printed with decimals shifted by one (W/10 to 4 decimals, W*10 to 2), so it carries exactly the information of the 3-decimal original.

## Accuracy per condition

| Condition | Runs | Correct | Accuracy | Mean confidence | Mean conf. (wrong) | Breakout | Pong | Pacman | Freeway |
|---|---|---|---|---|---|---|---|---|---|
| original | 12/12 | 12 | 100% | 95.5 | – | 3/3 | 3/3 | 3/3 | 3/3 |
| x10_input | 8/8 | 8 | 100% | 96.4 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| div10_input | 8/8 | 8 | 100% | 96.2 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| x10_output | 8/8 | 8 | 100% | 96.2 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| div10_output | 8/8 | 8 | 100% | 96.2 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L0s_sig3 | 8/8 | 8 | 100% | 95.1 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L2_chscale | 8/8 | 8 | 100% | 97.1 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L3_chaffine | 8/8 | 8 | 100% | 96.4 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L4_flip | 8/8 | 8 | 100% | 96.4 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L5_perm | 8/8 | 8 | 100% | 92.9 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L6a_flip_scale | 8/8 | 8 | 100% | 95.9 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L6b_perm_flip_scale | 8/8 | 8 | 100% | 92.5 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L6c_perm_flip_scale_affine | 8/8 | 8 | 100% | 92.1 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L7_givens10 | 8/8 | 8 | 100% | 96.5 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L7_givens50 | 8/8 | 8 | 100% | 95.5 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L7_givens250 | 8/8 | 8 | 100% | 92.5 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L8_anon | 8/8 | 8 | 100% | 86.6 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L8_anon_flip | 8/8 | 8 | 100% | 89.0 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| L9_hidden_perm_sign | 8/8 | 8 | 100% | 95.6 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| P_aff | 8/8 | 8 | 100% | 94.6 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_1 | 8/8 | 8 | 100% | 92.2 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_2 | 8/8 | 8 | 100% | 91.6 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_4 | 8/8 | 8 | 100% | 89.9 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_8 | 8/8 | 8 | 100% | 89.4 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_16 | 8/8 | 6 | 75% | 77.9 | 63.5 | 1/2 | 2/2 | 1/2 | 2/2 |
| P_xs_32 | 8/8 | 8 | 100% | 83.1 | – | 2/2 | 2/2 | 2/2 | 2/2 |
| P_xs_64 | 8/8 | 6 | 75% | 64.4 | 27.5 | 2/2 | 2/2 | 0/2 | 2/2 |
| P_xs_128 | 8/8 | 6 | 75% | 49.5 | 22.5 | 2/2 | 2/2 | 0/2 | 2/2 |
| P_sha | 8/8 | 6 | 75% | 43.8 | 20.0 | 2/2 | 2/2 | 0/2 | 2/2 |
| P_sha_out | 8/8 | 2 | 25% | 15.6 | 11.7 | 1/2 | 1/2 | 0/2 | 0/2 |

Per-game cells: correct / runs. Paper (1 run each): 4/4, confidences 99/96/96/97.

## Tokens and wall time per condition

Mean (min–max) per run. Ours: Responses API `usage` (input_tokens, input_tokens_details.cached_tokens, output_tokens, output_tokens_details.reasoning_tokens); wall time = the HTTP request. Paper: `exp1_which_game/runs/<game>/run.json` -> `audit.usage` and `wall_s` (Codex CLI, one run per game).

| Condition | Runs | Input | Cached input | Output | Reasoning | Wall s |
|---|---|---|---|---|---|---|
| **paper (Codex CLI)** | 4 | 73,722 (73,695–73,749) | 608 (0–2,432) | 1,780 (1,679–1,838) | 983 (833–1,034) | 82.9 (70.8–107.2) |
| original | 12 | 70,242 (70,215–70,269) | 5,845 (0–70,144) | 1,943 (1,654–2,551) | 980 (670–1,552) | 74.5 (61.2–88.7) |
| x10_input | 8 | 86,294 (86,266–86,320) | 0 (0–0) | 2,096 (1,690–3,013) | 1,046 (516–1,976) | 78.2 (64.9–99.6) |
| div10_input | 8 | 70,296 (70,268–70,322) | 0 (0–0) | 2,084 (1,473–2,413) | 1,078 (470–1,436) | 73.0 (53.2–91.7) |
| x10_output | 8 | 70,470 (70,442–70,496) | 0 (0–0) | 2,145 (1,258–2,657) | 1,146 (338–1,552) | 77.2 (50.0–91.0) |
| div10_output | 8 | 70,308 (70,280–70,334) | 0 (0–0) | 2,254 (1,894–3,044) | 1,220 (895–2,070) | 77.2 (60.3–105.6) |
| L0s_sig3 | 8 | 80,518 (79,993–80,790) | 0 (0–0) | 2,045 (1,546–2,534) | 997 (516–1,552) | 72.0 (56.4–88.3) |
| L2_chscale | 8 | 81,309 (81,053–81,540) | 0 (0–0) | 1,546 (1,243–1,842) | 457 (216–763) | 57.2 (46.5–69.4) |
| L3_chaffine | 8 | 86,708 (86,695–86,722) | 0 (0–0) | 1,698 (1,332–2,686) | 614 (311–1,552) | 61.2 (51.1–84.6) |
| L4_flip | 8 | 80,544 (80,019–80,816) | 0 (0–0) | 1,843 (1,463–2,165) | 832 (510–1,034) | 65.3 (45.0–85.6) |
| L5_perm | 8 | 82,102 (81,577–82,374) | 0 (0–0) | 2,711 (2,082–3,688) | 1,507 (1,034–2,367) | 89.9 (70.6–126.5) |
| L6a_flip_scale | 8 | 81,384 (81,128–81,615) | 10,144 (0–81,152) | 1,815 (1,344–2,144) | 709 (354–1,034) | 64.6 (46.9–81.3) |
| L6b_perm_flip_scale | 8 | 82,776 (82,728–82,840) | 0 (0–0) | 3,162 (2,586–4,393) | 1,917 (1,552–3,106) | 109.1 (58.0–141.0) |
| L6c_perm_flip_scale_affine | 8 | 91,690 (91,662–91,738) | 0 (0–0) | 3,751 (2,337–7,077) | 2,431 (1,034–5,696) | 122.7 (78.7–200.3) |
| L7_givens10 | 8 | 81,404 (80,929–81,648) | 0 (0–0) | 2,413 (1,894–3,253) | 1,238 (516–2,070) | 82.1 (64.6–105.9) |
| L7_givens50 | 8 | 83,636 (83,200–83,823) | 0 (0–0) | 2,690 (2,271–3,861) | 1,507 (1,034–2,549) | 92.0 (72.4–125.0) |
| L7_givens250 | 8 | 95,208 (95,178–95,232) | 0 (0–0) | 5,019 (3,157–6,822) | 3,706 (1,815–5,434) | 167.7 (107.4–228.1) |
| L8_anon | 8 | 80,426 (79,901–80,698) | 0 (0–0) | 3,064 (2,360–4,510) | 2,059 (1,355–3,589) | 110.0 (92.8–173.4) |
| L8_anon_flip | 8 | 80,452 (79,927–80,724) | 0 (0–0) | 2,744 (2,148–3,153) | 1,714 (1,132–2,070) | 102.3 (70.2–144.2) |
| L9_hidden_perm_sign | 8 | 80,505 (80,041–80,800) | 0 (0–0) | 2,004 (1,455–2,403) | 1,025 (497–1,524) | 71.0 (51.8–87.2) |
| P_aff | 8 | 80,711 (80,186–80,983) | 0 (0–0) | 2,470 (1,781–3,109) | 1,348 (799–2,070) | 80.8 (62.7–113.9) |
| P_xs_1 | 8 | 80,835 (80,310–81,107) | 0 (0–0) | 3,539 (2,274–5,210) | 2,425 (1,034–4,142) | 123.8 (78.7–189.2) |
| P_xs_2 | 8 | 80,849 (80,324–81,121) | 10,112 (0–80,896) | 4,330 (3,212–6,357) | 3,194 (2,070–5,178) | 141.5 (123.6–205.0) |
| P_xs_4 | 8 | 80,877 (80,352–81,149) | 0 (0–0) | 4,123 (3,267–6,147) | 2,982 (2,070–4,890) | 140.8 (101.5–218.5) |
| P_xs_8 | 8 | 80,933 (80,408–81,205) | 0 (0–0) | 6,560 (4,754–10,066) | 5,382 (3,624–8,804) | 223.8 (171.9–284.7) |
| P_xs_16 | 8 | 81,045 (80,520–81,317) | 0 (0–0) | 8,082 (4,645–13,694) | 7,001 (3,624–12,430) | 266.1 (160.7–351.4) |
| P_xs_32 | 8 | 81,269 (80,744–81,541) | 0 (0–0) | 11,713 (8,516–16,144) | 10,577 (7,250–15,020) | 348.8 (246.8–466.9) |
| P_xs_64 | 8 | 81,717 (81,192–81,989) | 0 (0–0) | 13,444 (8,961–19,157) | 12,464 (7,962–18,126) | 422.8 (312.1–558.1) |
| P_xs_128 | 8 | 82,613 (82,088–82,885) | 10,336 (0–82,688) | 2,959 (1,016–14,272) | 2,141 (228–13,226) | 107.8 (43.0–480.2) |
| P_sha | 8 | 80,761 (80,236–81,033) | 0 (0–0) | 1,200 (951–1,474) | 399 (208–516) | 49.0 (37.1–61.5) |
| P_sha_out | 8 | 80,892 (80,362–81,163) | 0 (0–0) | 1,204 (973–1,585) | 467 (304–865) | 48.9 (36.4–66.3) |

Per game, paper vs our original condition (mean of 3):

| Game | Paper in / cached / out / reasoning / wall s | Ours (original) in / cached / out / reasoning / wall s |
|---|---|---|
| breakout | 73,749 / 2,432 / 1,679 / 833 / 107.2 | 70,269 / 0 / 1,786 / 883 / 75.8 |
| pong | 73,723 / 0 / 1,833 / 1,031 / 82.7 | 70,243 / 23,381 / 1,849 / 892 / 76.9 |
| pacman | 73,723 / 0 / 1,838 / 1,034 / 70.8 | 70,243 / 0 / 2,066 / 1,061 / 77.1 |
| freeway | 73,695 / 0 / 1,768 / 1,034 / 70.9 | 70,215 / 0 / 2,070 / 1,085 / 68.5 |

## Wrong or unmapped answers

- **P_sha / pacman (bdf99279) r1** -> `other`, confidence 20.0: Game: "Undetermined. My best-supported classification is a four-direction grid-navigation or target-collection game, not a reliably identified named game."
- **P_sha / pacman (bdf99279) r2** -> `other`, confidence 20.0: Game: "Tentatively, a two-dimensional target-collection gridworld; the specific game is not reliably identified."
- **P_sha_out / freeway (0bbcc3ea) r1** -> `other`, confidence 0.0: Game: "Undetermined—I cannot reliably identify the game from these permuted weights under the stated constraints."
- **P_sha_out / freeway (0bbcc3ea) r2** -> `other`, confidence 0.0: Game: "Undetermined from the analysis I can reliably perform under the no-tools constraint."
- **P_sha_out / breakout (a9f535cc) r1** -> `pong`, confidence 40.0: Game: "A two-direction paddle-control game, plausibly Pong or Breakout. I cannot reliably distinguish the specific game under the no-tools constraint."
- **P_sha_out / pacman (bdf99279) r1** -> `other`, confidence 0.0: Game: "Not reliably identified from this manual inspection."
- **P_sha_out / pacman (bdf99279) r2** -> `other`, confidence 0.0: Game: "Not reliably identified from my analysis of these weights."
- **P_sha_out / pong (dfc6cb65) r1** -> `breakout`, confidence 30.0: Game: "Tentatively Breakout—a paddle-and-ball brick-breaking game. The stronger conclusion is merely “a one-axis paddle/control game.”"
- **P_xs_128 / pacman (bdf99279) r1** -> `other`, confidence 20.0: Game: "Tentative guess: Snake. This is a low-confidence guess, not a decoded identification."
- **P_xs_128 / pacman (bdf99279) r2** -> `other`, confidence 25.0: Game: "Not reliably identified. The most specific defensible characterization from my analysis is a likely four-direction grid-movement game, rather than a confidently identified named game."
- **P_xs_16 / breakout (a9f535cc) r2** -> `other`, confidence 82.0: Game: "Space Invaders-style, probably an automatically firing grid-based variant."
- **P_xs_16 / pacman (bdf99279) r2** -> `other`, confidence 45.0: Game: "Best guess: Dodge — an open-grid moving-enemy avoidance/survival game."
- **P_xs_64 / pacman (bdf99279) r1** -> `other`, confidence 30.0: Game: "Tentatively, “Dodge”: a full-grid moving-enemy avoidance/survival game."
- **P_xs_64 / pacman (bdf99279) r2** -> `other`, confidence 25.0: Game: "Best guess: a “Chase” or moving-target collection game. The exact game remains undetermined."

## All Game: lines

| Condition | Truth | Replica | Guess | Conf | Game: line |
|---|---|---|---|---|---|
| L0s_sig3 | freeway | r1 | freeway | 96.0 | Frogger — most likely a simplified traffic-only Frogger / road-crossing grid game. |
| L0s_sig3 | freeway | r2 | freeway | 95.0 | Frogger — a grid-based traffic-crossing variant. |
| L0s_sig3 | breakout | r1 | breakout | 97.0 | Breakout — a grid-based brick-breaker, also resembling Arkanoid. |
| L0s_sig3 | breakout | r2 | breakout | 96.0 | Breakout — a grid-based brick-breaking paddle-and-ball game. |
| L0s_sig3 | pacman | r1 | pacman | 93.0 | Pac-Man — a small, fixed-maze grid variant with collectible pellets and moving ghosts. |
| L0s_sig3 | pacman | r2 | pacman | 97.0 | Pac-Man — a small, fixed-maze gridworld version. |
| L0s_sig3 | pong | r1 | pong | 93.0 | Pong — most likely a single-player, left-paddle wall-Pong variant. |
| L0s_sig3 | pong | r2 | pong | 94.0 | Single-player Pong — a vertical left-paddle, wall-bounce variant, also resembling Squash. |
| L2_chscale | freeway | r1 | freeway | 98.0 | Frogger — a simplified grid-based traffic-crossing version. |
| L2_chscale | freeway | r2 | freeway | 96.0 | Frogger — most likely a simplified grid-based traffic/road-crossing version. |
| L2_chscale | breakout | r1 | breakout | 98.0 | Breakout — a grid-based brick-breaker. |
| L2_chscale | breakout | r2 | breakout | 97.0 | Breakout — a simplified grid-based brick-breaking game, also resembling Arkanoid. |
| L2_chscale | pacman | r1 | pacman | 97.0 | Pac-Man — a simplified, grid-based maze-and-ghosts version. |
| L2_chscale | pacman | r2 | pacman | 96.0 | A small grid-based Pac-Man-style maze game. |
| L2_chscale | pong | r1 | pong | 97.0 | Pong — a grid-based variant with the player controlling the left-hand paddle using up and down. |
| L2_chscale | pong | r2 | pong | 98.0 | Pong — a grid-based variant with the player controlling the left-hand vertical paddle. |
| L3_chaffine | freeway | r1 | freeway | 96.0 | Frogger — a simplified grid-based traffic/road-crossing variant. |
| L3_chaffine | freeway | r2 | freeway | 97.0 | Frogger — a simplified grid-based road-crossing variant. |
| L3_chaffine | breakout | r1 | breakout | 98.0 | Breakout — a grid-based brick-breaker game. |
| L3_chaffine | breakout | r2 | breakout | 97.0 | Breakout — a grid-based brick-breaker variant. |
| L3_chaffine | pacman | r1 | pacman | 95.0 | Pac-Man — a small, fixed-maze gridworld variant with ghosts and collectible pellets. |
| L3_chaffine | pacman | r2 | pacman | 96.0 | A small grid-based Pac-Man-style game, with a fixed maze and moving ghosts. |
| L3_chaffine | pong | r1 | pong | 95.0 | Pong — a small-grid, left-paddle ball-return variant, probably single-paddle. |
| L3_chaffine | pong | r2 | pong | 97.0 | Pong — a grid-based variant with a vertically moving paddle on the left. |
| L4_flip | freeway | r1 | freeway | 96.0 | Frogger — a grid-based road/traffic-crossing variant. |
| L4_flip | freeway | r2 | freeway | 96.0 | Frogger — specifically a simplified traffic/road-crossing version. |
| L4_flip | breakout | r1 | breakout | 98.0 | Breakout — a grid-based brick-breaker, also resembling Arkanoid. |
| L4_flip | breakout | r2 | breakout | 97.0 | Breakout — a grid-based paddle-and-ball brick-breaking game. |
| L4_flip | pacman | r1 | pacman | 96.0 | Pac-Man — a simplified, fixed-maze grid version. |
| L4_flip | pacman | r2 | pacman | 97.0 | A small grid-based Pac-Man variant, played in a fixed maze. |
| L4_flip | pong | r1 | pong | 96.0 | Pong — a grid-based variant with a vertically moving paddle on the left. |
| L4_flip | pong | r2 | pong | 95.0 | Pong — a grid-based version with the player’s paddle on the left, possibly a single-paddle “bounce against the far wall” variant. |
| L5_perm | freeway | r1 | freeway | 93.0 | Frogger — most likely a simplified traffic-dodging, bottom-to-top road-crossing variant. |
| L5_perm | freeway | r2 | freeway | 90.0 | Frogger-style road crossing, most likely a simplified, road-only Frogger / Freeway-like grid game. |
| L5_perm | breakout | r1 | breakout | 97.0 | Breakout — a simplified grid-based brick-breaking game. |
| L5_perm | breakout | r2 | breakout | 97.0 | Breakout — a small grid-based brick-breaking paddle-and-ball game. |
| L5_perm | pacman | r1 | pacman | 85.0 | Pac-Man — a small grid-based maze-and-pellet variant with moving ghosts. |
| L5_perm | pacman | r2 | pacman | 89.0 | A small grid-based Pac-Man-style game: collect pellets in a maze while avoiding moving ghosts. |
| L5_perm | pong | r1 | pong | 96.0 | Pong — a grid-based version with a vertically moving paddle on the left. |
| L5_perm | pong | r2 | pong | 96.0 | Pong — a small-grid version with the agent controlling the left-hand paddle. |
| L6a_flip_scale | freeway | r1 | freeway | 95.0 | Frogger — most likely a simplified grid-based road-crossing version with horizontally moving traffic. |
| L6a_flip_scale | freeway | r2 | freeway | 96.0 | Frogger — a grid-based, bottom-to-top road-crossing game with moving traffic lanes. |
| L6a_flip_scale | breakout | r1 | breakout | 97.0 | Breakout — a grid-based paddle-and-ball brick breaker. |
| L6a_flip_scale | breakout | r2 | breakout | 97.0 | Breakout — a grid-based brick-breaking paddle-and-ball game, also resembling Arkanoid. |
| L6a_flip_scale | pacman | r1 | pacman | 96.0 | A miniature grid-based Pac-Man game. |
| L6a_flip_scale | pacman | r2 | pacman | 95.0 | A small-grid Pac-Man-style maze-chase game. |
| L6a_flip_scale | pong | r1 | pong | 96.0 | A small grid-based Pong game, with the player controlling the vertical paddle on the left. |
| L6a_flip_scale | pong | r2 | pong | 95.0 | Pong — a grid-based variant with the player’s paddle on the left, controlled by up/down movement. |
| L6b_perm_flip_scale | freeway | r1 | freeway | 92.0 | A simplified grid-based Frogger / Freeway-style road-crossing game. |
| L6b_perm_flip_scale | freeway | r2 | freeway | 94.0 | A simplified Frogger-style road-crossing game. |
| L6b_perm_flip_scale | breakout | r1 | breakout | 95.0 | Breakout — a simplified grid-based brick-breaker. |
| L6b_perm_flip_scale | breakout | r2 | breakout | 96.0 | Breakout — a grid-based brick-breaker, in the Breakout/Arkanoid family. |
| L6b_perm_flip_scale | pacman | r1 | pacman | 86.0 | A simplified grid-based Pac-Man game: collecting maze pellets while avoiding moving ghosts. |
| L6b_perm_flip_scale | pacman | r2 | pacman | 89.0 | A small grid-based Pac-Man-style maze game. |
| L6b_perm_flip_scale | pong | r1 | pong | 94.0 | Pong — a grid-based version with the player controlling the left-side vertical paddle. |
| L6b_perm_flip_scale | pong | r2 | pong | 94.0 | Pong — a grid-based version with the player controlling the left-hand vertical paddle. |
| L6c_perm_flip_scale_affine | freeway | r1 | freeway | 91.0 | Frogger — most likely a simplified, traffic-lane road-crossing version. |
| L6c_perm_flip_scale_affine | freeway | r2 | freeway | 93.0 | Frogger — most likely a simplified road-crossing variant, similar to Freeway or Crossy Road. |
| L6c_perm_flip_scale_affine | breakout | r1 | breakout | 96.0 | Breakout — a grid-based paddle-and-ball brick-breaking game, similar to Atari Breakout. |
| L6c_perm_flip_scale_affine | breakout | r2 | breakout | 96.0 | Breakout — a small grid-based brick-breaking paddle-and-ball game. |
| L6c_perm_flip_scale_affine | pacman | r1 | pacman | 89.0 | A grid-based Pac-Man-style maze-chase and pellet-collection game. |
| L6c_perm_flip_scale_affine | pacman | r2 | pacman | 84.0 | A small grid-based Pac-Man variant — a fixed-maze pellet-collection and ghost-avoidance game. |
| L6c_perm_flip_scale_affine | pong | r1 | pong | 94.0 | Pong — a small grid-based version, most likely controlling the left paddle with up/down actions. |
| L6c_perm_flip_scale_affine | pong | r2 | pong | 94.0 | Pong — a grid-based variant with the player controlling the left paddle vertically. |
| L7_givens10 | freeway | r1 | freeway | 97.0 | Frogger — a simplified grid-based traffic/road-crossing version. |
| L7_givens10 | freeway | r2 | freeway | 96.0 | Frogger — most likely a simplified grid-based traffic-dodging / road-crossing version. |
| L7_givens10 | breakout | r1 | breakout | 98.0 | Breakout — a grid-based brick-breaker. |
| L7_givens10 | breakout | r2 | breakout | 97.0 | Breakout — a grid-based brick-breaker, also resembling Arkanoid. |
| L7_givens10 | pacman | r1 | pacman | 97.0 | A small grid-based Pac-Man variant: collect pellets in a fixed maze while avoiding moving ghosts. |
| L7_givens10 | pacman | r2 | pacman | 95.0 | A small grid-based Pac-Man-style maze game. |
| L7_givens10 | pong | r1 | pong | 95.0 | Pong — most likely a single-player, left-paddle wall-Pong variant. |
| L7_givens10 | pong | r2 | pong | 97.0 | Pong — a grid-based, vertically controlled left-paddle variant, possibly single-player Pong. |
| L7_givens250 | freeway | r1 | freeway | 95.0 | Frogger-style road crossing — most likely a small grid-based Frogger game. |
| L7_givens250 | freeway | r2 | freeway | 95.0 | Frogger — most likely a simplified grid-based traffic-crossing game. |
| L7_givens250 | breakout | r1 | breakout | 96.0 | Breakout — a small grid-based brick-breaker, similar to Atari Breakout or Arkanoid. |
| L7_givens250 | breakout | r2 | breakout | 94.0 | Breakout — a small grid-based brick-breaking game, similar to Atari Breakout. |
| L7_givens250 | pacman | r1 | pacman | 88.0 | Pac-Man — a small grid-based maze-and-pellet variant with moving ghosts. |
| L7_givens250 | pacman | r2 | pacman | 85.0 | A small grid-based Pac-Man-style maze game. |
| L7_givens250 | pong | r1 | pong | 94.0 | Pong — a grid-based version with the player’s paddle on the left, moving up and down. |
| L7_givens250 | pong | r2 | pong | 93.0 | Pong — a grid-based version with a vertically moving paddle on the left side. |
| L7_givens50 | freeway | r1 | freeway | 94.0 | Frogger-style road crossing — most likely a simplified, traffic-focused Frogger game, also resembling Freeway. |
| L7_givens50 | freeway | r2 | freeway | 95.0 | Frogger — a simplified, Freeway-like traffic-crossing grid game. |
| L7_givens50 | breakout | r1 | breakout | 96.0 | Breakout, or a simplified grid-based Arkanoid-style brick-breaking game. |
| L7_givens50 | breakout | r2 | breakout | 97.0 | Breakout — a grid-based brick-breaker, closely resembling Atari Breakout or Arkanoid. |
| L7_givens50 | pacman | r1 | pacman | 97.0 | Pac-Man — a small, fixed-maze gridworld version. |
| L7_givens50 | pacman | r2 | pacman | 95.0 | Pac-Man — a small, fixed-maze gridworld variant. |
| L7_givens50 | pong | r1 | pong | 94.0 | Pong — a grid-based version with a vertically moving paddle on the left. |
| L7_givens50 | pong | r2 | pong | 96.0 | Pong — a grid-based version with an up/down-controlled paddle on the left. |
| L8_anon | freeway | r1 | freeway | 86.0 | A grid-based Frogger-style road-crossing game, most likely a traffic-dodging variant. |
| L8_anon | freeway | r2 | freeway | 86.0 | Frogger-style road crossing, most likely a simplified grid-based traffic-dodging variant, also resembling Freeway. |
| L8_anon | breakout | r1 | breakout | 94.0 | Breakout — a grid-based brick-breaker, also resembling Arkanoid. |
| L8_anon | breakout | r2 | breakout | 96.0 | Breakout — a simplified grid-based brick-breaker, also resembling Arkanoid. |
| L8_anon | pacman | r1 | pacman | 82.0 | A small, fixed-maze Pac-Man-style game, most likely a gridworld version of Pac-Man. |
| L8_anon | pacman | r2 | pacman | 85.0 | A small grid-based Pac-Man variant, played in a fixed 10 × 10 maze. |
| L8_anon | pong | r1 | pong | 78.0 | A grid-based Pong-style game, with the agent controlling a vertical paddle on the left. Possibly a one-player wall-return variant rather than standard two-paddle Pong. |
| L8_anon | pong | r2 | pong | 86.0 | Pong, most likely a simplified grid-based version with the agent controlling the left paddle vertically. |
| L8_anon_flip | freeway | r1 | freeway | 80.0 | Most likely a Frogger-style road-crossing game—a small gridworld variant of Frogger. |
| L8_anon_flip | freeway | r2 | freeway | 84.0 | A Frogger-style traffic-crossing game—most likely a simplified road-only Frogger / Freeway variant. |
| L8_anon_flip | breakout | r1 | breakout | 95.0 | Breakout — a simplified grid-based brick-breaking game, possibly an Arkanoid-style variant. |
| L8_anon_flip | breakout | r2 | breakout | 95.0 | Breakout — a simplified 10 × 10 grid-based brick-breaker, in the Breakout/Arkanoid family. |
| L8_anon_flip | pacman | r1 | pacman | 87.0 | A small grid-based Pac-Man variant, played in a fixed 10 × 10 maze. |
| L8_anon_flip | pacman | r2 | pacman | 84.0 | A small fixed-maze Pac-Man-style game: collecting pellets while avoiding ghosts, probably with power pellets or another special collectible. |
| L8_anon_flip | pong | r1 | pong | 94.0 | Pong, specifically a small grid-based version with the agent controlling the left paddle using up and down. |
| L8_anon_flip | pong | r2 | pong | 93.0 | Pong — a grid-based, vertically controlled left-paddle variant, possibly a simplified single-player return-the-ball version. |
| L9_hidden_perm_sign | freeway | r1 | freeway | 97.0 | Frogger — a simplified grid-based road-crossing variant. |
| L9_hidden_perm_sign | freeway | r2 | freeway | 96.0 | Frogger — most likely a simplified road-crossing variant with moving traffic. |
| L9_hidden_perm_sign | breakout | r1 | breakout | 94.0 | Breakout — a simplified grid-based brick breaker, also resembling Arkanoid. |
| L9_hidden_perm_sign | breakout | r2 | breakout | 96.0 | Breakout — a grid-based paddle-and-ball brick breaker, similar to Arkanoid. |
| L9_hidden_perm_sign | pacman | r1 | pacman | 95.0 | Pac-Man — a small, fixed-maze gridworld version with pellets and moving ghosts. |
| L9_hidden_perm_sign | pacman | r2 | pacman | 93.0 | Pac-Man, most likely a simplified grid-based Pac-Man clone with a fixed maze. |
| L9_hidden_perm_sign | pong | r1 | pong | 97.0 | Pong — a grid-based paddle-and-ball game, likely a single-paddle wall-return variant with the paddle on the left. |
| L9_hidden_perm_sign | pong | r2 | pong | 97.0 | Pong — most likely a single-player, wall-return variant with a vertically moving paddle on the left. |
| P_aff | freeway | r1 | freeway | 94.0 | Frogger — a grid-based road-crossing variant. |
| P_aff | freeway | r2 | freeway | 95.0 | Frogger-style road crossing, most likely a simplified Frogger, also resembling Freeway. |
| P_aff | breakout | r1 | breakout | 97.0 | Breakout — a grid-based paddle-and-ball brick-breaking game. |
| P_aff | breakout | r2 | breakout | 97.0 | Breakout — a grid-based brick-breaker, in the Breakout/Arkanoid family. |
| P_aff | pacman | r1 | pacman | 91.0 | Pac-Man — a miniature grid-maze version with pellets and roaming ghosts. |
| P_aff | pacman | r2 | pacman | 92.0 | Pac-Man — most likely a simplified grid-based Pac-Man variant. |
| P_aff | pong | r1 | pong | 96.0 | Pong — a grid-based version with the player’s paddle on the left, moving up and down. |
| P_aff | pong | r2 | pong | 95.0 | Pong — a grid-based version with the player’s paddle on the left, controlled by up/down. |
| P_sha | freeway | r1 | freeway | 40.0 | Frogger-style road crossing, tentatively; possibly a simplified Freeway-like variant. |
| P_sha | freeway | r2 | freeway | 45.0 | Frogger, or a simplified grid-based road-crossing variant — my best guess, not a verified identification. |
| P_sha | breakout | r1 | breakout | 35.0 | Best guess: Breakout — a grid-based paddle-and-ball brick-breaking game. |
| P_sha | breakout | r2 | breakout | 30.0 | A horizontal paddle/catcher game; my tentative best guess is a small grid version of Breakout. |
| P_sha | pacman | r1 | other | 20.0 | Undetermined. My best-supported classification is a four-direction grid-navigation or target-collection game, not a reliably identified named game. |
| P_sha | pacman | r2 | other | 20.0 | Tentatively, a two-dimensional target-collection gridworld; the specific game is not reliably identified. |
| P_sha | pong | r1 | pong | 82.0 | Pong — a grid-based paddle-and-ball game with a vertically moving paddle. |
| P_sha | pong | r2 | pong | 78.0 | Pong—or a closely related vertical paddle-and-ball return game. |
| P_sha_out | freeway | r1 | other | 0.0 | Undetermined—I cannot reliably identify the game from these permuted weights under the stated constraints. |
| P_sha_out | freeway | r2 | other | 0.0 | Undetermined from the analysis I can reliably perform under the no-tools constraint. |
| P_sha_out | breakout | r1 | pong | 40.0 | A two-direction paddle-control game, plausibly Pong or Breakout. I cannot reliably distinguish the specific game under the no-tools constraint. |
| P_sha_out | breakout | r2 | breakout | 25.0 | A one-axis paddle game; my tentative specific guess is Breakout. |
| P_sha_out | pacman | r1 | other | 0.0 | Not reliably identified from this manual inspection. |
| P_sha_out | pacman | r2 | other | 0.0 | Not reliably identified from my analysis of these weights. |
| P_sha_out | pong | r1 | breakout | 30.0 | Tentatively Breakout—a paddle-and-ball brick-breaking game. The stronger conclusion is merely “a one-axis paddle/control game.” |
| P_sha_out | pong | r2 | pong | 30.0 | Best guess: a simplified grid-based Pong-style paddle-and-ball game. The evidence supports the paddle/interception family more strongly than Pong specifically. |
| P_xs_1 | freeway | r1 | freeway | 93.0 | A gridworld version of Frogger—most likely a traffic-dodging, bottom-to-top road-crossing game. |
| P_xs_1 | freeway | r2 | freeway | 94.0 | Frogger — a simplified grid-based traffic-crossing variant. |
| P_xs_1 | breakout | r1 | breakout | 94.0 | Breakout — a grid-based paddle-and-ball brick-breaking game. |
| P_xs_1 | breakout | r2 | breakout | 97.0 | Breakout — a grid-based brick-breaker, also resembling Arkanoid. |
| P_xs_1 | pacman | r1 | pacman | 88.0 | A grid-based Pac-Man-style maze game. |
| P_xs_1 | pacman | r2 | pacman | 85.0 | Pac-Man, or a simplified Pac-Man-style grid maze game. |
| P_xs_1 | pong | r1 | pong | 93.0 | Pong — a grid-based version with an up/down-controlled paddle on the left, likely single-player wall Pong. |
| P_xs_1 | pong | r2 | pong | 94.0 | Pong-style grid paddle-and-ball game, with the player’s vertical paddle on the left. |
| P_xs_128 | freeway | r1 | freeway | 45.0 | Best guess: a simplified Frogger-style traffic-crossing game. |
| P_xs_128 | freeway | r2 | freeway | 45.0 | Frogger — most likely a simplified grid-based traffic-crossing variant. |
| P_xs_128 | breakout | r1 | breakout | 91.0 | Breakout — a small grid-based brick-breaker, in the Breakout/Arkanoid family. |
| P_xs_128 | breakout | r2 | breakout | 35.0 | Best guess: a small-grid Breakout-style paddle-and-ball game. The firmer conclusion is a horizontally controlled interception game. |
| P_xs_128 | pacman | r1 | other | 20.0 | Tentative guess: Snake. This is a low-confidence guess, not a decoded identification. |
| P_xs_128 | pacman | r2 | other | 25.0 | Not reliably identified. The most specific defensible characterization from my analysis is a likely four-direction grid-movement game, rather than a confidently identified named game. |
| P_xs_128 | pong | r1 | pong | 65.0 | Best guess: a grid-based Pong variant, with a vertically moving paddle. |
| P_xs_128 | pong | r2 | pong | 70.0 | Probably a small grid-based version of Pong, with a vertically moving paddle. |
| P_xs_16 | freeway | r1 | freeway | 87.0 | Frogger-like traffic crossing, most likely a simplified grid version of Frogger. |
| P_xs_16 | freeway | r2 | freeway | 84.0 | Most likely Frogger — a simplified upward, lane-crossing game, possibly closer to Freeway if its hazards are exclusively traffic. |
| P_xs_16 | breakout | r1 | breakout | 91.0 | Breakout — a grid-based brick-breaking paddle-and-ball game. |
| P_xs_16 | breakout | r2 | other | 82.0 | Space Invaders-style, probably an automatically firing grid-based variant. |
| P_xs_16 | pacman | r1 | pacman | 50.0 | Best guess: a simplified Pac-Man-like collection-and-avoidance game. |
| P_xs_16 | pacman | r2 | other | 45.0 | Best guess: Dodge — an open-grid moving-enemy avoidance/survival game. |
| P_xs_16 | pong | r1 | pong | 94.0 | Pong — a grid-based, vertically controlled paddle-and-ball variant, with the player’s paddle on the left. |
| P_xs_16 | pong | r2 | pong | 90.0 | Pong — a grid-based variant with the player’s paddle on the left, moving vertically. |
| P_xs_2 | freeway | r1 | freeway | 96.0 | Frogger — most likely a simplified grid-based traffic-crossing version. |
| P_xs_2 | freeway | r2 | freeway | 90.0 | Frogger — a simplified grid-based traffic-crossing variant. |
| P_xs_2 | breakout | r1 | breakout | 96.0 | Breakout — a small grid-based brick-breaker. |
| P_xs_2 | breakout | r2 | breakout | 96.0 | Breakout — a grid-based paddle-and-ball brick-breaking game. |
| P_xs_2 | pacman | r1 | pacman | 87.0 | A simplified grid-based Pac-Man game. |
| P_xs_2 | pacman | r2 | pacman | 87.0 | Pac-Man — most likely a simplified grid-based pellet-collecting, ghost-avoidance variant. |
| P_xs_2 | pong | r1 | pong | 89.0 | Pong — most likely a simplified single-paddle, vertical paddle-ball variant, with the paddle on the left. |
| P_xs_2 | pong | r2 | pong | 92.0 | A simplified Pong-style paddle-and-ball game, with the controlled paddle on the left moving up and down. |
| P_xs_32 | freeway | r1 | freeway | 80.0 | Most likely a simplified grid-based Frogger: an upward traffic-crossing game. |
| P_xs_32 | freeway | r2 | freeway | 82.0 | Most likely Frogger — a simplified grid-based road-crossing variant, possibly closer to Freeway than full arcade Frogger. |
| P_xs_32 | breakout | r1 | breakout | 90.0 | Breakout — a simplified grid-based brick-breaker. |
| P_xs_32 | breakout | r2 | breakout | 92.0 | Breakout — a small grid-based brick-breaker. |
| P_xs_32 | pacman | r1 | pacman | 68.0 | Most likely a small grid-world Pac-Man variant: collect pellets while avoiding moving ghosts. |
| P_xs_32 | pacman | r2 | pacman | 65.0 | Most likely a simplified grid-based Pac-Man: collect pellets while avoiding moving ghosts. |
| P_xs_32 | pong | r1 | pong | 94.0 | Pong — a grid-based version with the agent controlling the left-hand vertical paddle. |
| P_xs_32 | pong | r2 | pong | 94.0 | Pong — a small grid-based version, with the agent controlling the left paddle vertically. |
| P_xs_4 | freeway | r1 | freeway | 90.0 | Frogger-style road crossing, most likely a simplified grid version of Frogger. |
| P_xs_4 | freeway | r2 | freeway | 86.0 | Frogger — most likely a simplified traffic-dodging, bottom-to-top crossing variant. |
| P_xs_4 | breakout | r1 | breakout | 95.0 | Breakout — a small grid-based paddle-and-ball brick-breaking game. |
| P_xs_4 | breakout | r2 | breakout | 96.0 | Breakout — a grid-based brick-breaking paddle-and-ball game. |
| P_xs_4 | pacman | r1 | pacman | 83.0 | Pac-Man, or a small grid-based Pac-Man-like maze game. |
| P_xs_4 | pacman | r2 | pacman | 83.0 | Pac-Man-style maze chase, most likely a small grid-based Pac-Man implementation. |
| P_xs_4 | pong | r1 | pong | 93.0 | Pong — a grid-based version with the player controlling the left vertical paddle. |
| P_xs_4 | pong | r2 | pong | 93.0 | Pong, most likely a grid-based version with the player controlling the left-hand vertical paddle. |
| P_xs_64 | freeway | r1 | freeway | 70.0 | Frogger — most likely a simplified grid-based traffic-crossing variant. |
| P_xs_64 | freeway | r2 | freeway | 70.0 | A simplified Frogger-like road-crossing game. |
| P_xs_64 | breakout | r1 | breakout | 60.0 | Most likely a grid-based Breakout-style brick breaker. |
| P_xs_64 | breakout | r2 | breakout | 82.0 | Breakout — a small grid-based brick-breaker variant. |
| P_xs_64 | pacman | r1 | other | 30.0 | Tentatively, “Dodge”: a full-grid moving-enemy avoidance/survival game. |
| P_xs_64 | pacman | r2 | other | 25.0 | Best guess: a “Chase” or moving-target collection game. The exact game remains undetermined. |
| P_xs_64 | pong | r1 | pong | 90.0 | Pong — a grid-based vertical-paddle variant, with the player’s paddle on the left and a right-edge scoring target. |
| P_xs_64 | pong | r2 | pong | 88.0 | Pong, or a close grid-based Pong variant, with the player controlling the left-hand vertical paddle. |
| P_xs_8 | freeway | r1 | freeway | 93.0 | Frogger — specifically, a simplified grid-based traffic-crossing variant. |
| P_xs_8 | freeway | r2 | freeway | 92.0 | Frogger — most likely a simplified Frogger/Freeway-style traffic-crossing game. |
| P_xs_8 | breakout | r1 | breakout | 93.0 | Breakout — a grid-based brick-breaker variant. |
| P_xs_8 | breakout | r2 | breakout | 93.0 | Breakout — a grid-based brick-breaker, similar to Atari Breakout. |
| P_xs_8 | pacman | r1 | pacman | 78.0 | Pac-Man — most likely a simplified grid-based maze-and-ghosts variant. |
| P_xs_8 | pacman | r2 | pacman | 80.0 | Pac-Man — most likely a simplified grid-based Pac-Man-style game. |
| P_xs_8 | pong | r1 | pong | 92.0 | Pong — a small-grid, vertically controlled paddle-and-ball variant, with the player’s paddle on the left. |
| P_xs_8 | pong | r2 | pong | 94.0 | Pong — a grid-based version with the player controlling a vertical paddle on the left. |
| div10_input | freeway | r1 | freeway | 95.0 | Frogger-style road crossing — most likely a simplified grid version of Frogger, focused on dodging traffic. |
| div10_input | freeway | r2 | freeway | 98.0 | Frogger — a grid-based, likely traffic-only road-crossing variant. |
| div10_input | breakout | r1 | breakout | 97.0 | Breakout — a small grid-based version of the classic paddle-and-ball brick breaker. |
| div10_input | breakout | r2 | breakout | 97.0 | Breakout — an Atari Breakout / Arkanoid-style brick-breaking game. |
| div10_input | pacman | r1 | pacman | 96.0 | A miniature grid-based Pac-Man-style maze-chase game. |
| div10_input | pacman | r2 | pacman | 96.0 | A small-grid Pac-Man variant: collecting pellets in a fixed maze while avoiding moving ghosts. |
| div10_input | pong | r1 | pong | 96.0 | Pong — a grid-based variant with the player’s paddle on the left, moving vertically. |
| div10_input | pong | r2 | pong | 95.0 | Pong — most likely a single-player, left-paddle wall-return variant. |
| div10_output | freeway | r1 | freeway | 97.0 | A grid-based Frogger-style traffic-crossing game, resembling Freeway: cross horizontal lanes of cars from bottom to top. |
| div10_output | freeway | r2 | freeway | 96.0 | Frogger — a simplified grid-based road/traffic-crossing variant, also resembling Freeway. |
| div10_output | breakout | r1 | breakout | 98.0 | Breakout — a small grid-based brick-breaker, also resembling Arkanoid. |
| div10_output | breakout | r2 | breakout | 96.0 | Breakout — a grid-based brick-breaking paddle-and-ball game, also resembling Arkanoid. |
| div10_output | pacman | r1 | pacman | 96.0 | A small grid-based Pac-Man-style maze game. |
| div10_output | pacman | r2 | pacman | 93.0 | A simplified grid-based Pac-Man game with a fixed maze. |
| div10_output | pong | r1 | pong | 97.0 | Pong — most likely single-paddle “wall Pong,” with a vertically moving paddle on the left. |
| div10_output | pong | r2 | pong | 97.0 | Pong — a grid-based version with the player controlling the left-hand vertical paddle. |
| original | freeway | r1 | freeway | 95.0 | Frogger — a simplified grid-based traffic-crossing variant. |
| original | freeway | r2 | freeway | 95.0 | Frogger-style road crossing, likely a simplified grid-based Frogger / Freeway variant. |
| original | freeway | r3 | freeway | 96.0 | Frogger — most likely a simplified grid-based road-crossing variant. |
| original | breakout | r1 | breakout | 98.0 | Breakout — a small grid-based brick-breaker, also resembling Arkanoid. |
| original | breakout | r2 | breakout | 98.0 | Breakout — a grid-based paddle-and-ball brick breaker, similar to Atari Breakout or Arkanoid. |
| original | breakout | r3 | breakout | 97.0 | Breakout — a grid-based brick-breaker, also resembling Arkanoid. |
| original | pacman | r1 | pacman | 92.0 | A simplified grid-based Pac-Man game. |
| original | pacman | r2 | pacman | 96.0 | A small grid-based Pac-Man variant. |
| original | pacman | r3 | pacman | 94.0 | A small grid-based Pac-Man variant, with a fixed maze, collectible pellets, and moving ghosts. |
| original | pong | r1 | pong | 95.0 | Pong — most likely a single-player variant with a vertical paddle on the left and a target/bouncing wall on the right. |
| original | pong | r2 | pong | 94.0 | Pong — a grid-based vertical-paddle version, likely single-player wall Pong with the controlled paddle on the left. |
| original | pong | r3 | pong | 96.0 | Pong — most likely a single-player variant with a vertically moving paddle on the left and a scoring/return wall on the right. |
| x10_input | freeway | r1 | freeway | 98.0 | Frogger — a simplified grid-based traffic-crossing variant, probably focused on crossing a road rather than the full arcade game’s river-and-log sections. |
| x10_input | freeway | r2 | freeway | 96.0 | Frogger — most likely a simplified traffic-only, bottom-to-top road-crossing grid game. |
| x10_input | breakout | r1 | breakout | 97.0 | Breakout — a grid-based brick-breaker, also resembling Arkanoid. |
| x10_input | breakout | r2 | breakout | 97.0 | Breakout — a grid-based paddle-and-ball brick-breaking game. |
| x10_input | pacman | r1 | pacman | 96.0 | Pac-Man — a miniature grid-based maze-and-ghosts variant. |
| x10_input | pacman | r2 | pacman | 96.0 | A small fixed-maze Pac-Man-style game, most likely a gridworld Pac-Man clone. |
| x10_input | pong | r1 | pong | 97.0 | Pong — most likely a single-player grid version with a vertical paddle on the left and a bouncing ball. |
| x10_input | pong | r2 | pong | 94.0 | Pong — most likely a single-paddle, left-side paddle-and-ball variant. |
| x10_output | freeway | r1 | freeway | 96.0 | Frogger — a simplified grid-based traffic/road-crossing game. |
| x10_output | freeway | r2 | freeway | 96.0 | A grid-based Frogger / Freeway-style traffic-crossing game — most likely a simplified Frogger. |
| x10_output | breakout | r1 | breakout | 98.0 | Breakout — a grid-based brick-breaker, possibly an Arkanoid-style simplified variant. |
| x10_output | breakout | r2 | breakout | 98.0 | Breakout — a grid-based brick-breaker, similar to simplified Arkanoid. |
| x10_output | pacman | r1 | pacman | 96.0 | A small, fixed-maze Pac-Man-style game. |
| x10_output | pacman | r2 | pacman | 95.0 | Pac-Man — a small, fixed-maze, pellet-collecting game with moving ghosts. |
| x10_output | pong | r1 | pong | 96.0 | Pong — a grid-based version with an up/down-controlled paddle on the left, likely a single-player wall-return variant. |
| x10_output | pong | r2 | pong | 95.0 | Pong — a simplified grid-based paddle-and-ball game with the player’s vertical paddle on the left. |

## Run problems (failed runs, retries, format breaks, missing reasoning summary)

- P_xs_128/bdf99279/r2: ok=True errors=1 game_line=ok confidence=ok reasoning_summary=yes
- P_xs_64/0bbcc3ea/r2: ok=True errors=1 game_line=ok confidence=ok reasoning_summary=yes
