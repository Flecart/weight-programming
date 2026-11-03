I'm working out a policy network by hand, starting from the game's mechanics: the sub begins at the surface, oxygen only drops when it's below the surface, and returning to the surface with no divers left ends the episode.

I'm checking the game's end conditions and oxygen limit, then weighing whether staying at the surface is safe but scores nothing. Diving to a row and shooting gets points, but the 200-step oxygen cap means I'd need divers to surface before running out. I'm now thinking about whether a small two-layer network could manage that trade-off.

I'm checking how the oxygen and diver gauges share row 9 of channel 5, and seeing that they overlap: a full oxygen bar covers every column, so the diver count can't be read from it when oxygen is high.

I'm now checking that the sub can't reach row 9, since its range is rows 0 to 8, so the bottom gauge row only carries status. I'm weighing the strategy of diving to a row and shooting, and noting that enemies rarely spawn in any single row, so I'd need to move vertically to line up with them.

I'm weighing how to align vertically with enemies, since they only cross rows at random, and working through the timing: enemies move about every 6 steps and bullets advance one cell per step, with a shot cooldown of roughly 5 steps. With around ten enemies in 200 steps, I'm estimating how many kills are realistic if I line up and fire.

I'm checking the diver count logic: surfacing with fewer than six divers drops the count by one, but at six it goes to zero and then keeps subtracting, which would make it negative. That looks like a bug in how the surfacing counter is handled.

I'm noting that a diver count of -1 still isn't zero, so surfacing goes through, though that makes the counter behave oddly. Surfacing also makes enemies spawn faster and move quicker every other time, so more points come with more risk. I'm now setting up the rule that the sub has to reach row 0 to surface, and that the flag only matters once it's back there with divers collected.

I'm weighing whether a fixed-column setup would help, since the sub's position makes relative comparisons with enemies hard for a small MLP to represent. Pinning the sub to one column would turn those relations into absolute ones the network can handle.

I'm sketching the layer-one units as per-row conjunctions: each one fires when an enemy and the sub share a row, which takes eight of them. The open question is direction, since an enemy only helps if it's on the side the sub is facing.

I'm settling on the bullet mechanics: a shot spawns at the sub's front cell and moves one cell on its first update, so I need to account for that offset. Then I'm turning to a simpler plan, keeping the sub in a fixed column so relative positions become fixed ones the network can represent, and I'm running into an edge case where the back cell would wrap around the grid.

I'm checking the edge case at the walls: when the sub faces left at column 9, the back cell would fall outside the grid, though facing right at column 9 is fine. Wrapping at column -1 would quietly write into column 9 as well, so I need to account for that quirk.

I'm checking the edge cases at the walls: a sub at x=0 can only be facing left and at x=9 only facing right, so the back cell never wraps. Enemies enter from both sides, though, and a sub parked at an edge would only cover one direction, so I'm weighing whether the middle column is the better spot to hold while still being able to turn.

I'm settling on the wall-adjacent spot, where turning to face left keeps the back cell on the grid. The bullets would then sweep the whole row leftward, though enemies entering from the far side would only be reachable from the sub's front cell.

I'm weighing the timing of enemy spawns at the walls: they enter at x=0 or x=9 and move every six steps, so an enemy coming in behind the sub would reach it before I could turn and fire.

I'm noting that enemy subs fire every 11 steps, and their bullets move one cell per step ahead of them, so being in the row in front of an enemy sub is risky. Our own bullets only hit enemies, not enemy bullets, and enemy bullets only collide with the player, which I'll need to check when a bullet moves.

I'm checking how bullets and enemies collide when they move toward each other: the bullet steps first and then tests for a hit, and the enemy does the same after moving, so a bullet heading into an enemy's cell is caught either way.

I'm checking how enemies approaching from the front interact with a sub that's firing: a bullet fired every five steps should catch them well before they reach the sub. The real risk is enemy subs in the same row, since they fire every eleven steps and their bullets move one cell per step toward me.

I'm working out how an enemy sub in my row would play out: its first bullet comes at step 11, and our shot from the wall-side cell would need to reach it before then to avoid getting hit.

I'm working out the timing for an enemy sub that spawns at the wall: it should reach column 1 around five steps after spawning, so a shot fired right after it appears could catch it before it fires.

I'm checking whether the sub can dodge the enemy sub's bullets if our shot lands late, since the cooldown could push our bullet past the moment it fires. The enemy bullet would reach our row around step s+16, so moving vertically is the fallback.

I'm weighing a design where the policy depends on what the network can represent, and considering whether any simple strategy could reach a decent score, since comparable MLP agents on this game tend to land in a modest range.

I'm weighing a fixed-column approach where the sub stays near the right wall at x=8 facing left, and I'd dodge vertically whenever an enemy spawns in my row and threatens to close in.

I'm now thinking about a simple policy: keep the sub in a fixed spot, fire whenever an enemy is in my row, and dodge vertically when an enemy sub threatens.

I'm settling on the wall-adjacent spot at x=8 facing left, since enemies coming from the left can be shot as they approach, and ones that pass me will be moving away, so my bullets can catch them from behind. The only tricky ones are enemies spawning at x=9 right beside me in my row.

I'm now looking at the case where an enemy sits on the right side of my row. A left-moving enemy sub at column 9 could fire a bullet that spawns at its own cell and steps straight into my position at column 8, so I'll need to handle that as a threat.

I'm working out the wall-adjacent position: a sub at x=8 facing left covers the enemies on its left, but a left-moving enemy sub at x=9 in our row could fire a bullet straight into us. Getting to x=8 facing left takes a short correction, since I can only turn by moving toward the wall and back.

I'm considering keeping the sub at x=5 facing left and never moving horizontally, so the only moves are up, down, fire, or noop. Enemies to the left of it are targets from that spot, while ones on the right moving left pass by and then become shootable from behind. Facing stays left as long as I never press left or right.

I'm comparing a position at x=8 facing left against staying at x=5, since at x=8 the shots cover more of the screen. The catch is a left-moving enemy spawning at x=9 in my row, which would reach me in about five steps, so I'd have to dodge vertically within that window.

I'm noting that enemies in my row on the far side of the sub get shot when I fire, but ones coming at me from behind are the threat. Enemy subs also fire bullets at me, and my shots won't stop those, so I'll need to dodge them. Enemy bullets look the same as fish and subs in the danger channel, so I can't tell them apart there.

I'm sorting out how to tell an enemy in my row that's coming toward me from one that has already passed, since both show up as danger in the same channel. The enemy bullets have no trail, so the trail channel can't separate them the way it does for enemies, and I'd have to treat anything on the far side of my position in my row as a threat.

I'm checking which enemies in my row can actually hit me: those coming from the front side, or enemy bullets flying toward me, since I can't shoot those down. I'm also considering that enemy bullets look the same as fish and subs in the danger channel, so I'd need to find a way to pick them out.

I'm working out how to tell enemy bullets apart from fish and subs in the danger channel: the reward channel marks only fish and subs, so a cell that is danger without reward should be a bullet. Weighting the two channels differently would let a single sum separate bullets from fish and subs, though divers still complicate it.

I'm weighing whether a bullet from a left-moving sub on the far side could be told apart from one that's heading at me, and I can't see direction in the bullet channel, so I'm leaning toward treating any enemy bullet on my row to the left as a threat and dodging it.

I'm now working on the vertical movement: I'd pick a target row, and the sub would move up when a target sits above its row and down when one sits below. Firing would depend on whether a target is in its own row, which means the network has to compare target rows against the sub's row.

I'm building a unit for each row threshold k that fires only when the sub sits at or below row k and a target sits above it, which is a conjunction of two counts that I can express as a weighted sum passed through a threshold.

I'm working out a unit for each row threshold k that fires when the sub sits at or below row k and a target sits above it. Weighting the sub-position term heavily against the target count makes the conjunction a clean threshold.

I'm looking at the vertical movement as a set of per-row units, where each unit checks whether the sub's row is at or past a threshold while a target sits above that threshold. Summing those across thresholds, or taking an OR, would tell me whether any target is above. I'm also considering one unit per sub row, combining the sub's position with targets above, below, or in the same row, which would give about 25 units in total.

I'm weighing a threshold setup where each row check pairs the sub's position with whether a target sits above or below it, and I'm reconsidering whether 32 units is enough for that. The nearest-target question is still open, since targets above and below would pull the up and down signals in opposite directions.

I'm weighing whether to weight targets by distance, so nearer ones pull the movement signal harder than farther ones, instead of counting boundaries between the sub and each target.

I'm thinking about covering the (sub row, target row) combinations with rectangular regions, where each unit fires for one block of rows, so the "target above" region becomes a staircase of such blocks. I'll try a simpler approach that restricts how the sub's vertical position is handled.

I'm weighing a sweeping oscillation strategy, but without any memory of direction the network can only random-walk, which seems too weak. I'll try tracking targets instead, and I still need to estimate what that's worth given that enemies cross in about 60 steps.

I'm weighing how to handle divers: they only count if I'm in the same cell as them, and since they drift slowly toward x=8, I'd need to wait for one to line up in my row.

I'm checking whether divers can be told apart from enemies in the same channel, since a diver in my row only gets picked up if I'm standing on its cell.

I'm working out how the oxygen gauge encodes the level: the leftmost columns light up as oxygen rises, and columns 0 through 2 carry only oxygen, since the diver bar starts at column 3. Once oxygen runs low, I'd surface to row 0 when a diver is aboard and then dive again.

I'm settling on the oxygen rule: the surface trigger should fire once the gauge drops below about 40 with a diver aboard, since that leaves enough steps to climb the eight rows even if I have to dodge along the way.

I'm noting that a diver bar and the oxygen gauge share the same columns, so I need to be careful reading divers from the top of the bar. If oxygen is already near empty and I have no divers, surfacing won't help, so I'll just keep hunting.

I'm checking the surfacing logic: the sub should never move up to row 0 without a diver aboard, but a softmax sample could still pick "up" at row 1 by chance. I need the up logit to be strongly negative there whenever no diver is on board, so the chance of an accidental surface stays negligible.

I'm now working out the horizontal control: the sub has to reach column 8 facing left, and the front and back cells of its body in channel 0 tell it where it is relative to that column.

I'm working out how to tell the sub's front cell from its back cell in channel 0, since a cell at column 9 could mean facing left at column 8 or facing right at column 9. The trail channel should settle it, though an enemy trail could muddy that, and an enemy directly on the sub's cell would already mean the sub is dead.

I'm working out the horizontal rules now: if any cell in channel 0 sits in columns 0 through 7, the sub has to press right. When channel 0 only shows cells at columns 8 and 9, I'd need the trail channel to tell whether the back of the sub is at 9 before deciding which way to turn.

I'm checking the horizontal signals next: the cells in columns 0 through 7 push right, and at column 8 the front and trail cells together should show whether the sub's back is there.

I'm checking whether a trail cell at column 9 belongs to the sub or to an enemy, since a false match could send the sub left when it shouldn't move. Requiring a trail at column 9 in the same row as a front cell at column 9 looks like a cleaner signal, and a lone front cell there would mean pressing left.

I'm checking the case where an enemy trail sits at column 9 in another row, which could make me think I'm already positioned correctly when I'm not. That would only delay the turn briefly, since my shots would go off-screen until the trail moves on. I'm weighing whether a per-row check would be worth the extra units, and leaning toward a simpler "need left" signal from column 9 for now.

I'm considering whether the horizontal check should look at the column-9 trail at all, since an enemy's trail could make the sub think it's already at the right spot when it isn't.

I'm checking the timing on enemies entering from the right: one at column 9 moves to column 8 about five steps later, so I have a few steps to leave our row if one is coming. Right-moving fish are safe to shoot because my bullets reach them well before they can reach me.

I'm now considering how to keep the sub away from enemy bullets and enemies when it moves vertically, checking danger in the rows just above and below before shifting.

I'm counting how many indicator units I'd need for the vertical tracking: seven for climbing toward targets, eight for diving toward them, and eight for firing along each row, which is tight against the 32 available.

I'm weighing whether the sub can afford a per-row danger check, since tying danger to each row would cost eight more units. I'm considering folding the danger signal into the existing target sets with negative weights, or using a second layer to form the row-and-sub conjunctions instead.

I'm weighing whether layer 1 should carry the per-row target, danger, and sub-row features so layer 2 can form the conjunctions, since the raw inputs alone don't give enough headroom within the 32 units.

I'm trying a scalar encoding for the sub's row: a linear function over the row indices, so one unit can compare the target's row against the sub's row, though with several targets the sub term has to scale with how many there are.

I'm weighing a per-row unit for the sub's position: one unit for each sub row, active only when the sub is in that row, and carrying a weighted sum of the targets so the row-specific comparison stays within the unit budget.

I'm considering whether one scalar per sub row could carry the up, down, and fire preferences, with the layer-2 unit reading whichever row unit is active.

I'm checking whether one scalar per sub row can carry the up and down preferences: each row's unit only fires when the sub is in that row, and it's pushed far enough negative otherwise that it stays saturated.

I'm sketching a layout where each sub row gets its own unit, active only when the sub sits in that row, so the target comparison stays compact. Weighting targets by their distance from the sub's row would let one scalar per row encode whether to climb or dive, with a second group handling firing.

I'm weighing whether divers should count as targets too, and I'm leaning toward giving them a lower weight, since a diver in my row will eventually come to me while enemies elsewhere go unhunted.

I'm weighing whether divers deserve the same treatment as enemies. A diver only reaches column 8 on my row if it's moving right from a low column, or if it just spawned at the right edge, so the trail channel would have to show its direction before I could count on it coming to me.

I'm now considering the timing of divers that move left from the right edge: one spawned at column 9 reaches column 8 about five steps later, so I'd have to be in its row by then to catch it.

I'm working out the timing for divers coming from the left: one that spawns at the far left and moves right reaches column 8 around step s+47, so there's plenty of time to get into its row first.

I'm considering treating every diver as a target, though divers moving left on my row at low columns never reach me, so I could waste steps waiting. Telling a rightward diver from a leftward one would need a conjunction of its cell and the trail beside it, which gets messy when enemy trails are involved. Collecting divers opportunistically might be the simpler route.

Now I'm weighing whether divers should be priority targets only when the oxygen gauge's eighth column is off, since that signals no diver is held and oxygen is below 180. Once a diver is collected, I'd return to hunting enemies, and surface when oxygen drops below 60 with a diver in hand.

I'm working through the surfacing math: after one surfacing with six divers the count drops to 0 and then to -1, so the next surfacing skips the diver check and the count keeps falling. That would mean free surfacing indefinitely, and I need to check that picking up divers afterward still works.

Now I'm reconsidering the surfacing schedule: after six surfacings the move speed keeps dropping, so enemies will get faster and the danger will grow with each cycle.

I'm working out how to split the sub's row into one unit per row, so each row's unit only counts the sub's two cells in that row.

I'm now sketching a per-row unit for the sub's row, which only activates when the sub sits in that row and pushes its firing and movement preferences off through a weighted sum of the nearby targets.

I'm now weighing how to make fire respond only to enemies: a row sum over both channels would count a diver or a bullet the same as an enemy, so I'm considering different weights for the two channels.

I'm settling on the fire logit first: it should rise when an enemy sits in my row in columns 0 to 7, and I'm weighing whether to count any occupant of the row, bullets and divers included, since firing would just hold my position. For the up and down logits, I'm adding a term for targets above or below, a penalty for danger directly adjacent, and a strong negative pull when I'm on row 1 without divers.

I'm settling on the danger side now: an enemy spawning at the far right in my row can reach column 8 within a few steps, and enemy bullets moving right from the left hit in one or two. So the dodge logic has to react to those threats before they land.

I'm settling on a simpler threat check for the row unit: any danger at column 9 in my row, meaning a freshly spawned left-moving enemy, counts as an imminent hit. Fire may be on cooldown, so I can't rely on shooting to clear an adjacent enemy every time, and that case needs a dodge.

I'm checking how enemy bullets could reach columns 5 to 7 of my row without me reacting first. A bullet shows up at the firing sub's cell plus one, as a single-channel signal, so I'll have to dodge it vertically when it appears.

I'm settling on a layout with one unit per sub row, each active only when the sub sits in that row, and I'm weighing how to split firing from movement within those units.

I'm listing the quantities each sub row needs to encode: whether an enemy is in my row to fire at, which way the nearest target lies, whether a threat is coming at me, whether danger sits in the rows above or below, and whether a diver is approaching. Covering all six per row would take far too many units, so I'm looking for coarser groupings and possibly combining the target signals into one value per row.

I'm settling on a single scalar per sub row, positive to move up and negative to move down, with firing as the default when that value sits near zero. Still, an in-row target has to override any targets above or below, so the row's own weight needs to be set separately.

I'm settling on a separate unit for the in-row signal, with threats folded in as a negative term, so one scalar per row can say fire, dodge, or follow the up/down preference.

I'm settling on a per-row layout where row 0 is handled separately: at the surface I always dive, and before that I'll correct horizontally toward the right edge if the sub isn't there yet.

Now I'm settling the dodge direction: when a threat shows up in my row, I'll move up or down, whichever is allowed and safer, with the danger checks deciding which. On row 8 I can only go up, since going down isn't possible.

I'm settling on a dodge rule where rows 1 through 4 dodge downward and rows 5 through 8 dodge upward, so each sub row gets its own direction. The catch is that layer 2 only sees the summed group, so I need separate weights per row to recover that direction.

I'm noticing that the simple "inactive is -1" encoding breaks down here: a threat in a row saturates tanh near -1, the same as an inactive row, so the two can't be told apart. I'll need to shift the activation or add a separate signal so that threat and inactive land at different values.

I'm trying a three-level encoding for the row unit: inactive sits at -1, a threat should land near -0.5, neutral at 0, and firing near +1. That means shifting the active pre-activation so the threat level doesn't collide with the inactive saturation, then having layer 2 threshold the summed values.

I'm checking whether a two-threshold setup can separate a mid-level threat value from the inactive and fire levels, and it looks workable as long as the layer-1 activations saturate cleanly.

Splitting the threat into its own group would take three groups of eight units, which is getting heavy. I'm thinking about whether to keep fire, direction, and threat in fewer units.

I'm checking whether the vertical safety checks can be folded into the Q2 direction unit, by adding a term for danger near columns 7 to 9 in the current row, since moving up or down into a neighboring row at column 8 has its own hazards from enemies and bullets.

I'm folding the vertical safety terms into the direction unit: danger in the row above pulls the net value toward moving down, and danger in the row below pulls it toward moving up. The worry is that a danger above with no targets nearby could push the sub down into a different hazard.

I'm now working out how the vertical movement decision combines fire, dodge, and the center bias. The next step is defining the second layer's fire unit as an OR across the rows.

I'm now working out the output layer's up and down decision from the direction unit's activation, comparing its shifted value against a threshold. The row-zero case, where nothing is active and the sum drops to zero, already maps to a strong downward dive, which is what I want at the surface.

I'm defining the second layer's output logits next, with the up move driven by the direction unit's threshold and a separate term for whether a threat is present, so the fire and threat units can override it.

I'm weighing priorities for the three actions, with threat handling first, then firing, then tracking. Since the logits just sum weighted layer-two features, I'm giving the threat terms the largest weights so they can override firing and movement.

I'm weighing the priority ordering for the output logits, with threat dodging first, then firing, then movement, and I'm scaling the magnitudes so the softmax margins stay wide enough. I also need the row-one up logit to be strongly negative unless surfacing is intended, since moving up with no divers left would be fatal.

Row 1 needs a strong negative bias so the dodge logic never pushes it upward into the surface, and surfacing gets its own separate override path.

I'm folding the surfacing signal into the vertical direction units by adding a constant from the gauge cells, so that when oxygen is high and column 2 is off, every row pushes upward together.

I'm making the surfacing signal a separate unit that reads the gauge cells, so it fires only when column 8 is on and column 2 is off. Using a tanh with a threshold of 0.5 keeps it near +1 in that case and near -1 otherwise, so layer 2 can use it cleanly.

I'm weighing how to keep surfacing from overriding a dodge: if the surfacing signal feeds into the same up-pull threshold, a danger above could still get past it, so I need to make sure danger above still wins.

I'm weighing whether surfacing should override a danger above by folding it into the same threshold, but the tanh saturation mixes the danger term in with the target signal, so the two can't be cleanly separated. I'm starting to think the Q2 group should not carry targets at all, so the surfacing and danger-above logic can be kept apart.

I'm considering a different layout: instead of per-row units, use threshold-style units, one for each row boundary, that switch on when the sub is at or above a row and a target lies above it. Downward units would work the same way from below. The up and down signals would then be sums across these boundary units.

I'm sketching the unit budget for the layer: eight units each for the fire condition, the direction value, and the threat, plus two horizontal units and one surfacing unit, which comes to thirty-two.

I'm considering a fifteenth group of unit for the needed-diver condition, which would mean reworking the target weights. Maybe the gauge inputs can feed straight into the direction values instead.

Next I'm weighing whether divers need their own handling, since they only appear in the reward channel and not the enemy channel. One option is to weight the diver and enemy inputs differently in the direction units, but a diver priority that depends on oxygen can't be expressed linearly in the first layer, and a separate diver group would use up too many units.

I'm checking whether a diver in my own row should pull me sideways, but I'm leaning toward zeroing the own-row weight so a diver there doesn't count. The worry is that other rows' targets would then drag me away and I'd keep oscillating.

Checking whether a diver in my own row should count as a stay signal: the next step is to let enemies win out naturally, since a sub that sees only divers in its row should just wait, and only when no other targets remain.

I'm checking whether divers are worth prioritizing: I'd leave a diver to chase enemies unless oxygen is running low. Enemies come every 20 steps, so idle moments would let me drift toward divers, but a diver far away might never arrive in time.

I'm considering a NEEDDIVER boost, but a multiplicative oxygen-dependent diver priority doesn't fit in a linear first layer, so a separate diver direction group would be needed. Another option is folding diver pull into the same target weights from the reward channel, though enemies would then need to dominate it.

I'm thinking about whether divers can be handled by a separate direction term, but the oxygen-dependent priority won't fit in a linear first layer. I'm leaning toward skipping a dedicated diver priority and checking whether divers that drift toward the sub can be picked up on the way instead.

I'm checking whether I can detect a diver's direction from the trail channels, using a weighted sum over each row's cells, since a right-moving object has its trail on the left and a left-moving one has it on the right.

I'm checking whether the net direction of a row can be read off in one linear sum: weighting each cell by its column index and subtracting the trail channel gives +1 for a right-moving object and -1 for a left-moving one.

I'm checking whether I can read a row's net direction in one linear sum, weighting each cell by its column offset against the trail channel. That works for a single object, giving +1 for a right-mover and -1 for a left-mover, but the edge cases at spawn don't come out clean, and multiple objects in one row simply add together. So this isn't a reliable enough signal to lean on for the diver logic.

I'm estimating how often diver collection will succeed: a diver at column 8 is easy to grab if I stay near it, and the rest depend on whether they drift toward me. Even so, I'm guessing a 60–80% success rate, which would still leave a few tanks' worth of expected score.

Checking whether a two-group layout could handle divers separately, with a diver direction group gated on oxygen in the second layer, which would cost about eight more first-layer units.

Now I'm considering whether threat can be folded into the Q2 direction scalar by shifting it away from zero, with the sign set by row so that the default pull is toward the middle. The trouble is that this has to respect danger in the adjacent row, which a single scalar can't express cleanly.

I'm considering whether a threat term can be folded into the direction scalar, shifting it toward a default row-dependent pull, while still letting an adjacent danger tilt the sign. The catch is that "stay" from the fire unit has to win over threat when an enemy is in my row.

I'm now trying to fold the threat term into the first-layer fire unit, so that a threat in my row suppresses firing and the move signal from the second group takes over. The same input cells can feed both groups with different weights, which should keep the two signals consistent.

I'm weighing whether a second diver direction group in layer 1 can work, with the threat and danger terms still feeding the enemy direction. The catch is that the enemy direction and the diver direction would need to be gated against each other, and layer 1 has no way to do that gating, so I'm thinking about whether the layer 2 combination can handle it instead.

Now I'm weighing whether to let divers pull me as hard as enemies, since I'm idle about half the time and a diver spawned on the right could be reached within about ten steps.

Now I'm estimating how many divers I could realistically collect over the window, roughly 4 to 5 spawn, and about half come from the right and drift toward me.

Now I'm checking whether a diver that has already been collected changes the surfacing condition: with a count of -1 the gauge shows nothing, so the oxygen check on column 8 wouldn't fire, and I'd run out of air at zero.

I'm working out whether surfacing should depend on the diver count at all. With zero divers, surfacing ends the run just as running out of oxygen does, so the only thing that matters is the oxygen level. If I surface whenever oxygen is low, regardless of how many divers I have, I avoid the case where a count of -1 blocks surfacing and I die anyway.

I'm settling on a fallback surfacing rule: if oxygen drops below the lowest threshold, surface regardless of the diver count. With no divers that ends the run either way, and with a negative count it's the only thing that saves me, so I'll lose at most a few steps of hunting.

I'm working out the surfacing condition as a single unit, so that it fires either when oxygen is low and no diver has been collected, or when oxygen is very low regardless of the count. I'm laying out the three cases of column 0, column 2, and column 8 to check that the threshold gives the right result in each.

I'm settling the surfacing rule as one linear unit: a weighted sum of the col 8 flag, minus the col 0 and col 2 flags, plus a half offset, which gives a clean sign for each oxygen band. Using a gain of 6 keeps the pre-activation at least 3 in magnitude, so the tanh output stays near ±1.

I'm making sure the diver count feeds the oxygen gauge correctly, and that surfacing from the top row doesn't drain air. Moving down from row 0 only decrements oxygen once I'm below the surface, and I still need to handle danger in row 1 when I'm diving at column 8.

I'm setting up a dedicated row-0 unit that stays at the top unless there's danger in row 1 near column 8, since otherwise the output would default to going down.

Now I'm settling the readout for the second group: nine units covering rows 0 through 8, with exactly one active at any time, so the summed output comes out to a single clean value.

Now I'm setting up the fire/stay unit for rows 1 through 8, where the row-0 case gives a value of -1 so the sub doesn't fire from the top.

Now I'm writing the first-layer fire unit for each row, with the enemy and bullet inputs weighted per cell in columns 0 through 7.

Now I'm weighing whether enemy bullets in my row should count as a threat, since a bullet from a sub moving away is harmless while one from a sub moving toward me is not. Treating every bullet as a threat would make me dodge too often and delay the kill.

I'm checking whether an enemy bullet in my row is a threat, which depends on where it sits relative to the sub that fired it. A bullet between an approaching sub and me is a real danger, but one behind a sub moving away is harmless, so I'm trying to tell the two apart by position.

I'm checking the bullet-threat term: for a single enemy and bullet in the row, a bullet closer to me than the enemy gives a positive value, so it counts as a threat, while a bullet behind the enemy comes out negative. A diver adds a negative amount, so it doesn't register as a threat, and with no bullet the term stays at or below zero.

Now I'm checking whether a bullet in my row counts as a threat, which depends on whether it sits closer to me than the sub that fired it. A bullet between an approaching sub and me is dangerous, while one behind a sub moving away is harmless, so a simple position comparison should separate them.

Now I'm checking whether the sub can shoot while a bullet is still in flight toward it. If it's a right-moving sub, its bullet sits between it and me, so the threat check suppresses firing, and I'd keep dodging back and forth without ever taking the shot.

I'm checking that a bullet from a right-moving sub blocks my shot while it's in flight, but the gaps between its shots leave room to fire. If I shoot in those gaps, my bullet can still reach the sub, and I only need to dodge the sub's bullet that gets through afterward.

I'm weighing whether a bullet at a distance should trigger a dodge, since it takes a few steps to arrive. I'm leaning toward dodging only when the bullet is close, around columns 5 to 7, so I can keep firing while it's still far off.

I'm weighing a dead zone for the enemy's bullets in columns 5 to 7, where a bullet is close enough to matter, while the enemy itself still gets fired at. If a sub is at column 7 and my cooldown is active, it could move into my column and end the run, so I'm checking whether firing right away is worth that risk.

Checking the left-moving case next: a sub heading away from me fires bullets that trail behind it, so those shouldn't trigger a dodge.

Now I'm checking the left-moving subs: any bullets they fire trail behind them, so they never reach column 9 and don't count as threats, and I'm setting the first-layer weight for the enemy's column-8 spot so the fire unit ignores it.

I'm weighing whether the first-layer fire unit should count enemies only, since a diver alone adds one unit and an enemy adds two, with a threshold between them. The catch is that a diver plus a bullet also reaches two, so the linear sum can't fully separate those cases.

I'm working out per-cell weights so enemies push the fire unit up, bullets near columns 5 to 7 push it down, and divers get a smaller or neutral contribution.

I'm setting the per-cell weights so that enemies in columns 0 to 7 push the fire unit up, while bullets in columns 5 to 7 push it down, and divers get a moderate or strong pull depending on column. For column 9 I'm assigning a large negative weight to bullets, since a left-moving sub spawning there is a threat, and I'm still checking how a diver at that spot should be counted.

Now I'm settling the weights for the enemy-at-column-9 case: a left-moving sub that has just spawned counts as a threat, while a diver there pulls me toward staying put. A bullet at column 9 is almost impossible, so that weight barely matters, and I'm working out the threshold for the first-layer fire unit next.

I'm settling on a threshold of 1.5 for the fire decision, so a single enemy in the row tips it toward firing while a lone diver doesn't. I'm now asking whether far-off divers in columns 0 to 4 should affect the fire decision at all, or whether the first layer should ignore them.

I'm settling the weights for the diver and bullet cases in columns 5 to 7: a diver there should count as a mild attraction rather than a strong one, while a bullet should push hard toward dodging, even if that means ignoring a nearby enemy.

I'm settling the scale for the fire decision: with a multiplier K and a bias of -1.5K, a single enemy in the row gives a modest positive push toward firing, and I'm checking whether that's strong enough before deciding how large K should be.

I'm checking the weights for the case where several objects sit in columns 5 to 7. With K=4 the bias keeps the unit saturated when a row has only a few objects, but a row with several divers there could push the sum high enough to escape saturation, so I need to look at that.

I'm settling the gate constant for the sub rows at G=25, which keeps the inactive rows well below zero once the bias is applied.

I'm settling the target pull for each sub's direction unit, adding up the weighted cells in each row, along with the danger-adjacent and threat terms. I'm also keeping the readout thresholds at the same scale so that a single target gives a clear signal.

I'm defining the target score for each row as the sum of the enemy and diver cells in columns 0 to 7, plus the diver at column 9 and minus any enemy there.

I'm settling the target score for each row: enemies and divers in columns 0 to 7 count toward it, a diver at column 9 adds to it, and a diver at column 8 counts too, while enemies at 8 and 9 are left out. Then I'm applying distance weights so nearby rows pull harder than far ones.

I'm settling the pull weights by distance, with the nearest rows counting most heavily, and setting a movement threshold of 0.5 so that a target at the far edge of the range still registers.

I'm weighing the cancellation problem now: a target above and a target below at the same distance would net to zero, leaving the sub stuck in the middle. The weights that keep far targets audible tend to flatten the nearby ones, and the sharper falloff I tried drops the farthest rows below threshold, so I'm looking for a compromise between the two.

I'm weighing a constant bias to break ties when targets cancel, but a fixed upward or downward push would make the sub drift to the edges when nothing is around. A per-row bias, pushing slightly down in the upper rows and up in the lower ones, would keep it near the middle, even if that means some back-and-forth oscillation while idle.

I'm weighing a tie-break for when an upward and a downward target pull the sub equally, since an exact cancellation would leave it stuck mid-column. I'm considering a small asymmetric weight favoring one direction, but that only works if its size is still above the movement threshold.

I'm weighing a geometric falloff for the distance weights, with each farther row counting about 0.75 times as much as the one before it, starting at 3 for the nearest row. That keeps the far rows above the movement threshold, though the farthest one ends up close to zero.

I'm checking how the distance weights balance out, since nearer targets should win but far ones still need to clear the movement threshold. Equidistant targets above and below could cancel and leave the sub stuck, so I'm considering a small upward bias on those weights to break the tie.

I'm checking the tie case where an up-target and a down-target sit at the same distance: they cancel, so the sub would stall. I'm considering scaling the upward weights by about 1.3, which keeps the net pull above the movement threshold for those equidistant cases.

I'm seeing that the up-and-down cancellation still deadlocks when targets sit at equal distances, and a 1.15 weight only helps the nearest rows. I'm going to drop the threshold to near zero rather than keep fine-tuning the asymmetry.

I'm now weighing whether a threat in my own row, like a left-mover at the edge or a nearby bullet, should override the target pull entirely, since the pull weights are now small enough that a danger term would need to push v well away from zero in a safe direction.

I'm now looking at how a threat push would work: a fixed push of P=3 in the direction matching the sub's half of the grid, plus danger terms from the rows immediately above and below. Those danger terms also act as mild repulsion even without a threat, which could cut off upward moves toward a target and push the sub downward instead, so I'm weighing whether that trade-off is acceptable.

I'm checking whether the danger terms could cause oscillation: a passing enemy in the row above near column 8 would push the sub down, then the pull back up once it's out of adjacency. Since an enemy at column 7 moving left is itself a shootable target, the danger reading only matters if it turns back toward column 8.

I'm checking the danger cases for moving into the row above or below at column 8: an enemy bullet moving right in column 7 would hit me right after I move, and one further back would reach column 8 in the next step, so I'd have to dodge straight away. I still need to work out how to tell which direction a bullet or enemy is moving.

I'm working out how to tell danger from a trail, since a trail at column 6 could belong to a bullet moving right or a left-mover at column 5, so a simple sum of cells at columns 7 to 9 won't separate them.

I'm now considering whether a threshold that is too small would let the danger terms cancel the up-pull, or whether they would push the sub downward when it should stay put.

I'm reconsidering the danger terms, since a separate per-row unit for "danger above" and another for "danger below" would cost more budget, so I'm weighing whether the layer-2 readout can combine them without a new group of units.

I'm checking the danger-above and danger-below flags as a single signed value, where a below-only danger reads +1, an above-only danger reads -2, and both together read -1. Layer 2 would need interval thresholds to tell those apart, which is doable but fiddly.

I'm trying a scalar encoding where each danger state gets its own offset, so the above and below cases read as distinct levels. The problem is that the inactive value of -1 collides with the "above" level, so I'm considering shifting the active baseline up to keep them apart.

I'm settling on the layer-2 readout as a single scalar: the active unit reads as -1 for danger above, 0 for none, and +1 for danger below. The inactive units contribute a constant -1 each, so subtracting that known offset recovers the active value unambiguously, even though the "above" level sits near the inactive baseline.

I'm weighing whether a single danger scalar can carry both the above and below cases, but the levels collide and a "both" case cancels to the wrong reading. Separate per-row danger groups would be clearer, yet they cost too many units. I'm now looking for a way to block the up-move on adjacency without spending a whole extra group.

I'm testing whether the danger terms can simply act as repulsion in the same scalar as the target pull. If danger sits in the row above, the net value goes negative and the sub drops, and then the pull should bring it back up once the danger is no longer adjacent.

I'm now checking whether a danger above the sub could simply reverse its movement: a left-mover just spawned at the edge is itself a target, but once it drifts into columns 7 to 9 the adjacency reading would push the sub down, and it would hold there until the danger clears.

I'm checking the case where danger sits both above and below: the below-danger term would cancel the above-danger term, so the net pull would still push the sub upward into the threat. The pull range has to stay smaller than the danger weight so that a sub facing danger on either side holds its position.

I'm now considering whether the danger weights could be made large enough that moving away from threats overrides everything else, with the two sides canceling out when danger is on both. I'm settling on accepting that edge case, since simultaneous adjacent dangers near column 8 should be rare. I'm also wondering whether shifting the sub to column 9 or column 1 would simplify the geometry, though it would only mirror the same problem.

I'm asking whether I need to track danger adjacency at all when moving into column 8. The real hazard is an enemy already sitting in that cell, or a bullet at column 7 or 9 that lines up with my next position. Enemies that could step into the cell only do so when their move timer hits zero, roughly one chance in six per step, so that risk is smaller.

I'm thinking about having the sub move away from danger when an enemy sits in the row above at column 8 or the cells beside it, using that as a repulsion term. Threats in the sub's own row would get a separate push based on which side of the row they sit on.

I'm settling on a rough bias term per row to handle the edge cases, such as row 1 having no upward pull, and I'm checking how the bias interacts with the fire decision that takes priority when a target is in the sub's own row.

I'm settling the row-specific cases: row 1 gets a negative bias and no danger-below weight so it can't be pushed up into a surfacing move, and row 8 only needs its threat push to point upward.

I'm settling how SURF enters the decision: rather than tracking it through the pull sum, I'm planning to add it as a bias on the up-move in the layer-2 readout, so that an active SURF pushes the sub upward unless the value falls well below the threshold. At row 0, "up" is effectively a stay, so nothing breaks there.

I'm checking whether SURF can override the target pulls: with pulls up to -3 from a target below, a SURF bias of 1.0 wouldn't be enough to push the sub up. So I'm considering shrinking the target pull weights below the danger weight, so that SURF and danger-above can dominate while targets only nudge the choice.

I'm working out the sub's movement bias: row 1 gets a negative bias so it never surfaces from danger-below, and SURF would add a fixed push upward. I'm also checking whether SURF can compete with the target pulls, which may mean making the danger weight larger than the pull range.

I'm weighing a SURF bias on the up-move against the target pulls, so that danger above still blocks upward movement. With pulls kept small and the adjacency weight around 5, SURF can nudge the sub upward unless danger is directly above.

I'm adding a SURF bias to the up-move in the readout, which needs a threshold set so that danger directly above still blocks upward movement. The target pulls and the threat push can both pull the sub back down, so SURF has to be large enough to overcome them in the usual case.

Now I'm defining the layer-2 readouts: F from the row-1-to-8 fire group and V from the full up-move group, with SURF and the horizontal signals as ±1 inputs. I'm working out how to build the fire unit so it fires only when F is positive and SURF is off, using a scaled threshold on F.

I'm working out the layer-2 readouts now: the fire unit should fire only when the fire signal is positive and SURF is off, and the up-move unit gets a SURF bias so it can override the target pulls.

I'm checking whether SURF can override the down-move too: during SURF with targets below, the up and down pulls would conflict, so I'm suppressing the down-move when SURF is active. That leaves a gap when a threat sits in my row and danger is above, since I'd need to dodge down, and I'm working out how to keep that case from getting stuck.

I'm weighing whether to drop the separate SURF-suppression on the down-move and instead let the two thresholds overlap in a narrow band, accepting a small ambiguous zone where V sits near -0.96. Danger above pushes V low enough that the down-move wins anyway, which is acceptable.

Still working through how SURF should bias the up-move, and I'm settling on tightening the target pull weights so the threat and danger terms can dominate the decision.

Now I'm settling the priority ordering: when an enemy sits in my row with no threat, firing should win over the up and down moves, and under a threat the fire signal drops out so the movement from the threat push takes over. I'm also weighing whether to fire when idle, since a shot costs little and only delays by a few steps if an enemy shows up.

I'm settling on fire versus movement weights for the output logits: fire gets a strong boost when it's active, and up and down get smaller ones. The margins are still too narrow, though, since the up logit comes close enough to the fire logit that a pure up choice would still show up about 2% of the time.

I'm setting horizontal correction to win over everything else with a logit of 30, since alignment comes first. I'm checking whether a correction could be triggered by accident, and the noise margin is so small that it effectively never fires, so repeating a left or right press is only a problem when I'm already at the edge.

I'm checking the left-right correction next: with the sticky repeat, a stray press can move the sub the wrong way for a step or two, but the detour stays short.

I'm defining the horizontal correction as a sum over the sub's column: NR is active when the left-side ch0 count exceeds the threshold, and NL compares ch0 against ch4 in column 9, with the same kind of bias term.

Now I'm checking the case where the sub sits at column 9 facing right: the left-correction stays off there until the trailing enemy clears, so it may fire rightward and miss for a few steps. Then I'm asking whether the right and left corrections could both trigger at once at column 8 facing right.

I'm settling the layer-2 units: FIRE, UP, DOWN, and the two horizontal corrections NR and NL, which are copied from layer 1 since outputs only read from layer 2. That's five units out of the 32 available, so there's room to move some conjunction work into layer 2 as well.

I'm now weighing whether a third layer-1 group, such as danger-above and danger-below readouts for each row, would be worth the capacity, since layer 2 has room to decode those signals.

I'm trying to fit the danger information into the remaining layer-1 capacity: a single scalar for both above and below doesn't work, so I'm considering a third group encoding only danger above, since upward movement is the thing that has to be blocked.

I'm now setting the danger readout for the third layer-1 group: a scalar that goes up with danger below and drops hard with danger above, so both the up and down moves can be gated from it.

I'm weighing a way to encode the danger signal: a single unit can only hold about three well-separated levels, and I'd need four states (none, danger above, danger below, both). Mapping the "both" case onto any of the three existing levels breaks the gating, so I'm considering whether to spread the danger information across the existing layer-1 groups instead.

I'm wondering whether to drop the separate danger readouts and fold the above and below signals into a single three-level unit, which would mean merging the target pulls and the threat push into one group.

I'm weighing whether the spare layer-1 units can hold separate above and below danger groups, and the arithmetic says they can't fit both: 20 units are used, leaving 12, and a third group of seven or eight units would push past that.

I'm weighing a single merged group for the danger signal, Q34 per row, with an above-minus-below scaling so one unit covers both directions. The case where both sides have danger is the awkward one, but it's rare enough that I'm inclined to accept a rough mapping there and keep the layer-1 budget.

I'm settling the danger signal for rows 2 through 8 by merging the above and below checks into one readout that blocks up or down depending on its sign, accepting that a case with danger on both sides cancels out. Row 1 needs its own handling because it can never block upward, so I'm giving it a fixed mild downward bias so it never gets pulled up by mistake.

I'm checking the row-1 case: without a surfacing move, the sub drifts down, which is acceptable, and a threat there just pushes it down too. Adjacent danger below blocks that downward move, so it stays put. I'm also noting that the danger blocking lives in the danger group, so the target and threat pulls in layer 2 don't need their own danger terms. The one gap is that a threat should push the sub away from danger above even when the row-centre pull says up, which the blocking alone doesn't guarantee.

I'm making the layer-1 threat group three-level, so that fire, none, and threat each sit at a clean value, which lets layer 2 tell apart "dodge down" from "dodge up" when danger is adjacent.

I'm adding a row-0 detector so the threat readout is exact, with its output sitting at zero when nothing is there, and then I'm starting to think about how layer 2 turns those three readout levels into a dodge decision.

I'm working out how to fold the dodge direction into the adjacency readout W: blocking strength is set by danger above versus below, and a small centre-pull term nudges it toward the middle rows. That leaves the question of how to read a dodge direction off W when nothing dangerous is adjacent, which I haven't settled yet.

I'm working out the dodge rule: when a threat is present, the sub goes up if W is positive and down if it's negative, and normal moves are blocked only when W crosses the threshold in either direction. For row 1 I'm adding a negative bias to W so upward moves are blocked there, which means a danger below would make W land near the middle and the sign would still decide the dodge.

I'm checking the row-1 case again: with no targets above, the normal up path can't fire, so only a dodge could send the sub upward. If danger sits below at row 1 while a threat is present, the sub would be pushed down into it, which is an accepted edge case since surfacing with divers is fine.

I'm setting the row-0 dive unit to a fixed negative bias so it drifts down by default, and I'm making the row-0 adjacency readout block the downward move only when danger sits below. The surfacing check at row 0 is next.

I'm checking that the row-0 dive and the surfacing logic hold up once oxygen refills, and that horizontal alignment comes first before any dive. Next I'm starting to work out how the pull weights from the target scores should be built for each row.

I'm defining the target-pull score for each row as a sum over the enemy and diver cells in columns 0 to 7, and I'm still deciding whether column 8 belongs in that sum.

I'm weighing whether to give the diver channel a different weight from the enemy channel, since enemies are rewards and divers are about survival. Giving the bullet channel a small positive weight would let enemies and divers count for more than bullets, but it would also pull the sub toward bullets a little, so I'm still deciding between that and equal weighting.

I'm setting the target-pull coefficients by distance, positive for rows above and negative for rows below, and I'm noting that a target exactly equidistant above and below would cancel to zero, leaving the sub stuck.

I'm trying to break the tie when a target sits at equal distance above and below: giving upward pulls a small extra weight makes the equal case go up, but then an upper target one row further away can cancel it out, so ties still come back in some configurations. I'm leaning toward accepting that, since targets move and get removed and the stall should clear on its own.

I'm trying a threshold of 0.08 so the small tie-break bonus still clears it, but then I need to check whether that leaves other near-cancel cases that stall the sub.

I'm settling the pull coefficients so that a target above is preferred over one at the same distance below, but the nearest target still wins. The up and down weights need a gap that keeps a tie from cancelling to zero, so I'm checking whether a threshold of about 0.05 with a sharp gain in layer 2 holds up.

I'm settling the per-distance pull coefficients now, with each upward weight set just above its matching downward one and both shrinking with distance. The gaps between neighbouring values stay around 0.08 to 0.15, so the nearest target keeps winning and equal distances tilt upward.

I'm settling the pull magnitudes so each row's upward weight sits just above its downward weight, with both shrinking as the distance grows, which keeps ties leaning upward. I still have to check that the gaps between neighbouring values stay wide enough for the threshold to hold.

I'm dropping the -4 bias on row 1 so a surfacing sub can still move up there, since V can't exceed the threshold at row 1 anyway with no targets above. Then the dodge direction at row 1 comes from the sign of W, with the center preference pushing it down.

I'm checking whether a threat above or below should count as a dodge signal in row 1, and whether the -4 bias there can stay or has to go.

I'm checking whether a threat in our row, like an enemy bullet approaching from the left or a left-moving enemy spawning at the right edge, can be dodged in time, given that our shot cooldown is about 5 steps.

I'm checking how an enemy bullet in our row gets handled: if it's still far off, we can keep shooting back at the sub, and once it reaches the threat columns we'll dodge.

Checking how a bullet fired along row s plays out after a dodge: the sub drops or rises out of that row, and the pull toward the target sub should bring it back afterwards.

I'm checking how a bullet in our row plays out: when it reaches col 5 we dodge into the adjacent row, but then the pull back toward row s could bring us into its path while it's still passing through cols 6 to 8.

I'm checking whether bullets should count in the adjacency block, since if only the far columns are blocked, the sub could step back into the bullet's path as it passes.

I'm now looking at how the enemy-side threat cells should be weighted for the adjacency block, leaning toward counting bullets at the mid columns and enemies closer to the sub's column, and I'm still working out how to tell an approaching enemy from one moving away.

I'm working out a danger score for each row in the neighbourhood of the sub: enemy bullets and enemies on the right side count against moving there, while a left-moving enemy at column 7 is less of a threat since its trail sits at column 8 and cancels the signal.

I'm checking the case where a right-moving enemy at column 9 exits and its trail at column 8 cancels any danger signal, so the sub doesn't treat it as a threat. A left-moving enemy just spawned at column 9, though, is a real danger since it will reach column 8 soon.

I'm working out the danger term for the adjacent rows: a bullet at col 8 counts double, enemies at cols 7 and 9 count once, and a trail at col 8 cancels out an enemy that's moving away. A diver at col 8 adds nothing, so it reads as safe.

Working out the threat term for the row itself now: a left-moving enemy spawned at column 9 counts as a danger, and I need to decide how to handle a right-moving enemy bullet that is still too far away to matter.

I'm now checking the threat in my own row: a right-moving enemy's trail at column 8 should cancel out a sighting at column 9, so only a left-moving enemy just spawned there counts as a danger. Next I'll work out how the enemy-side score for row s works.

I'm working out the per-row enemy score next, counting fish, subs and divers in the sub's row over columns 0 to 7. A diver alone wouldn't justify holding position, so I'm weighing whether bullets plus divers should count the same way.

I'm settling on a single combined score for the row: the enemy count over the sub's columns, halved per cell, drives the choice between firing, holding, and dodging, with the three-way threshold set at 1.5.

I'm settling the none-case baseline so an empty row reads as neither fire nor threat, which means shifting the constant so the middle band catches it, and I'm keeping the threat penalty large enough to dominate.

I'm weighing a single score q that is linear in the summed enemy channels, but a constant offset puts "none" and "diver" at the same level, so I'm checking whether one linear term can separate the three cases.

I'm trying a fixed offset of -1 for the no-enemy case and checking whether a diver-only row can still land in the middle band, but the threat cutoff would then need to be quite deep, around -4.

I'm weighing whether a steeper gain fixes the threshold margin, and it does: with K around 50, the none case lands near -7 and the threat case near +5, so the two sit cleanly on opposite sides of the -0.9 cutoff.

I'm settling the per-row score as a constant offset of -1 plus the summed enemy and diver channels over columns 0 to 7, minus a heavy penalty for any threat, so that an empty row reads as neither fire nor threat.

I'm now treating bullets in columns 5 to 7 as threats by using the bullet-only signal, ch1 minus ch2, so that an enemy sub or diver in those columns doesn't get marked as dangerous by mistake.

I'm weighing how to weight the threat cells in row s: bullets in columns 5 to 7 count against holding, and the trail cancellation near column 9 decides whether a right-moving enemy is a threat or not.

I'm weighing a penalty on the trail cancellation at column 8, since using a smaller weight there could keep a left-moving enemy at 9 from being masked, but I'd rather not drop the cancellation entirely.

I'm settling the gate for the row as a tanh of gain times the sum of ch0 across the row, shifted by -2G, plus the per-row score q, so the gate output sits in a usable range.

Now I'm checking the gate for the first row: each unit's pre-activation is the ch0 sum minus a fixed offset, so an empty row settles to a moderately negative value that still reads as "none." Nine such units cover rows 0 through 8, and the readout adds a constant of 8 on top.

I'm defining a second group of gate units, one per row, where each unit mixes the row's own gate input with the difference between the threat-and-bullet signals in the rows directly above and below, so the sub can tell whether a neighbouring row is safer to move into.

I'm setting the sub's row-danger readout to block a move up when the summed gate output drops below -0.75, and to block a move down when it rises above 0.75, with the per-row preference nudging rows 0 to 4 toward moving down and rows 5 to 8 toward moving up.

I'm working out the per-row pull term now: each row's enemy and diver channels, weighted by a fixed bias, with the sub's own row getting a diving offset of -3.

I'm weighing whether enemy bullets in columns 0 to 7 should repel the pull term, since a bullet cancels the attraction of a sub in the same row. I'm leaning toward giving bullets no weight in that term, so that rows with fish are the ones that draw the sub.

Still working out the pull term for the sub's row; the self-row pull gets a diving offset, and the per-row weights come from the enemy and diver counts with bullets left at zero.

I'm checking the surfacing unit for the sub: a single row of weights on the oxygen-level channels at columns 0, 2 and 8 in row 9, with a bias of +3, so that surfacing fires only when oxygen is below 20 or in the 20 to 60 band.

I'm checking the oxygen-surfacing edge case now: with zero divers the oxygen threshold check is too late to save the sub, but a diver pickup is unlikely in the final steps, so I'll keep the rule as is. I also want to confirm that the diver-count cell at column 8 lines up with the state indexing when one diver is held.

I'm weighing whether to use column 1 for the oxygen surfacing threshold instead of column 2, since that would cut how often the sub has to surface and spend a diver.

I'm setting the no-enemy unit for the right-moving check: it fires when any ground cell in columns 0 to 7 across rows 0 to 8 is lit, with a bias of -3, and the left-moving check follows the same pattern on column 9 with the enemy subtraction.

I'm sorting out the layer-two units now, and I'm still deciding how to combine the layer-one outputs.

I'm building the layer-two fire unit: its pre-activation is 10 times the fire score minus 4 times the surf signal minus 8, so it only goes positive when the fire score is high and the sub isn't surfacing.

I'm checking the fire unit's edge cases with the 0.76 and 0.995 values, then moving on to the threat-dodge unit that only fires when the threat term and the upward-direction readout both hold.

I'm checking the threat-dodge unit: when a threat is present and the readout favours moving up, the pre-activation comes out to 4.6 and the unit fires, but a threat with the opposite direction goes to -4.6 and stays off.

I'm now defining the threat-down unit as the mirror of the dodge-up unit: it fires when a threat is present and the direction readout points down, and I'm giving the dodge units larger weights so they take priority over surfacing.

I'm working out the layer-two move-up unit now: it should fire when the pull term is above threshold or the surfacing unit is on, but only while the neighbouring-row readout isn't too dangerous. I'm still sorting out how to combine those two conditions into one unit.

I'm trying to combine the two conditions into one gate, so the unit should only fire when the pull or surfacing margin is positive and the neighbouring-row readout is above the blocking level. That means a sum of weighted margins with an offset, so that either condition alone can't push it past zero while the block term is active.

I'm working out the blocking term for upward moves: a unit that fires when the neighbouring-row readout is below -0.75, so the up logit can be pushed down whenever that block applies. I'm leaving the raw move-up unit at a fixed pre-activation of 40 for now, since the final up logit combines it with the block unit.

I'm setting the move-down unit to run opposite to the move-up one, switching it off whenever the surfacing signal is on, and I'm checking that the two raw pull units don't fire together.

I'm finishing the block-up and block-down units for the vertical moves, and setting the no-enemy and neighbour-row copies to pass their readouts along.

I'm now setting the output logits: each one is a weighted sum over the layer-two units, rescaled from the ±1 outputs to the 0-to-1 range, so the weights carry over directly as the W3 entries.

I'm now setting the output logits for the four moves plus fire: up gets a boost from the move-up and dodge-up units and a penalty from the block-up unit, down mirrors that, and fire gets its own smaller weight.

I'm checking the output priorities now: fire at 20, the regular move at 10, and dodge at 35, so a dodge keeps winning when both are on. When the sub is surfacing, fire is off and the down move is off too, so the block-up case falls back to no-op.

I'm checking the leak in the move-up unit: with no targets, the pre-activation sits near -1.2, which still pushes a small amount of probability onto the up logit, so I'm weighing whether to tighten the offset or accept that residual.

I'm tightening the move-up and move-down units with a steeper slope so they stay saturated near zero, which stops a stray probability from leaking onto the up logit at row 1. I'm also giving the bottom row a small downward bias so the sub drifts down when idle, and checking that the blocking unit covers the remaining vertical cases.

I'm now handling the row-1 case, where the up move could leak through if nothing blocks it. The problem is that blocking up at row 1 would also stop the surfacing move I need there, so a simple block won't work. I'm weighing a separate row-1 gate instead, one that's tighter than the general danger threshold so it doesn't interfere with the surfacing logic.

I'm checking whether the row-1 leak is safe when the down move is blocked: with the down logit pushed negative, the idle logits all sit near zero, so the up move could get sampled by accident.

I'm recalculating the output logits with larger magnitudes, since small neutral biases would still let up, left, and right fire too often when nothing is happening. I'm setting the noop baseline high, with the movement and fire logits pushed well above it, and blocked moves pushed far negative.

I'm checking the combined logits for the idle, move-only, and fire-plus-move cases, and the margins look wide enough that the baseline noop should dominate when nothing is happening.

I'm checking the combined logits for the threat-dodge and blocking cases, and the margins hold: a moving-up unit that's blocked gets pushed far negative, and the mirror-image dodge units can't fire together. Since the threat-direction readout stays well away from zero, the integer-scaled pre-activations never land in the ambiguous middle.

I'm checking that the layer-two units are saturated enough that their inactive outputs contribute almost nothing to the logits, and that every case keeps a margin of about 3 to 4. For the move-up unit near the threshold, I'm confirming that a single target gives a pre-activation of at least 34, while an empty board gives about -5.

I'm checking how the sustained surfacing state plays out now: with the surface signal on, the move-up unit stays active across rows, the move-down and fire units switch off, and the leftover threat-dodge logic still runs.

I'm checking the row-0 case once more: once oxygen is refilled, the surface flag clears, so the down pull takes over and the sub dives again. A surface flag that's already on at row 0 shouldn't happen, since surfacing is what turns it off. If oxygen runs out with no divers picked up, the sub surfaces and dies, which is acceptable, and when the surface flag is active at row 1 the up move carries it to row 0 and the surfacing takes place.

I'm checking the start of the run: the sub begins at x=5, y=0 facing left, and sees a target at column 5-6, so it moves right to x=8 and turns around. After that it dives, and the underwater hunting comes next, with the pull units steering it toward rows that have targets.

I'm checking how the left-moving enemy spawned at the far column affects the row it's in: once the sub has dodged to an adjacent row, that row's target count goes to zero, so nothing pulls it back, while the danger readout still blocks a return. As the enemy drifts closer to the sub's column, the row starts registering a target again, and I'm verifying that the trailing-edge term keeps the blocking signal consistent with that.

I'm checking the row-to-row blocking now: a bullet left behind at column 5 only matters for the adjacent-row check, since the other cells are already covered by the earlier terms.

I'm extending the danger check so bullets at columns 5 and 6 also count toward blocking the adjacent row, since a right-moving sub fires about every 11 steps and those bullets otherwise slip past the check.

I'm checking the bullets at column 4 and the row-1 dodge timing, and the next step is a bullet at 5 triggering the dodge. I'm also considering a right-moving enemy and whether its bullets can be avoided, which looks fine since the sub fires and the dodge follows.

I'm settling how the target counts should feed the pull, starting with whether an enemy on the far right column should count at all.

I'm weighing how divers at cols 5..7 should pull me: they keep me in their row until they move, since the fire-or-stay signal is strong there. I still need to check what happens with a diver at (t,8) when I'm in an adjacent row.

I'm working out how a diver on the far-right column should steer the sub: setting its pull weight at columns 8 and 9 higher so pickups happen sooner. The complication is that an enemy at column 9 in my own row has to keep a threat signal, so I need to make sure the diver weight there doesn't cancel it out.

I'm setting the enemy cell at column 9 in my row to -10 and the diver cell there to +4, so the enemy still reads as a threat while the diver reads as a reason to stay and wait for the pickup.

I'm weighing how to keep the diver-masking case from blocking entry: a diver at column 6 pulls the down-weight negative, so I'm considering dropping that weight to cancel only the enemy contribution.

I'm checking whether a target sitting at column 6 in an adjacent row would pull me in, since the blocking check on that row may still be masking it.

I'm checking whether an enemy at column 6 in the row above gets through the blocking check: the difference there is zero, so nothing blocks, and I'd enter at column 8 and fire. The bullet would reach column 7 first and then hit the enemy on the next step if it's still on that path.

I'm also weighing sticky actions: a 10% chance a repeated move could overshoot once I arrive, which I'd correct on the next step, and a delayed dodge if I was firing, which the multi-step warning from an approaching bullet should cover.

I'm checking the timing of the bullet dodge: a bullet at column 5 gives me about three steps to get clear before it reaches my column, and the action on the third step still resolves before the bullet moves.

I'm settling how the sub should handle a left-moving enemy sitting in its own row, and whether a right-moving enemy's bullet from an adjacent row matters. Those bullets stay in their row, so they don't need a dodge. The bullets that do matter are the ones moving through rows I'd pass through, and the existing danger check already covers those.

I'm settling the surfacing cost: each surface drops one diver when I have fewer than six, so I need to collect at least one per oxygen tank to keep the count up. The row-1 pull with its small downward bias keeps me idling there until I move, and from row 0 only the bias applies, so no pulls are needed.

I'm setting the row-1 and row-8 dodge preferences, and checking that a threat from below still pushes the sub up. Next I'm deciding the per-row pull coefficients for each sub unit, starting with how the upward and downward offsets map to the row distance.

I'm defining the per-row pull weights for each sub unit: cells in the target row's columns 0 to 7 count once, columns 8 and 9 count double, and bullets at 8 and 9 subtract from that. Then I'll scale each row's input by a distance-based coefficient, with the upward and downward offsets handled separately.

I'm sanity-checking the pull weights: a single target one row away gives a value of about 2, which clears the movement threshold. The remaining worry is a target in my own row, where firing takes priority over moving.

I'm checking the two-bullet case in the own row: with two bullets at columns 0..4, the count comes out to 1, so the fire-or-stay signal still triggers and I'd stay put instead of moving.

I'm now setting the weights for the rows above and below the sub, and I'm about to define how the cells in its own row contribute to the fire signal, starting with the columns 5 to 7.

Now I'm setting the own-row weights for the fire signal: columns 0 to 4 count +1 for enemies and divers alike, columns 5 to 7 give enemies a small +2 and divers +9, and column 9 subtracts for enemies and adds a little for divers. With a -1 bias, a lone enemy anywhere in columns 0 to 7 comes out at +1, so the fire signal still triggers.

I'm settling the fire threshold: an enemy in my row scores +1 and gives a fire signal, while a diver there scores 0 and doesn't.

Checking the fire thresholds again: an enemy in my row scores around 0.76, comfortably above the 0.4 cutoff, while a diver there scores 0 and doesn't trigger firing. I'm now moving on to the row-0 unit and the wall-dodge weights.

I'm checking that the inactive groups stay saturated: with a large gate the negative term dominates, so the stray positive contributions from targets, walls and divers can't flip them on.

I'm settling the group-gate weights: every ch0 cell in the sub's row gets a +25 and the bias is -50, so the groups net to zero when active and stay strongly negative when inactive. Next I'm laying out the layer-2 units, which will sum the Q1, Q2 and W outputs and the surfacing signal into the final action.

I'm switching the fire unit's weights to a version that scales the enemy signal more cleanly, testing the numbers against a few cases before settling on them.

I'm setting the weights for the first dodge-up unit: a large negative term on the Q1 fire signal plus a boost from the wall-threat input, with a bias of -45, and I'm checking that the sign works out.

I'm working out the dodge-up unit's sums: the fire signal enters with a -50 weight, the wall-threat term with +10, and the bias comes to -370 once the constants are folded in. Plugging in a few cases, a threat gives a small positive value and no threat a small negative one, which is the sign I need.

I'm rechecking the dodge-up unit with a sharper gain of 60, so the none case lands near -4.4 and the threat case near +4.6, which keeps both clear of the threshold.

Checking the dodge-up unit's constant term once more: at the threat case it comes to +4.6, and with no threat near -4.3, both clear the threshold. I'm now expanding the sum in terms of the layer-one outputs and the wall weights.

Next I'm writing out the dodge-down unit, with the same Q1 and W terms flipped in sign and a similar constant offset.

I'm checking the move-up unit's sign: with the surfacing signal on, the V term still has to stay positive even when targets below push V strongly negative, so I need to see whether the constant offset covers the full range of V.

Writing the move-down unit's weights now, with the same V term flipped and the surfacing signal entering with a negative weight.

Writing the block-up and block-down units now, scaling the wall-threat sums by 30 with offsets of -0.75 and checking the sign on both sides.

Writing the output layer now: the no-op logit gets a constant of 12, the left move reads the layer-two block signal with weight 30 and offset 30, and the up move combines the move-up and dodge-up units with block-up subtracted.

Writing the output layer's weights for the down move and the fire unit, with the no-op and directional logits set so that the idle state produces only the no-op.

Now I'm checking the weight-based wall-threat sum for row 1, where the preference term is -0.5 and nothing sits in row 0, to see what sign the dodge logic gets.

I'm weighing whether to lower the row-1 preference so dodging up needs two dangers, but that would make the block-up unit stop the surfacing move from row 1. I'm considering a surfacing override on the block unit to avoid that.

I'm weighing whether a smaller row-1 preference would let the dodge logic send the sub upward only when two dangers line up, since a stronger block could stop the surfacing move from row 1.

I'm weighing a lower threshold for the block-up unit at row 1, since the preference alone would otherwise stop the surfacing move from row 1, and I'm considering scaling the danger term so the threshold can sit between the two cases.

I'm weighing the row-1 case: since the danger below makes dodging down the wrong move, I'll accept the small preference and let a threat push the sub upward even if that risks surfacing into danger.

I'm checking the dodge-down weights against the fire and wall terms, and then I'm going over how the sub should behave when dangers sit on both sides at once. Those cases blur the blocking logic, and I'm checking whether it still picks a sensible dodge direction. I'm also weighing whether the pull toward targets should respect rows that are currently blocked, and I'll come back to what the sub should do when it surfaces.

Checking the oxygen threshold next: the surfacing unit reads the oxygen bar at row 9, column 1, and I want to confirm it fires below 40.

Now I'm checking the oxygen bar's column mapping, where the diver gauge overlaps but columns 0 and 1 are oxygen only, and I'm wondering whether the trail channel at the sub's back is handled correctly.

Checking whether a threat at column 9 counts as a threat to the sub in row 1, then moving on to the enemy pull logic.

Still checking the enemy-spawn rule and the expected score range, and I'm weighing whether to increase how often the sub collects divers to offset the cost of surfacing.

I'm weighing the diver pull: divers in my own row at columns 0 to 4 don't count as a reason to stay, so the sub only holds still when nothing else pulls it, and a right-moving diver is worth chasing while a left-moving one isn't. I'm also considering whether to make a diver's row weigh more when the sub is idle, and I'll go back to the enemy at column 9 in another row.

Still working out the unit layout, now assigning index ranges for the query, wall, and surfacing units in the first layer...

Writing the per-row gate weights now, with the ch0 cells of each row set to 25 and a bias of -50 so each group unit responds only to its own row. For the row-1-to-8 quick-decision units I'm setting the first two channels to +1 and +2 for the open columns, -7 and +9 for the middle, and -10 and +4 for the far column, with a bias of -51.

Still writing out the weight indices for the query unit in each row, using the channel and column ranges as I go.

Still writing the query unit's weights for row 1, setting the gate and channel values across the open and middle columns.

Still writing the query units' weights, now the pull toward other rows' targets in the Q2 units.

Still writing the Q2 pull weights, now the per-row contributions to each query unit.

Working out how to write the Q2 pull weights more compactly, since the per-row statements would run to hundreds of lines.

Still working out the strided weight writes for the Q2 units, now deciding whether to fill each block as a 2-D list or to set the entries one unit at a time.

Still working out the strided weight writes for the Q2 units, now counting how many statements the per-pair approach would take versus a 2-D block per input row.

Still weighing how to write the Q2 block weights compactly, now considering a single 8-by-8 list per input row instead of many separate strided assignments.

Still writing the Q2 pull weights, now considering a 2-D block per input row so each row's contributions go in one statement instead of many separate strided assignments.

Still writing the Q2 pull weights, now simplifying the enemy terms so each row contributes with one statement per pair.

Still working out the Q2 pull weights, now considering a compact form: one long list per unit covering all the channel-2 cells in rows 1 through 8, with the enemy terms in the odd channel handled separately.

Still weighing how to write the per-unit weights compactly, now comparing one long list per unit against several shorter blocks, since counting the exact number of entries by hand is where mistakes would creep in.

Still working out the Q2 pull weights, now settling on one scalar fill per pair of rows, with the enemy columns handled by a separate pair of statements.

Still writing the Q2 pull weights, now filling each source row's channel-2 cells with a scalar per target unit.

Still writing the weight indices for the upward and downward diver pulls, now working through the per-row cell weights for the wall and fire terms.

Still writing the Q2 pull weights for each unit, now filling the cells of the rows just above and below with the per-row gate values.

Still writing the weight fills for each unit, now the row-pair contributions for the enemy and diver cells in the rows just above and below.

Still setting the surfacing unit's weights, now the cells that gate it on the oxygen bar and its bias.

Still writing the no-right and no-left unit weights, setting the ch0 cells for each row and a bias of -3 for the first.

Setting up the second layer now, with the fire unit's weights on the first-layer units and its bias.

Still setting the second-layer weights, now working out the bias for the dodge-down unit so its pre-activation comes out to the target form.

Still setting the second-layer weights for the middle-value and the bottom-unit cases, now working out the bias that makes the pre-activation match the target form.

Still setting the second-layer weights, now checking the bias on the BD unit against its target form.

Writing the output layer weights now, with the left, up, right, and down action columns each tied to specific second-layer units.

Checking the output-layer logits for each action with every unit off, and confirming that the up and down logits come out as intended.

Checking the threat-avoidance cases now: a dodge-down response should win when danger sits above, and a dodge-up response when danger sits below.

Still checking the scenario by hand: at row 0 the medium-danger unit's pre-activation comes to about 94, so it should fire.

Checking the dive timing near row 1: the down logit beats noop, so I'm weighing whether a bottom-danger unit would block it.

Checking the idle case at row 2: with no targets, both the down and up logits stay below noop, so the agent just waits there. Next I'm setting up the scenario where an enemy appears at row 5, column 0, moving right.

Checking the enemy's descent timing against the diver's trajectory, I'm finding that the Q2 pull lands at row 5 with a positive fire signal, so the agent should fire, and I'm tracing the bullet's path from column 8 leftward to confirm it reaches the target.

Checking the left-mover case: it spawns on my row at column 9, and since it's in my row I have to decide whether to dodge it. Once I'm past it, the cell at its current spot doesn't pull me back, but the trail it leaves behind is what matters as it moves toward column 7.

Checking the left-moving enemy's bullet at column 7, and whether my own bullet reaches its target before the enemy fires back.

Now I'm checking the oxygen-threshold case: below 40 with a diver present, the surfacing unit pulls me upward row by row. Once I reach row 0 and surfacing resets the oxygen to 200, the surface flag is set, so the dive response takes over again.

Still checking the oxygen-threshold case: with no divers and oxygen under 40, the surfacing signal stays off, so I keep hunting, and if oxygen drops below 20 I'll head up regardless.

Checking the oxygen-gate fallback: if the diver count went negative, the gauge reads empty, so I'm weighing whether to keep the surface trigger on when oxygen falls below 20 even with zero divers.

I'm weighing whether to keep the oxygen-under-20 surface rule even when there are no divers, since the cost of dropping hunting time looks small next to the chance of a negative diver count.

Still checking the scenarios by hand: I'm working out that an idle agent at row s can still be pulled toward a diver in row t, where it fires once aligned and picks the diver up. I'm also noting that a fish passing just below only registers as a danger signal, which doesn't matter while the agent is idle. The open question is whether a far-off pull target could lead the path through a danger zone.

Now I'm reconsidering the gating weight and whether the units for other rows could interfere. The row-s pre-activations look fine: the other rows' units start far negative and stay saturated off, since their sums are bounded by the scale of the cell weights.

Checking the weight bounds now: the row-s pre-activation for the wall-avoidance unit comes out around -26 at worst, so it saturates to -1 and stays off.

I'm checking whether the sticky "up" repeat could carry the agent from row 2 into row 0 with no divers to surface for, which would be a fatal move, so I'm tracing when the up action gets pressed at row 2.

Moving up into row 1 carries a 10% chance of the sticky repeat pushing me on to row 0, which would be fatal with no divers to surface for. I'm considering keeping row 1 off-limits except during a deliberate surfacing, even if that means passing up targets there.

Stepping up from row 2 into row 1 is risky: the sticky-action repeat could push me on to row 0 by accident, and with no divers that would be fatal. So I'm inclined to keep row 1 off-limits except during a deliberate surfacing.

Row 1 is off-limits outside a deliberate surfacing, since a sticky repeat of "up" could send the agent into row 0 with no divers to surface for. So I'm dropping row-1 targets from the pull units and keeping the dodge-up response from firing at row 2.

I'm weighing the row-2 dodge: if I dodge down there, I'd land in danger at row 3, so dodging up into row 1 looks safer despite the sticky-repeat risk, and I'm setting the bias so that the up response wins when no danger is present.

Working out the row-2 conflict: the pseudo-block I was planning for row 2 would also stop an intentional surfacing move, so I'm looking for a way to separate a real danger from that bias. Giving real dangers a much stronger weight than the artificial one, and raising the block threshold only during surfacing, might let both work.

Now I'm settling the row-2 blocking rule: the up-block threshold should loosen during surfacing, so a deliberate surfacing isn't stopped by the artificial row-2 bias, while real dangers still hold. At the surfacing setting, though, the row-2 bias sits just under the adjusted threshold, so I still need to check that it stays off.

Checking the float32 precision now, with a steeper gain K so that the real-danger term still beats the tighter surfacing threshold.

Now I'm checking the dodge-up case: with the scaled danger term, a danger below pushes the agent upward into row 1 despite the sticky-repeat risk, while an empty row below keeps it dodging down.

I'm dropping row 1 from the pull targets so the agent never has a reason to step into it, since the sticky repeat could push it into row 0 with no divers. That means the pull units only respond to rows 2 through 8. With nothing above row 2 to pull toward, the up-move at row 2 can't fire on its own, and the extra row-2 block just guards against any leftover pull.

I'm settling on a dodge-up from row 2 whenever danger sits below, since risking the sticky repeat beats walking into the hazard. The row-2 pseudo-block isn't needed for that move, so I'll keep the up-block threshold simple at -0.75. I still need to think about the accidental surfacing that a sticky repeat could cause after a dodge up into row 1, which costs a diver.

Row 1 enemies don't threaten me, since I only enter row 1 during a surfacing or a dodge. If I happen to be in row 1 mid-transit and an enemy is there, I'd fire, and repeating fire or down is harmless, so the sticky risk only matters for moving up.

I'm checking the sticky "left" repeat next: after alignment I press left from x=9, landing at x=8 facing left, and a 10% repeat would carry me on to x=7 and force a realignment underwater, which is risky.

I'm checking whether a sticky "left" repeat right after alignment could push the agent to x=7, which only matters if it happens underwater. Alignment happens at row 0, so that case is safe, and the agent will be at (0,8) facing left when the policy calls for "down."

I'm now checking the pull coefficients using only rows 2 through 8 as targets, so the agent has no reason to aim into row 1. For each starting row, the pulls point at the lower targets (or the upper ones for the deeper starts), and the largest upward distance is six rows from row 8 to row 2. Q2 at row 1 is biased down with only negative pulls, so it resolves to a dive.

Now I'm checking the sticky "left" repeat once more, and whether a shot fired from a sub in our row could be an issue, though the fire-when-idle question is settled: noop is still preferred.

Now I'm checking how a sub in our row to the left would play out: the policy fires at it once bullets are close, then dodges when a bullet nears.

Now I'm checking whether rows with divers could draw the agent back and forth between two rows, since the pull from one row may fight the pull from another once it arrives.

Two diver rows could pull me back and forth, since each row's pull toward the other never gets resolved by firing. Making divers count as a stay signal in their own row would stop that, but it would also keep me parked when enemies are elsewhere. So I'm considering weighting divers far below enemies and softening the stay response for them.

I'm weighing a fix for the oscillation: two diver rows could pull me back and forth, so I'm considering having a diver in my own row count as a weak stay signal, which keeps me from bouncing between them.

Diver rows are a problem here: if a diver alone triggers the fire-and-stay response, I'd park at diver rows and miss enemies elsewhere. Maybe I can split the two by magnitude instead, so an enemy in my row fires with the higher priority and a diver in my row only gives a weaker stay signal that loses to real targets.

I'm weighing two-level pulls so enemy rows draw me strongly and diver rows only weakly, which should stop me bouncing between two diver rows. A diver in my own row would then give a modest stay signal that loses to real enemy targets.

I'm weighing two levels of pull so enemy rows draw me strongly and diver rows only weakly, with baseline, weak, diver-stay, and strong logit scales spaced so the margins hold. The open question is how V's magnitude changes with a diver's distance and how many divers are on screen.

I'm settling on weights where enemies count for three times the pull of divers, so a distant enemy still outweighs a close diver, and then checking the margins against the threshold.

I'm considering leaving divers out of the pull targets entirely, except when they get close to the right edge, to avoid bouncing between two diver rows. Then divers would only be collected when they drift near my column or when I happen to be idle in their row.

I'm weighing whether to let divers in column 7 count as pull targets, since a right-moving diver there will reach column 8 soon, while a left-moving one is leaving. I'm also considering whether the trail behind a diver can tell me its direction.

I'm checking whether pulling toward enemies while leaving divers out can work: weighting the enemy channel above the diver channel would separate them, though bullets in that channel would still attract me.

I'm thinking about whether a shared pull could make me bounce between two diver rows, and whether weighting diver pulls lower than enemy pulls would stop that. A nonzero diver pull still seems to leave the oscillation open unless the move threshold sits above what a diver alone produces.

I'm settling the pull weights so that divers at columns 0 through 7 don't attract me, since a weak diver pull stays below the move threshold. Only enemies and bullets in those columns would draw me, and divers near the right edge would get a stronger pull for quick pickups.

Now I'm checking whether moving between two bullet-only rows could bounce me back and forth, which seems unlikely since those bullets exit quickly. Next I'm looking at divers in columns 8 and 9, to see whether stepping onto a diver's cell right away counts as a pickup.

I'm checking whether two divers sitting at columns 8 and 9 in different rows could make me oscillate, and it looks fine: if I'm at (t,8) with a diver at (t,9), the stay response outweighs the pull, so I hold position. The remaining worry is the collection rate, since a left-moving diver spawned at column 9 stays catchable for roughly eleven steps, which only works if I can reach its row within about six rows.

I'm working out the expected diver yield per tank: roughly five divers spawn, and about two or three of them would be catchable, with the limiting factor being whether I'm busy firing at an enemy when the window opens.

I'm checking how a diver that moves into an edge column would affect the pull weights, and whether the surfacing rule could drop my count to a point where I die before I can recover it.

I'm checking whether counting six divers could trigger an earlier surface for a bigger bonus, since the oxygen gauge might be hiding that count.

Checking whether a six-diver surface could come earlier, around oxygen 80, for a larger bonus.

I'm weighting the diver-column pulls at columns 8 and 9 so that enemies there cancel out and bullets there repel me, while the rest of the pull sums up the enemy and bullet channel across columns 0 through 7.

I'm weighing whether a diver in my own row should draw a stay signal, and I'm settling on giving divers at columns 8 and 9 a heavier pull than enemies, since their windows are short, while enemies still take priority when they share my row.

I'm reworking the stay weights for divers in columns 5 through 7, since a left-moving diver there would just pull me into wasted steps while I'm already in its row.

I'm tuning the weights so an enemy in column 5 to 7 gives a net positive pull while a bullet gives a strong negative one, which means the diver signal can't be set to zero without shrinking the enemy margin too far. Keeping the diver weight near the enemy's makes the stay signal dominate when I'm already in a diver's row, so I'm trying to find a bullet weight that stays below it.

I'm checking whether a trail term at column 8 could cancel a left-moving diver at column 7, since that would be a negative net pull and would make me dodge when I should stay. The trail weight I'm considering would flip the sign, so I'm testing whether that's worth it.

I'm settling the row weights for the stay case: keeping bullets in columns 5 through 7 as strong repellers and divers there as pulls, and I'm wondering whether to include column 4 as well, since dodging earlier might buy more time.

I'm settling the pull weights for the next step: enemies in columns 0 through 4 count a little, while in columns 5 through 7 a bullet repels strongly and a diver draws me to stay. Divers at the right edge get a stronger weight so I can reach them quickly.

Writing the stay weights as indexed assignments across all the row-and-column pairs...

Still writing the weight matrix...

Still working through the weight matrix, now weighing whether to fill the diver and enemy columns per unit or use one block per row.

Still writing the weight matrix, now deciding whether to fill the diver and enemy columns per unit or group the cells in a single list per row.

Still writing the weight matrix...

Still working out the per-pair weights for the next block, sorting out whether to simplify the diver weight so the arithmetic stays manageable.

Still working out the per-cell numbers, now checking the scaled values so the diver weights line up with the enemy ones in the next pass.

Still checking the diver weights at columns 8 and 9 against the surrounding cells, making sure a diver in my own row at those columns still registers as a stay signal.

I'm checking whether a diver's trail at column 8 could make a stay-or-dodge decision flip, since a trail term would give a false block above or below me. The problem is that -ch4 at column 8 can push a neighboring row's weight to -1, which reads as danger when there's nothing there.

I'm checking whether a left-moving diver at column 7 would leave a trail term at column 8 that reads as a false danger signal, and I'm wondering whether a negative weight on that trail could cancel it out.

I'm checking whether any sign pattern can make a left-moving diver at column 7 read as zero while an enemy in that same spot reads as one, and it looks like the diver trail term can't do both at once.

I'm weighing whether dropping the trail term would be cleaner, since keeping it forces a choice between a false block on enemies moving away and a false block on divers I want to enter.

I'm thinking about whether a diver in column 6 should count as danger, and I'm leaning toward letting any enemy in columns 6 through 9 raise the signal, even if that costs a few steps of delay.

I'm settling on a diver-count term that lumps enemies and bullets from columns 6 through 8 into one sum, with the column-8 entries doubled.

Still writing the weight indices for the row-factor pattern...

Still writing the weight assignments for the first row, now setting the enemy and diver entries in columns 0 through 9.

Still working through the row-weight assignments, now double-checking the indices for the enemy and diver columns and moving on to the pull weights for the rows below.

Now I'm checking the diver-trail term at column 8 against the dodge thresholds, since the new Q1 levels push threats to about -6 or -7.

Checking how a diver at column 5 to 7 combines with a bullet's repulsion, and whether the dodge threshold still triggers at around -4 once an enemy sits ahead of the bullet.

Checking the bullet-plus-diver case, a diver at column 6 pushes the net pull to about +2 and the bullet repels, so I'm reweighting the column-9 enemy to a stronger repel and the diver there to a pull, so a left-moving threat still reads as danger.

Still working through the threshold checks on the combined signal, confirming the fire and dodge cases still resolve correctly at these levels.

Checking the sign-and-threshold math for the moving-unit layer, I'm confirming the pull magnitudes clear the move threshold and that the stay and dodge cases come out on the right side.

Checking the logits once more across the hunting, threat, and dodge states, the values still fall in the expected ranges. For a dodge-up threat, the DU pre-activation comes out to about 10·Wv, so it only wins when Wv is positive, and I'm testing a threat at F about -0.964 where it lands near 3.8.

Still checking the dodge and surf cases against the new weights, and the no-op at the current row still wins in the surf state. I'm also re-examining whether the right-edge alignment unit gets muddied by trailing negatives from left-moving units in neighboring rows.

Still checking how a right-mover in our row gets handled when we're at column 8, and whether the fire decision still holds.

Still writing the per-row weight entries, now setting the gate and bias values for each unit and filling in the factor pattern for the row below.

I'm working out how the enemy-row pull term should apply to the adjacent row, since a right-moving target at column 6 would sit in the dodge zone before it ever reaches me. That makes the broad column-6 check look like it might block me from a lane I'd otherwise be able to shoot from.

I'm checking whether dropping the column-6 check would be safe, since an enemy at column 6 in the adjacent row can't reach my column before I shoot it from the lane.

Checking the timing on the diver-column case: if I step into the lane with the enemy at column 6, it could reach column 7 before I can fire, and a cooldown from an earlier shot would block the shot entirely.

I'm weighing whether bullets at column 6 are safe to leave out of the danger check, since an enemy there could reach column 7 before I can shoot. Bullets are different: a bullet at column 6 would reach column 7 next step and I could step out of its way, so I'm leaning toward keeping bullets in the check while dropping the enemy at column 6 for cooldown reasons.

Still weighing the row weights: I'm settling on a column-6 exclusion for enemies, since entering with an enemy there could be survivable if the shot isn't blocked by cooldown, and keeping column 7 through 9 in the danger sum instead.

Now I'm checking the case where the left-moving enemy sits in our row at column 9 and both adjacent rows are blocked, since the dodge units only fire in one direction depending on the sign of Wv.

I'm checking whether an enemy at column 0 moving left, about to exit, is worth going after or can safely be skipped.

Now I'm checking whether a left-moving sub at column 9 in my row can actually fire before it moves, given that it spawns there and steps toward column 8 after a few steps.

Now I'm checking the timing for a right-moving sub in my row at column 7: if I fire, my bullet would reach it before it can shoot me, since friendly bullets update before the enemy subs do.

Now I'm checking how fast the enemies get: they move every three steps at the slowest speed, and surfacing spawns get quicker over time, so the screen could fill up late in a run. For a left-moving enemy spawned at column 9, I'd have two actions before it reaches me, which is tight but workable.

Next I'm weighing whether to let firing take priority over the surface move: with about 39 steps of oxygen left when SURF triggers, there's time to clear an enemy in front before going up, so I'm considering putting FIRE ahead of the move.

Now I'm wondering whether to add a layer-1 unit that tracks low oxygen, so FIRE can be suppressed only when the gauge is actually low, using one of the spare units.

I'm adding a low-oxygen unit that switches FIRE off only when the gauge drops below 20, so fire still wins during a surface climb while an enemy is in my row. Once oxygen runs low I'll go up without stopping to shoot, though I still need to confirm there's enough time left to climb.

Writing the low-oxygen unit weights for FIRE...

Now I'm weighing whether a right-moving sub at column 7 in my row should be fired on, and whether the bullet from the next step might catch me first.

Now I'm laying out the layer-1 unit assignments: the nine Q1 units, the nine Q2 units, the nine W units, and the extras for SURF, NR, NL, and LOWOX, with one spare left over. Next comes the gate weights for each of those groups.

Still writing the bias values for each group, and setting the Q2 pull weights for each pair of rows.

Now I'm filling in the Q2 pull weights for unit 10, the row-1 enemy pull, working through the distances to rows 2 through 8 with their down-moving coefficients.

Still filling in the Q2 pull weights for the rest of the rows, working through each enemy-row unit's distances and signs.

Still filling in the Q2 pull weights, now working through the remaining enemy-row units and their distances to the rows below.

Now I'm working out the 2-D block layout for the Q2 pull weights, weighing whether one large list per row is safer than many single-value statements.

Still weighing how to write the Q2 pull weights, now leaning toward three scalar statements per row rather than one large block, since fewer long lists are less risky to get wrong.

I'm considering whether to drop the negative ch1 terms at columns 8 and 9, which would leave a positive pull toward enemies there. That's mostly harmless, since an enemy at column 9 will soon become a target, though right-movers at those columns are leaving and would pull falsely.

Writing the weight statements for the wall-unit gates and their coupling to the rows below and above...

Still writing the wall-unit weights, now the shifted-row gates: each wall unit couples to the row just below with positive weights and to the row just above with negative ones.

Still writing the layer-1 gate weights, now setting the Q1 firing and dodge weights for each row's unit.

Still writing the gate weights, now weighing whether one strided assignment across all three unit groups for each group index would be safe or whether separate per-unit lines are the better choice.

Still writing the gate weights, now the rest of the layer-1 weights for each row, starting with the row-to-row gates for the nine Q1 units.

Still writing the layer-2 weights, now the output pull for each group of units.

Still writing the layer-2 output weights, checking the bias terms for the down-move and up-move units against the sums of the Q1 and W units.

Still writing the bias and output weights, checking each sum against the Q1 and W units.

Still writing the output-layer weights, now the bias for the first output unit and the coupling terms to the hidden units.

Still writing the output-layer weights, now the bias and coupling terms for the hidden units, and checking the left-direction case where the gate sits near tanh saturation.

Still checking the zeroed-out weights on unused unit 31 and the empty layer-2 rows, and confirming the output stays silent there.

Now I'm stepping through the early moves of the episode: the diver starts with full oxygen and no enemies, so the right-move detector fires at the first step and the sub heads right, then keeps going right on the next two steps as the sensors keep counting it in the front columns.

Checking the down-move logic at the next step: the sub has turned left at column 8, and the down-move unit fires because the enemy pull is strong while the back-side sensor is clear.

Still checking the step-by-step behavior: the sub drops down from row 1 to row 2 at column 8, and the first enemy spawns at step 20.

Still checking the firing timing: the fish at row 5 is coming toward the sub, so I'll line up in row 5 and shoot once the bullet path is clear.

Still checking how the threat detection handles an enemy at column 9 when I'm on the same row, where it gives a fire signal.

Still checking the dodge logic: once the sub moves off a row, the back-side sensor keeps that row blocked until the enemy has passed, so I'll wait for it to reach column 8 before firing.

Checking how a bullet-only row behaves: with no enemy in it, the attraction from the bullet still pulls the sub toward that row, so I'd expect it to bounce between two rows rather than settle.

Bullets are short-lived, so pulling toward their rows would only cause brief oscillation, whereas divers linger and matter more. I'm weighing whether to drop bullets from the pull inputs and keep only the diver-row signal, since that trade-off seems cleaner.

Weighing whether bullets should feed the pull at all: they're short-lived, so chasing their rows would just cause brief oscillation, while divers that linger matter more. I'm also noting that a right-moving diver at column 9 would be a wasted pull, since it exits soon.

Checking the start-of-episode behavior, the surface flag is set at row 0 so staying there costs no oxygen, which means the sub should dive right after it lines up. I'll also confirm how the surface and low-oxygen rules interact on the return trip, and whether the first step down from row 0 to row 1 gets pulled back up.

Checking the dodge logic at row 2: when a threat is coming, the sub prefers moving down, unless the row below already has something in the way.

Still checking the dodge case where row 2 is blocked below, and whether a sticky move back up could drop the sub onto the surface.

Still checking the dodge behavior near the bottom row: I'd dodge upward there, since downward isn't available. I also want to confirm that the Q2 pull for each row ignores that row's own cells, so the sub doesn't get stuck trying to chase a target it's already sharing a row with.

Checking whether a bullet's row would pull the sub back, since bullets only count in the front columns and miss the dodge block at column 9 to 8.

I'm checking the dodge case again: a bullet at column 7 leaves only one step of margin, but a sticky repeat of an upward move still carries the sub out of its path. The exceptions are row 1, where going up surfaces it, and the bottom row, where down does nothing. Including bullets in the pull would be cleaner.

Now I'm weighing whether bullets could be masked in the danger detector: a diver at column 6 would cancel a bullet signal at the same column, so I'm considering weighting the bullet detection at columns 5 and 6 separately.

Weighing a half-weight on the bullet terms at column 6, so a bullet's signal is strong enough to trigger a dodge but a diver there only partly cancels a real enemy threat.

Weighing whether to fold the bullet terms into the pull toward each row, so the sub doesn't drift back toward a row where a bullet is about to pass through columns 5 and 6.

Checking whether a bullet moving left through columns 5 and 6 could trigger the dodge logic before the sub has a chance to move back into that row.

Checking whether a bullet at column 5 would trigger a needless dodge when the sub returns to that row; the first shot should clear it within a couple of steps, so that's acceptable. I'm also estimating how often enemies spawning in row 1 go unhandled, roughly one in eight, and noting that the first-layer gating works out to a bias of about -50 per row.

Checking whether the sub's row-0 and row-1 behavior holds up, and whether the sensors leave a gap I'm missing. Oxygen runs down over the long wait, but the sub still has room to surface.

I'm looking at how divers at columns 8 and 9 pull the sub toward their rows, and timing the left-moving ones that wait at column 8 for six steps before reaching column 7. Right-moving divers reach column 8 later, so I'm checking when those arrive.

Now I'm weighing the diver pull for a right-moving diver at column 9, which would draw the sub toward a row it is about to leave, so I'm considering using the trail at column 8 to subtract that pull.

I'm adding a subtraction of the trail at column 8 to the pull terms, so right-moving divers at column 9 don't draw the sub toward their rows, and the same term keeps a right-moving diver at (s,9) from triggering a threat signal.

I'm testing whether the ch4 trail term at column 8 should go into the Q1 threat check too, but a left-moving enemy at column 7 would then look like no threat and I'd miss shooting it. Since a left-mover in my row at column 7 would mean I just entered the row, that case is rare, so I'll leave ch4 out of Q1 and keep the trail only in the pull terms.

I'm considering adding a fourth pull term at column 8 to cancel the attraction toward right-moving divers at column 9, since those are about to leave. The catch is that it would also repel toward enemies and might not cover the diver case cleanly. I'll check whether left-moving divers at column 9 still pull correctly.

I'm weighing whether to fold the ch4 trail at column 8 into the pull terms as a negative weight, which would stop right-moving divers at column 9 from drawing the sub away. The side effect is that a left-moving enemy at column 7 would start to repel the sub, but that only happens briefly as it passes, so it seems acceptable. The gain is maybe 5 to 10 percent of hunting time, against roughly 49 extra statements to write.

Still settling the pull terms: I'll cancel the attraction toward right-moving divers at column 9 by subtracting the column 8 trail, which means two statements per row pair instead of three.

Working out the final pull terms: I'll add a fourth weight at column 8 that cancels the attraction toward right-moving divers at column 9, since those are about to leave. Each row pair then needs just two statements, one for the threat gate and one for the list of eight weights.

Working out the numeric pull weights now, starting with the s=1 row pairs and their k and 2k values for each target row.

Still computing the pull weights for the remaining sub-pairs, filling in the values for the s=3 through s=5 rows.

Still computing the pull weights for the remaining sub-pairs, filling in the values for the s=6 and s=7 rows.

Still computing the pull weights for the last sub-pairs, filling in the values for the s=8 row.

Writing out the index ranges for the pull weights now.

Still writing the weight table for the pull terms...

Still listing the index ranges for the Q1 threat check across the sub's row, with the column-by-column offsets set out.

Still computing the weight table: the threshold for the shared pull terms and the bias values for each query, and checking the row-0 indices for the no-run case.

Checking the initial alignment: pressing right at row 0 four times, I want to confirm the row-0 dive trigger doesn't fire while the sub is still lining up.

Now I'm checking whether the sub's movement keeps it out of the wrong rows, and I'm confirming that the left and right presses stay quiet during normal play, since the logit gap should make stray moves rare. Looking at the upward case next, I'm noting that an idle sub at row 1 stays put, but the bigger worry is a sticky action that keeps firing after the sub has already realigned.

Still checking how the second-layer pull terms line up with the sub's row, and how the initial right presses at row 0 might trigger an early dive.

Still checking the pull terms for the diver columns, and whether the trail at column 8 needs its own weight so right-moving divers at column 9 don't draw the sub away.

I'm checking how an enemy moving right in an adjacent row, arriving at column 7 while I sit idle, gets blocked by the diver pull and then passes column 8 without touching me, which only costs a kill if I wanted to enter that row. I'm also starting to look at enemies spawning in my row.

