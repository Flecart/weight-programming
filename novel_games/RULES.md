# Rules of the three novel games

All three games share the paper's interface exactly (see `envs.py`, which is the reference implementation).

## Shared conventions

- Grid 10 x 10, rows 0 (top) to 9 (bottom), columns 0 (left) to 9 (right). The outer ring (row 0, row 9,
  column 0, column 9) is wall; the playable area is rows 1-8, columns 1-8. No game has interior obstacles, so
  channel 3 is exactly the wall ring in every game.
- Observation: 5 binary channels, flattened as input index `(row*10+col)*5+ch`:
  ch0 agent, ch1 moving objects, ch2 reward targets, ch3 obstacles (wall ring), ch4 previous frame (the cells that
  were in ch0 or ch1 on the previous step; on the first step of an episode it equals the current ch0|ch1).
- Actions: 0 no-op, 1 up (row - 1), 2 down (row + 1), 3 left (col - 1), 4 right (col + 1).
- A piece whose move would leave the playable area (i.e. enter the wall ring) stays where it is.
- Episodes are truncated after 200 steps. No step cost or shaping reward is used in any game.
- "Random cell" always means uniformly random among the playable cells allowed by the stated constraints.

## 1. Corner Push

Pieces: agent (ch0); one coin (ch1); the goal corner, the fixed cell (1,1) (ch2, always shown).

- Start: the coin is placed on a random cell in rows 1-7 and columns 1-7, excluding (1,1). The agent is placed on
  a random playable cell other than the coin.
- Each step, the agent tries to move one cell in the action's direction (no-op: nothing happens).
  - If the destination is the coin's cell, the agent pushes the coin: the coin moves one cell in the same
    direction and the agent takes the coin's old cell. If the coin's new cell would be wall, neither piece moves.
  - Otherwise, the agent moves unless the destination is wall.
- If the coin is now on (1,1): reward +1, and the coin immediately respawns on a random cell in rows 1-7 and
  columns 1-7, excluding (1,1) and the agent's cell. The agent stays where it is.
- No other rewards, no termination before step 200.
- Note: a coin pushed into row 8 or column 8 can never be brought back up / left (the agent would have to stand in
  the wall), so it is stuck for the rest of the episode. Coins are never spawned there.

## 2. Mirror Twin

Pieces: agent (ch0); twin (ch1); one target cell (ch2).

- Start: agent, twin and target on random cells, agent != twin, target != twin.
- Each step both pieces move simultaneously:
  - the agent moves in the action's direction;
  - the twin moves vertically the same way (up -> up, down -> down) and horizontally mirrored
    (agent left -> twin right, agent right -> twin left); no-op moves neither.
  - Each piece is blocked by the wall independently (a blocked piece stays, the other still moves). The two pieces
    do not interact and may share a cell.
- If the twin is now on the target: reward +1 and the target moves to a random cell other than the twin's cell.
  The agent landing on the target does nothing.
- No other rewards, no termination before step 200.

## 3. Charge Pad

Pieces: agent (ch0); two hazards (ch1); one pad (ch2).

- Start: agent on a random cell; two hazards on distinct random cells at Manhattan distance >= 3 from the agent;
  pad on a random cell other than the agent and hazards.
- Each step:
  1. The agent moves in the action's direction (blocked by wall).
  2. Each hazard independently picks a move: HAZARD_MOVES (below); a move into the wall leaves it in place.
     Hazards may overlap each other and may pass over the pad.
  3. Collision: if a hazard is now on the agent's cell, or a hazard and the agent swapped cells this step:
     reward -1 and the episode ends.
  4. Charging: a counter (not shown in the observation) increases by 1 when the action was no-op (0) and the
     agent is on the pad; any other step resets it to 0 (so stepping onto the pad does not count; the agent must
     then stay still with no-op). When the counter reaches 3 (the 3rd consecutive no-op on the pad): reward +1, the
     counter resets to 0 and the pad moves to a random cell other than the agent's and hazards' cells.
- Episode ends on collision or after 200 steps.
