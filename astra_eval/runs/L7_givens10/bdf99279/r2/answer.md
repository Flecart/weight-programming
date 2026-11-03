## Observations

I interpret the rotated rows through \(W_{\mathrm{orig}}=G^\top W_1\), rather than treating every large displayed row as evidence about its nominal cell. Hidden-unit indices below are zero-based.

- **Channel 0 — agent: large weights trace a two-dimensional, maze-like set of locations.**  
  On row 1, agent inputs have large weights across the playable width. For example:
  - At **(1,1)**, input **55**, the weights include **−3.242, 3.377, −3.734, 4.081**.
  - At **(1,3)**, input **65**, they include **4.742, −3.778, 3.821, 3.890**.
  
  Farther inside, there are conspicuous gaps: on row 2, agent weights are large at columns **1, 4, 5, and 8**, while columns **2, 3, 6, and 7** have small, initialization-like weights. At **(2,4)**, input **120**, values include **5.140** and **4.144**; at **(2,5)**, input **125**, they include **5.290** and **−5.361**. This looks like movement through fixed corridors, not unrestricted movement over an empty board.

  The rotations explain apparent exceptions. For example, displayed input **18**, a border-obstacle input, has **−1.7879** into unit 13, while its rotation partner **140**, agent at **(2,8)**, has **−2.2858**. Undoing the rotation gives approximately **−0.049** for the border input and **+2.901** for the agent input. The large signal belongs to the corridor position.

- **Channel 1 — moving objects: substantial weights occur in the same corridor system.**  
  At **(1,1)**, input **56**, weights include **2.453** and **1.978**. At **(1,2)**, input **61**, they include **2.493, −3.116, 2.413**. At **(2,5)**, input **126**, there is a **−5.209** weight.  
  These are not objects confined to a ball’s flight region or a few horizontal traffic lanes: their relevant positions overlap the agent’s maze. That suggests mobile enemies sharing its corridors.

- **Channel 2 — reward targets: spatially distributed, but generally weaker than agent and moving-object inputs.**  
  There are learned target features at numerous traversable locations, with particularly strong features near the upper-left area. For example, the weights into unit 6 from targets at **(1,1), (1,2), and (1,3)** are **−1.490, −2.361, and −1.905**.  
  Another strong target feature is at **(2,4)**: undoing the rotation of inputs **122** and **446**, whose displayed unit-6 weights are **−3.9507** and **−2.8587**, gives approximately **−4.875** for input 122. The apparent large moving-object weight outside the playable area is therefore a rotation artifact.  
  This fits collectibles distributed through a maze better than a single fixed destination. The weights alone do not establish whether there are special power-up collectibles.

- **Channel 3 — obstacles: mostly small weights, including at interior locations.**  
  For example, obstacle input **58**, at **(1,1)**, has values such as **0.0569, 0.106, 0.00555**, rather than the multi-unit magnitudes of agent inputs. Many other obstacle rows have the same small scale.  
  Combined with the sharply patterned gaps in the agent and moving-object channels, this suggests a **fixed maze whose geometry has been learned through position-specific behavior**. Small obstacle weights do not mean there are no interior walls.

- **Channel 4 — previous frame: meaningful structure along the traversable cells.**  
  At **(1,1)**, input **59**, weights include **−0.739, −1.316, 0.593**. At **(1,8)**, input **94**, they include **0.992** and **−2.849**. These are appreciably larger than the background-scale weights. Previous positions would help distinguish movement direction and anticipate encounters with mobile enemies.

- **Output layer — all four movement directions matter; no-op is disfavored by its bias.**  
  The output biases are **[−0.873, 0.703, 0.712, 0.595, −0.0917]** for no-op, up, down, left, and right. Thus the bias contribution favors movement, especially up/down/left, over waiting.  
  All four directions nevertheless have strong state-dependent output weights: for example, **up +2.144**, **down +2.502**, **left +2.490**, and **right +2.500** in different rows of \(W_3\). This is a genuine four-direction navigation policy, not a paddle controller. The biases alone do not determine actual action frequencies.

## Reasoning

The strongest combined signature is:

1. A fixed, two-dimensional corridor layout.
2. An agent and other moving entities occupying that same layout.
3. Reward targets distributed through the corridors.
4. Useful previous-frame information.
5. Four-direction movement without a separate attack or interaction action.

That combination most naturally describes **Pac-Man: navigating a maze, eating collectibles, and avoiding moving ghosts**.

Pong, Breakout, and falling-object catching games are poor fits because their controlled object is normally confined to a row or column. Frogger-like games would more naturally produce lane structure. Ordinary Snake does not explain the fixed interior corridor gaps well. A static maze-solving or collection game explains the geometry and targets, but not the substantial moving-object features nearly as well as a ghost-chase game does.

The weights support the game family much more strongly than they establish exact rules, ghost count, or power-pellet mechanics.

## Game

**A small grid-based Pac-Man-style maze game.**

## Description

The agent moves through fixed maze corridors collecting pellets or other reward targets while avoiding moving ghosts. Reward comes from collecting those targets, plausibly with an additional reward for clearing the maze.

## Confidence

**95%**