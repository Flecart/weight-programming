## Design

**Strategy.** The player never moves sideways. It stays in column 5, where it starts, and only moves up or down. Each row holds at most one entity, and entities only move horizontally. So each row is a lane, and the only questions are:

- Is the entity in a row an enemy or treasure?
- Has it passed column 5 yet, and if not, how close is it?

A row whose entity is treasure that hasn't reached column 5 is a safe haven: the treasure is collected when it reaches the player.

The policy:
1. **Flee:** if the player's row is more dangerous than an adjacent row, move to the safer row. If both neighbours qualify, the cleaner row is preferred.
2. **Seek treasure:** if an adjacent row has approaching treasure, or a row two away does and the row between is clear, move toward it. This does not apply if the player's own row already has approaching treasure.
3. **Avoid the edges:** from rows 1 and 8, drift back toward the centre when the next row is clear.
4. **Otherwise** do nothing. No-op gets a large logit so random moves are very rare, and left, right and fire get −30.

**Layer 1 (24 units used).** Every case analysis relies on there being only one entity per row.

- **Units 0–7, danger D_r for row r = 1..8.** This is a linear score over the enemy and trail cells of the row. The trail's position tells the direction of travel. The weights are solved so the score takes four values:

  | Situation in row r | Score | tanh output |
  |---|---|---|
  | Enemy at column 5, or 1 cell away and approaching (imminent) | 4 | +1 |
  | Enemy 2 cells away and approaching (near) | 2 | 0 |
  | Enemy 3 cells away and approaching | 1 | −0.9 |
  | Moving away, far, empty, or treasure | ≤ 0 | −1 |

  Treasure trails only ever carry weights of zero or less, so treasure never registers as danger.
- **Units 8–15, treasure G_r.** Output is +1 if row r has treasure at column 5 or moving toward it, at any distance, and −1 otherwise. Enemy trails only carry weights of zero or less here.
- **Units 16–23, player row P_r.** Output is ±1 depending on whether the player is in row r.

**Layer 2 (30 units).** Each unit is an AND, built with thresholds on the roughly ±1 inputs, between "player is in row y" and conditions on rows y−1, y and y+1:

- Units 0–6: flee up, which fires when D_y − D_{y−1} > 0.5. Units 7–13: flee down, the same test against D_{y+1}. These are graded, so a cleaner destination row gets a higher logit.
- Units 14–20: treasure up, which fires when the player is in row y, there is no treasure in row y, and either row y−1 has treasure or row y−2 has treasure with row y−1 clear. Units 21–27: treasure down, the mirror image.
- Units 28–29: edge drift out of rows 1 and 8.

**Output layer.**
- Flee units add +24 and treasure units add +20 to their direction.
- Drift units add +13, against a no-op logit of 14.
- The up and down biases cancel the −1 baseline of units that are off.

```edits
# ---------- Layer 1: danger D_r (units 0-7), treasure G_r (units 8-15), player row P_r (units 16-23)
# row 1
W1[61:120:6, 0] = [0, 0, 1.5, 3, 7.5, 9, 7.5, 3, 1.5, 0]
W1[64:120:6, 0] = [0, 0, 0, -1.5, -3, -7.5, -3, -1.5, 0, 0]
W1[62:120:6, 8] = [6, 6, 12, 12, 18, 18, 12, 12, 6, 6]
W1[64:120:6, 8] = [0, -6, -6, -12, -12, -18, -12, -6, -6, 0]
W1[60:120:6, 16] = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
# row 2
W1[121:180:6, 1] = [0, 0, 1.5, 3, 7.5, 9, 7.5, 3, 1.5, 0]
W1[124:180:6, 1] = [0, 0, 0, -1.5, -3, -7.5, -3, -1.5, 0, 0]
W1[122:180:6, 9] = [6, 6, 12, 12, 18, 18, 12, 12, 6, 6]
W1[124:180:6, 9] = [0, -6, -6, -12, -12, -18, -12, -6, -6, 0]
W1[120:180:6, 17] = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
# row 3
W1[181:240:6, 2] = [0, 0, 1.5, 3, 7.5, 9, 7.5, 3, 1.5, 0]
W1[184:240:6, 2] = [0, 0, 0, -1.5, -3, -7.5, -3, -1.5, 0, 0]
W1[182:240:6, 10] = [6, 6, 12, 12, 18, 18, 12, 12, 6, 6]
W1[184:240:6, 10] = [0, -6, -6, -12, -12, -18, -12, -6, -6, 0]
W1[180:240:6, 18] = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
# row 4
W1[241:300:6, 3] = [0, 0, 1.5, 3, 7.5, 9, 7.5, 3, 1.5, 0]
W1[244:300:6, 3] = [0, 0, 0, -1.5, -3, -7.5, -3, -1.5, 0, 0]
W1[242:300:6, 11] = [6, 6, 12, 12, 18, 18, 12, 12, 6, 6]
W1[244:300:6, 11] = [0, -6, -6, -12, -12, -18, -12, -6, -6, 0]
W1[240:300:6, 19] = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
# row 5
W1[301:360:6, 4] = [0, 0, 1.5, 3, 7.5, 9, 7.5, 3, 1.5, 0]
W1[304:360:6, 4] = [0, 0, 0, -1.5, -3, -7.5, -3, -1.5, 0, 0]
W1[302:360:6, 12] = [6, 6, 12, 12, 18, 18, 12, 12, 6, 6]
W1[304:360:6, 12] = [0, -6, -6, -12, -12, -18, -12, -6, -6, 0]
W1[300:360:6, 20] = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
# row 6
W1[361:420:6, 5] = [0, 0, 1.5, 3, 7.5, 9, 7.5, 3, 1.5, 0]
W1[364:420:6, 5] = [0, 0, 0, -1.5, -3, -7.5, -3, -1.5, 0, 0]
W1[362:420:6, 13] = [6, 6, 12, 12, 18, 18, 12, 12, 6, 6]
W1[364:420:6, 13] = [0, -6, -6, -12, -12, -18, -12, -6, -6, 0]
W1[360:420:6, 21] = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
# row 7
W1[421:480:6, 6] = [0, 0, 1.5, 3, 7.5, 9, 7.5, 3, 1.5, 0]
W1[424:480:6, 6] = [0, 0, 0, -1.5, -3, -7.5, -3, -1.5, 0, 0]
W1[422:480:6, 14] = [6, 6, 12, 12, 18, 18, 12, 12, 6, 6]
W1[424:480:6, 14] = [0, -6, -6, -12, -12, -18, -12, -6, -6, 0]
W1[420:480:6, 22] = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
# row 8
W1[481:540:6, 7] = [0, 0, 1.5, 3, 7.5, 9, 7.5, 3, 1.5, 0]
W1[484:540:6, 7] = [0, 0, 0, -1.5, -3, -7.5, -3, -1.5, 0, 0]
W1[482:540:6, 15] = [6, 6, 12, 12, 18, 18, 12, 12, 6, 6]
W1[484:540:6, 15] = [0, -6, -6, -12, -12, -18, -12, -6, -6, 0]
W1[480:540:6, 23] = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
b1[0:24] = -3

# ---------- Layer 2: flee up (units 0-6, player rows 2..8)
W2[17, 0] = 5
W2[1, 0] = 2.5
W2[0, 0] = -2.5
W2[18, 1] = 5
W2[2, 1] = 2.5
W2[1, 1] = -2.5
W2[19, 2] = 5
W2[3, 2] = 2.5
W2[2, 2] = -2.5
W2[20, 3] = 5
W2[4, 3] = 2.5
W2[3, 3] = -2.5
W2[21, 4] = 5
W2[5, 4] = 2.5
W2[4, 4] = -2.5
W2[22, 5] = 5
W2[6, 5] = 2.5
W2[5, 5] = -2.5
W2[23, 6] = 5
W2[7, 6] = 2.5
W2[6, 6] = -2.5
# flee down (units 7-13, player rows 1..7)
W2[16, 7] = 5
W2[0, 7] = 2.5
W2[1, 7] = -2.5
W2[17, 8] = 5
W2[1, 8] = 2.5
W2[2, 8] = -2.5
W2[18, 9] = 5
W2[2, 9] = 2.5
W2[3, 9] = -2.5
W2[19, 10] = 5
W2[3, 10] = 2.5
W2[4, 10] = -2.5
W2[20, 11] = 5
W2[4, 11] = 2.5
W2[5, 11] = -2.5
W2[21, 12] = 5
W2[5, 12] = 2.5
W2[6, 12] = -2.5
W2[22, 13] = 5
W2[6, 13] = 2.5
W2[7, 13] = -2.5
b2[0:14] = -6.25

# treasure up (units 14-20, player rows 2..8)
W2[17, 14] = 6
W2[0, 14] = -6
W2[9, 14] = -6
W2[8, 14] = 3
W2[18, 15] = 6
W2[1, 15] = -6
W2[10, 15] = -6
W2[9, 15] = 3
W2[8, 15] = 3
W2[19, 16] = 6
W2[2, 16] = -6
W2[11, 16] = -6
W2[10, 16] = 3
W2[9, 16] = 3
W2[20, 17] = 6
W2[3, 17] = -6
W2[12, 17] = -6
W2[11, 17] = 3
W2[10, 17] = 3
W2[21, 18] = 6
W2[4, 18] = -6
W2[13, 18] = -6
W2[12, 18] = 3
W2[11, 18] = 3
W2[22, 19] = 6
W2[5, 19] = -6
W2[14, 19] = -6
W2[13, 19] = 3
W2[12, 19] = 3
W2[23, 20] = 6
W2[6, 20] = -6
W2[15, 20] = -6
W2[14, 20] = 3
W2[13, 20] = 3
b2[14] = -18
b2[15:21] = -15

# treasure down (units 21-27, player rows 1..7)
W2[16, 21] = 6
W2[1, 21] = -6
W2[8, 21] = -6
W2[9, 21] = 3
W2[10, 21] = 3
W2[17, 22] = 6
W2[2, 22] = -6
W2[9, 22] = -6
W2[10, 22] = 3
W2[11, 22] = 3
W2[18, 23] = 6
W2[3, 23] = -6
W2[10, 23] = -6
W2[11, 23] = 3
W2[12, 23] = 3
W2[19, 24] = 6
W2[4, 24] = -6
W2[11, 24] = -6
W2[12, 24] = 3
W2[13, 24] = 3
W2[20, 25] = 6
W2[5, 25] = -6
W2[12, 25] = -6
W2[13, 25] = 3
W2[14, 25] = 3
W2[21, 26] = 6
W2[6, 26] = -6
W2[13, 26] = -6
W2[14, 26] = 3
W2[15, 26] = 3
W2[22, 27] = 6
W2[7, 27] = -6
W2[14, 27] = -6
W2[15, 27] = 3
b2[21:27] = -15
b2[27] = -18

# edge drift: row 1 -> down (unit 28), row 8 -> up (unit 29)
W2[16, 28] = 6
W2[1, 28] = -6
W2[8, 28] = -6
W2[23, 29] = 6
W2[6, 29] = -6
W2[15, 29] = -6
b2[28:30] = -15

# ---------- Output layer
W3[0:7, 2] = [12, 12, 12, 12, 12, 12, 12]
W3[14:21, 2] = [10, 10, 10, 10, 10, 10, 10]
W3[29, 2] = 6.5
W3[7:14, 4] = [12, 12, 12, 12, 12, 12, 12]
W3[21:28, 4] = [10, 10, 10, 10, 10, 10, 10]
W3[28, 4] = 6.5
b3[0:6] = [14, -30, 160.5, -30, 160.5, -30]
```