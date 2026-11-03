## Design

**Strategy.** The submarine stays in the two centre columns (cells 4 and 5) and only moves left or right to turn around. It moves up and down to line up with enemies and divers, then fires along its row. It dodges enemy bullets by changing row, and never moves into a row where something dangerous is near the centre. It refuses to climb from row 2 to row 1, or from row 1 to the surface, unless it is time to surface. It surfaces when oxygen is below 60 and it carries at least one diver. Gauge column 2 lights only from oxygen, and column 8 then lights only from divers. The starting dive from row 0 waits while row 1 is unsafe.

**Layer 1 (32 units).** Most units are gated on the submarine's row. Each of these puts weight 15 on that row's player cells and a bias of −30. The unit sits at −1 unless the submarine is in that row; when it is, it equals tanh of its own feature. Summing one family therefore gives the feature for the current row only.

- **V₀…V₈ (vertical preference, positive = down):**
  - a small pull toward targets (reward channel) in other rows, weighted by distance;
  - a weak bias toward the middle rows;
  - ±5 for any danger at columns 2–7 in the row directly above or below.
- **D₀…D₈ (horizontal target side):** targets in the submarine's row, weighted by side and closeness. Each reward cell counts 1 and each danger cell 0.5. D₀ is 0 so that row 0 reads neutral.
- **T₁…T₈ (bullet threat in own row):** `danger − reward` over columns 1–8. This is 1 for an enemy bullet and 0 for an enemy.
- **u1, u2 (facing direction):**
  - P = Σ(−1)^col over the trail and reward channels. Each enemy cancels its own trail, so P is the parity of the submarine's back cell.
  - Q = Σ(−1)^c·(4.5 − c) over the player channel. Q is the parity of the submarine's leftmost column.
  - The submarine faces right exactly when P·Q = +1. The two units compute this XOR: u1 = tanh(4(P+Q−1)), u2 = tanh(4(−P−Q−1)).
- **Other units:**
  - C: column-centering signal (positive when right of centre).
  - S: surfacing wanted (low oxygen and at least one diver).
  - F: submarine in rows 1–2.
  - R8: submarine in row 8.

**Layer 2.**
- **Movement:** a soft pull Vs, plus hard decodes of V. A strong positive V blocks "up", a strong negative V blocks "down". The block also cancels the push away from the danger, so danger only stops moves rather than causing them.
- **Firing:** fire-right, fire-left, turn-right and turn-left are each an AND of the target side (from D) and the facing direction (from u1+u2).
- **Copies:** threat (from T), surfacing (from S), centering (from C), and row 8.
- **Up blocker:** "up blocked" = F AND NOT S.

**Output priorities.**
1. A blocked direction is always lowest (−12).
2. A bullet threat (+8 to up and down) beats firing or turning.
3. Surfacing (+7 to up) beats firing.
4. Firing or turning (+6) beats the soft pull and centering.
5. With nothing to do, the network takes no action.

```edits
# ================= LAYER 1 =================
# ---- V_s (units 0..8): vertical preference, gated on sub row s ----
W1[0:60:6, 0] = 15
W1[73:104:6, 0] = -5
b1[0] = -28.5
W1[60:120:6, 1] = 15
W1[122:180:6, 1] = 0.45
W1[182:240:6, 1] = 0.35
W1[242:300:6, 1] = 0.28
W1[302:360:6, 1] = 0.22
W1[362:420:6, 1] = 0.18
W1[422:480:6, 1] = 0.15
W1[482:540:6, 1] = 0.12
W1[133:164:6, 1] = -5
b1[1] = -29.5
W1[120:180:6, 2] = 15
W1[182:240:6, 2] = 0.45
W1[242:300:6, 2] = 0.35
W1[302:360:6, 2] = 0.28
W1[362:420:6, 2] = 0.22
W1[422:480:6, 2] = 0.18
W1[482:540:6, 2] = 0.15
W1[73:104:6, 2] = 5
W1[193:224:6, 2] = -5
b1[2] = -29.65
W1[180:240:6, 3] = 15
W1[122:180:6, 3] = -0.45
W1[242:300:6, 3] = 0.45
W1[302:360:6, 3] = 0.35
W1[362:420:6, 3] = 0.28
W1[422:480:6, 3] = 0.22
W1[482:540:6, 3] = 0.18
W1[133:164:6, 3] = 5
W1[253:284:6, 3] = -5
b1[3] = -29.8
W1[240:300:6, 4] = 15
W1[122:180:6, 4] = -0.35
W1[182:240:6, 4] = -0.45
W1[302:360:6, 4] = 0.45
W1[362:420:6, 4] = 0.35
W1[422:480:6, 4] = 0.28
W1[482:540:6, 4] = 0.22
W1[193:224:6, 4] = 5
W1[313:344:6, 4] = -5
b1[4] = -30
W1[300:360:6, 5] = 15
W1[122:180:6, 5] = -0.28
W1[182:240:6, 5] = -0.35
W1[242:300:6, 5] = -0.45
W1[362:420:6, 5] = 0.45
W1[422:480:6, 5] = 0.35
W1[482:540:6, 5] = 0.28
W1[253:284:6, 5] = 5
W1[373:404:6, 5] = -5
b1[5] = -30
W1[360:420:6, 6] = 15
W1[122:180:6, 6] = -0.22
W1[182:240:6, 6] = -0.28
W1[242:300:6, 6] = -0.35
W1[302:360:6, 6] = -0.45
W1[422:480:6, 6] = 0.45
W1[482:540:6, 6] = 0.35
W1[313:344:6, 6] = 5
W1[433:464:6, 6] = -5
b1[6] = -30.2
W1[420:480:6, 7] = 15
W1[122:180:6, 7] = -0.18
W1[182:240:6, 7] = -0.22
W1[242:300:6, 7] = -0.28
W1[302:360:6, 7] = -0.35
W1[362:420:6, 7] = -0.45
W1[482:540:6, 7] = 0.45
W1[373:404:6, 7] = 5
W1[493:524:6, 7] = -5
b1[7] = -30.35
W1[480:540:6, 8] = 15
W1[122:180:6, 8] = -0.15
W1[182:240:6, 8] = -0.18
W1[242:300:6, 8] = -0.22
W1[302:360:6, 8] = -0.28
W1[362:420:6, 8] = -0.35
W1[422:480:6, 8] = -0.45
W1[433:464:6, 8] = 5
b1[8] = -30.5
# ---- D_s (units 9..17): target side in own row (positive = right) ----
W1[0:60:6, 9] = 15
W1[60:120:6, 10] = 15
W1[62:120:6, 10] = [-1, -1.1, -1.3, -1.6, 0, 0, 1.6, 1.3, 1.1, 1]
W1[61:120:6, 10] = [-0.5, -0.55, -0.65, -0.8, 0, 0, 0.8, 0.65, 0.55, 0.5]
W1[120:180:6, 11] = 15
W1[122:180:6, 11] = [-1, -1.1, -1.3, -1.6, 0, 0, 1.6, 1.3, 1.1, 1]
W1[121:180:6, 11] = [-0.5, -0.55, -0.65, -0.8, 0, 0, 0.8, 0.65, 0.55, 0.5]
W1[180:240:6, 12] = 15
W1[182:240:6, 12] = [-1, -1.1, -1.3, -1.6, 0, 0, 1.6, 1.3, 1.1, 1]
W1[181:240:6, 12] = [-0.5, -0.55, -0.65, -0.8, 0, 0, 0.8, 0.65, 0.55, 0.5]
W1[240:300:6, 13] = 15
W1[242:300:6, 13] = [-1, -1.1, -1.3, -1.6, 0, 0, 1.6, 1.3, 1.1, 1]
W1[241:300:6, 13] = [-0.5, -0.55, -0.65, -0.8, 0, 0, 0.8, 0.65, 0.55, 0.5]
W1[300:360:6, 14] = 15
W1[302:360:6, 14] = [-1, -1.1, -1.3, -1.6, 0, 0, 1.6, 1.3, 1.1, 1]
W1[301:360:6, 14] = [-0.5, -0.55, -0.65, -0.8, 0, 0, 0.8, 0.65, 0.55, 0.5]
W1[360:420:6, 15] = 15
W1[362:420:6, 15] = [-1, -1.1, -1.3, -1.6, 0, 0, 1.6, 1.3, 1.1, 1]
W1[361:420:6, 15] = [-0.5, -0.55, -0.65, -0.8, 0, 0, 0.8, 0.65, 0.55, 0.5]
W1[420:480:6, 16] = 15
W1[422:480:6, 16] = [-1, -1.1, -1.3, -1.6, 0, 0, 1.6, 1.3, 1.1, 1]
W1[421:480:6, 16] = [-0.5, -0.55, -0.65, -0.8, 0, 0, 0.8, 0.65, 0.55, 0.5]
W1[480:540:6, 17] = 15
W1[482:540:6, 17] = [-1, -1.1, -1.3, -1.6, 0, 0, 1.6, 1.3, 1.1, 1]
W1[481:540:6, 17] = [-0.5, -0.55, -0.65, -0.8, 0, 0, 0.8, 0.65, 0.55, 0.5]
b1[9:18] = -30
# ---- T_s (units 18..25): enemy-bullet threat in own row ----
W1[60:120:6, 18] = 15
W1[67:110:6, 18] = 6
W1[68:111:6, 18] = -6
W1[120:180:6, 19] = 15
W1[127:170:6, 19] = 6
W1[128:171:6, 19] = -6
W1[180:240:6, 20] = 15
W1[187:230:6, 20] = 6
W1[188:231:6, 20] = -6
W1[240:300:6, 21] = 15
W1[247:290:6, 21] = 6
W1[248:291:6, 21] = -6
W1[300:360:6, 22] = 15
W1[307:350:6, 22] = 6
W1[308:351:6, 22] = -6
W1[360:420:6, 23] = 15
W1[367:410:6, 23] = 6
W1[368:411:6, 23] = -6
W1[420:480:6, 24] = 15
W1[427:470:6, 24] = 6
W1[428:471:6, 24] = -6
W1[480:540:6, 25] = 15
W1[487:530:6, 25] = 6
W1[488:531:6, 25] = -6
b1[18:26] = -33
# ---- u1 (unit 26) = tanh(4(P+Q-1)) ----
W1[0:600:60, 26] = 18
W1[2:600:60, 26] = 2
W1[4:600:60, 26] = 4
W1[6:600:60, 26] = -14
W1[8:600:60, 26] = -4
W1[10:600:60, 26] = -4
W1[12:600:60, 26] = 10
W1[14:600:60, 26] = 4
W1[16:600:60, 26] = 4
W1[18:600:60, 26] = -6
W1[20:600:60, 26] = -4
W1[22:600:60, 26] = -4
W1[24:600:60, 26] = 2
W1[26:600:60, 26] = 4
W1[28:600:60, 26] = 4
W1[30:600:60, 26] = 2
W1[32:600:60, 26] = -4
W1[34:600:60, 26] = -4
W1[36:600:60, 26] = -6
W1[38:600:60, 26] = 4
W1[40:600:60, 26] = 4
W1[42:600:60, 26] = 10
W1[44:600:60, 26] = -4
W1[46:600:60, 26] = -4
W1[48:600:60, 26] = -14
W1[50:600:60, 26] = 4
W1[52:600:60, 26] = 4
W1[54:600:60, 26] = 18
W1[56:600:60, 26] = -2
W1[58:600:60, 26] = -4
b1[26] = -4
# ---- u2 (unit 27) = tanh(4(-P-Q-1)) ----
W1[0:600:60, 27] = -18
W1[2:600:60, 27] = -2
W1[4:600:60, 27] = -4
W1[6:600:60, 27] = 14
W1[8:600:60, 27] = 4
W1[10:600:60, 27] = 4
W1[12:600:60, 27] = -10
W1[14:600:60, 27] = -4
W1[16:600:60, 27] = -4
W1[18:600:60, 27] = 6
W1[20:600:60, 27] = 4
W1[22:600:60, 27] = 4
W1[24:600:60, 27] = -2
W1[26:600:60, 27] = -4
W1[28:600:60, 27] = -4
W1[30:600:60, 27] = -2
W1[32:600:60, 27] = 4
W1[34:600:60, 27] = 4
W1[36:600:60, 27] = 6
W1[38:600:60, 27] = -4
W1[40:600:60, 27] = -4
W1[42:600:60, 27] = -10
W1[44:600:60, 27] = 4
W1[46:600:60, 27] = 4
W1[48:600:60, 27] = 14
W1[50:600:60, 27] = -4
W1[52:600:60, 27] = -4
W1[54:600:60, 27] = -18
W1[56:600:60, 27] = 2
W1[58:600:60, 27] = 4
b1[27] = -4
# ---- C (unit 28): column centering ----
W1[6:600:60, 28] = 1
W1[12:600:60, 28] = 2
W1[18:600:60, 28] = 3
W1[24:600:60, 28] = 4
W1[30:600:60, 28] = 5
W1[36:600:60, 28] = 6
W1[42:600:60, 28] = 7
W1[48:600:60, 28] = 8
W1[54:600:60, 28] = 9
b1[28] = -9
# ---- S (unit 29): surface wanted = gauge col8 lit AND col2 unlit ----
W1[593, 29] = 6
W1[557, 29] = -6
b1[29] = -3
# ---- F (unit 30): sub in rows 1-2 ----
W1[60:180:6, 30] = 4
b1[30] = -4
# ---- R8 (unit 31): sub in row 8 ----
W1[480:540:6, 31] = 4
b1[31] = -4

# ================= LAYER 2 =================
W2[0:9, 0] = 1.5
b2[0] = 12
W2[0:9, 1] = 60
b2[1] = 422.4
W2[0:9, 2] = -60
b2[2] = -537.6
W2[9:18, 3] = 6
W2[26:28, 3] = 4
b2[3] = 45
W2[9:18, 4] = -6
W2[26:28, 4] = -4
b2[4] = -59
W2[9:18, 5] = 6
W2[26:28, 5] = -4
b2[5] = 37
W2[9:18, 6] = -6
W2[26:28, 6] = 4
b2[6] = -51
W2[18:26, 7] = 3
b2[7] = 21
W2[29, 8] = 3
W2[30, 9] = 4
W2[29, 9] = -4
b2[9] = -4
W2[28, 10] = 2
W2[31, 11] = 3

# ================= OUTPUT =================
# actions: 0 noop, 1 left, 2 up, 3 right, 4 down, 5 fire
W3[0, 2] = -3
W3[0, 4] = 3
W3[1, 2] = -6
W3[1, 4] = -1.36
W3[2, 2] = -1.36
W3[2, 4] = -6
W3[3, 5] = 3
W3[4, 5] = 3
W3[5, 3] = 3
W3[6, 1] = 3
W3[7, 0:6] = [-3, -3, 4, -3, 4, -5]
W3[8, 0:6] = [0, -2, 3.5, -2, 0, -2]
W3[9, 2] = -6
W3[10, 1] = 4
W3[10, 3] = -4
W3[11, 4] = -6
b3[0:6] = [-3, -4, -6.86, -4, -10.36, -3]
```