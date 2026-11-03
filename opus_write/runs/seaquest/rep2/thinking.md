I'm starting to plan a hand-designed policy network for MinAtar Seaquest, a 600-32-32-6 tanh MLP, and first want to get the game mechanics straight. The grid is 10x10, and the sub starts at the surface at x=5, facing left, so its back is at x=6. Its y position runs from 0 up to the bottom row.

I'm working through the Seaquest mechanics now: enemies spawn on rows 1 to 8 from either edge, and their timer means they step every 6 frames at the initial move speed, dropping to every 3 frames as the speed ramps down to 2. Spawns come every 20 frames at first and tighten by one frame per surfacing, while divers appear every 30 frames and enemy shots fire every 11 frames, travelling one cell per frame.

I'm checking how oxygen runs down while the sub is below the surface, and how surfacing with a full load of six divers resets the diver count, which in the code seems to drop it to -1.

I'm checking what happens when the sub surfaces with a diver count of -1: the zero-diver terminal check doesn't fire, so surfacing just restores oxygen and pushes the count further negative. That looks like an edge case the code handles by accident, and I'm weighing whether reaching six divers is common enough for it to matter.

I'm checking the termination conditions next: hitting an enemy, running out of oxygen, or surfacing with no divers. I'll keep the sub off the top row unless it has at least one diver.

I'm reasoning that the sub is safe at the surface, since enemies and their bullets never reach row 0 and oxygen doesn't drain there, so it could stay put for the full episode and score nothing. That makes me wonder what actually earns points, so I'm weighing how to get kills without giving up that safety.

I'm trying to recall how well DQN-style agents actually score on MinAtar Seaquest, and what the published numbers look like in the original paper versus later comparisons.

I'm weighing how much a hand-built policy can realistically score on MinAtar Seaquest, since typical RL baselines land somewhere around 5 to 20 points. My working goal is to maximize the mean score, so I'm sketching a heuristic. Shooting is the main point source, and a bullet fired along the sub's row travels one cell per frame, so an enemy in front of a facing sub can be hit before it moves much.

I'm checking how enemy subs in the sub's own row threaten it: they fire a bullet every 11 frames that moves one cell per frame toward it, and since friendly bullets don't cancel enemy ones, that's a real hazard to track.

I'm checking how an enemy bullet can catch the sub: it hits if it lands on the sub's cell before or after it moves. If the sub steps toward a bullet they can pass through each other, and if it steps away the bullet keeps closing in until the sub changes row, so dodging means getting out of that row.

I'm going over how divers get picked up: the sub has to reach a diver's exact cell, and divers drift sideways every 6 frames while spawning every 30 frames at a random row. Oxygen gives a 200-frame budget, so I need to collect at least one diver each cycle to keep surfacing legal.

I'm checking how divers get picked up: the sub collects one when they share a cell, and that happens whether the sub moves onto the diver or the diver drifts onto the sub. Shots pass over divers without hitting them, so I can fire freely while hunting for them. For collisions with enemy subs, only the sub's front cell matters, not its back.

I'm noting that a diver-collecting sub's collision check only looks at its front cell, and that the difficulty ramps up as the sub surfaces more often, so enemies spawn faster and move quicker over time. I'm now asking what a simple policy can realistically earn before that ramp takes over.

I'm estimating that spawns come roughly every 21 frames at the start, so about nine or ten enemies would appear in one 200-frame oxygen cycle. Killing most of them would be worth around nine points, but without collecting divers the total stays capped at whatever I can shoot down in that window.

I'm considering a simpler approach: pick a row, face one way, and fire, though that only covers about an eighth of the enemies and leaves me exposed to threats from behind. Tracking enemies by moving to their row and firing at them looks better. I'll also keep in mind that a hand-built policy has to fit a small 32-unit MLP.

I'm considering whether a single hidden unit can detect an enemy and the sub sharing a row, using the tanh to build the conjunction in the first layer instead of spending a unit per row.

I'm listing what a workable policy needs to know: how far the sub is vertically from the nearest target, whether an enemy sits in its row so it can turn and fire, how to avoid enemy bullets and collisions, and when to head up to surface with oxygen running low.

I'm weighing a simple policy that sits in one row and shoots at whatever comes along it, but enemies entering from behind would hit before I could turn, so I'd need to face them quickly.

I'm checking how a bullet fired left from the sub's cell reaches an enemy that's approaching from the left: the bullet moves one cell and tests for a hit, so a target right next to the sub dies immediately. I'm also noting that the enemy gets its own movement and collision check after that, so I still need to see how the order of those updates plays out.

I'm checking how enemy subs in the same row threaten the sub: their bullets move one cell per frame toward it, and the same bullet-first update order applies there too.

I'm checking how an enemy sub in my row would threaten me: it fires about every 11 frames, and its bullet crosses the row in under nine, so I'd need to kill it quickly or step out of the row.

I'm noting that enemy bullets leave no trail, so the danger channel can't show which way a bullet is moving, and a single frame won't tell me whether a bullet is coming toward the sub or away from it.

I'm noting that enemy bullets carry no direction on screen, so a single frame can't tell me whether a bullet is heading toward the sub or away from it. My guess is that a bullet in a row moves the way that row's enemies move, but a new enemy spawning the other way could make that wrong.

I'm settling on the idea that a fixed-row strategy is too brittle, since enemy bullets carry no direction on screen and can't be told apart by heading from one frame. I'm weighing whether to treat any enemy bullet in my row as a threat and dodge vertically, but that's only a conservative fallback. Designing a full tactical policy within the hidden-unit limit looks hard, so I'm considering a more constrained approach.

I'm now weighing a fixed-row strategy: keep the sub in one row near the surface, shoot whatever enemies come through it, and grab divers that pass by. The catch is that only about an eighth of the spawns land in any given row, so a single row won't generate enough divers or kills to sustain surfacing, even though it makes the features much simpler to express.

I'm considering whether to split the conjunction across units: one unit per row flags an enemy in the sub's row, and the relative column would need its own unit to tell left from right.

I'm weighing a column-weighted sum per row, so the enemy's column minus the sub's column gives the sign of left versus right in a single linear unit, with a gate to make sure they share a row.

I'm working out whether a single unit can gate on the sub's row while also carrying the enemy's column relative to the sub's. With the gate off, the enemy term alone should push the unit toward saturation, but when the sub is present and no enemy sits in that row, the subtraction of the sub's column still reads as "left," so presence has to be handled separately.

I'm weighing a layout where each row gets its own pair of units: one for whether the sub sits in that row, and one for whether an enemy is in that row coming from a given side. Layer two would then combine the two per row, but that spends most of the 32 units on row bookkeeping before any real policy logic fits.

I'm weighing whether layer two can combine per-row flags into a single "sub and enemy share a row" detector. Summing the sub-in-row and enemy-in-row units and thresholding looks like it fails when the sub and the enemy sit in different rows, so that exact-match detection doesn't work that way.

I'm weighing whether layer one can handle the same-row check directly: a unit per row that fires only when the sub is in that row and an enemy is there too. Layer two could then OR those per-row units into a single "enemy in my row" signal.

I'm looking at a per-row unit that combines whether the sub is in that row with whether an enemy is there, so the sub's row can gate the detection. For left versus right, I'm considering using the sub's facing, which might be readable from its front and back cells across the two channels.

I'm checking whether the facing direction can be read from the sub's front and back cells, but telling them apart needs channel 4, and the trail from other objects muddies the column sums.

I'm checking how the sub's facing direction shows up in the grid: the back cell sits one column behind the front, but channel 4 is what tells the two apart. At the edges, the back cell would land at column -1 or column 10, which means a wrapped index or an out-of-range error.

I'm checking whether the sub can ever sit at an edge while facing the wrong way, which would make the back-cell index wrap or fall off the grid. Moving left always leaves the sub facing left and moving right always leaves it facing right, so at x=9 it must be facing right and at x=0 facing left. The only exception is the starting position, which is fine. So the back cell never goes out of range.

I'm checking the orientation from the sub's back cell, which should sit one column behind the front. Working out whether a linear sum over the trail channel can isolate that cell, since other trails may muddy the column totals.

I'm considering whether the sub's orientation can be read without a per-row conjunction, since the trail channel from other objects in the same rows blurs any column-weighted sum. Another option is to skip orientation entirely: turn toward an enemy in my row first, then fire once it's aligned, though moving closer makes that riskier.

I'm considering whether the orientation can be read off the trail channel, but other trails in the same row muddy the column-weighted sums. The contamination is worth checking concretely, since that determines whether a linear unit can tell facing direction at all.

I'm now thinking about having the policy keep its orientation consistent by construction, such as facing toward the center of the screen based on which half the sub is in. Another idea is to drop orientation tracking altogether and rely on the sub's column position as a proxy.

I'm stepping back to a different approach, an edge-camping strategy, where the sub sits near the screen edge. But placing it at x=0 fails because enemies spawn there and would collide with it, so I'm considering x=1 facing right, where enemies coming from the left would have to reach it.

I'm thinking about camping near the center and shooting at whatever comes along the sub's row, but enemies can come from both sides there. Vertical dodging could help avoid threats, and firing when something is in front is the simplest scoring idea. I'm wondering how well a small 32-unit MLP can actually do on this, and what benchmark results for MinAtar Seaquest might look like.

I'm picking the vertical target next: the row of the nearest diver when oxygen is low, or another row otherwise, and the rest of the policy hangs off that choice.

Now I'm looking at the vertical side of the policy: the target row should be the nearest diver's row when oxygen runs low, otherwise something else, and I'm thinking about whether a linear unit can express "above or below the sub" by comparing the target row to the sub's row.

I'm weighing whether the vertical target can be expressed as a weighted sum over target rows minus the sub's row, but the count of targets varies, so that product can't be built linearly. I'm considering per-row units keyed to the sub's row instead, since the sub's position is already readable from the input.

I'm checking whether one unit can express "a target sits above the sub" for every sub row at once. The weights would have to depend on the sub's row, and a single linear unit can't do that, so I'm considering one unit per threshold instead.

I'm working out whether the "target above the sub" signal can be built into the first layer, by letting each unit combine the target count in rows above a threshold with a term for the sub being in that row. That would avoid needing an OR over ANDs in the second layer.

I'm working out whether one unit per sub row can flag a target above or below the sub, with a parallel set for enemies in the sub's row. That lands around 24 units in the first layer, which is tight but possible, and the open question is how to prefer the nearest target when there are targets on both sides.

I'm working on the vertical pull signal: one unit per sub row, weighting targets above or below, with a gate that keeps the output from being ambiguous when the sub is not in that row.

I'm working out the sign of the vertical pull for each sub row: a pair of units that flip the target-row sum for targets above and below, so both stay at -1 when the sub is elsewhere and their difference only carries signal in its own row.

I'm noting that a single per-row unit could fold the sub's row into the sum, so the baseline term sits at a fixed offset and the remaining signal depends only on the tanh of the row's pre-activation.

I'm checking that the summed units give a clean signal: once the sub is in one of rows 1 through 8, the total across row units reduces to a constant plus tanh of that row's pre-activation, so the layer-2 bias can absorb the constant. The surface row gives a different total, which I'll need to handle separately. The saturation step depends on the gate strength being large enough against the input magnitude.

I'm looking at whether the per-row units can each carry a signed signal for the sub's own row, since the sum over rows then collapses to one scalar that depends only on that row's pre-activation.

Layer 2 can weight each per-row unit separately, so it can treat rows differently, though only the sub's current row's unit moves off its saturated value. I'm also wondering whether the column-relative features, like an enemy to the left or right of the sub in its row, need their own comparison.

I'm checking whether an enemy's left-or-right position relative to the sub can be read off a single row unit, but the column sum breaks as soon as there are several enemies or none. Using the enemies' motion direction as a proxy looks more promising, though I'm not sure it holds up.

I'm working out how an enemy in the sub's row could be told apart as threat or harmless from its motion direction and its trail, since a right-moving enemy leaves its trail one cell behind it.

I'm considering keeping the sub at a fixed column, such as the far left, so enemies in its row only come from one direction and no relative-column comparison is needed.

I'm checking the edge case where the sub sits in column 0: an enemy spawning on the same cell would kill it, but only if the sub doesn't move away first in that step. The spawn chance works out to roughly 1/16 per spawn, so over a couple hundred frames that adds up to several close calls.

I'm considering whether the sub at column 1 facing left could catch an enemy spawned at column 0, since a shot would reach it in one step, though the cooldown could block that. Keeping the sub off the edge column also avoids spawn collisions, but an enemy from the right side would still need the sub to turn around.

I'm weighing a fixed-column strategy, keeping the sub near the center and only shifting one cell to turn around. That would sidestep the relative-column problem, since the sub would only ever occupy two known columns.

I'm weighing a two-state scheme where the sub alternates between columns 4 and 5, so it always occupies those two cells and only the orientation changes. The catch is that the sub's front and back look identical in channel 0, so I'd have to lean on the trail channel at one column or the other to tell which way it faces. That signal can be muddied by enemy or diver trails sitting right next to the sub.

I'm weighing whether to keep the sub in columns 4 and 5, since then only the trail at one of those cells would show which way it faces. An enemy trail could sit at the back cell only if an enemy had just come from there, which seems rare and harmless. I'm also setting aside the tight column restriction and leaning instead on a column-independent heuristic for horizontal choices.

I'm weighing how much each score source matters: kills keep the points coming, and staying alive long enough to kill is what lets the sub collect divers and keep up its oxygen. A run that just holds out one oxygen cycle and racks up a handful of kills is worth maybe five points, while a clean surface-and-dive cycle adds more, though the harder waves cut both ways. Looking at what other agents reach on this game, a small MLP like this one probably lands well below the convolutional baselines, so I'm aiming for something around ten.

I'm settling on a center-column strategy where the sub moves vertically to line up with the best target, since enemies at the edges need about 24 to 30 frames to reach it. Turning and firing takes only a step or two, and bullets are fast, so this should keep the sub mostly out of danger.

I'm working out the timing of enemy sub fire: a newly spawned enemy sub that starts at x=9 and fires after about 11 updates, so I'd have a short window to kill it before its first shot.

Working through the enemy-sub timing: a sub spawned at x=9 fires its first bullet around frame 11, and that bullet would reach the middle columns by about frame 14. If I enter its row and fire early enough, my shot can beat its first volley; otherwise I'll have to dodge. A hand-built policy won't handle every case, so I'm aiming for something robust rather than perfect, with the main priority being not to surface empty-handed.

I'm weighing the diver-collection problem now: divers drift one cell every six frames in a random row, so I'd need to line up vertically first and then close the distance horizontally. I'm wondering whether to prioritize divers early in each oxygen cycle or grab them whenever they're convenient, since the full policy has to juggle target selection, facing, firing, danger avoidance, and surfacing within the unit budget.

I'm thinking about gating groups of hidden units by sub row, so each row gets its own features about the sub's situation, with the surface case handled by all gated units sitting at -1.

I'm sketching the next feature group: a vertical-pull feature that pushes the sub toward targets above or below its row, weighted by distance and boosted when oxygen is low and divers are on hand. I'm also considering a second, horizontal feature for enemies in the same row, but I'm not yet sure how to encode the sub's relative column into it.

I'm trying to make a single linear feature track whether an enemy sits left or right of the sub, but the presence problem gets in the way: with no enemy, the sub's column term still pushes the value away from zero. Weighting the sub's column by enemy presence would fix it, though that means a product, which the layer can't express directly.

I'm checking whether a single linear feature can capture an enemy's side relative to the sub, but the sub's column term pushes the value off zero even when no enemy is present. Keeping the sub confined to columns 4 and 5 would make the enemy's column alone decide the side, which would avoid that problem.

I'm noting that divers can be collected without chasing them: if the sub holds a row near the center, a diver drifting along that row will eventually reach the sub's front cell. The open question is whether the back cell matters for pickup, since the sub's front and back are what would need to line up with the diver's path.

I'm noting that a diver spawned at the edge needs roughly 25 to 30 frames to drift to the center, so a sub camping there can wait for divers to come to it. A diver moving across the sub's row only gets picked up when it lands on the front cell, which can also happen if the sub turns toward it, so the timing is worth tracking.

Divers spawn about every 31 frames and each needs roughly 25 to 30 frames to drift to the center, so a few arrive over the 200-frame oxygen budget. I only need one diver per surfacing, and any extras I collect act as a buffer, since surfacing removes just one.

I'm working out when to start surfacing: the oxygen bar shows one cell per 20 frames, and rising from the deepest row takes about 8 frames, so I'd want to begin surfacing once the bar drops to two cells to leave a safe margin.

I'm checking the surfacing margin against the oxygen bar, weighing whether starting to rise at two cells is worth the cost of spending a diver earlier. Oxygen drops by one per frame underwater, so the terminal check happens before each decrement, leaving roughly 201 frames from a full tank. The remaining question is whether rising through rows with enemies in them is safe enough to take that route.

I'm laying out the danger check for a vertical move: before stepping up or down, I need to look at the cells just beyond the sub's row near its fixed column band. Since the sub's row varies, I'd fold that check into each row's own unit so the whole policy is built from per-row pieces.

I'm checking whether the sub can hold its column band through sticky actions: a repeated right-turn from x=5 would push it to x=6 while still facing right, so the policy needs to know the absolute column to correct back into the band.

I'm now asking how the sub could tell which side an enemy is on without a fixed column band, since pressing left or right also changes its facing and the column could drift past the band through sticky repeats. One option is to lean on facing plus the line of fire: an enemy counts as in front if it sits past the sub's column in the direction it faces. I'm weighing that against reading the threat from the absolute column, and I haven't settled which is more robust.

I'm sketching a per-row unit that should fire when an enemy sits to the left of the sub in that row, using column-weighted sums over the enemy and player channels. The open question is how to set those weights so the sign depends only on enemy position relative to the sub's column.

I'm working out how to get a single threshold unit to fire only when some enemy in the row sits to the left of the sub's column. A weighted sum over the row's cells can order enemies by column, but on its own it gives a positive value even with no enemy present, so I still need a presence term to gate it.

I'm stuck on the same wall: a single threshold on a fixed weight per column can't mean "enemy left of the sub" for every possible sub column, since each column would need a positive weight and a negative one at once. Adding a sub-column-dependent term g(c_s) might compensate, but then multiple enemies could still combine in ways that break the rule.

I'm testing a single threshold unit with weights that decrease with column, and it works for one enemy since the bias can be set to match the sub's column. Two enemies on opposite sides could cancel each other out, though, which would give a false negative.

I'm checking whether a single threshold unit can work with positive weights for the columns left of the sub. Requiring those weights to be positive for every possible sub column runs into the false-positive case when no enemy is present, so I'm testing whether a presence gate could resolve that.

I'm checking the threshold constraints: the weights have to decrease with column so that an enemy on the left crosses the threshold while one on the right does not, and the bias has to keep the no-enemy case below it.

I'm checking how the threshold behaves when several enemies sit to the right of the sub, since their weights add up and could push the unit past its threshold, giving a false positive. Within one row there are usually only one or two enemies, so the case may be rare enough to accept, though it would worsen as difficulty rises.

I'm reconsidering the per-row approach, since separating enemies from divers and bullets across every relative position gets expensive. A fixed-column layout should be much simpler to build.

I'm weighing a fixed-column layout, where the sub stays put and simply turns between facing left and right, against letting it wander. One version has it never turn at all, but then it can only fire leftward and enemies from the right would reach it. Parking it at the edge column doesn't help either, since bullets fired outward leave the screen.

Checking the edge columns next: starting at x=0 facing left leaves no room, since anything spawning at x=0 hits immediately, and starting at x=8 facing left just moves the problem to x=9.

I'm settling on a two-state center scheme: one state at front column 4 facing left, the other at column 5 facing right, with the sub switching between them to face whichever side the threat is on. If it needs to face the other way, I just press the turn key, and if it's already facing the threat, I fire.

I'm noting that the two states already tell the network which way the sub faces, since the trail sits at column 5 in one and column 4 in the other. The catch is that the trail channel also lights up in other rows at column 5, so reading it reliably means gating on the sub's own row again, or folding that gate into each row's unit.

I'm weighing whether the sub's own orientation can be read from the grid: the trail sits at column 5 in one state and column 4 in the other, but that channel also lights up at column 5 in other rows, so I'd need to gate on the sub's row again or fold that gate into each row's unit.

I'm considering whether the starting column could itself encode orientation, with the sub at column 4 facing left and column 5 facing right, so long as only the two turn-and-step moves are used. The reset state (5, facing left) breaks that pairing, so I'd need either a single initial left press or a different column pair to keep the invariant.

I'm checking whether the band {5,6} can work for orientation, but both states occupy the same two cells, so the occupancy alone can't tell them apart. The front/back split would have to come from the trail channel, which brings back the same row-gating problem. I'll try a wider band of {4,5,6} to see whether the cell pattern separates the states.

I'm checking whether ch4 in columns 5 and 6 can tell the two states apart without row gating, but the difference flips sign only in the sub's row, and trails from enemies and divers in those central columns contaminate the sum across the whole grid. So a per-row gate looks unavoidable.

I'm trying a three-column layout where the front column itself marks the facing direction, with the two states occupying different cell pairs. The transition from one state to the other passes through an intermediate position, so I'm checking whether that intermediate state breaks the encoding.

Checking whether the cell pair alone can encode orientation: the same two adjacent cells can mean either facing, so the occupancy never settles it. That leaves the trail channel, which brings back the per-row gating problem I was trying to avoid.

I'm wondering whether the back cell can be found by summing across rows instead of gating each row: a column-wise sum of the trail and sub channels might hit a threshold only where the sub's back sits. That would avoid a unit per cell, though a single enemy trail coinciding with the sub could still throw it off.

I'm looking at whether the sum over a column could tell a back cell apart from trails, but it stays ambiguous whenever enemy trails share that column. Now I'm considering per-row units that handle orientation within the sub's own row, so the orientation check and the enemy check can share the same gating, and I'm working out what a linear function inside one row can encode.

I'm weighing the per-row budget again: 32 first-layer and 32 second-layer units, so I'll look for a cheaper policy. A simple row-sweeper that stays in the center and moves up and down to track enemies and shoot seems like the natural candidate.

I'm estimating how often a blind patrol would hit an enemy: with about three enemies on screen across eight rows and ten columns, any given center cell is occupied only around 4% of the time, so random movement would still die quickly.

I'm now thinking about a per-row gated design, since the sub's row has to be known to read the danger around it. Layer 1 could compute a separate gated unit for each row, though that costs a lot of units. I'm weighing whether a cheaper way to handle vertical movement exists, since the sub needs to see rows above and below it.

I'm giving each per-row unit the freedom to read the rows above and below with its own weights, which gives four features per row. That uses all 32 first-layer units, so global signals like low oxygen and diver count would have to be folded into each row's linear function instead.

I'm checking how the oxygen bar and diver bar share row 9, since the oxygen fill can reach column 9 and collide with the diver cells.

I'm checking how the oxygen fill and the diver bar share row 9: once oxygen is high enough, its cells cover the diver bar's columns, so the diver count can't be read reliably.

I'm checking that cell (9,8) only lights up for the diver bar while oxygen stays at or below eight cells, which is true whenever oxygen is low, so the diver count can be read exactly when the surfacing decision needs it. When divers are absent I still need to pick one up before oxygen drops, and with at least one diver I'd like a spare, though that's less urgent.

I'm now checking the start: the sub begins at row 0 facing the surface, so it has to dive first. With no divers, going up from row 1 would end the episode, so the "up" move has to be blocked there unless oxygen is low and a diver is in hand.

I'm checking the sticky-action risk: if the sub is at row 2 and moves up to row 1 with no divers, a repeated 'u' would send it to the surface and end the episode. So moving into row 1 without a diver looks unsafe.

I'm checking the rule for when the sub may enter row 1: with no divers in hand, that move is off limits, since a repeated up-press would carry it to the surface and end the episode. Only when oxygen is low and a diver is aboard does the surfacing move make sense. At row 0 with the surface flag unset, the surfacing step refills oxygen and uses up one diver, after which the sub should go back down.

Next I'm checking the dive from row 0: stepping into row 1 is only safe if no enemy sits in the column below, so I need a danger check on the row beneath the sub before committing.

I'm now asking what happens when the sub sits in row 0, since that row has no per-row unit of its own. A row-0 gated unit, or a fixed-column danger feature for row 1, would let the sub decide whether diving is safe.

I'm sorting out which per-row signals the sub needs: vertical moves depend on enemies and divers in other rows, the danger in adjacent rows, and oxygen for surfacing, while horizontal facing and firing depend on what sits in the sub's own row. I'm starting to think each row could carry a single vertical-preference value that points up, down, or stays put.

I'm weighing whether one scalar per row can carry the up/down/stay choice, with large weights making danger above block upward movement without forcing a downward one.

I'm laying out one scalar per row for the vertical choice, where a large positive value means up, a large negative value means down, and near zero means stay, with danger above pushing it negative. A second scalar per row would handle horizontal turning and firing, and a third would track which way the sub faces within its row.

I'm checking whether a single row's features can tell which way the sub is facing. Summing trail positions with weights gives a clean sign only when no other trails share that row, so this encoding breaks down in crowded rows and I'm looking for a more local way to read orientation.

I'm wondering whether the projectile channel could reveal facing: a bullet appears in front of the sub after firing, so its position relative to the sub would show which way it points, and it would be far less cluttered than the trail channel.

I'm now working through the orientation problem: a row's trail features get mixed with any other trails in that row, so the facing estimate breaks down when an enemy shares the sub's row.

I'm considering whether the sub's facing direction can be read from only two columns, say 4 and 5, so the orientation signal is a simple difference between those two cells in each row. That would limit the contamination from trails sitting elsewhere in the same row, though any trail exactly at those columns would still throw the reading off.

I'm checking that the sub stays in columns 4 and 5, since a trail at either cell would only come from an object moving away, so the orientation reading stays mostly clean. The catch is that the policy has to keep the sub in that pair, and sticky actions or deliberate moves could push it to other columns, where the reading would break.

I'm working out the horizontal control now: if the front is at column 3 or left of it, pressing 'r' moves the sub right, and two presses take it from the left drift to the home state at (5,R). From column 6 or further right, two 'l' presses bring it back to (4,L). The two home states both occupy cells 4 and 5.

I'm checking the horizontal homing rule: if the occupied cells are {3,4}, pressing 'r' moves toward the home state at (5,R), and if they're {5,6}, pressing 'l' moves toward (4,L). Either way two presses land in the safe pair of columns.

I'm considering whether the horizontal rule can rely on global column features: a sum over rows of ch0 at columns 0 to 3 signals the sub is left of home, and columns 6 to 9 signals right of home. That avoids any per-row gating. Facing at the home position is the harder part, since it would mean comparing columns 4 and 5 within the sub's own row, which brings back the row-gating problem.

I'm weighing whether gating the orientation signal per row by the sub's home cells could keep the trail contamination down, and I'm checking how the danger and trail channels line up in each row.

I'm noticing that a single bias term can't separate the "absent" case from facing right, since both land near -1. So I'm considering shifting the present-case values with an offset so that facing left, facing right, and absent each map to a distinct value.

I'm working out the orientation signal for each row: when the sub sits at home, a row-level unit can give the two facing states distinct values, and a shift keeps the absent case from colliding with them. Summing those per-row units would then let a later layer read off which way the sub faces.

I'm settling on the layout for the sub's local situation: whether there's danger on the left or right of its row, and whether it's facing left or right, which decides when to fire.

I'm settling the escape logic for the sub's row: when an enemy sits on the side it isn't facing, it should turn to face it, and when one is on the side it faces, it should fire. If enemies sit on both sides and both are close, the sub should shoot one and then move vertically to get clear. Incoming enemy bullets in the sub's row are the other threat, so it has to dodge those vertically rather than trade shots.

I'm now thinking about how the network could tell fish apart from enemy subs in a row, since that decides whether dodging or shooting is the right response.

I'm sorting out how to tell enemy subs from fish, since the representation merges them, so the policy will treat all enemies alike and dodge bullets. Bullets and enemies can be separated through the danger and reward channels, but a diver lands on the opposite sign, so a plain row sum mixes them together.

I'm now separating the threat types: an enemy and a bullet both show up as danger, so on the left side I'll treat any danger as a threat, shooting it if it's an enemy and dodging if it's a bullet, since a bullet closing in is what I need to get out of the way of.

I'm weighing how to dodge bullets without an exact timing: a bullet at distance 3 reaches me in three frames, and with sticky actions a dodge can be delayed, so I'd start moving vertically once a bullet is about two cells away. Since bullets only travel horizontally, I can't remove the threat by changing rows, so the dodge has to clear the bullet's row. Enemy subs fire roughly every 11 frames, which leaves a gap between shots to line up on them.

I'm now turning to vertical targeting: deciding which row the sub should move toward, based on where enemies and divers are relative to its current row.

I'm now weighing how a per-row unit can encode whether a target sits in the sub's own row, since that signal should override any vertical move.

I'm deciding whether a target in another row should pull the sub toward it. Enemies can be shot from behind as long as the sub faces them, and diver chasing is fast enough to be worth it, though a diver that has already moved past the center would take some pursuit.

I'm going to keep the simplest version: rather than separating approaching divers from receding ones, I'll treat any diver in any row as a target and let the sub move toward it.

I'm still working out how the target selection stays safe, since moving into a neighboring row means the cells at columns 4 and 5 there have to be clear of danger first.

I'm checking whether the vertical move would walk into a danger: an enemy one row over, a few columns from mine, could step into my column before I get there. The per-row unit would need a penalty for danger in those neighboring cells, but a single scalar can't capture both "blocked above" and "should go down" without tangling the two signals together.

I'm laying out the vertical units now: one that fires when moving up is safe and useful, one for moving down, and a horizontal and orientation unit per row, which comes to about 24 units for rows 1 through 8.

I'm settling on how layer 2 reads the per-row units. If a feature's layer-1 unit takes a value, I'm working out what that value would look like when layer 2 sums it, since tanh can make multi-level coding fragile.

I'm checking how the per-row units combine in layer 2: each row gives the same weight, so the summed contribution works out to a row-agnostic scalar that stays the same whichever row the sub is in.

I'm checking whether the per-row units can carry a graded signal: if each unit outputs one of three levels, layer 2 could read it with two thresholds, but that only holds if the levels stay cleanly separated once several terms are added together, which gets messy quickly. So I'm leaning toward keeping each per-row unit to a simple on/off detector.

I'm considering whether to spend separate units on enemies to the left and right of the sub in its row, or to fold both into one signed code. Folding them together collapses "none" and "both" into the same value, so I'm weighing whether a combined encoding can still tell those cases apart.

I'm checking whether "enemy in front" can be a single linear threshold over the orientation bit and the left and right enemy counts, or whether it's an XOR-style case that needs more than one unit.

I'm checking whether "enemy in front" can be one linear threshold over the orientation bit and the left and right enemy counts. Testing the four cases where the orientation bit is on and the four where it's off, the combination of the two counts can't be separated with a single weighted sum, so it's an XOR-style case that needs more than one unit.

I'm checking whether "enemy in front" can be built from layer-2 units that combine a per-row orientation signal with the left and right enemy signals, since a single threshold over those three won't separate the cases. Splitting it into an "A and left enemy" unit and a "B and right enemy" unit would handle it, though that's more units than I'd like.

I'm trying to see whether the vertical targeting can avoid per-row gating altogether, for example by comparing the sub's row against the rows of targets using global linear features, though an exact comparison of the nearest target's row with the sub's row looks nonlinear.

I'm trying to find a way to express "target above me" without products, since comparing the sub's row with target rows is nonlinear. One option is per-row threshold indicators of the sub's row, which would still need layer 2 to combine them with target indicators in a way that gets messy quickly.

I'm comparing two ways to flag vertical targets: a set of units for each pair of sub row and target rows, which gives about 14 units, versus a per-row version that costs about 16, so the two come out roughly even. The per-row version looks more flexible because its weights can depend on distance. Adding in the orientation units, the total budget is starting to get tight.

I'm trying to fit the orientation and enemy-in-front signals into fewer units, since the per-row budget is running over. One idea is to fix home positions so that the two facing states occupy different cell pairs, which would let the board itself reveal orientation without a separate unit.

I'm checking whether the two cell pairs can tell the facing states apart: the intermediate state after one turn press also occupies columns 4 and 5, so from that pair alone the network can't tell it apart from the starting position.

I'm checking whether the intermediate state after one turn press, at columns 4 and 5, can be mistaken for the starting position, since it occupies the same cells. If the network misreads it and keeps pressing the same way, the sub could get stuck facing the wrong direction. A sticky move back from the other home position produces the same ambiguity.

I'm considering whether the sub could alternate facing left and right each cycle, firing both ways, so the occupied cells would show both orientations. The five-frame cooldown between shots would make that pattern awkward to time, though.

I'm considering a variant where the sub alternates facing left and right every few frames, firing each time, so both orientations show up in the occupied cells. With the five-frame cooldown, though, a shot every ten frames in each direction could still hit an approaching enemy, since it stays in its fixed row while closing in.

I'm noting that if the sub is in the same row as an enemy, the next shot kills it unless a closer enemy gets hit first, so it only needs a few frames of alignment. Alternating fire would avoid needing orientation, but the network has no memory to run a timed cycle, so it would have to infer the phase from the bullet's position, and the bullet's direction isn't visible.

I'm considering whether a bullet's position in the sub's row could reveal which way it was fired: bullets to the right would mean a rightward shot, and bullets to the left a leftward one. I'm also weighing a stochastic policy that picks left, right, or fire at random when the orientation is unknown, though moving left while facing left would bring the sub toward an enemy.

I'm weighing whether to fold the orientation signal into the per-row left-enemy unit, so one neuron yields distinct levels depending on both whether an enemy is on the left and which way the sub faces.

I'm considering a graded encoding where the per-row enemy unit's output shifts with the orientation bit, so one value distinguishes enemy-on-left from enemy-on-left-while-facing-left. The output levels would be separated enough for a layer-2 threshold to pick them apart, though the margins are tight and multiple enemies could blur them.

I'm weighing a saturating version of the left-enemy unit, since with two enemies on the left the count would push the orientation-shifted level into the wrong band. Another option is to restructure around the multiplexing problem, letting the orientation choose which side's window is read.

I'm considering whether the orientation can be computed globally, without gating per row, by summing trail and cell channels across all rows in columns 4 and 5. The difference between the two columns would then track which way the sub faces, though other trails in those columns would add some contamination.

I'm estimating how often trails land in columns 4 and 5 across the other rows, and whether the difference between those two columns is mostly noise from moving objects rather than a real signal about facing.

I'm weighing whether the orientation can be read from a single column rather than per row: a "back" cell in the sub's row would be a true signal, but other rows' trails and objects in column 5 would add false positives, so summing across rows looks unreliable.

I'm wondering whether the sub's vertical range could be restricted to a few rows, which would cut the per-row cost, though I'd still need all eight rows if it can move freely. The more promising direction is a front window defined relative to the orientation signal rather than fixed absolute columns.

I'm weighing whether the sub can drift its way into a known orientation: if it presses 'l' from home, the column change would reveal which way it was facing before the turn.

I'm working out whether the sub can encode its facing direction through where it drifts: pressing 'l' from home lands it at {3,4} if it was already facing left, and at {4,5} otherwise. I'm now testing a scheme where each facing has its own preferred column, so the occupied cells themselves carry the orientation.

I'm noticing that if the sub just presses 'l' or 'r' based on which side the enemy is on, the occupied pair {3,4} or {4,5} could mean either orientation, so the network can't tell which way it's facing. Without some orientation signal, the policy can't be trusted to aim correctly.

I'm checking whether a policy can keep facing and column in step: if a pair like {4,5} always means facing left, the policy can never press 'r' from the states that would produce a right-facing sub at column 5. That leaves a conflict, since turning right from a left-facing home position seems to require exactly that move, so the convention needs to pair one left-facing column with another right-facing one.

I'm considering a stochastic workaround for the turning problem: when the orientation is unknown and the sub sits at {4,5}, it could fire with high probability instead of committing to a turn, though a bullet fired while facing right would travel the wrong way.

I'm considering using the bullet itself as an orientation cue: if the sub fires while facing right, a bullet would appear to its right in its row, so seeing that bullet alongside an enemy on the left would mean it's facing right and should press 'l'. The cooldown of five frames means nothing fires during the wait, and the bullet is visible for only a few frames before leaving the field.

Now I'm checking whether a bullet visible to the sub's right, while an enemy sits on the left, could signal that it's facing right and should press 'l', though that would still need the bullet's row checked per row.

I'm settling on per-row enemy units that also take an orientation input, so each row's left and right signals carry the facing direction as well.

I'm checking how the two output levels for the left-enemy unit separate, with the gap between 1.76 and the threshold at 1.9 being the tight part.

I'm checking whether a single shared orientation term could work, since with the enemy-count term large the two output levels land too close together to separate once several enemies are on the same side. Swapping the weights, with the orientation input made the bigger one, might keep the levels apart.

I'm checking whether counting enemies per side could collide with the orientation levels: with two enemies on one side, the count term might land on the same value as orientation alone, so I'm looking for a weighting that keeps the codes distinct even when several enemies are present.

I'm weighing whether counting enemy bullets alongside enemy subs in the same window would push the count to two and blur the orientation levels, and I'm testing weights where the facing term is larger than the presence term so that the levels stay apart.

I'm considering dropping the per-row layout and restricting the sub to a few rows, which would free up units for vertical targeting, though it would limit where the sub can move.

I'm sketching a vertical scheme where each row gets a signed pull unit that adds up the targets above and below, though the per-row cost keeps climbing.

I'm considering a vertical pull unit per row that sums targets above and below with distance-weighted signs, giving an up, down, or neutral signal from the output level. At the surface, where the sub is off the grid, that signal reads as "down," which might actually suit the start. A single vertical unit can't also handle blocked movement, so I'll need separate danger checks for above and below.

I'm folding the safety check into the vertical unit by pushing its value down when something is blocking above and up when something is blocking below. That works in the simple cases, but if the sub is boxed in on both sides the pull still leaks through, so I'll need to handle that case separately. Next I'm defining what "danger above" means: an enemy or bullet at the row above, near the column the sub would move into.

I'm working out which cells a sub moving up would need to avoid: the cell directly above at its front column, plus the neighbors on either side of it, since enemies and bullets in that row could slide into it this frame.

I'm settling on a surface rule: at row 0, if the danger cells in row 1 around columns 3 through 6 are clear, the sub dives; otherwise it waits. I'm also noting that the danger check for moving up has to cover those same columns, with a small margin on each side.

I'm settling the sub's homing and the main loop: first return it to home columns 4 and 5 with a press of 'l' from cells 5 and 6, then in its row dodge vertically if a bullet is close, fire when an enemy is on the facing side, and turn toward an enemy on the back side.

I'm weighing how to handle the sub's movement: if it's not at home it heads back first, then dodges vertically when a bullet is close, fires at enemies on the facing side, and turns toward enemies behind it. Otherwise it moves vertically toward targets, but never up to the surface unless oxygen is low and it's carrying divers. Waiting while the cooldown runs costs nothing, so pressing 'f' then just acts like a no-op. Diver collection will mean parking in the diver's row until it drifts over, and I still need to settle how horizontal movement fits into all of that.

I'm weighing a potential-field approach for vertical targeting, where each row's pull is a distance-weighted sum of targets in other rows, so the sub drifts toward the nearest concentration. Enemies and divers both count as targets there, since both are worth moving toward, with the weight falling off as the row distance grows.

I'm checking how a sub entering a row near an approaching enemy would fare: turning and firing takes a couple of frames, and the bullet and enemy closing in could meet in the same frame, so the timing matters.

I'm now checking the timing for shooting at close range: a bullet fired at an adjacent enemy still connects, since the bullet and the enemy meet in the same frame, so facing it and having the cooldown ready is what matters. Next I'm working out how enemy bullets affect this.

I'm working out the timing for enemy bullets: a shot from an enemy sub at distance d reaches us after about d-1 frames, so once I see a bullet coming in my row I need to leave before it arrives.

I'm checking the timing of an incoming bullet: if it's adjacent I have to move out of its row this very action, and at distance two I still have one spare frame. Since a sticky action could repeat my previous move, I should start dodging once the bullet is within about three cells, which means giving up the attack and coming back afterward.

I'm weighing how far the bullet check needs to reach: any bullet within about three cells in my row should trigger a dodge, and I still need a way to tell bullets apart from enemies in the per-row features.

I'm weighing whether to treat any enemy or bullet within two cells as a reason to dodge, since shooting from further away would avoid that. Splitting the row into left and right danger features still leaves a separate near-danger feature to track, which is getting expensive.

I'm settling on a short list of global features rather than piling up per-row ones, starting with oxygen: column 2 of the bottom bar lights up only when oxygen is at least three cells, so its being off is a clean low-oxygen signal.

I'm settling on combining the per-row danger features into front and behind categories using absolute windows, which should cut down the feature count, though I still need to check how that interacts with the orientation feature.

I'm trying to fold the sub's orientation into the per-row danger features, since "danger in front" depends on which way it faces and that's not a simple linear combination. One option is to add a signed term based on the trail channel at home columns 4 and 5, so the same unit can weight left and right danger differently.

I'm testing whether a single unit can separate the four cases by adding an orientation term to the left-danger count, so that danger in front of the sub sits well above the rest. The levels for "fire" and "nothing" come out close, so tanh squashes the separation and I'll need different weights.

I'm checking the orientation weighting on the left-danger unit: with two dangers on one side the saturated value can't tell facing left from facing right, so it would wrongly choose to turn, moving the sub toward the danger.

I'm checking whether a per-row orientation term can work: the back cell's column relative to the front. The problem is that the sub at (3,L) would read as facing right and turn back toward the danger, so the orientation signal has to hold even when the sub has drifted off home.

I'm checking whether orientation can be read straight from the trail channel: a front cell has no trail and a back cell does, but that needs a per-cell AND, and any trails near danger would throw off a row-wide sum. So I'm wondering whether the facing direction could be ignored and the sub made to alternate sides on its own, using the projectile channel as a cue.

I'm thinking about whether a per-row feature for "bullet fired on my own side" could replace the facing-direction term. The idea is to fire at an enemy on the left regardless of facing; if my bullet shows up on the right instead, I know I'm facing the wrong way and should turn left. I'd then fire again once the cooldown lets me.

I'm testing whether the bullet itself can act as the cue: if one of my bullets sits right next to the sub on the right side, I know I'm facing the wrong way and should press left, and once it moves away I can fire again.

I'm now weighing a turn rule that only fires when one of my own bullets sits just beside the sub in its row, since that bullet's position reveals which way I'm facing. The catch is that this per-row gating would need more units, and I still have to fold it into the left and right danger features without losing the multi-enemy cases.

I'm checking whether a per-row turn unit can AND "an enemy on this side" with "my bullet just beside the sub." Weighting the enemy count at 2 and the bullet at 4 with a bias of -5 gives a clean split: the only case that clears zero is one enemy plus the bullet, while two enemies alone stay negative.

I'm considering a fixed-row strategy instead: the sub stays in one row at its home columns, so every row-based feature becomes an absolute, linear unit with no gating needed. I'd then check how orientation affects the enemy-side features in that single row.

I'm considering a fixed-row strategy, where the sub camps in one row so every feature is a simple absolute cell lookup. The catch is that only about one in eight enemies would pass through that row, so the kill rate would be too low to sustain it. Splitting the work across two or three rows seems like the natural extension, but each row would need its own features.

I'm considering a layer-2 version of the same idea: layer 1 computes plain per-row left and right danger presence for all eight rows plus one-hot row indicators, and layer 2 ANDs each row's indicator with its danger unit. The output layer can then sum those layer-2 units, since exactly one row indicator is active at a time.

I'm laying out a layer-2 design where each row gets its own AND unit, so the one-hot row indicator gates the per-row danger presence. Since only one row indicator is active at a time, summing those units lets the output layer read "danger in my row" directly. The open question is whether the decision logic can stay linear in the logits or needs a conjunction inside layer 2.

I'm weighing whether the orientation can be folded into the per-row features at all, since each row would need its own gated units and that eats the budget. A fixed-row setup avoids the gating but meets too few enemies to keep the kill rate up, and the layer-2 conjunction approach doesn't come out cheaper either.

I'm working out whether the home states can avoid the orientation problem by placing the sub at (3,L) and (6,R), where the two occupied cell pairs {3,4} and {5,6} don't overlap, so the cells alone would reveal facing.

I'm noticing that the trail cells are ambiguous at the home positions: (3,L) covers {3,4} and so does its first step right to (4,R), and the same overlap holds for {5,6}. Only the transit pair {4,5} is unique to a moving sub. So the cell pattern alone can't tell me the facing direction right after a reversal, and I'd need the policy to press the direction key first and let the next state resolve it.

I'm noticing the "intent" carries over between frames, so the sub can press left toward a left-side enemy and keep pressing until it reaches the home cells {3,4}. The snag is that {3,4} is also the cell pair for (4,R), so the rule "{3,4} with an enemy on the left means fire" would misfire if the sub had actually arrived there facing right.

I'm working through the reversal case: from (3,L), a sticky 'l' would carry the sub to (2,L), and getting back to (3,L) from there needs r, r, l, since the sub can't step right without turning right first.

I'm now checking whether a global feature, an AND over column 5's back cell and its orientation channel across rows, could replace per-row units. Per-row gating would cost too many units, so I'm weighing a single shared unit against the alternative of giving each row its own orientation unit.

I'm testing a two-unit trick: each row's back-cell presence in column 5 combined with its orientation channel, summed across rows and shifted by one, so the result reads as "back at my row's column 5." The catch is that trails in column 5 from other rows would corrupt the sum, and those show up often enough to matter.

I'm concluding that a per-row trail check can't be folded into a single shared unit without corruption from other rows, so I'd need separate orientation units for each row. I'm also considering a behavioral workaround: when an enemy is on the left, the policy could split between moving left and firing, which accepts some drift but avoids needing orientation at all. Facing left that split helps, but facing right it wastes shots.

I'm checking what pressing 'l' does to the cell pair: from {4,5} it stays put if the sub is facing right, but shifts to {3,4} if it's facing left. So the pair alone tells me whether a left press is a turn or a step, and I'm weighing a rule that branches on which pair is occupied.

I'm working out a lean rule: when enemies are on one side, the sub presses toward that side and lets the cell pair it occupies reveal whether a press turns it or moves it, so it ends up at the home position facing the threat, at the cost of one extra step.

I'm sketching the full decision rule now: with the threat on the left, I'd press 'l' whenever the occupied pair sits at P ≥ 4 and fire once it reaches {3,4}, and I'm checking what to do if the sub has drifted even further left.

I'm checking whether pair {3,4} always means facing left. It doesn't, since (4,R) occupies the same pair, and it can be reached by pressing 'r' from (3,L) or from (3,R). So the rule that pressing 'r' at P ≤ 3 only happens under the enemy-on-right condition needs a closer look.

Now I'm checking the case where the sub sits at (4,R) with P=3 and an enemy appears on the left. The rule says fire, which would send it the wrong way, and firing wouldn't change the state, so it could stall there while the enemy closes in.

I'm considering dropping the homing step once the sub has leaned into a threat's side, so it stays put at P ∈ {3,4,5} and only recenters when it has drifted to P ≤ 2 or P ≥ 6. That avoids the case where a fresh threat appears while it's still transiting through an ambiguous pair.

Now I'm checking the case where the sub is at (3,L) and an enemy shows up on the right: pressing 'r' only turns it in place, so the pair stays {3,4} and it has to press again to reach (5,R) before the move resolves.

Checking the wrong-direction fire case: if the threat flips to the left while the sub sits at (4,R) with P=3, the rule fires rightward, and the sub could stall there. Sticky repeats of the last move also matter, since a repeated 'l' after leaning left only drifts it further while still facing left, which the fire rule handles fine.

I'm now considering a deadlock: if the sub is at P=3 facing right and a threat appears on the left, the rule fires rightward and it stalls. Detecting the wrong-way bullet would need per-row state again, so I'm weighing whether the sub should keep pressing 'l' until it reaches P ≤ 2 and only fire from there.

I'm weighing a cleaner option now: give each row its own orientation unit so the horizontal logic doesn't depend on which cell pair is occupied. That costs eight units, and I'm checking whether the rest of the budget still fits once the row-level units are added.

I'm weighing whether to merge the orientation signal into the per-row threat units, or to split EL and ER into a single signed unit, and I'm checking how much the layer-2 surface detection and the row-0 dive check would cost in units.

I'm now weighing whether a single shared unit can tell apart a threat on either side, or whether the sign cancels when threats appear on both sides at once. I'm also wondering how to handle vertical safety, since the unit may need separate up and down signals along with a check for an unavoidable threat in the same row.

I'm now sketching how the vertical units would work: one unit for wanting to go up that also requires being safe from danger above, and a matching one for going down, with the surfacing override handled inside the same gating.

I'm weighing whether a sweep-style vertical policy could replace precise per-row targeting, since the sub has time to reposition before enemies arrive.

I'm considering letting the sub sweep vertically between rows 2 and 8 instead of tracking each enemy's row precisely, with the orientation hinting at the sweep direction. The catch is that the boundaries would need a reversal rule, and I haven't worked out how to trigger it.

I'm considering a random walk for vertical movement, where the sub moves up or down with equal odds, but that would take too long to cover eight rows before enemies arrive. A more deterministic approach might use a global feature that compares which half of the screen holds targets against which half the sub occupies, though I haven't worked out the details yet.

I'm considering that the vertical unit might need to act as a push away from danger instead of a pull toward targets: danger above should block going up, but danger below shouldn't force a move, since enemies don't move vertically and only block a move into their row.

I'm checking whether a single signed vertical unit can handle "stay" when danger sits both above and below, since a plain pull-plus-penalty sum tends to nudge the sub into whichever side is clear.

Splitting the vertical decision into two gated units per row, one for going up and one for going down, so that a row blocked on both sides cancels out to stay put. That brings vertical to 16 units, and with the horizontal EL, ER, and orientation units the budget comes to 40, which is over the 32 available. I'm now looking for something to cut from the horizontal side, starting with whether the orientation signal can be dropped.

I'm thinking about merging the left and right threat signals into one signed unit, and about whether an orientation-based trick could save units instead.

I'm considering giving each side its own pair of units per row: one that fires when a threat is on the left and the sub faces left, and one that turns it when the threat is on the left but it faces right, with the mirror pair for the right side. That makes four units per row.

I'm trying a two-unit version for each row: one unit that turns the sub left only when a threat is on the left and it faces right, and a fire unit for the matching case. The fire case doesn't separate cleanly from the turn case under a single weighted sum, so I'm checking whether a gated unit for the turn can keep the two apart.

I'm weighing whether fire can simply be the default when nothing else applies, which would drop the separate threat-in-row unit and bring the per-row count back under budget.

I'm settling on a default action of firing whenever the sub isn't turning or moving vertically, which would remove the need for a separate threat-in-row unit. The cost is that constant firing could burn the cooldown and delay a shot by a few frames when a threat first appears up close. That leaves only the two turn units per row to worry about.

I'm still weighing whether firing by default is worth the cooldown cost, and whether moving toward distant targets would conflict with keeping the sub in a row that has a threat in front.

I'm checking whether bullet dodging can stay separate from the threat-in-row suppression, so that an incoming shot can still trigger a vertical move even when enemies are in the same row.

I'm checking whether bullets and enemies can share the same channel-based signal, since a plain linear weight can't separate enemies from bullets and divers at once.

I'm weighing whether bullets can be picked out separately from enemies and divers by a weighted sum over the two channels, which works if divers in the row are rare. That would let me build an "escape up" or "escape down" unit that fires when a bullet is close, while the vertical pull stays suppressed whenever an enemy sits in my row. Counting up the units, that comes to four per row: up, down, and the two turns.

I'm weighing whether dropping rows 1 and 8 would free enough units, since the sub could pass through those edges and only lose a few targets. That would leave 24 units for rows 2 through 7 and room for the global and edge handling.

I'm trying to fold the two turn decisions into a single signed unit, using the difference of the threat indicators plus an orientation term, but a linear unit can't express the difference of two AND conditions cleanly, so I'm checking whether the weights can still separate the three cases.

I'm testing whether a single signed unit with a threshold can separate the turn-right, turn-left, and no-turn cases when the orientation term is weighted equal to the threat difference. Checking the cases one at a time, the two turn cases land clearly past the threshold while the no-turn case with the sub facing right stays inside it. I still need to see what happens for the threat-on-left case while facing left.

I'm checking the sign-and-threshold version against each case: with the orientation term matching the threat difference, the turn cases land at plus or minus 2κ and the no-turn cases stay near zero or at plus or minus κ. Two enemies on the left while facing left gives minus κ, which still falls inside the no-turn band.

I'm checking whether one signed unit can handle both turn directions, with the orientation term weighted against the threat difference. Most cases separate cleanly at a threshold of about 1.5κ, but three enemies on the left while facing left would wrongly trigger a left turn, so that edge case needs a note.

I'm checking the threshold for the layer-2 unit next: with κ set to 0.6, the turn levels sit well apart from the no-turn levels, so a sharp gain should separate them cleanly.

I'm checking the gated baseline now: when the sub is at row 0 every turn unit reads -1, so the aggregate would look like a left turn, and I'll need a row-0 override to cover that case.

I'm checking whether the gating for the row units holds: when the sub is in another row, the pre-activation should stay strongly negative so each unit saturates near -1, and I'll confirm the margin with a large gate constant. The row indicator is the sum of the front-and-back channel-zero cells in that row divided by two, so it equals one only when the sub is there.

I'm writing the gate term so each row's unit is pushed strongly negative unless the sub is in that row, and I'm wondering whether the orientation reading holds when the sub has drifted off its home column, since then the turn units could read the threat difference alone and press a direction toward an enemy. A homing rule that takes priority away from home might fix that.

I'm checking whether the orientation signal can be read locally from the sub's own cells, since the row's trails from enemies would contaminate any row-wide sum. The row-wide version is too noisy when threats are present, so I'll restrict the orientation term to the columns around the sub, which only works while it stays near home.

I'm checking whether the orientation can be read from the sub's own cells at home, so the row-4 and row-5 trail values give facing direction. The concern is that an enemy trail on those same cells could mimic the orientation signal, so I'm checking which object positions could produce a trail there.

I'm checking whether the orientation can be read from the sub's own home cells without enemy trails throwing it off. With the sub in state B, a right-moving enemy trail on the cell next to it leaves the orientation reading at zero, but the threat term still keeps the unit under threshold, so firing still works. In state A, the same trail reinforces the turn toward it, which is the correct response.

I'm checking the case where an enemy comes along the sub's back cell instead of its front, since that collision would go unnoticed and needs its own handling.

I'm working out what happens when an enemy sits on the sub's back cell, since it will step into the front cell next and collide if I just keep going. Turning right in that case would move the front onto the enemy, so vertical escape is the only option, and columns 4 and 5 need to count as close-danger for that.

I'm laying out the remaining per-row units: each row gets a turn unit plus an up and a down unit, which makes 24 for rows 1 through 8, leaving 8 spare units for the row-0 dive check, global homing, low oxygen, and similar signals. I'm also wondering whether the vertical moves should be suppressed while an enemy sits in my row, since moving away forfeits the kill even when it's safe.

I'm settling how the vertical units handle targets: a target in my own row pulls against moving up or down so I stay and fire, while targets above or below pull toward that direction. Escape from a close danger in my row adds a push to both vertical moves, and when both are active the choice between up and down is random, which is fine since both are safe.

I'm working out how to combine the oxygen-low and surface-depth signals into one urge to surface, which means adding a large bonus to the up unit and a large penalty to the down unit when both conditions hold. Since the unit sums everything, that AND only holds if the other terms don't outweigh it.

I'm working out how the oxygen-low and dc≥1 signals enter the surface urge, since the sign of the term flips depending on whether oxygen is OK or low. I'm tabulating the cases for the oxygen cell and the danger-count cell to check whether the urge stays neutral when oxygen is fine.

I'm checking the oxygen-and-danger term again, and this time the tabulated cases show that when oxygen is between 3 and 8 but the danger count is zero, the surface term subtracts from the up unit and would block normal upward targeting.

I'm noticing that a single global SURF unit can't be ANDed with each row's safety bit through a plain linear sum, so the per-row up and down units would need to carry the safe-up and safe-down condition on their own. That means the surfacing signal has to be routed in a way that doesn't depend on the other rows' gating.

I'm testing whether a single linear term can give the surfacing signal only for the case where oxygen is low and the danger count is nonzero, and I find it can't: the four input patterns would need contradictory coefficients, so the AND has to come from elsewhere.

I'm weighing a global surfacing unit against the per-row up units, since a plain linear sum can't express the oxygen-low-and-danger AND without suppressing normal upward targeting. One option is to let the up unit take a surfacing pull whenever oxygen is low, whatever the danger count, and then handle the top row separately.

I'm weighing whether a surfacing term can be applied only when oxygen is low, without suppressing normal upward targeting when danger is absent. I'm considering whether adding a term that is positive when oxygen is low and neutral otherwise avoids that problem, though if oxygen is low with no danger, the sub would just climb to row 1 and stall.

I'm weighing whether the surfacing term can live inside each row's up unit, but a plain linear sum makes that awkward, so I'm thinking about adding a separate global unit for the surfacing signal and passing it through to the up units.

I'm checking whether a single linear term can encode the oxygen-low case and I'm working through the tabulated cases to see where the oxygen bar and the danger count interact.

I'm checking whether a bias of -1.5Ω can work, since it would leave only the oxygen-low-and-danger case positive, but it would also push down the ordinary pull-based targeting in every other case. The normal upward pull would have to be large enough to overcome that offset.

I'm dropping the global surfacing term in favor of pure per-row safety units that depend only on the cells above, and leaving the urge to rise as a separate signal that layer two combines with them.

I'm now trying to fold the surfacing desire into the per-row up unit as an OR with the target pull, so that the safety bit gates both together. The open question is whether a single linear threshold over a continuous target pull and a binary surfacing signal can still implement that combination cleanly.

I'm weighing a per-row safety unit for the row 1 to row 0 step, while the other rows rely on an oxygen-low term that pushes the sub upward whatever the danger count is.

I'm building a dedicated unit for the final step to the surface from row 1, so it fires only when the surfacing condition holds, using a linear term for the oxygen-low and danger AND.

I'm considering whether the oxygen-low term should also include the danger-count condition, since without it the sub would rise to row 1 and then hover there, possibly oscillating with rows 1 and 2 when no divers are around.

I'm considering whether to give the down unit the same oxygen and danger terms, so that the surfacing bias cancels out when a diver is present and doesn't suppress normal upward targeting when oxygen is fine and no divers are around.

I'm considering letting the down unit carry the same oxygen and danger terms, but that would bias the sub downward whenever no divers are around and oxygen is moderate. Letting oxygen-low push it upward regardless of danger avoids that, though it may leave the sub hovering near the surface when no divers are nearby.

Now I'm weighing whether the sub can descend to row 0 when no divers are around and oxygen is low, and it looks like it would get stuck at row 1, so I'm considering pushing divers harder in the targeting weights when the count is zero.

Now I'm weighing whether to give divers extra pull weight in the targeting, since a linear term can't condition that on the diver count. I'm considering simplifying the overall design to keep the core loop manageable.

Now I'm looking at how to keep the sub from getting stuck: if it steps into row 1 with no divers aboard, one more repeated up-move could carry it to the surface with nothing gained, so that step carries real risk.

I'm considering whether the row 2 to row 1 step can carry the diver condition, so the sub only moves up into row 1 when a diver is aboard and the accidental surfacing costs little.

I'm now checking whether row 2 can move up into row 1 at all, since a sticky repeat of the up-move could carry the sub to row 0 with no diver aboard. That suggests blocking the row 2 to row 1 step except when surfacing, and letting a dive from the surface run straight down past row 1.

I'm checking that row 0 is safe to dive back into after surfacing, since oxygen is full again and the urge to rise is off. The open point is that the sticky previous action of 'u' could keep the sub at row 0 instead of letting it dive.

I'm working out how the sub gets to home: if it starts at row 0 off to the side, it homes first while the surface is safe, and then dives. I'm adding two global features that push it right when it's left of home and left when it's right of home, and that homing takes priority over vertical moves and turning, since row 0 is safe.

I'm checking whether the homing step can conflict with turning: if the sub drifts to columns 3 and 4 facing left, the back-at-4 pattern reads as facing right, so the turn logic would misfire and push it further left.

I'm still stuck on the ori estimate: a single linear term can't tell which way the sub faces once it has drifted off home, so I'm looking for a position-independent version that works from the pair of cells it occupies.

I'm checking whether a linear ramp over the window's trail cells can recover which way the sub faces, since a single enemy trail in the window would shift the estimate.

I'm checking whether a linear ramp over the window's trail cells can recover facing, but a trail at column 2 or 3 would throw the estimate off by several units. So orientation can't be read reliably when the sub has drifted, and I'll need to keep it at home and let homing take priority over turning when they conflict.

I'm checking the drift cases now: a sticky repeat of 'r' can carry the sub from home at (4,L) to (6,R), and when a threat sits on the left, homing and the turn logic each push a different way, so I'll let homing win and accept a few extra frames.

I'm checking whether enemies in the far columns, 0 and 9, belong in the left and right windows, since one that is leaving the field may still be shootable before it exits.

Now I'm weighing how the threats on each side interact: if enemies approach from both directions in the same row, the turn term roughly cancels, so the sub keeps facing its current way and fires at the nearer one, then turns toward the other once the first is gone.

I'm weighing whether escape should trigger only for threats within one cell, since an enemy directly in front of a ready sub is better shot than fled from.

I'm weighing whether escape should trigger on any danger within a few cells, or only on a direct threat, since an enemy right in front of a ready sub may be better shot than fled from. I'm leaning toward escaping only when danger is at distance one, and handling bullets separately.

I'm weighing whether escape should fire on bullets two cells out, using a combined term that counts bullets as positive and treats enemies as neutral and divers as negative, so a shot isn't dodged when it would just cost a kill.

Now I'm checking whether escape should also fire on bullets two cells away, since a bullet that's moving away from us won't hit, and dodging it would just cost time.

Now I'm working out how the escape term should weigh danger right in front of the sub against the pull to stay and fight, so it fires when the adjacent row is clear. I'm also checking whether enemies in the same row should keep the sub in place, and whether danger in the row above the sub's front would block moving up.

I'm now working out the danger-above check for the up-move: bullets two cells either side of the sub's front could slide into it in a frame or two, and enemies one cell either side could step in, so I'm weighing whether to union the columns or use a single front column.

I'm now defining the danger-above check as a sum over columns 2 to 7 of the row above, so any threat there blocks an upward move, even if it is two cells away. I'm also thinking about how to weigh targets in nearby rows against farther ones when pulling the sub vertically.

I'm weighing how to combine the vertical pull from targets above and below, and I'm leaning toward making the up and down moves compete, so the side with more weighted targets wins and ties leave the sub where it is. I'm still deciding which columns should count when tallying targets in each row.

I'm settling on which enemies count toward the vertical pull: anything in a row counts, including ones near the edges that are about to exit, since they can still be shot as we approach. The bullets in the enemy channel don't count toward the pull, only the enemies themselves.

I'm now setting the vertical weight for each row: targets in the same channel count positively, and bullets count slightly against, so I'm writing that as a weighted sum over the row's cells. For each row above or below the sub, the contribution scales with distance, with the sign flipped depending on which side it sits on.

Now I'm writing out the per-row weights as strided ranges, so each row and channel can be set in one edit rather than cell by cell.

Still working out the per-row target weights; I'm counting roughly 128 statements if I drop the diver bonus, which is a lot to write out, so I'm looking for a way to cut that down.

Now I'm looking at whether layer 2 can handle the per-row gating itself, with layer 1 supplying a one-hot read of the sub's row alongside a summary of each row's targets, so each layer-2 unit only has to combine those two.

I'm working out how layer 1 should supply the per-row features that layer 2 gates on, since each row's own escape and stay signals need its left and right threat counts and facing direction.

Now I'm laying out how layer 1 should split its units: one set reads the sub's row, and others flag which rows have targets, which threats sit on each side, and which way the sub is facing. The aim is to let layer 2 combine those per row.

I'm checking whether layer 1 can merge the per-row features into fewer units by using linear combinations in its near-linear range, since layer 2 needs those features anyway.

I'm now looking at whether layer 1 can supply the row totals as moments, so that layer 2 can get the per-row weighting it needs without a separate unit for each row.

I'm seeing that a moment-based layout could let each gated unit in layer 2 weight targets by their offset from the sub's row, so the sign of that sum tells whether the centroid of targets sits above or below. I'm noting that distance weighting would pull the wrong way for this purpose, though the sign still carries the signal I need.

I'm weighing whether a polynomial weight can capture the pull toward the nearest target, since sign(d)/|d| isn't a polynomial and a low-degree fit would stay smooth. Something like d·(a − d²) keeps the sign of the offset and fades with distance, though it only works within a limited range.

I'm checking whether a degree-3 polynomial in the distance can keep the pull's sign while fading out for far targets, since the nearest target should count most. The fit works for small distances, but the sign flips too early for larger ones, so nearer targets don't end up weighted more.

I'm settling on a per-row layout where each row's pull comes from its own unit, since a centroid-style moment sum would leave the sub stuck between two targets with nothing in its row. The downside is the unit count, so I'll try to keep each row's nearest-target signal in a single shared feature.

I'm tallying the layer-1 budget now: 24 units for the per-row up, down and turn signals, plus a few global ones for surface, homing and dive safety, which brings it to about 29. I'm also wondering whether the sub should just fire constantly, since there's no ammo cost, and the only drawback is the cooldown.

I'm deciding whether to fire by default when idle, since firing costs nothing beyond the cooldown. The worry is that a shot wasted on empty space delays a shot at an enemy that enters the row a moment later, so I'm weighing a constant fire bias against a lower no-op bias.

Now I'm writing the threat-turn unit, combining the sub's offset from the row with the counts of threats on each side, with the sign set by which side has more.

Still writing the turn-signal weights...

Now I'm checking the turn logic: a right turn fires when the signed turn value passes 1.5κ, a left turn when it drops below -1.5κ, and the sub at row 0 reads as a strong left turn.

I'm checking how the turn signal behaves at row 0, since the gate there pushes the value to an extreme and would read as a left turn. Setting the off state to a neutral value would avoid pressing 'l' at the surface, but neither sign of the gate gives a neutral result, so I'm looking at other ways to suppress it.

I'm now checking whether the turn-left and turn-right threat units should draw on the danger channel, which includes bullets, or on the enemies-and-divers channel, since turning toward bullets wouldn't help.

I'm weighing whether to use ch1 alone for the turn threats, since bullets are harmless to turn toward but only briefly present, while divers would pull the sub the wrong way. Mixing in ch2 would make divers pull the sub around, so I'll stick with ch1 for the danger window.

I'm checking the edge cases for the turn signal with multiple enemies on each side, and it holds: two enemies on the right while facing away still turns right, while the same count on the left with the sub facing left produces no turn and the sub keeps firing.

Working out the turn signal's tanh levels: at κ = 0.5, the sigmoid-like compression puts the threshold at 1.5κ near 0.635, and a two-cell imbalance sits at 0, which is where the decoder needs to separate cleanly.

Working out the layer-2 gain for the T_k units: at κ = 0.5 the turn threshold sits near 0.61 on the gated scale, so a gain around 18 separates the "turn" level (about 0.76) from the "no turn" level (about 0.46) with room to spare. I still need to account for how the other rows' gated units contribute, so I'll come back to that after setting the bias.

I'm working out the up and down units for each row next, starting from how the gate and the sign of the offset should shape what each row contributes.

Now I'm defining the vertical pull for each row, weighting each target row by its distance from the sub and leaving out row 1, since the sub never moves into it except when surfacing. For the up signal, rows above count toward pulling up, and rows below pull down. The up signal for rows 2 through 8 starts from a baseline.

I'm working out the up-pull for row s from the weighted targets above it, minus a stay penalty and an escape term. The worry is that escaping upward from row 2 into row 1 could expose the sub to the sticky risk, so I'm weighing whether to block that escape.

I'm dropping the escape term from the up-pull for row 2, so the sub only moves down to escape threats. The oxygen-driven rise to row 1 is still allowed, but I'm noting that if the surfacing check fails there, the sticky repeat of 'u' could carry the sub to row 0 and into danger.

I'm working out the up-pull for the rows above, where a diver in the row is the only case that should trigger a rise from row 2. For the middle rows the oxygen term should probably depend on whether a diver is present, so I'm checking whether that holds.

Now I'm working out the down-pull for row s, keeping it suppressed when oxygen is low and a diver is present, so the sub stays put rather than descending into danger.

I'm working out the sign of the down-pull for the deeper rows, and how the surface gate should combine with it so that the 'd' decision is suppressed when the sub is about to surface.

I'm settling the logic for the 'd' and 'u' decisions: a down-go unit should fire only when the descend signal is on and surfacing is not, and the up-go unit needs its oxygen-rise term tied to having a diver present, so that surfacing with no diver doesn't send the sub upward by default.

I'm now checking the down-pull for the deeper rows: the oxygen term would suppress descending when the sub is low on air and a diver is present, but with no diver it should leave the pull alone, so I'm working out whether one term can cover both cases.

I'm checking the up-pull for rows 3 and below, where the oxygen term would make the sub rise whenever it runs low and drag it upward even with no diver present. Adding an oxygen rise that's tied to the diver count gives a sinking bias when oxygen sits between 60 and 180 and no diver is around, so the design would need a different combination.

I'm checking whether a single layer-1 unit can capture the "low oxygen and a diver present" condition, since no linear per-row term can switch the vertical bias on only in that case. That points toward a global surfacing unit, and I'm thinking about how the layer-2 up and down decisions would have to combine with it.

I'm checking whether a linear per-row term can work here: the oxygen rise should only happen when oxygen is low and a diver is present, and any linear combination of those two conditions forces the no-diver case to bias the sub. Setting the coefficient on the diver count to zero shows the rise reduces to the unconditional version, so the gating has to live elsewhere.

I'm checking whether the sticky-repeat risk can be avoided by letting the rise depend on having a diver present, but any linear term in oxygen and diver count can't switch the bias on only when both hold. So I'm weighing whether a sub that rises on low oxygen and hovers at row 2 with no diver is an acceptable corner case, since it would only happen after a surfacing leaves the diver count at zero.

I'm checking the diver-bar edge case next: once the oxygen bar starts covering more columns, I need to see whether the diver count still reads cleanly at that boundary.

Now I'm settling the oxygen threshold for the surfacing signal: the bit o = ch5(9,2) lights up once oxygen reaches 60, so "low" means under 60, which leaves about 59 frames of air.

I'm weighing whether to use column 1 for the surfacing threshold, since oxygen under 40 leaves more room before the sub has to rise. The worry is that a blocking enemy could hold the sub in place for a long stretch while the oxygen keeps draining.

I'm weighing whether the sticky-risk window should be narrower than cols 2..7, since an enemy entering at col 2 could hold the sub in place for a long stretch. Settling on the oxygen trigger at column 2 (rise below 60) gives enough slack for that.

I'm narrowing the danger check above to columns 3 through 6 for enemies and bullets, and adding bullets at columns 2 and 7 weighted against the enemy channel. A bullet at column 2 reaches column 4 within two frames, so I'd need to keep moving up or dodge again rather than stopping in the row above.

I'm simplifying the danger checks: for the row above, enemies and bullets in columns 3 through 6 count, plus bullets alone at columns 2 and 7, all weighted heavily. I'm also writing the same kind of check for the sub's own row, to decide whether an enemy close by should trigger an escape or be shot instead, since the cooldown often blocks firing.

I'm now looking at the case of an enemy one cell behind the sub, since my reasoning about the forward-facing cases so far doesn't cover it.

Now I'm checking the case where an enemy sits two cells behind the sub, since the sub would turn toward it and step forward. Stepping forward puts the sub next to the enemy in front, so it fires there. The risk is that the enemy advances into the same cell on the same frame, which would be a collision.

I'm weighing an escape when enemies or bullets sit within a few columns behind the sub, since the target pull would otherwise drag it back toward them. Escaping vertically is safer than turning and firing at an adjacent enemy, even though it means giving up some kills. If both neighboring rows are unsafe, the sub just stays and keeps firing.

I'm settling how the sub should move when an enemy sits in its own row: it should stay put and shoot or turn toward the target, and divers in the same row get the same treatment.

I'm now sorting out how to tell a diver heading toward the sub from one already moving away, since the trail cells would show the direction but a plain weighted sum can't separate those two cases.

I'm now weighing how to score the diver-direction term: the trail cells differ by one column depending on whether a diver is approaching or receding, and I'm thinking about whether a weighted sum over enemies and divers in my row can account for that without waiting too long on divers that have already passed.

I'm sorting out how a diver in my own row should count toward staying put, since one approaching from the left has its trail one cell to its left, while a receding one has it one cell to its right.

I'm weighing whether divers in my row should pin the sub in place: ignoring direction keeps the logic simple, but a receding diver would hold the sub for up to ~30 frames, so I'm considering giving divers a lower STAY weight so stronger pulls can override them.

Now I'm working out whether divers approaching from the sub's side can be told apart from receding ones, since only approaching divers are worth waiting for. The idea is a per-cell feature: a diver's trail sits one cell behind its direction of travel, so a trail on the near side marks an approaching diver.

I'm checking whether divers approaching from the left and receding ones can be told apart with a per-column weighted sum over the trail channel, and it doesn't work: a trail one cell left of a diver at column 1 looks the same as one one cell right of a diver at column 1, so a linear weight on the trail can't separate them.

I'm working out how many divers the sub can realistically collect: a fresh diver takes about 24 frames to reach the center, and the sub can reach its row within about 6 frames, so grabbing a diver before enemies distract it looks feasible.

I'm still weighing whether divers in my row should keep the sub in place. Enemies alone should set the stay-and-shoot rule, but then the sub might drift off a row where a diver is still approaching whenever other targets pull it away.

I'm settling the target pull as enemies and divers counting positively, with bullets slightly negative, and setting the STAY term to react to enemies and bullets in my row.

I'm weighing how far away targets should pull the sub: the STAY term will count enemies in its row at full weight and bullets and divers at half weight, and I'll sort out the exact pull weights by distance later.

I'm weighting targets by distance so the nearer one wins: a target one row away counts for more than two targets further off. The up-or-down decision then comes from comparing the two sides, with any direction that's blocked by danger ruled out, so the sub just stays and keeps firing.

I'm settling the escape rule: a close danger in my own row adds a push that keeps both directions in play, while a danger directly above or below blocks that way. With the pull weights I'm using, one side can still win strongly, so the sub would move toward the stronger target unless the safety check overrides it.

I'm settling the action priority: at the surface the sub homes left or right when needed, otherwise dives if it's safe, and waits otherwise. Underwater, escape from close danger comes first through the up and down terms, then homing back to base with left and right moves.

I'm settling the action order: escape from close danger comes first, then homing and turning toward targets, with vertical targeting only when the sub isn't already held in its row. When a threat sits in the sub's row, the stay term suppresses targeting so the turn wins, but the escape term needs its up and down weights to outrank the turn.

I'm settling that homing takes priority over targeting but not over escape, and that the vertical pulls should stay in order. Row 1 is just a pass-through for the sub: it always wants to dive further, and only needs a surfacing unit there if it returns. Row 8 has no downward unit since there's nowhere lower to go. That gives eight upward units and seven downward ones.

I'm settling how the surface state and the turn units interact: at row 0 all the turn units read as off, so the sub would wrongly turn left there. I'm considering either a dedicated flag for "sub is in rows 1 to 8," or offsetting the turn gating so its off state reads as neutral.

I'm checking how the off-state of the turn units affects the sum: with every unit at -1 at row 0, the total is just a constant, but once the sub is in row s the active unit shifts that sum by its own deviation.

I'm looking at whether the T_s gating can make row 0 read as neutral, since the off state currently reads as a constant turn-left signal. Splitting each turn into separate left and right units would fix that but doubles the unit count to 16, which is too many, so I'm checking whether a single scalar per row can encode neutral and both turn directions at once.

I'm weighing how to get row 0 to read as neutral, since the turn units currently default to a turn-left signal there. One option is a separate row-0 indicator to suppress the turns at the surface, and I'm looking at whether the dive unit could serve that role.

I'm defining a row-0 indicator unit Z0 that reads positive only when the sub is at the surface, so the turn units can be suppressed there.

I'm checking the surface-row indicator once more: the dive unit can't separate "at row 0 but unsafe" from "not at row 0", so I'll keep the separate Z0 unit to suppress the turns there. The surfacing unit U_1 handles the row-1 case, and U_2 covers the climb from row 2.

I'm checking whether the down-going unit can avoid sinking bias: subtracting oxygen times the difference between the diver and oxygen terms gives the right result in three of four cases, but when oxygen is fine and no diver is present, it pushes the sub downward.

I'm checking whether the down-going unit can avoid a sinking bias: a term that blocks descent when oxygen is low could also push the sub down when oxygen is fine and no diver is present, which is the case I'm trying to avoid. I'm considering whether a different oxygen cell would make that case rarer, but the mid-cycle state is common, so that doesn't fix it.

I'm making the per-row units encode safety and pull together, so an unsafe row reads as off, a safe row with no pull sits at neutral, and a safe row with a pull reads strongly on. Then the up-go decision in layer two can take a threshold on that single value, plus the surfacing case.

I'm working out how the per-row units can carry safety and pull in a single value: unsafe rows read as off, safe rows with no pull sit at neutral, and safe rows with a pull read strongly on. That lets one layer-two threshold handle both the up-go decision and the surfacing case.

I'm working out how to keep the surfacing case working when there are targets below: the pull has to stay small enough that a safe row still reads as up-capable during surfacing, so I'm bounding its magnitude and setting the danger offset to keep unsafe rows clearly separate.

I'm testing whether a single scalar per row can encode safety and pull together: x = -3 + 3·safe plus a graded pull term, so unsafe rows sit near zero activation, safe-neutral rows sit at one, and safe rows with a pull sit higher. That keeps the surfacing threshold workable even when targets are below.

I'm weighing whether the surfacing case can work without a per-row safety signal in layer two. If oxygen is low, the rise term pushes the sub up unconditionally, and the descent term keeps it from sinking back, so at row 2 it stays put and can still shoot or catch divers there.

I'm now weighing a shortcut for the surfacing case: rather than a per-row safety signal, the global surfacing unit could gate the rise directly, so the sub climbs to the surface when oxygen runs low and a diver is held.

I'm checking whether the output-layer 'u' and 'd' logits can split the choice cleanly. If the dive term is removed from the down-going unit and suppressed by the surfacing unit at layer two instead, then with no divers and low oxygen both the up and down signals can fire, so the sub's motion looks like a biased random walk. I'm weighing whether that is acceptable when the aim is to hunt.

I'm considering dropping the oxygen term from the up-going unit entirely and handling the surfacing case with a separate global mechanism instead. During a surface, the output would get a strong boost toward up and suppress down, but the per-row units would still need some way to block upward moves into danger.

I'm considering a redesign where U_s encodes safety plus a mild target preference, so it stays on whenever the row is safe and the 'u' decision draws on that combined signal in layer two.

I'm giving the up-going unit a safety offset and a signed pull term, with the down-going unit mirroring it with the opposite sign on the pull. That way both units stay on under neutral pull, and layer two can compare them. I still need to check whether a strongly negative pull could push the up unit below threshold even when the row is safe, which would break the surfacing case.

I'm checking the safe-unsafe threshold on the up-going units: with the pull bounded, a safe row lands well above 0.8 and an unsafe row well below it, whatever the pull. I'm now comparing the up and down values for the same row, where a 1.5 pull gives a clear gap between the two outputs.

I'm weighing whether a tanh-compressed single scalar per row can cleanly separate the pull levels, since the spacing gets small when the pull is weak. Splitting the work differently might be cleaner, perhaps with layer-1 units that just summarize the row contents without gating, and letting layer 2 handle the row-specific logic.

I'm considering a layout where the per-row units do the gating and layer 2 combines them, but that means many units per row. Gating in layer 1 by row is more efficient, since a gated unit can read the raw pixels for any row with its own weights. I'll see whether a "safe to go up" check can work during surfacing without spending a unit on each row.

I'm checking whether a single threshold unit per row can encode the oxygen and diver logic together, with the danger check as a large negative term. Tabulating the four combinations of oxygen and diver state will show where the AND condition holds.

I'm trying a different use of the oxygen term: it gets in the way when there are no divers, so I'm checking whether a second diver-related cell could offset it. Then I want to see what the full row of cells gives for each combination of oxygen and diver state.

I'm trying to find a linear combination of the row-9 cells that is about +1 when oxygen is low and there are divers, zero when oxygen is high, and at or below zero when oxygen is low with no divers. The o2 and d8 cells look like the starting pieces, with o1 and o0 as possible additions.

I'm checking whether any linear mix of the row-9 cells can isolate the low-oxygen, has-divers case. The trouble is that the diver cell (9,8) also shifts with the diver count when oxygen is high, so it can't be used alone without leaking dive information into the oxygen-high states.

I'm now looking at whether a single global surfacing unit can handle the ascent safety, since per-row danger checks would cost too many units. The AND of low oxygen and diver presence doesn't come out of a linear mix of the row-9 cells, so that logic needs its own unit. I'm considering letting the up-moves follow low oxygen directly and leaving the dive-count-zero case to a separate rule at row 2.

I'm settling for a simpler rule: the oxygen term alone decides the upward and downward pull in the low-oxygen case, and I'll accept that the no-diver case just stalls at row 2. Then I'm checking whether the diver cell can be folded into the up unit with a weaker weight so the low-oxygen, no-diver case is suppressed without blocking the normal targeting.

I'm looking at whether a fixed-weight term for oxygen could be made to depend on the diver count, but the linear pieces I have can't separate the dive-count-zero case without also disturbing the oxygen-high states. I'm considering a small trade-off: accept some suppression of upward targeting when there are no divers, or let that case just stall at row 2.

I'm weighing the diver-count problem again: a linear mix of the row-9 cells can't isolate the no-diver case without disturbing the oxygen-high states. So I'll accept that the no-diver, low-oxygen case stalls at row 2, and try to make divers more attractive so the sub still collects them. Next I'm turning to enemy bullets, which travel along their row, and how a sub in that row ahead of an enemy would be affected.

I'm checking how the escape rule handles enemy bullets in my row: a bullet at columns 2 to 7 triggers a dodge, and if I escape and come back, the enemy may still be there, so the cycle just repeats. Targets behind me on the far side get handled by turning and firing, and divers in my row don't cause turns because the target logic ignores them. Our own bullets go on their separate channel.

I'm checking whether a turn-and-fire response is needed when a bullet, not an enemy, is behind me, since turning to face it would just waste time. I'm also weighing the enemy-at-the-edge timing case, where turning to shoot the second threat should usually work out.

I'm checking how the sub's own row behaves near the middle columns, since the escape window and the drifted-home cases overlap there.

Checking the enemy at column 3 against the escape rule: the escape takes priority over firing, so the sub would leave the row before the enemy is in range. That's usually fine because constant fire should kill the enemy before it gets close, unless the sub has only just entered the row.

Next I'm checking the arrival case: an enemy at distance 2 doesn't block a move into the row, so after arriving, the sub turns if needed and fires once the cooldown is ready. If the enemy closes to column 3 before that, the escape rule takes over.

Next I'm setting the logits sharp enough that the chosen action dominates the softmax, and I'm starting to lay out how each cell's input index is computed.

Still laying out the unit layout: each group of layer-1 units is assigned a slot, with the threat, escape, and home-column rules each getting their own block of units.

Still writing the gate and threat units...

Still writing the threat unit's gating math...

Checking the turn threshold: the level step κ is set so that one danger in the window gives a clear signal while two or three give a stronger one.

Still writing the turn-decoder math...

Still working out the turn-left term: at the surface row it would fire spuriously, so I'm subtracting a surface-row correction to suppress it.

Writing the U-unit formulas for the normal rows now...

Working out the upward unit for the surface-adjacent rows: it's gated like the others, with the oxygen term pushing up when oxygen is low and divers are present, and a large penalty for danger directly above.

Still working out the D-unit for row 1: when there are no divers and oxygen is low, I'm deciding whether going down there is the right fallback.

Now I'm setting the initial-state homing rule for row 0: the dive only fires when the row below is clear, and I still need to make sure the sub homes before diving at the start.

Setting up the upward and downward pull terms for the middle rows now.

Now I'm defining the drift-pull terms for the upward and downward units: each row's pull is weighted by distance and the target counts there, and the downward unit's pull is just the negative of the upward one, with row 1 always pulling down.

Still working out the pull terms for the drift units: the downward pull for row 2 comes only from rows below, and the upward pull for row 8 only from rows above, with weights falling off by distance.

Still setting the pull and stay terms for the up and down units, with the gain and threshold chosen so distant targets give only a weak signal.

Still working out the stay term for the row's own targets: I'm setting it to subtract a fixed amount per enemy or diver or bullet in the sub's row, so it overrides the pull terms, and I'm checking whether bullets there should weigh as much as the others.

Now I'm weighing the escape term against the stay term for enemies in the sub's own row, so that a close danger there overrides staying put.

Now I'm weighing the bullets at columns 2 and 7 against the escape term, and I'm setting its weight high enough that a bullet there still pushes the sub out of its row.

Checking the danger-above term for the up units: enemies in the row above at columns 3 to 6, and bullets at columns 2 and 7, get a large penalty, while divers there don't block the move.

Now I'm setting the oxygen term for the up units: when oxygen runs low, it adds a strong push upward regardless of whether a diver is in view, though it still can't override the danger penalty. The matching down term subtracts the same push, so the sub won't dive while low on air and can still escape upward.

Now I'm checking the gate for the up units: the oxygen push is strong enough that, with no gating, it could switch a unit on even when the sub isn't in that row.

Still checking the gate: I'm making sure it's large enough that a unit stays off whenever the sub isn't in its row, even when the escape and oxygen terms push the other way.

Next I'm checking that the gate is large enough to hold each unit off when the sub is in another row, and confirming that the two sub cells share the same row. Then I'll set a matching gate for the threat units.

Still working out the layer-2 decoding for the up and down units: I'm summing the row-gate outputs so that the total reads as the sub's tanh signal, with a bias chosen so the sign flips at the threshold.

Now I'm settling on a threshold for the layer-2 up decision, with a sharpening factor so the sign cleanly separates a clear signal from a weak one. I'm also weighing whether to feed the layer-1 units straight into the logits or to add a thresholded layer-2 stage, and I'm leaning toward thresholded units so the output is cleaner.

Now I'm setting the row-0 detector: it's a gate that's on only when the sub is in the surface row, using a small weight on each of those cells. Then I'm adding a homing check that fires when any sub cell sits in columns 0 to 3, so the sub knows it needs to press right.

Still laying out the action units: the signals for moving left, up, right, down and firing come next, and I'm working out how they should rank against each other.

Still working out the priority order between the vertical and turning signals: escape and surfacing should win, then homing, then turning, with firing as the fallback when nothing else fires.

Now I'm checking how homing interacts with the turn signals, since a homing move could change the sub's row or column in a way that undoes a turn decision.

Working out the output logits now: each action gets a weighted sum over the layer-2 signals, with the vertical signals outranking homing, homing outranking turning, and firing as the fallback.

Now I'm settling the logit weights: the vertical signals get the strongest gap, homing and turning sit lower, and firing is the baseline, so the sharpest choice is picking u and d with a bigger margin than 10 over 6.

Now I'm settling the logit gaps: vertical signals at 22, homing at 16, turning at 10, and firing at 3, so the leakage between them stays under a fraction of a percent. Where the turn and homing signals point opposite ways, homing wins, and when escape pulls both up and down, the two vertical logits tie and split evenly. I still need to check how the homing and dive signals interact at the surface.

Setting the row-0 gate to fire only when the sub sits on the surface, and checking that the layer-2 threshold holds. I'm also confirming that the up and down pull terms are antisymmetric, so U and D can both switch on only through the escape term.

I'm checking whether the escape terms can ever turn on both directions at once, and they can't, since the pull terms are opposites and only the escape term adds to both. I'm also looking at the danger windows: for the up units it's the row above, and for the down units it's the row below, both covering the adjacent columns plus the two-away bullet columns.

Now I'm estimating how likely a sticky repeat of 'u' lands the sub in a cell where an enemy has just arrived, since the danger window only covered the first step.

I'm estimating the per-move risk of a sticky repeat landing the sub next to an enemy: roughly 0.5% per vertical move, since only about 0.4 enemies share a row on average. Over about 30 moves that adds up to around 15% per oxygen cycle, which is significant enough that I need to account for it.

Sticky repeats only hurt when the policy chose something other than 'u' and the environment repeats 'u' anyway, so I need to check for that case specifically. That means estimating how often the policy will avoid 'u' while a repeat is pending, and whether I can cut vertical moves down to the ones that are really needed.

I'm weighing a 2-rows-ahead safety check for the up move, but it would block moves whenever the row two above is dangerous, which is too conservative. The sticky-repeat risk is about 0.5% per stop-after-move, roughly 5% per oxygen cycle, so I'll accept it.

I'm checking whether a sticky repeat of 'r' could carry the sub into column 5, the cell behind it, since an enemy could be sitting there.

Now I'm checking the threat windows against the sub's home position, and whether a sub drifted one cell to the left or right still has its back cell covered.

Checking the pair at columns 5 and 6 now: the front cell reads as facing left, and the back cell's channel is zero, so the orientation comes out neutral there too.

Now I'm checking the drifted pairs against the turn logic, and the homing signal already covers those cases. Next I'm defining the pull terms, where each target cell adds weight by its type: enemies count as a moderate pull, divers as a stronger one, and bullets as a push away.

Now I'm weighing the oxygen rise: with low oxygen, the up signal for rows three and below gets a strong boost, which pulls the sub toward the surface unless danger is above it. Staying put in a row with an enemy costs it eight points, so the boost still wins and the sub leaves to surface.

I'm lowering the down-escape suppression from -20 to -14, so that an escape downward still goes through when a bullet is coming and going up is blocked, while the pull-based down terms stay switched off. Next I'm checking the row-1 case, where a down move should yield to surfacing whenever the up move is available.

Now I'm checking the upward surfacing terms: once oxygen runs low, the surface-only signal for row 2 fires only when a diver is present and the sub is empty of air, and it's blocked by any danger in row 1. The row-1 surfacing signal uses the same oxygen weight.

Now I'm working through the row-0 dive term: it's a dive bonus of 6 minus a threshold of 1, and it only turns on when no danger sits in row 1 across columns 2 to 7.

Now I'm checking the dive gate for row 1: it adds the dive bonus of 6, subtracts the danger penalty for row 2, takes off the oxygen suppression when the air is low, and then applies the threshold of 1.

I'm checking whether the dive gate at row 1 should also weigh the enemies further away in that row. Since row 1 is only a transit row, the dive term alone should drive the sub downward, and I'm ruling out an escape upward because it would either leave it at the surface with no diver or push it into row 0 with nothing to show for it.

Now I'm writing out the down-move terms for the rows below the middle, with the escape term, the stay penalty, and the danger and oxygen costs. The up-move terms for the rows above follow the same pattern, with the oxygen boost added. I'm also checking the row-2 surface case, which is surface-only, and wondering whether the stay penalty counts correctly across every column of the sub's row.

I'm checking how the escape weight compares to everything else, so I'll test the pull, stay penalty, and oxygen terms against it.

Now I'm checking the on/off threshold for the up moves in the second layer: the sum of the per-row up terms, shifted by 7, has to clear a fixed cutoff before the up signal fires.

Now I'm checking the thresholds for the up and down moves at each row, and the surface case, where all the up terms switch off.

Now I'm checking the row-8 case for the down units, which have no unit at that depth and switch off on their own. I'm also confirming the gating for the trigger units on each row, where a strong bias keeps them quiet unless the weights on their own row's cells fire.

Still working out the fire default: I'm weighing whether firing constantly costs anything, since a new target might wait up to four frames for the cooldown.

Still working through the enemy submarines' bullet spawn position and how their shots move, so I'm checking whether a bullet in front of an enemy sub overlaps its cells.

Now I'm checking the collision rules again: a bullet sitting on our cell at the start of an update is fatal, and so is moving into an enemy's cell, which the danger window already covers in columns 3 to 6.

Now I'm working through a simulated sequence: the sub starts at the surface and the homing signal pulls it right, but the dive term wins, so it drops into row 1 and then row 2 while still tracking the enemy approaching in its row.

Now I'm checking the enemy spawn timing and the row-2 idle state, with the sub firing left by default. Once an enemy appears in a row three or lower, the pull should draw the sub down toward it, and I'm checking whether the danger below at row 6 would block that move.

Now I'm checking how the sub reaches row 6 and turns to face the enemy, which takes one right move before firing. Divers are next: they spawn at frame 31 and the sub waits in position for them to reach the center, while enemies keep appearing and the pull weights decide which one it chases. Once oxygen drops below 60, the rise term should take over and send the sub to the surface.

Now I'm working through the survival risks: enemy bullets, sticky moves, enemies on both sides, and blocked escapes. I'm also checking how the difficulty ramps up after each surfacing, since the spawn interval shrinks and the sub's speed increases every second surfacing.

Now I'm working through the timing: after six surfacings the enemies move every three frames and spawn every fifteen, and by about nineteen surfacings they spawn every two frames, so the game gets very dense. A surfacing cycle runs roughly 140 to 200 frames, which suggests a good policy might last only five to ten cycles. Next I'm checking how many enemies spawn per cycle to estimate the points.

Now I'm estimating the payoff: roughly 9 points in the first cycle and around 18 by the tenth, so a policy that kills about half the enemies might land near 25 to 30 points, which should be competitive. I'm also noting that the 6-diver bonus adds up to 10 more, but there's a counter bug where the diver count drops to -1 after the bonus.

I'm working through the diver counter: after the six-diver bonus the count goes to -1, so the diver bar looks empty and the policy would read that as zero. That means it would need to collect two more divers before it sees a surfacing signal.

Now I'm checking the divers case again: with six collected the counter maxes out, so any further divers can't be picked up while it sits there.

Now I'm checking whether the diver bonus is worth chasing: with six divers the bonus is only a few points at moderate oxygen, so I'm weighing whether to add logic that surfaces early when the count hits six, and deciding that the diver bar can't be read at higher oxygen anyway. I'm also about to recheck how the surfacing threshold at row 2 fires once oxygen drops below 60.

I'm considering whether the sub should rise only when a diver is actually on board, since with no divers it would otherwise rise to row 2 and stall. I'm weighing whether tying the up term to the visible diver count helps, but it would push the sub down whenever the count is zero at moderate oxygen.

Now I'm weighing whether the rise can be made conditional on a visible diver: any oxygen-based term that suppresses upward targeting when the count is zero would also push the sub down in the common case, so that's a poor trade. I'm leaning toward keeping the rise unconditional.

I'm considering whether the rise could be gated by a spare unit that fires only when oxygen is low and a diver is on board, so the sub doesn't surface empty-handed. The catch is that the upward term would still conflict with the downward pull whenever the diver count is zero, so I'm weighing how to separate those two cases in a second layer.

Now I'm weighing how to handle the diver case: the rise should only win when a diver is on board, so I'm considering a separate spare unit that flags "oxygen low and no divers," which could let the hunting pull win in that state.

Now I'm weighing a layer-2 fix: the rise should lose when no diver is aboard and an enemy target sits below, so I'm considering adding a separate starvation unit and tuning the logits so the hunting pull wins in that state.

Now I'm checking whether the rise term, which fires whenever oxygen is low, would override the stay-in-row behavior when a diver is approaching in my row. It would pull the sub upward and cost the diver, so I'm weighing whether that conflict is acceptable under the starvation state.

Stuck on how to keep the sub hunting divers when its diver count is zero and oxygen is low, since a linear rise term would override that. I'm weighing whether it's worth handling that starvation case at all, given it might end many cycles, and considering whether pushing diver hunting harder could avoid it.

Now I'm weighing a different fix: raising the diver weight from 1.5 to 2.0 so the sub prefers divers over enemies, which builds the count faster and leaves more buffer before oxygen runs out. The cost is fewer enemy kills, and I'd still get the bonus when the count reaches six. I'm also thinking about a diver in my row, where a stay term of about -4 should keep the sub from leaving while it approaches.

Now I'm thinking about whether the sub can tell approaching divers from receding ones in its own row, since the trail cells on each side should separate them. A diver to the left that is moving right would leave its trail on the left, which could be used to keep the sub in place while it approaches.

I'm weighing whether the trail cells on each side of the sub could tell an approaching diver from a receding one, but a window that spans the sub's own back cell gets messy, and enemy trails would mix in too. I'm also estimating that a receding diver stays in the row for about 24 to 30 frames before it reaches the edge.

I'm weighing whether the sub could tell approaching divers from receding ones in its own row by looking at which side the trail sits on, with the trail on the outer side for an approaching diver. I'm sketching a per-row weighted function over the columns to capture that, though the per-column weights are still unclear.

I'm working out how the approach-versus-recede distinction could be encoded per cell: for a diver on the left half, approaching means its trail sits one column to its left, receding means it sits to its right. So I'm trying to pick weights where the trail term makes the approaching case positive and the receding case non-positive, which means the trail weight has to shrink toward the center.

I'm working out a per-column weighting for the left half of the row: diver cells get a weight that grows with column, and trail cells get the negative of that, so an approaching diver scores positive and a receding one scores negative.

I'm checking whether enemies on the left side would also register as repelled by the trail term, which would make them push against the approach signal, and roughly estimating how strong that negative pull gets.

Checking the sign convention for enemies on the right half, where the weights mirror the left, so the approach signal stays positive for divers and nonpositive for receding ones.

Checking the boundary cases at the center: a right-half diver just outside the midline, or a left-half one just inside it, gives a zero score instead of the negative one I want, so those near-center divers are ambiguous. That's acceptable since they're about to be collected or have already passed. I also need to account for enemy trails, which would feed into the same term and push enemies away.

I'm trying to cancel the enemy trails out of this approach signal, since an enemy's trail would otherwise push enemies away. One option is to add a term that rewards the enemy's own cell in proportion to its column weight, which should roughly offset the trail contribution.

I'm checking whether the diver indicator's weight still leaves enemy trails pushing enemies away, and I'm adding a term on the ch1 channel to offset that contamination.

Checking the sign for enemies on the right half, the weights come out mirrored, so an approaching object scores positive and a receding one negative. The rest of the row sum works out to a net of approaching minus receding objects.

I'm checking the edge cases for this approach-detector: objects at the very edges have trail cells off-screen, so they score zero until their first move. Near the center, an object approaching from one side gives a score of 1 while one receding gives 0, which is still usable.

I'm compensating for the sub's own back cell in its row by adding a constant that cancels its trail contribution, since it sits at column 4 or 5 whenever the sub is at home.

I'm combining the approach measure with the enemy and diver counts into one target score per row, weighting each term so the sub can rank rows by how much is coming toward it.

I'm combining the enemy count, the diver count, and an approach bonus per row, with the approach term rewarding objects heading toward the sub and penalizing those moving away. The sub's own back cell gets compensated, and I'm settling on a single weighted sum per row as the target score.

I'm settling on enemy base weight 1.5 with an approach bonus of 1, so approaching enemies come out around 2.5 and receding ones near 0.5, and I'm weighing whether divers should use the same split with the extra diver bonus on top.

I'm settling the per-cell weights: a plain object cell gets a base weight plus a distance term, and the trail cells subtract the distance term. That puts diver scores at 3 when approaching and 1 when receding, enemies at 2.5 and 0.5, and bullets at -0.5.

I'm settling the weights by column: the trail cells contribute m(c) at their column, so the bullet and diver weights line up across the row. The per-column values come out as a ten-element list for each channel, so one assignment per row and channel covers it.

Now I'm working out the "my row" stay term, where enemies in the sub's row count as shootable and divers count only if they're approaching.

I'm checking the stay term for my own row: enemies there count for about 4 each, approaching divers add a bit, and receding divers subtract, with a fixed offset for the sub's back cell at home. The bullet case is still unresolved, since an incoming bullet would score positive for staying.

I'm checking the stay term for my own row: enemies there get a large weight, approaching divers add a little, and receding divers subtract, with a compensation for my back cell. Trails that land on my own cells don't change the binary value, so the compensation may slightly overcount, but that's minor.

I'm defining a per-row pull value that weights each row's cells: the diver and enemy cells count positively, bullets count against, and trail cells subtract. The up-and-down pull on the sub then sums these row values weighted by distance, with the rows above and below pulling in opposite directions. I'm also noting that a receding diver could leave a negative value in its row, which I'll have to account for.

I'm checking how a bullet and a trail cell in one row contribute to the pull, and whether any trail can exist without an object behind it. The only sources are enemies, divers, and the sub's back cell, so I'm working out a typical row with one approaching enemy.

I'm working through the stay term for my own row: an approaching enemy there scores about 7, and the pull from a single approaching diver at distance 1 comes to about 6, so I'd stay put. Two divers close by would push the pull above that, so I'd leave. I'm also setting the escape value at 20 per nearby danger and the oxygen values at +20 for up and -14 for down.

I'm adjusting the danger check so a diver in the adjacent row can't cancel out an enemy's penalty, since a diver at column 2 would otherwise add back the points that an enemy at column 4 takes away. I'll drop the subtraction there and just weight the enemy cells directly.

I'm dropping the diver's extra weight at the outer columns, since a diver there would otherwise cancel out an enemy's penalty. For those two columns I'll use a smaller penalty for enemies, so they only mildly discourage a move.

I'm now going over the escape check for my own row and how the danger windows in the adjacent rows should weigh enemies and bullets at distance two, to see whether a partial penalty is enough.

I'm working out the escape rule for close bullets and divers: cells two columns out get a smaller bullet weight and a negative diver weight, so a nearby diver can't cancel out a bullet's pull to escape.

I'm simplifying the escape term so that bullets two columns out add a modest push to leave, enemies there add very little, and divers there subtract. Distance-one cells in the sub's row get the full weight, and I'm settling that ESC rule for now.

I'm working through the gating weights for the up and down units, making sure they're large enough to outweigh the other terms whenever the sub isn't in that row.

I'm estimating the worst-case totals for the pull, escape, and oxygen terms, which come to roughly 100 in the extreme, so I'm setting the gating weight for the up and down units to 150 to stay safely above that.

I'm defining the layer-1 units for each row: a threshold unit for each column of the grid, an up-movement unit, and a down-movement unit, indexed so that the threshold units come first, then the up units, then the down units.

I'm laying out the rest of the layer-1 and layer-2 units now: the zero-feature and left/right home units, the unused slots, and then the up and down gating units.

I'm setting the layer-2 units for the row-up and row-down decisions, and the turn-right unit gets a weight and bias that make it fire on a positive sum over the row's threshold units. The turn-left unit does the mirror image, with the same weights negated and an extra term that suppresses it when the sub is at the home position.

I'm laying out the output layer now: the sub-units for the row-up and row-down choices and the turn-left and turn-right units, each wired to the threshold, home-position, and zero-feature units with fixed weights and biases.

Still writing the output-layer biases, filling in the logit weights for the up, down, turn and fire outputs.

I'm checking the fire term: with every signal off, the bias leaves fire at only about 80% against the other actions, which is too loose since a random up or down move could be fatal. I'll raise the fire bias to 8 so it dominates almost all the time.

I'm setting the output weights so that the fire action sits at a bias of 8, since anything lower leaves random moves too likely. The vertical moves get 26 and the turn and homing moves get 14 and 20, so they clear the fire bias. When a turn and a homing signal point the same way they stack to 34, and when they oppose each other the left move wins by 6.

Checking the output weights: the up and down logits come to 13 each, with the turn logits at 7 and the homing logits at 10. The row decisions are fixed, so the leftover margin is what remains after the fire bias of 8.

Still working out the weight layout for the layer-1 units, with the gating weight set so the threshold units for each row stay out of the way.

Still filling in the weight matrix for the threshold units: each row's pull term gets its ch0 cells weighted at 10 with a bias of -20, then the left and right danger cells get a fixed negative and positive weight, plus the orientation cells in the middle columns.

Still filling in the weight matrix for the threshold units: each row's left and right danger windows get fixed weights, and the orientation cells in the middle columns are set to pull in opposite directions.

I'm weighing whether enemies close to the sub should count more than far ones, since two distant cells on one side could otherwise outvote a single nearby threat on the other.

I'm settling the turn rule: when the sub faces left, a right turn needs the right-side enemy weight to beat the left-side one by more than half the threshold, and the mirror condition applies facing right. A single enemy at any column clears that bar, but when enemies sit on both sides I need the difference to exceed that margin, so I'm checking how the graded weights work out in a concrete case.

I'm checking the turn threshold against the graded enemy weights: with the target at 0.9, a single enemy at the nearest column gives a total of about 1.0, which clears it.

I'm checking tanh saturation: with larger weights the threshold margin collapses, so I'm shrinking the scale to keep the enemy-side weights in the linear range, taking them down to about 0.2 to 0.4 with κ at 0.3 and the threshold at 0.45.

I'm weighing whether to keep the enemy weights graded by distance or make them uniform, since the tradeoff only matters in the rare case of an enemy and a bullet on one side against a single enemy on the other. I'm leaning toward a mild gradient, with the far columns weighted at half the close ones.

I'm checking the graded version next: near-column enemies at full weight, far ones at half, to see whether the margins still hold once the weights aren't uniform.

I'm checking the margins on the graded version: a single far enemy on the wrong side only clears the turn threshold by a hair, so the weights need a little more room.

