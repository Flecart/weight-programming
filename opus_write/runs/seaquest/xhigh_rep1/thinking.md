I'm sketching out a hand-built policy network for MinAtar Seaquest. The sub starts at the top, facing left, and oxygen drains only while it's below the surface, so I need to watch that budget. Surfacing without any divers ends the episode, so I have to

I'm weighing what a typical score looks like here, since a basic policy that shoots enemies and dodges collisions should pick up a few points. The plan I'm considering is to dive to a fixed depth, hold position, and fire in the direction I'm facing, turning or dodging vertically when enemies come from behind. Enemies move slowly and bullets travel one cell a step, so the main constraint is that I can't surface without a diver, and I can't survive past the 200-step oxygen limit.

Surfacing only helps if I have a diver aboard, so each return to the top costs one diver. Divers spawn about every 30 steps, so I'd need to pick up roughly one per oxygen cycle, which looks feasible if I chase them.

I'm checking how the diver count fits into the observation: the gauge row is shared between oxygen and divers, so the bars overlap when both are high. Column 9 can only mean full oxygen, but column 8 is ambiguous, since it could be a diver or oxygen near 180.

I'm checking the oxygen gauge arithmetic: oxygen reads as oxygen divided by twenty cells, so column 8 only lights from oxygen once it reaches 180. Below that, a lit column 8 means I have at least one diver. Row 9 holds only the gauge, since enemies and divers never leave rows 1 through 8, so I can read it cleanly.

I'm settling on a hand-built policy for the moment, since trained networks of this size probably don't score much better than a modest heuristic. Before choosing a strategy I want to pin down the danger mechanics, so I'm working out how enemies and bullets interact with the sub during each step.

I'm now looking at how enemy subs move: each one only shifts a cell every few steps, governed by a countdown timer that gets shorter as the game speeds up.

Enemy bullets fire from the sub's position every 11 steps and travel one cell per step along its row, so they're a threat only when they sit in the same row ahead of me. My own bullets move one cell right after spawning and hit anything they land on, and I'm checking whether an enemy can slip past one by stepping into it on the same turn.

I'm checking the collision rules more closely: only the sub's front cell can be hit, and enemies move after the player each step, so an enemy whose timer runs out right next to me can step onto me in the same turn.

I'm working through how the enemies move and how fast I can fire: enemy subs step once every six steps, and my shots can only go out every five, which shapes how I should line up on them. Facing matters too, since an enemy approaching from behind means I'd need to turn with a left or right press before I can shoot back.

I'm checking what happens at the walls: pressing toward a wall keeps me in place but still turns me, so I can face the side enemies come from without moving. At the left edge facing right, an enemy spawning on my cell kills me on the spawn turn, which is a real risk over a long episode, roughly one in sixteen per spawn by my estimate.

I'm weighing a simple priority list for the policy: shoot anything dangerous in my row that's coming from the way I'm facing, move vertically away from threats coming from behind, and otherwise steer toward enemies or divers.

I'm thinking about how to represent the sub's position in the input, since the front cell is distinguishable from the back only by combining the sub channel with the trail channel, which a single linear first-layer unit can't do cleanly.

I'm trying to tell front from back using only channel 0 and channel 4: the back cell lights both, while the front lights only channel 0 unless an enemy trail happens to sit there. The open question is whether a single linear sum over columns can encode which side the front is on, since the trail channel also picks up enemy trails and muddies the signal.

I'm weighing a simpler alternative to the orientation problem: keep the sub in one fixed column and patrol vertically, firing whenever the cooldown allows. That sidesteps needing to read which side the front is on from the trail channel.

I'm working out whether the sub's orientation can be read linearly from the input, since the back cell shares the trail channel with enemy trails and that noise could blur which side the front is on.

I'm weighing whether a linear first layer can recover the sub's orientation from the trail channel, since the back cell carries both the sub and trail signals while enemy trails add noise. Column-weighted sums over channel 0 are symmetric between front and back, so orientation has to come from channel 4, and I'm checking whether a few units can separate it cleanly.

I'm checking whether a single linear unit can separate the sub's back cell, which lights both channels, from the front cell, which lights only one. Doing that per cell would take about a hundred units, so I'm looking for a way to combine the columns into a sum instead.

I'm considering whether to avoid needing orientation altogether by controlling it through movement, so that moving left faces left and moving right faces right, with the sub's facing following from its last horizontal press.

I'm realizing that shuttling between columns 4 and 5 won't help, because both facings put a sub cell in each of those columns, so channel 0 looks the same either way. Telling the back cell apart needs channel 4, and I still have to check whether that's achievable with the units I have.

I'm checking whether I can tell the sub's back cell apart by pairing columns 4 and 5 with the trail channel, though enemy trails in other rows would add noise. I'm weighing whether a sum over rows could separate the two facings well enough to be useful.

I'm checking whether the orientation signal can come from the difference between columns 4 and 5 in channel 4, summed over rows. A facing-left sub puts its back cell in column 5, which adds positive signal, and facing right does the reverse. The catch is that enemy trails in those two columns add noise, though since the trail frequency is fairly low, it might still be usable.

I'm considering a policy that ignores facing entirely: fire whenever an enemy is in my row, accepting that some shots will miss if the enemy is behind me, and dodge vertically from threats. Then I'm wondering whether the second layer could combine per-row signals for each of the sub's possible rows, though the first layer only has 32 units to spend on that.

I'm thinking about giving each row its own units so a second layer can combine "sub is in this row" with "enemy on the right side of this row," though with only 32 first-layer units that gets tight. A linear unit can't multiply the sub's position by an enemy's position directly, so I'd need a thresholded unit per row to act as an AND.

I'm considering a per-row unit that acts as an AND of "sub is in this row" and "danger is in this row," which would take about eight units for rows 1 through 8. I'm also thinking about holding the sub near the center columns and shuttling between columns 4 and 5 to turn, though the orientation question is still unresolved.

I'm weighing a simple fixed policy, holding a row and firing constantly, against the stronger options. It would likely die once enemies approach from behind, so I'd guess moderate scores at best, maybe in the single digits to low teens for a small network.

I'm weighing a fixed policy that surfaces to extend survival, noting that the surfacing ramp only slightly raises difficulty, and I'm budgeting the 32 first-layer and 32 second-layer units to see whether that's feasible.

I'm considering a dodge-first approach: shoot enemies as they come, and move vertically into rows that are clear of danger near the sub, then line up to fire. I'm also noticing that if the sub stays at column 0 facing right, its back cell would wrap around to column 9 of the same row, which could be a usable orientation signal.

I'm checking the edge case where the sub sits at column 9 facing left, since its back cell would land at column 10 and fall outside the grid. Moving left only ever steps the sub down to column 8, so reaching column 9 while facing left seems impossible, which leaves the wraparound at column 0 facing right as the only case to consider.

Next I'm looking at the walls: at the edge columns a bullet leaves the grid at once, so those positions are useless for shooting. Orientation at the middle columns depends only on the last horizontal move, so I'm thinking about whether a global weighted sum over channel 4 can recover it, and whether channel 2 can cancel the trail noise.

I'm working out whether the sum of column-weighted channel 4 minus channel 2 gives the back cell's position minus the enemies' trail directions, since each trail sits one cell behind its enemy. The edge clipping at spawn is the wrinkle I still need to account for.

I'm checking whether the sum over channel 0 minus twice the difference of channels 4 and 2 separates the facing directions, since the trail term is what introduces the error at the screen edges.

I'm going to try to cancel the trail noise with a period-2 weighting on channel 4, so that its contribution for each entity matches the negative of channel 2 regardless of its direction.

I'm settling on the alternating weight (-1)^c for both channels, since it cancels each trail against its enemy's position. That leaves the sum equal to the back cell's parity sign, plus whatever errors the edges and overlaps add. The sub's front cell then has the opposite parity, so parity alone gives me the back cell's location, but I still need to see how that combines with the front cell's position.

I'm checking whether the parity of the back cell's column, which the sum of (-1)^c over channels 4 and 2 isolates, can tell me the orientation once I know the sub's column pair. The plain alternating sum over channel 0 is always zero, since the two sub cells are adjacent, so I need some nonlinear step tied to the sub's position.

I'm checking the edge cases in the trail cancellation: an enemy spawned at column 0 moving right has its trail off-grid, so the channel-2 term leaves a +1 error for roughly the first six steps, and a right-spawned enemy at column 9 gives the opposite -1 error.

I'm working through edge errors in the trail cancellation: an enemy at column 0 moving left has its trail at column 1, so zeroing the weight at column 0 doesn't fully fix it. I'm considering how to assign the edge-column weights.

I'm checking how the edge columns should be weighted: an entity at column 0 moving right has no visible trail, while one moving left does, so setting the weight to +1 or 0 at column 0 each leaves a different error.

I'm settling on half-weights at the edge columns to split the spawn error between the two cases. Overlaps where entities share a cell are rare enough that I'll mostly ignore them, and enemy bullets stay out of the sum since they leave no trail.

I'm checking how the overlap and edge errors affect the parity sum, which should roughly recover the back cell's parity. The problem is that the sum over channel 0 is always zero, so I can't read the front cell's parity from it directly, and I'm still looking for a way to pin down orientation.

I'm noting that a plain alternating sum can't recover the sub's orientation, because the only weightings that cancel trail noise are period-2, and those carry parity information alone. The column-weighted sum gives the sub's mean position, which isn't enough to pin down which cell is the back one.

I'm looking for a way to make "c is even" show up in the channel 0 sum, which the plain alternating weights can't do because they always cancel to zero. I'm trying weights f on the two adjacent columns so that each pair {c, c+1} gives +1 when c is even and -1 when c is odd.

I'm testing a weighting f with alternating-sign structure, setting the values at each column so that adjacent pairs sum to +1 or -1 depending on whether the left column is even or odd. I'm picking a = 4.5 so the values come out to a concrete table, and checking the first pairs to see that the pattern holds.

I'm checking that the two parity signs multiply to give the orientation, and that a product like that needs two separate units to combine them, since it isn't linear.

I'm combining the two parity signs into a single orientation signal, using two layer-1 units that each test one matching-sign case. Their sum gives a value near +1 for right and -1 for left, and the noise from the edge weights could still shift P slightly.

I'm checking how often entities sit at the edge columns, since those spots are where the trail weighting still leaves error. I'm estimating the expected count of entities at column 0 to decide how much weight to give the edge trail term.

I'm checking the expected frequency of edge entities and settling on half-weights there, since spawned right-movers and left-movers reaching the edge leave opposite errors that roughly balance. The sign check works out: weighting both channels by (-1)^c cancels each trail against its entity, and the back cell's parity still comes through the sum.

I'm checking the edge weights for the rightmost column, where the trail sign flips, and then turning to the overlap cases where a diver shares a cell or trail with an enemy.

I'm settling on the orientation: the sub's facing comes from comparing the back cell's parity with the column parity, combined through two layer-1 units that each test one matching-sign case.

Now I'm weighing a simpler policy: pick a vertical target row and hold position there, firing toward whichever side an enemy appears, though that only catches enemies in that single row. I'm leaning toward tracking the nearest enemy vertically instead, which needs danger checks so the sub doesn't step into an enemy's path.

I'm weighing how fast enemies arrive from the edges, roughly 24 to 30 steps to reach the center, which leaves time to shift rows and fire before they get close. Tracking an approaching enemy looks feasible, though an enemy sub's bullets travel back along the line I'd be aiming down, so lining up has its own cost.

I'm checking whether a sub firing from the same row can hit me. Its bullets travel toward me at one cell per step, and mine toward it, so they pass through each other and I need to dodge if a shot is already in flight.

I'm noting that enemy bullets spawn at the sub's position and move the same step, so they'll hit me if I'm in their row. Dodging vertically is the response, though my reaction time and sampling noise leave some risk.

I'm working out how to handle vertical moves safely: stepping into a row where an enemy sits at my column or is closing in is deadly, and so is entering a row with an enemy bullet approaching. The policy will need to compute everything relative to the sub's current row and column.

I'm weighing a design where the sub stays in columns 4 and 5, so column-relative checks become fixed absolute ones, and only the rows vary.

I'm settling on keeping the sub in columns 4 and 5, so that column checks become fixed absolute ones and only rows vary. The remaining question is how to keep it centered there while still turning to face whichever way it needs to go.

I'm weighing how close enemies at column 6 are to our front cell. If I turn toward them while they're approaching, the timing could put us in their path, so I'm thinking about which engagements are safe.

I'm working out target selection next: whether to pick a row to move to based on enemy positions, and how to tell enemies, enemy bullets, and divers apart from the channels.

I'm thinking about the vertical control now: moving up or down toward a target row, but a single sum over enemy rows won't pick out the nearest one. I'm considering per-row units that flag where enemies are, combined with the sub's own row, to tell which enemies lie above or below.

I'm trying to find a single linear unit that flags whether any enemy sits above the sub's row, by weighting enemy cells according to their row relative to the sub. That would avoid having to build a separate AND unit for every row pair.

I'm trying to find a way to tell whether an enemy sits above or below the sub's row. One option is a separate unit for each possible sub row, each firing only when the sub is in that row and an enemy lies in a row above it. That's workable but needs a lot of units.

I'm working out whether one unit per sub-row can detect an enemy above or below, which would mean 16 units in total. Each would fire only when the sub sits in that row and an enemy lies in the rows on one side. The catch is that enemies on both sides would cancel out, so I'm considering weighting each enemy by how close it is.

I'm working out a gated unit for each sub-row that sums enemy positions weighted by distance and fires only when the sub sits in that row, though I'm still checking whether the inactive case really drops to a neutral value.

I'm working out how to get both vertical directions out of a per-row unit. Gating on the sub's row leaves the inactive case saturated, so the active case only adds a partial difference, which means a single unit gives one-sided output. Splitting into separate up-pull and down-pull units per row would fix that, though it doubles the count.

I'm checking the sign convention: with each sub-row unit saturated at -1 when inactive, the sum reduces to a single signed pull term plus a constant that the bias absorbs, so one unit per row can give both directions.

I'm settling the bias so that the active sub-row unit gives a clean signed pull, and I'm checking the row-0 case, since at the start the sub sits in row 0 where no unit fires and the sum would come out wrong.

Now I'm settling on eight per-row units for vertical pull, though I still need to handle danger avoidance and whether enemies lie to the left or right. I'm considering a second layer that combines the sub's row with left and right enemy features, so each row can be checked against where enemies sit relative to center.

I'm working out a per-sub-row unit that gates on the sub's row and checks for enemies to its right, since a single layer-2 unit can't AND those conditions across rows.

I'm sizing up the feature count: 8 units for the pull, 16 for left and right enemies in the sub's row, plus orientation, centering, and oxygen or diver handling, which lands near 30 units. Danger checks for vertical moves would push it further, so the budget is tight.

I'm now weighing whether a single fixed-row unit can handle both sides of a vertical decision, since each per-row unit can carry only one signed value. Separate features for danger on the left and right within the sub's row might be cleaner, but I'm stuck on how to combine them without a separate unit for every row. Fixing the sub's row would simplify things, but it would cut down how many enemies I can hit, so I'm considering whether layer 2 can combine per-row features that don't depend on the sub.

I'm weighing whether a layer-2 unit can combine sub-row gating with enemy-row features, but a linear threshold can't express an OR over eight ANDs, so the per-row gating has to happen in layer 1. That gives each sub row only a few scalar outputs. I'm now wondering whether the sub could be limited to a band of rows, which would free up units.

Now I'm thinking about whether the sub should be limited to a band of rows, since that would free up units but leave some enemies unreachable. Shooting probably needs to cover all eight rows. For firing, the key is whether an enemy sits in my row on the side I'm facing, and orientation can come from two units.

I'm deciding on the firing and turning logic from the signed per-row pull: fire when the signed difference points toward the facing direction, and turn when it points the other way.

Now I'm weighing how to handle vertical dodging: an enemy approaching from behind in my row, or one moving toward me from the side, and whether I should step up or down into a row where a threat could land on my column or the one beside it.

I'm settling on a single signed vertical score per row: pull toward enemies, minus a large term for danger above and plus one for danger below. If danger exists on both sides the terms cancel, which means staying put, and that may be acceptable when the current row is safe. I still need to deal with an enemy in my own row that is closing in.

I'm folding the row-danger check into the per-row scores too, though it might make them too complicated. Then I'm budgeting units: 16 for the per-row scores, 2 for orientation, and 14 left for oxygen, diver, centering, row 0, and cooldown. For cooldown, I'm looking at friendly bullets in the third channel, since a bullet fired from the middle columns clears the screen in about five steps.

Now I'm checking the cooldown: a friendly bullet on screen roughly means the shot is still reloading, and firing while on cooldown just does nothing, so it's harmless. Next I'm working out turning versus firing, where an enemy to the right means pressing 'r' if I'm facing left, and 'f' if I'm already facing right. I'm starting to think about how the column centering should keep the sub in cells 4 or 5.

I'm settling the centering term: the sub's mean column relative to 4.5 pushes toward 'r' when it sits left of center and toward 'l' when it sits right, and that pull has to be weighed against the turn term.

I'm settling how each row's vertical score is built: enemies below add a pull toward going down, enemies above pull up, weighted by distance, so I'm writing out the linear function for that per-row signal.

I'm weighing which channel should drive the vertical pull: channel 2 picks up enemies and divers, channel 1 picks up enemy bullets, which I don't want to attract the sub. A signed mix of the two, with bullets counting against and divers counting for, might give a cleaner per-row score.

I'm checking whether enemies far out in my row are still worth targeting, and realize that bullets outrun enemies, so any enemy in the facing direction in my row is a valid target regardless of how far it is. Enemies approaching within a cell or two of my column make the row above or below risky to move into.

Divers drift horizontally too, so a diver coming toward the center will eventually cross the sub's cell if the sub sits in that row.

I'm weighing whether a row-danger signal above or below the sub should push the vertical score, since that could cancel out the pull toward enemies. Moving up when there's danger overhead would be bad, but a push away from danger might override the pull when I actually want to hold position and fire. I think the fire decision needs to dominate the up/down logits when an enemy sits in my row and I'm facing it.

I'm checking the danger from an enemy in my own row that is closing in behind me. Turning to face it would step me toward it, so I'm working through whether firing from my current facing or stepping away would be safer.

Working through how a near enemy at column 6 changes things: turning toward it could let it step into my cell, so I'm weighing whether to fire from my current facing or dodge vertically instead.

I'm weighing whether to dodge a bullet coming along my row from an enemy sub, since it would reach my front cell in about two steps, so I'd need to move vertically out of that row.

I'm now setting up a scalar for the bullet threat by summing the difference between the two channels across the nearby cells in my row, so enemies cancel out and bullets stand out. Alongside that, I'm defining a separate scalar for enemies to the right minus those to the left, which will decide which way I face and when to fire.

I'm tallying up the per-row scalars, which comes to 24 units and leaves only 8. I'm wondering whether the bullet-threat term could fold into the vertical score instead, with the sign set by the safer direction while the magnitude still says to move. Another option is a separate dodge signal that raises both the up and down logits and suppresses fire, leaving V to pick the direction.

I'm thinking about whether the per-row gating is really needed, or whether some features can be handled another way. Each row needs its own signal because the sub's row is effectively a one-hot choice, so I'm checking whether a few per-row scalars with nonlinear responses could carry several pieces of information at once, with the next layer decoding them through thresholds.

I'm weighing whether each row really needs its own gated unit, since the sub's row acts like a one-hot choice. Layer-two thresholds might be able to decode several features packed into one per-row value, though with tanh saturation that gets messy fast.

I'm sorting out the per-row units: in-row targets drive turning and firing, vertical pull and move safety are merged into one per-row signal, and in-row bullet danger gets its own. That's 24 units, which leaves 8 for orientation, column centering, the diver logic, and the row-0 case.

I'm considering whether the in-row bullet-threat signal could be folded into the vertical score instead of getting its own unit, pushing the sub toward a default direction when a bullet is closing in on its row. The push would need to stay weaker than the safety terms for adjacent rows, so it doesn't override them.

I'm weighing whether to fold the in-row bullet threat into the vertical score as a default push, and checking that the adjacent-row danger terms would still outweigh it. I'm also noting that enemies closing in from behind are a threat unless I turn, so I'd want the facing signal weighted by how close each enemy is.

I'm sizing the per-row units: one vertical signal that folds in the pull, the safety check, and the bullet dodge, and one horizontal signal for target direction and firing. That's 16 units, which still leaves room in the 32-unit budget.

I'm settling on a sign-and-magnitude split for the in-row target signal: D flips positive or negative depending on which side has enemies, and its size indicates whether any are there at all. From that, the fire and turn decisions reduce to thresholding D against my current orientation, which takes four layer-two units. Orientation itself will take two layer-one units, and I'm still working out how to combine them with D through a threshold.

I'm checking whether the orientation can be folded into the threshold for firing and turning: since the two facing units can't both be active, their sum acts as a single linear facing signal, so the AND with the target score is just a threshold on a linear combination.

I'm checking whether layer two can read the vertical signal directly, or whether the tanh nonlinearity forces another layer-two stage before the up and down logits.

I'm checking how to handle the oxygen and surfacing logic: the sub should surface when oxygen runs low and it carries at least one diver, and never surface without divers. Since surfacing means moving to row 0, I'm considering what the vertical logits should do when the sub is in row 1 and the up signal is active.

I'm checking row 1 specifically: with no enemies in row 0, the only thing that could push the sub up is the danger-below term, which would surface it by accident and drown it if it has no divers. So I'm zeroing that term for row 1 and making sure the pull downward can't lead into danger there.

I'm settling on a separate layer-one unit that signals whether the sub is in row 1 or above, since the per-row gated unit can't serve as a clean indicator. That indicator lets a layer-two unit push hard against the up logit in row 1 whenever surfacing isn't wanted, so the danger term can't accidentally drown the sub.

I'm working out the oxygen-low condition, where the gauge columns depend on how many oxygen cells are lit, and I need to separate those from the diver cells that share the same bar.

Checking the gauge columns against the oxygen levels: if oxygen is under 60, only columns 0 and 1 can be lit by oxygen, so column 2 is free of it. Column 2 lighting up would then mean oxygen is at least 60. Column 8 depends on whether there's a diver or the oxygen is at least 180.

I'm settling on a surfacing threshold for oxygen: column 2 can only be lit by oxygen, so the sub surfaces once oxygen drops below 60 and it has at least one diver, with row 0 reachable well within the time left.

I'm settling the oxygen threshold at column 2 being unlit, meaning oxygen under 60, since that column can only be lit by oxygen itself. Attraction to divers stays strong throughout, because they are worth collecting before oxygen runs low.

Now I'm checking whether a camping strategy works: parking in row 1 to shoot row-1 enemies and surfacing to refill divers. The catch is that surfacing needs at least one diver, or the sub dies, so the plan depends on collecting divers first.

Now I'm checking the surfacing timing: it only happens when the sub moves into row 0 without the surface flag set, and each surfacing uses up a diver. Oxygen does not drop while the sub sits at row 0, so the refill is a one-time event per visit.

I'm settling the per-row vertical units for rows 0 through 8, each gated to be active only when the sub sits in that row, and I'm checking that the row-0 unit only sends the sub down when no enemies sit in row 1 near the center. Then I'm counting the layer-one units for the vertical and horizontal signals.

I'm settling on a surface-desired unit that fires when oxygen is under 60 and column 8 is lit, meaning there's at least one diver. I'm also setting up a no-diver indicator from column 8 being unlit while oxygen is below 180, so the sub doesn't try to surface empty-handed.

I'm checking that surfacing can only be triggered by moving up from row 1 while the surface condition holds, so the oxygen reading near 180 can't make me surface by mistake. Once I've left row 0 for row 1, the surface flag gets set.

I'm now weighing the sticky-action risk: if the sub moves up into row 1 and the repeat-previous-action rule fires, it would step into row 0 unintentionally, which means a forced surface and a lost diver when none is available. So upward moves into row 1 need to be avoided unless surfacing is actually wanted.

I'm going to keep the sub out of row 1 unless surfacing is actually wanted, since a sticky repeat of an upward move could carry it into row 0 and cost a diver it may not have. So upward moves from row 2 only happen when the surface condition holds, and row 1 is for diving down from row 0.

I'm weighing whether to keep the sub out of row 1 entirely, since an upward move into it could repeat through the sticky-action rule and carry it into row 0 with no diver to spend. Restricting movement to rows 2 through 8 costs some row-1 targets, but avoids that risk, and I'd only pass through row 1 while diving down from row 0.

Next I'm weighing whether row 1 needs its own movement unit, given the sub could stall there when danger sits below. Counting the units so far, nine vertical and eight direction units plus a few helpers leaves room, though adding per-row dodge units would strain the budget. I'm still deciding whether that trade-off is worth it.

I'm now writing the vertical unit's formula, where each row's pull depends on danger above and below plus a threat term. I'm also considering a surfacing term tied to low oxygen, though a linear unit can only approximate the oxygen-below-60 condition rather than the full AND.

I'm weighing whether to let the surfacing unit override the vertical preferences directly, since a plain danger-avoidance term would push the sub the wrong way when oxygen runs low. I'm considering a layer-two up logit that combines the surfacing signal with the danger terms, though I haven't settled the exact weighting yet.

I'm working out how to scale the vertical pull, weighting each target row by its distance so nearer enemies count more. When a target sits in my own row I want the vertical signal near zero so I stay and shoot, and I'll handle that suppression in the second layer.

I'm weighing how to split the vertical signal into a soft pull toward targets and a hard danger term, since fire and turn need to win over small pulls but lose to real threats.

I'm still tuning the pull term, since with several enemies it could grow past the range where the danger signal stays clearly dominant. My current idea is to weight each target row by distance and cap its contribution, keeping the total well below the danger magnitude.

I'm weighing the pull strength: with four targets on the board, the sum could approach the limit, so I'm keeping each row's weight small. Now I'm turning to the danger term for vertical moves, which fires when an enemy sits in the row above near my front column, or when bullets are closing in on that column.

I'm now working out which columns count as danger when the sub moves into a new row: bullets could reach it from two columns away, while enemies only matter one column out. Since the exact front column isn't settled, I'm considering a wider band for bullets and a narrower one for enemies, perhaps giving the outer columns half weight.

I'm weighting the danger columns for a vertical move: enemies count in columns 3 to 6, and columns 2 and 7 get a smaller weight since only bullets there matter. I also want to flag in-row bullet threats, which should force a vertical dodge, but I'm still deciding how to handle bullets moving away from me.

I'm considering how bullets in my own row could threaten me, since one moving toward my column means a dodge is needed, and enemies approaching from behind at distance one also count as threats if I'm not facing them.

I'm settling on a default dodge direction for in-row bullet threats: down when the row is 4 or higher, up otherwise. I'm also setting aside adjacent enemies in my own row, since the existing firing and turning logic already covers them.

I'm noting that the threat term and the danger term can disagree, so when a bullet threat pushes one way and a danger below pushes the other, the net can land on a weak upward pull. That's a corner case I'm willing to accept for now, but I'm also considering giving threat its own per-row unit so it can push either direction and let the danger term decide, even though that costs eight units from the budget.

I'm still working out the row restrictions: rows 1 and 2 should never produce an upward pull from the vertical units, so the only way upward is through the surfacing signal, and the baseline up logit has to stay low enough to keep it that way.

Still checking how the up logit sits against the others, since even a small baseline could let the sub drift upward by chance over many steps.

I'm now checking how diver pickup works: the sub has to share a row and column with the diver, and since the diver crosses columns 4 and 5, either front column works. Reaching its row is feasible given the slow diver speed, though enemy pulls may compete with that goal.

Diver attraction stays constant rather than being gated by the oxygen gauge, since that would need a product of inputs a linear unit can't express. The pull for both enemies and divers comes from channel 2, and I'm leaving channel 1 out of the pull because it would also count bullets.

I'm now checking how the pull and danger terms combine for the same row, and whether enemies that are only shootable need a separate signal from divers, which I can't shoot anyway.

I'm settling on how bullets in my own row should be handled: I'll pick a default dodge direction and I'm not going to shoot at a bullet coming toward me, since firing doesn't stop it.

I'm setting the diver-and-enemy attraction aside for a moment and working out how an enemy in the same row should count. I'm weighting each column by its side: columns right of my front cells push right, and columns on the left push left, with closer enemies weighted more heavily so the turn follows the nearest threat. I'm also checking what happens when an enemy sits in one of my own cells, since that bears on which direction is safe.

I'm checking the turn logic: turning left from facing right just moves the front cell to 4 with the back at 5, and turning right does the reverse, so the sub stays within columns 4 and 5 either way.

I'm checking the centering logic against the turn logic: when the sub sits at cells {3,4} it has to recenter, but a turn in the opposite direction could also shift it, so centering needs to win once the offset reaches one column.

I'm checking whether the centering pull is actually needed: if the sub drifts one column off-center, the centering term and the turn logic can pull against each other, so I'm weighing whether to let firing take precedence while off by one.

I'm working out the in-row turn logic: pressing toward a target on the right while facing left means turning right, and firing when already facing it. Once a target is fired on, the policy keeps firing for a few steps until it's gone, even though those presses do nothing during cooldown.

I'm weighing whether the sub's own bullet could come back at it after a dodge, and how a new row's danger would affect the move.

I'm now weighing how bullets moving toward me in my own row should trigger a dodge, with threat cells covering the whole row since closer bullets need an earlier response.

I'm weighing whether bullets moving away from the sub still count as threats, since a bullet that has already passed my column could still be in my row. I'm leaning toward treating any bullet in my row as a threat unless it is clearly moving away, and accepting an early dodge as a cheap cost. The tricky part is that dodging out of the row also drops the shot at the enemy that fired.

I'm narrowing the threat check to the cells near my sub, roughly columns 2 through 7, and including the back cell since a bullet there moving toward the front hits next step. I'm wondering whether bullets already past my column are still threats, but without a trail I can't tell their direction from one frame, so I'm leaning toward counting any bullet in my row.

I'm settling on a threat window of roughly columns 1 through 8 with equal weight, since a bullet at column 7 still leaves two or three steps to react and an extra column of margin covers sampling noise. Bullets already past my column on the far side will keep registering for a few more steps, which is an acceptable cost.

I'm now assigning each row three features: one for the pull and adjacent-row danger, one for targets, and one for bullet threats. That makes 24 row features plus a dive-control unit, orientation and centering, which leaves a few spare units.

I'm settling on how the layer-2 units will combine the diver-and-enemy pull with the threat signal, starting with the fire and turn units for each facing direction.

I'm now mapping out the layer-2 units: fire and turn units gated on the pull signal and facing, a soft and a hard vertical unit driven by the row danger, a threat unit that pushes up or down and suppresses other actions, plus the surfacing, centering and row-0 control units.

I'm making sure the row-by-row threat signal doesn't push a sub up toward the surface in rows 1 and 2, since reaching row 0 with no oxygen would be fatal. I'm considering routing the bullet threat for those rows into the vertical-danger term so it only pushes down.

I'm considering folding the bullet threat into each row's vertical signal with a default direction per row, so rows 1 and 2 only ever push down. That would free up two units, but I need to check that a strong threat can still outweigh the pull toward the target.

I'm working out the threshold for the hard vertical level: with threat weighted at 3 and danger at 5, the combined signal stays strong enough, so I'm setting the hard cutoff to 0.78.

I'm settling on separate threat units for rows 3 through 8, since they can push in both directions, and folding the threat into the vertical signal for rows 1 and 2 so those rows only ever push down.

I'm checking whether rows 1 and 2 can still push the sub upward when the danger from below is counted, since a negative value there would make it rise toward row 0 with no oxygen. I'm considering dropping the below-danger weight for those rows and handling the threat in a different way.

I'm handling the up-restriction for rows 1 and 2 with a separate layer-1 unit that fires when the sub is in those rows. A layer-2 unit then subtracts a large amount from the up logit unless surfacing is active. That way the danger-below term can push the sub up without actually moving it, so it just stays put.

I'm giving the row-1 and row-2 up-restriction its own layer-1 flag for being in those rows, and a layer-2 unit that blocks upward movement there unless surfacing is active. For row 1, the dive keeps going down toward row 2 unless there's danger below, so I'm folding the downward bias into that row's vertical signal.

I'm now deciding whether the row-1 sub should also get a dedicated detector for nearby enemies, since without it a sub stalled in row 1 could not shoot an approaching enemy. I'm also noting that a threat in row 2 can only push the sub down, because the up direction is blocked there.

Now I'm weighing how much layer-1 capacity is left, and I'm going through the row units I've already assigned for the dive and the diver detectors.

I'm laying out the rest of the layer-1 units: four spare slots remain after the thread and orientation features. I'm also considering a gated unit per row, where the pre-activation drops by a large constant whenever the sub isn't in that row, so it only fires for the matching row.

I'm working out the gating for each row unit: a large negative offset whenever the sub is outside that row, so the unit only fires for its own row. With the offset sized to the largest feature value, the inactive units sit near -1, and the layer-2 sums stay predictable.

I'm checking how the row-0 case affects the gated detector units, since with every D unit inactive the sum comes out to about -8, which would read as a strong pull to the left. I'm weighing whether to add a dedicated row-0 unit or change the offset so the inactive units don't skew the sum.

I'm handling the row-0 case by adding a layer-1 unit that is high only when the sub sits in row 0. That unit offsets the baseline sum, so the fire and turn units read zero instead of a spurious leftward pull.

I'm checking the threat units for rows 3 through 8, where each one's output should read as -1 when there's no threat and +1 when there is. The inactive ones sit at -1 too, so the layer-2 sum stays neutral when nothing is present, and I'm making sure that holds when the sub is in rows 0 through 2.

I'm settling the row-0 case: the detector units for the other rows read -1 when inactive, which would skew the sum toward a leftward pull whenever the sub is in row 0. A dedicated row-0 unit that outputs 0 there would cancel that offset, and the threat units can avoid the problem by using a threshold so that no-threat and inactive both read -1.

I'm settling the row-0 offset: a D_0 unit that reads 0 at row 0 and -1 elsewhere lets the nine D units sum cleanly, and that brings the layer-1 count to 29 with three spare. I'm now asking whether D_1 earns its slot, since a sub stalled in row 1 with an enemy approaching would otherwise be unable to shoot.

I'm weighing whether the F unit is really needed, since the up-blocking for rows 1 and 2 could maybe be folded into the V_1 and V_2 signals instead. The catch is that without a way to clip the logit, danger below at row 2 would no longer stop a downward pull, so I'm keeping the F unit because it's cheap.

I'm making the row-2 threat push the sub downward through its vertical signal, and I'm keeping row 2's pull-up out of the picture so it can't drift toward row 1. For rows 1 and 2 the vertical signal is just the downward pull, plus a fixed threat term.

I'm checking the up-direction once more: the up-block for rows 1 and 2 is lifted only while surfacing is active, so a soft pull down can't fight it at that point. I'm also confirming that row 0 stays quiet, since surfacing is only triggered by low oxygen and gets cleared the moment the sub refills at the top.

I'm settling the input layout for each cell and channel, with the sub's columns fixed at 4 and 5 and the front cell at 4 when facing left or 5 when facing right. The features get defined concretely from there.

Still setting the weights for the vertical pull in rows 3 through 8, deciding which enemies in other rows should tug the sub up or down.

I'm setting the pull weights for each vertical unit, scaling them down with distance so a target far away tugs more gently. I'm also keeping row 1 out of the upward pull, since the sub can't reach it, and I'm wondering whether an enemy just outside the center columns in an adjacent row could still count as danger.

I'm defining the danger-above and danger-below terms for each row unit, with ch1 cells in the adjacent rows weighted more heavily in the centre columns, and I'm making the below-danger term subtract from the pull.

I'm realizing the danger terms would push the sub away from its target: an enemy in the adjacent row near the centre would drive a hard downward move that drops the sub out of line with a target it's shooting at. So danger should only block movement, not create it, and a single scalar for the vertical signal can't separate those two effects. I'm considering a separate per-row scalar to carry the blocking on its own.

I'm now checking whether a single signed danger scalar could cover both the blocking and the pushing, since the danger terms would otherwise drag the sub off target. Giving each row its own scalar would overrun the 32-unit budget, so I'm weighing whether the threat signal can absorb that job instead.

I'm weighing whether a single soft-versus-hard reading of the vertical signal can carry the danger-blocking on its own, so the sub doesn't get pushed out of line with its target.

I'm working out the down logit as a soft pull minus a correction whenever the hard danger term is active, so that a hard danger reading cancels the push down. The catch is that this same correction also hides any downward pull that sits underneath the danger, so I'm checking what that does to the sub's behaviour when danger and pull point in opposite directions.

I'm noticing that a pure additive danger term can't tell "block this direction" apart from "push the other way," so with both dangers active the sum just reduces to the pull and the sub could drift into danger. I'm wondering whether the asymmetric weighting can fix that without breaking the cancellation elsewhere.

I'm trying to make the danger signal block movement in each direction without pushing the sub away from its target. A single signed value can't cleanly do both, so I'm looking at whether different magnitudes for the above and below dangers, decoded with thresholds, could mark "block up," "block down," and "both" separately.

I'm trying a different encoding: put the two dangers at unequal weights so "block up," "block down," and "both" land at distinct levels. The catch is that tanh saturates these magnitudes, so I'm considering scaling the signal down so the levels stay separable after the nonlinearity.

I'm still weighing how to encode the danger so it blocks movement without pulling the sub off target, and I'm considering a layered decode with several threshold levels to tell "block up," "block down," and "both" apart.

I'm weighing whether to let an adjacent-row danger push the sub away, since that could pull it off a target in its own row, and I'm considering whether the push can stay small enough that firing or turning still wins.

I'm working through whether the adjacent-row danger term should be allowed to push the sub away at all, since that could move it off a target in its own row. Danger pushes around a magnitude of 4, which saturates to roughly 1, and fire at around 5 should outweigh it, so the sub holds still when it has a target lined up. If it isn't facing the target yet, the turn has to beat that push as well.

I'm settling on a fire logit of 6 for a target in line, and scaling the up and down logits from the signed danger value by about 2.5, so the sub moves away from the side with danger while still preferring to fire.

I'm checking whether the fire logit of 6 still beats the danger-induced moves, which it does, and whether a threat should suppress firing entirely so the sub doesn't sit still in a bullet's path. Without danger, the up and down logits tie with fire, so I'm weighing how much the fire suppression under threat needs to be.

I'm checking how the diver attraction in the same row would be handled, since divers and enemies share the same weight in the pull, and divers only matter for oxygen.

I'm weighing whether the diver term should count the same as enemies, since divers only matter for oxygen. I'm considering a half-weighted mix of the enemy and bullet channels for the fire signal, so a lone diver registers faintly without drawing as much firing.

I'm checking whether the diver term should carry the same weight as enemies in the pull. Turning toward a diver is harmless since the sub still picks it up as it drifts into the front cell, but firing at one just wastes cooldown.

I'm working out the orientation units next, computing a signed sum over the cells in each row with alternating signs, where the middle-column weights are halved at the edges.

I'm checking the sign convention for the two pooling channels: an entity contributes alternating signs across its cells, so the trail cancels it out, and the sub's back position enters with its own sign. I'm also confirming that enemy bullets and friendly bullets stay out of the sums.

I'm checking the parity signs for the two orientation units: the front column's sign pattern gives a value of +1 when the minimum column is even and -1 when it's odd, and I'm confirming that on a few cell pairs. Then the sub is facing right exactly when its back position has the same parity as that minimum column, so the two signs agree.

I'm checking that the two orientation units come out as facing right or left, with the parity signs P and Q agreeing in each case, and noting that edge noise in P can push the sum off its clean values.

I'm checking how much the tanh saturation costs: with K around 3 or 4, the half-unit parity noise from edge cells still leaves the orientation units close to ±1. The remaining worry is overlaps, where two trails land on the same cell or a diver and an enemy share one, which would flip a contribution by one.

I'm checking the edge cases in the orientation sums: an entity sitting at the far-left column, or spawning at the edges, contributes only half weight, so its trail leaves a small residual error of about 0.5. I'm also noting that entities overlapping on a single cell can flip a contribution, but the margins still hold.

Next I'm working out the pooled sums for the two orientation units, weighting the trail and body channels by column parity and the front-cell channel by a position weight, all scaled by K with a -K bias. Then I'll look at how the derived danger signal gets folded into the second layer.

I'm setting up the second-layer fire unit so it fires only when the danger-adjusted target signal clears a threshold and the sub is facing right. The idea is a linear term on the target strength plus a penalty of about 8 whenever the facing signal is off, which keeps the unit negative in every misaligned case.

I'm writing out the fire-left unit next, using a negated danger term and a penalty whenever the sub isn't facing left, mirroring the right-facing version.

I'm writing out the turn-right and turn-left units now, each gated on the danger signal and on whether the sub is currently facing the other way, and I'm weighing whether to merge the two fire units into a single OR-style fire logit.

I'm sizing the diver term for the danger signal, weighting each target by its column so a sub that is facing away from a nearby enemy still has to turn.

I'm checking what happens when the sub sits at columns 3 and 4, since an enemy approaching from the left could reach it in one step, and I'm assuming the turn-left and fire-left units handle that before the sub is hit.

I'm now considering the threat signal for the dodge units, counting bullets in each row near the sub while subtracting divers, since a diver sharing a row with a bullet would otherwise mask the danger and leave the sub with no reason to move.

I'm weighing a threat signal that counts bullets in each row near the sub, but a diver sharing that row with a bullet would cancel it out. I'm settling on a weighted form where a diver subtracts less than a bullet adds, so the threat stays positive when a bullet is present.

I'm settling the threat signal as bullets minus a fraction of divers, with the sub's own two cells counted at full weight, and I'm deciding whether columns 0 and 9 need to be included at all.

I'm settling how the threat signal should count bullets against divers across the rows near the sub, and whether to keep columns 1 through 8. Each row's threat unit then feeds a summed signal that flips on when a bullet is close.

I'm settling the dive logic for row 0: the down pull grows with a near-row danger term, and at the top row the dive wins whenever danger isn't present, while firing stays off there.

I'm setting the dive logic for rows 1 and 2: the down pull from targets below, plus a boost when a threat sits in the same row, minus a penalty when danger is one row further down.

I'm now asking whether the rows 3 to 8 should also be pulled up toward row 2, so the sub's vertical position stays sensible during the ascent.

I'm weighing a danger-override for the up direction: if danger sits above, the up pull from the start-of-ascent signal has to lose, so the layer-2 decode needs a hard block rather than a soft weight.

I'm setting the hard block for the up direction: a threshold on the combined signal so that pulls alone can't trigger it, but danger clearly does, which lets danger override the ascent.

I'm now setting the block-up and block-down units as sharp thresholds on the summed dive signal, with a steep slope, so that the pulls alone stay below the cutoff and a real danger signal clears it.

I'm settling on full weight for the danger cells in columns 2 through 7 so the hard block stays reliable, and I'm checking that the margins hold with the sharper threshold.

I'm checking whether the hard block still lets a soft push-away slip through when danger sits directly above, and I'm considering canceling that term so the sub stays put in its row rather than drifting away from an adjacent threat.

I'm checking the pull-down magnitude for a single target two rows below: with the weight at 0.32, the down logit comes out to about 0.3, which gives a softened signal of roughly 0.43 once I scale it through the tanh.

I'm checking the down pull at a distance of two rows: about 0.3 in the logit, which comes out to a down value near 1.08 and an up value near -1.08. Against the noop baseline of 0, that gives roughly a 0.6 chance of diving, which seems good enough. I'm also weighing whether to lower the noop baseline so the sub commits to moves more decisively, and I'm reviewing the baselines for the other actions, where left and right sit at -2 and fire at -1 so that firing with no target stays unlikely.

I'm setting up the oxygen-triggered surfacing signal: a unit that fires only when column 8 is lit and column 2 is not, and then feeding that into an up-logit boost.

I'm working out the up-direction override: the surfacing unit blocks up when fire-and-not-surfacing is active, and the block units keep danger above from being overridden by the oxygen pull. Surfacing should win over firing once oxygen is low, and at the top row there's no danger to worry about, so the sub can simply rise to the surface.

Checking the sticky-action risk: a repeated up-move could carry the sub from row 3 to row 2 and then into row 1 before the danger check catches it.

I'm checking the sticky-action risk more carefully: a repeated up-move from row 3 could chain into row 2, then row 1, and each extra step only happens on a repeat, so it stays fairly rare. I'm considering keeping normal movement in rows 3 to 8 to shrink that chance further.

I'm checking the sticky-action risk for the rows-2-and-up setup: an intended move into row 2 could repeat into row 1 and then row 0, but each repeat is only about a 10% chance, so the overall death risk stays small.

I'm now setting up the centering unit: it takes each column's weighted presence across all rows, halves it to account for the two sub cells, and offsets by a bias so that it pushes the sub toward the middle columns.

I'm settling the centering unit so that it pushes the sub toward the middle columns, and I'm setting its weight so a strong offset beats the small target pulls but still loses to a real threat or a fire opportunity.

I'm checking the centering case when the sub faces right at columns 5 and 6: pressing left twice brings it to columns 4 and 5, which is centered. Once it sits on 4 and 5 the centering push is zero, so a right turn just flips its facing. If noise pushes it left to 3 and 4 from a left-facing position, the centering term pushes it back right.

I'm checking the centering behavior when the sub is off-center and a target sits on the other side: the turn-left logit of about 6 minus the 4 from the centering push still leaves it at 2, below the right-turn logit of 4, so it drifts back to columns 4 and 5 facing right first, and only then turns left.

I'm adding a danger-avoidance term for vertical moves: cells at rows one step above and below count as threats when they hold enemies or bullets in columns 2 through 7. Bullets drifting toward the center from the outer columns matter too, since they could reach the sub after a move, so I'm including those with full weight.

I'm weighing whether an enemy at column 6 in the row below is too risky to move toward, since it could step into the sub's path in the same turn. An enemy at column 7 is a bit farther out, so I'm reconsidering how much weight the danger term should give to the outer columns.

I'm refining the danger term for vertical moves: enemies only count in columns 3 through 6, while bullets count across columns 2 through 7, which I can get by subtracting the column-2 channel from the column-7 signal. I'm also weighing the case where I'm facing left at columns 4 and 5 and drop into a row with an enemy at column 6, since that enemy could slide into my back cell and then into my front.

I'm working out whether the enemy-trail signal can tell an approaching enemy from a receding one: trail at column 7 means it's moving left toward me, trail at column 5 means it's moving away, so I'm weighting those to separate the two cases.

I'm settling the danger term so that a moderate pull toward a risky row still loses, and I'm checking that the trail weighting doesn't flip the sign in the wrong cases. Cells in columns 4 and 5 are already covered by the vertical check, and I'm now looking at the bullets in my own row across columns 1 through 8.

I'm checking how bullets fired from the far side behave: a bullet from column 9 appears at column 8 and reaches my cells in a few steps, so I have about three moves to get out of its path, and vertical dodging can still work in time.

I'm checking whether bullets fired from the far side can still reach the sub while it changes rows: at a delay of one or two steps there's still time to dodge, and a bullet heading toward a front facing left just hits the back cell first. The vertical danger check also covers rows the pull would bring the sub back into, so it won't walk into a bullet's path again.

I'm checking how enemies on both sides of the sub's row get handled: the closer one gets the facing and the fire, and after it's gone the sub turns to the other. An enemy approaching from behind weights more heavily as it closes in, which should flip the sub to face it.

I'm settling the no-target case: with nothing to chase, staying put should win over any move. I'm also weighing whether to use the spare weight for something like extra caution about enemies right behind the sub, but I'm leaving that out for now. Divers are worth pulling toward since they can be picked up if they cross the sub's front, and turning to face one keeps the sub in its row.

I'm laying out the layer-2 wiring now: the V and D signals from layer 1 feed a unit that combines the eight vertical-move values into one vertical score, weighted and offset so it sits in the right range.

I'm writing out the layer-2 weights for the combined vertical score and the bullet-detection units, and now I'm setting up the fire units for right and left.

Writing the layer-2 weights for the TH threat unit and tying its sum to the threat inputs.

Writing the layer-2 weights for the centering and bullet units, and wiring the vertical-threat and fire signals into the sub's output.

Checking the inactive vertical units: with a large pull or danger term, the pre-activation could sit near the threshold, so I'm estimating how much stray output they'd leak into the sum.

I'm noticing the danger term could stack up to 8 in an adjacent row, which would leak into the bullet units, so I'm raising the per-cell gate to 10 with a matching bias to keep the inactive vertical units clearly off.

I'm settling the sizing of the gating units: with the per-cell weight raised to 10 and a matching bias of -20, the inactive vertical units stay well below threshold even when several danger cells stack up, while the active ones pass their pull through unchanged.

Checking the threshold weights for the threat unit: with the per-cell gate at 6 and a bias of -6, an empty threat sum lands around -3 and yields a clear negative output, while a single threat pushes it positive.

I'm working through the bias and gating values for the threat and vertical units, so that inactive units stay near -1 and active ones pass their pull through. I'm also checking the danger-cell weighting for the row above and below.

I'm now setting the output weights from the layer-2 vertical and bullet units onto the move logits, so that a vertical push and the block against it pull in roughly opposite directions.

I'm finishing the weights for the backward-push unit: the block term for the row below needs to cancel the upward pull, so I'm subtracting it from the up logit and pulling the down logit down too.

I'm settling the fire and turn units next: the bullet-in-row sign gets the same kind of sign check, and the push-away term from the block units is dropped.

I'm working out the output weights for the threat term: threats push both up and down by a similar amount, fire gets suppressed, and turning gets dampened so that moving away wins.

I'm adding a surfacing term that pushes the sub upward by about 7 and trims fire and turning by 4, while the down pull stays small. Then I'm setting the up-blocking term for the row above, and wiring the centering signal so it nudges left and right in opposite directions.

I'm settling the base logits for the move outputs: noop at 0, left and right at -2 so random drift is discouraged, fire at -2 since shots waste cooldown, and up and down at -1 so the sub doesn't wander vertically without a reason. I'm now weighing whether a weak pull of around 0.3 is enough to outweigh that base.

I'm working out the down-move base at row 0, where the top-row pull gives the down logit a boost of roughly 1.2 over noop, so the sub should move down most of the time.

Now I'm checking the danger-cell gating for the row above: with the threshold at 0.95, the pull at row 0 comes out to about 0.905, so the block term is effectively off there. Then I'm working out what happens at row 0 when there's danger in row 1, where the block flips the down move negative and the push-away on up gets cancelled.

Now I'm checking the oxygen gating for the diver gauge: with the danger count at 1 or more and oxygen under 60, the surfacing signal should fire, and I'm confirming the column indexing lines up for each count.

I'm checking the surfacing logic, and the diver count only matters once it reaches 6, so I'll keep hunting divers until then.

I'm checking the surfacing reset: if the diver count is 6 the code sets it to 0 and then subtracts one more, which could push it to -1, so that looks like a bug worth confirming.

I'm checking what happens after a six-diver surfacing: the counter seems to drop to -1 instead of zero, which would leave the gauge state empty and make later surfacing behave differently than intended.

I'm realizing that after a six-diver surfacing the counter goes to -1, and picking up one more diver brings it to 0, which would make a later surfacing fatal. Since the gauge can't distinguish -1 from 0, I can't rely on it to tell when surfacing is safe.

I'm checking whether surfacing right after a six-diver pickup would pay out more than the usual low-oxygen surfacing, which would be worth up to ten points. The catch is that the counter drops to -1 after that surfacing, so the gauge would look empty and I'd lose the ability to surface safely.

I'm checking whether the oxygen gauge can tell me when the diver count has hit six: the gauge also fills from the oxygen level, so the diver columns can't be read on their own.

I'm checking whether the diver gauge can actually tell me when the count reaches six, and it looks like it can only do that when oxygen is low enough that the gauge doesn't light the same columns, so the bonus would be small. I'll skip chasing the six-diver surfacing and reconsider whether surfacing at oxygen under 60 is the right trigger.

I'm weighing whether a surfacing rule that waits for two or more divers would pay off, since spawn rates and speed both climb with each surfacing. Then I'm estimating the overall score from enemy kills against the risk of collisions and bullets, though it's hard to pin down and I'd guess somewhere around 10 to 30 points per episode.

I'm checking how the pull toward enemies in other rows plays out: it steers the sub toward them, but danger blocks the move once it's adjacent, so the sub waits for the enemy to pass and then shoots it from behind. I'm also noting that divers and enemies get the same pull, and that targets in the sub's own row are handled separately.

I'm checking whether a diver-only signal would just keep the sub stuck firing in its row, so I'm considering weighting the danger signal so divers count less than enemies, with the threshold set so a lone diver never triggers the hold.

I'm weighing whether to scale the danger signal so that divers and bullets count for half of what an enemy does, which would keep a lone diver in my row from pinning the sub in place.

I'm sharpening the diver-versus-enemy weighting so the fire units only respond to enemies, using a steeper slope so the margin holds at the weakest enemy distance.

I'm running into a problem with separating enemies from divers: if I weight both the same way, a diver on the opposite side of the sub can cancel out an enemy, so the fire signal would fail to trigger.

I'm weighing separate left and right danger units for divers, but the budget is already spent, so that's out. I'll accept some waste from firing at divers and consider weighting by movement direction instead, since the trail shows whether an entity is heading toward or away from the sub.

I'm weighing the danger signal as enemies counting double, divers and bullets once each, so a lone diver can't pin the sub in its row. The thresholds would need to be set so an enemy triggers the hold while a diver or bullet alone doesn't.

I'm checking the numbers: scaling the danger signal by half lets an enemy alone clear the threshold while a lone diver doesn't, though a diver on the far side could still partly cancel an enemy. I'll try a threshold around 0.75 with a sharper slope to see if that holds.

I'm settling on a diver-only-for-fire rule: the danger signal will count only the second channel, so the sub keeps the same enemy-focused logic I had before, and I'll accept some wasted firing at divers rather than let them cancel enemies out.

I'm weighing whether weighting the danger signal by each entity's trail direction would help, since a diver heading toward the sub versus away could be told apart that way, though it would cost more budget.

I'm working out the danger signal's threshold for divers, checking the weights against the h values and seeing where a single target in my row would land.

I'm checking the fire thresholds for the layer-2 units: with a gain of 6 and an offset of 0.4, a facing-right shot stays well clear of the cutoff as long as the orientation units' sum sits near zero, even if one of them reads 0.9 instead of 1.

I'm checking the per-row pull term for each row: summing the second-channel entities in the other rows, weighted by distance, and adding the directional trail terms.

I'm working through the vertical pull term for the sub's row: it sums the second-channel pulls from the rows above and below, weighted by their row-distance, along with the trail-based adjustments. For the top row I'm treating the threat from its own row as a separate push downward, and I'm starting to check how that threat term decodes into the vertical signal.

I'm realizing that a threat term merged into the row-2 vertical signal would be read as "block upward" and cancel the downward push, so I'll give the threat its own units, one per row, so the up and down pushes stay separate.

I'm settling the vertical units: a threat term folded into the row-2 signal would read as "block upward" and cancel the downward push, so I'll give threats their own units, and I'm setting the base for the row-1 signal to 1 so it doesn't sit right at the cutoff.

I'm reworking the vertical base for row 1, weighing whether dropping it to 0.6 keeps the pull and the hard threshold from overlapping.

I'm settling the row-1 vertical signal: it only needs the pull from targets below and the danger term, with no base offset, since row 1 has no upward pull to worry about. For row 0 I'm working through what base value keeps it from triggering against the danger term.

I'm checking the threshold for the hard decode: setting it at 0.96 puts the cutoff at about 1.95, and the pull stays under that bound. A danger weight of 5 keeps the true-positive case clear, while a pull of 1.2 stays well below the trigger. At row 0 the base of 1.5 lands just under the cutoff, so it won't fire.

I'm checking the vertical units' gating: with the inactive offset of 20, the pre-activation stays below the cutoff as long as the pull sum is under 16, so the unit only fires on a real danger signal.

I'm checking the fire-enabling unit for rows 1 and 2: the sub being there gives a clean positive signal, and otherwise it's clearly negative. The stance-gating term looks at whether column 8 is lit while column 2 isn't, so it should flip cleanly either way. I'm also working out the column-weighted sum that decides the fire direction.

Now I'm listing the unit layout for the second layer: the vertical signals, the back-up and back-down units, the fire and turn units, and the rest of the indices.

Writing the output-unit weights now: the no-op unit gets a penalty when a threat is present, and the left and right turn units each have their own bias, pull, and gating terms.

Still writing the output weights for the action units...

Checking the threat cases now: with a threat in row 5 and no danger above, the up and down pushes come out roughly even, so the pull decides it. If the danger is above, the up unit turns off and the down push wins, and a threat in row 2 with the fire-enabling unit on does the same.

Checking the no-target case: with the vertical pull pushing down at about 0.43, the down unit comes out near zero, so the up and noop units are what decide the move.

I'm tuning the vertical signal's coefficient: a weight of 3 gives a stronger downward push when nothing is in the row, though the cancellation coefficient at the hard threshold still needs checking against the up-unit's danger term.

I'm now checking the bullet-impact rule for the next step: the drift term from a danger above should be cancelled by the same weight I set for the upward block, so the down push stays strong.

I'm checking how an enemy approaching from column 7 would play out: the danger zone covers columns 3 to 6, so it doesn't block me, and if I'm facing left I'd need to turn right and fire, which takes about two steps.

I'm checking the enemy approaching from the left: if I turn left and fire, the bullet reaches column 3 and then 2 on the next step, so an enemy at either spot gets hit, even if it moves one cell in the meantime.

I'm checking how an enemy at column 5 in a target row would play out: if I move there and it's behind me, it's harmless until I move left toward it, so I'll keep the danger zone covering columns 3 to 6 to rule that out.

Checking the sticky-action case now: after a turn, a repeated turn drifts the sub to the middle, and the target to the right still makes firing win over centering.

I'm checking how the drift case plays out: at {5,6} the target at column 6 sits right in front of me, so that's a dead end I need to avoid. I'm also confirming the orientation and column indexing cover rows 0 through 8, since row 9 has nothing in it.

I'm weighing how the pull from targets in other rows should be scaled: the values fall off with distance, and a typical count of two to four targets could push the sum to about 1.2, which seems acceptable. I'm also considering whether targets near the center columns, which are about to cross into the sub's path, should count more than the ones at the edges.

I'm now weighing the threat columns: a diver in the same row could cancel a bullet's threat signal, which would be a dangerous miss. Using a weighted subtraction, with the sub's cells counted at a reduced weight, should keep the bullet threat from being cancelled by a diver.

I'm weighing a threat signal built from the enemy trail cells instead, since bullets don't leave a trail and enemy subs do, so a diver in the same row wouldn't cancel a bullet.

I'm checking whether a weighted mix of the enemy and bullet channels can separate the threat cases, since a diver in the same row currently cancels a bullet's signal. The weights would need to give enemies a sum that reads as a threat, bullets a positive value, and divers a negative one, but the linear combination can't do all three with one pair of coefficients.

I'm testing whether a single linear mix of the enemy and bullet channels can separate the threat cases, but a diver in the same row cancels a bullet's signal, and no pair of coefficients handles all three cases at once.

I'm looking at whether restricting the threat columns to roughly 2 through 7 would keep a diver near my row from cancelling a real bullet, since a diver would then have to sit in that same narrower band to interfere.

I'm weighing a threat signal that subtracts the enemy-sub channel from the bullet channel, but a diver in the same row cancels a real bullet. A linear mix can't separate the three cases, so I'm checking whether a small negative weight on divers, with a threshold just above a single enemy's contribution, keeps a bullet plus a diver from reading as safe.

I'm checking whether weighting bullets by column helps: a bullet close to the sub would count for more than a diver further away, so a far diver wouldn't cancel a real threat. The catch is that a diver just ahead of a bullet could still offset it.

I'm settling on the threat weights: a bullet in a column near the sub should count for more than one further away, and a diver should subtract from the threat signal. Setting the near columns to a higher weight could keep a diver from cancelling a real bullet, though a bullet landing on a diver's cell would still look like an enemy for a step.

I'm settling on the threat weights for the next step: enemies count as neutral, bullets as a full threat, and divers pull the signal down, so I'll use the enemy-minus-diver form over columns 1 through 8 with a threshold of 0.5. I'm also thinking about whether bullets spawning on an enemy cell get hidden in the merged channel until they move out.

I'm checking whether a diver approaching from behind would be picked up: if I'm facing left, it moves from column 6 to 5 and then onto my front cell at 4, so it gets collected as expected.

Now I'm working out the starting position: the sub sits at row 0, column 5, facing left, and I'm checking the centering pull and the enemy pull for that row.

Working out whether a bias in the threshold will hold: with the value near 0.905 for row 0, the effective pull lands at a negative pre-activation, so I'm now checking the orientation and the facing-left conclusion against that.

Checking the bullet-and-diver case in my row: the diver subtracts from the bullet signal, so a bullet with a diver beside it would read as safe, which would be a dangerous miss. The fix I'm considering is distance weighting, letting near bullets count more than far divers, but that still fails when a diver sits just ahead of a bullet.

I'm checking the case where an enemy sits in an adjacent row at center, and whether firing covers it when we have a target in our row. I'm also looking at whether a dodge rule is needed for an approaching enemy when our cooldown is still active, and I'm leaning toward skipping that for now.

I'm checking the softmax pull when a threat sits above: moves up and down come out strongly weighted, so the policy should commit to dodging rather than staying put. Blocking the upward move when danger is above still lets the downward option carry the action, and the fire option stays suppressed in that case, which seems fine.

I'm checking whether a dive in row 1 with a threat below is handled: the down move gets blocked and the up move is blocked too, so staying put is the outcome. I'm also noting that a push-away term from a threat below is cancelled by the block term and the up-fire penalty, so it adds nothing. Next I'm moving on to row 8, which takes its danger from row 7 and pulls upward.

I'm deciding not to use the spare unit for an extra feature, since the diver-firing and cooldown wrinkles only cost a little time, so I'll leave it idle. I'm also confirming that the sign conventions hold: a positive target offset means the diver is to the right, and firing right requires facing right, so turning right is the correct move when facing left.

I'm checking the layer-2 expressions for the fire and turn units with exact numbers, working out how the summed D terms and the orientation terms combine into each pre-activation.

Now I'm writing out the turn-left and turn-right pre-activations as sums of the diver terms and orientation terms, and checking the fire-right unit at zero target with the facing-right case.

I'm checking the fire-right unit with a single far target on the right while facing right: the pre-activation comes out to about 2.16, so the fire output rises to roughly 5.9.

I'm checking the facing-right case where the back cells are both odd, so the orientation units come out near zero and the first one sits at about -1. I'm also checking the facing-left case with both orientation units at -1, and I'm now testing a small noise term of 0.5, where the first unit lands near -0.964.

Now I'm setting up the layer-2 value unit: the summed threat terms feed a pre-activation with a weight of 1.5 and a bias of 12, and I'm writing the two boundary terms next.

Checking the output bias: the threat channel's pre-activation comes out to 3·(ΣT + 7), so with no threat it sits near -0.995 and an active threat pushes it toward +1.

I'm checking the threat pull on the surfacing unit: a threat count near -6 puts the threat signal around 0.995, and a diver alone drops it to about -1. Next I'm wiring the surface-and-up-fire pair, then setting the cancellation weights for the layer-2 value terms.

Now I'm writing the bias terms for the output layer, starting with the noop action: its base is zero, and the threat unit contributes a -3 weight and -3 offset, so the bias comes out to -3.

For the left action, I'm adding the base of -2, the turn-left unit's +3 contribution, the cooldown unit's +4 weight, the threat unit's -3 term, and the surfacing unit's -2, which gives a bias of -4.

Next I'm turning to the up action, which starts from a base of -1.

Still writing the output weights...

Still writing the output weights...

Still working out the output weights for the action units, now the up action's bias and the fire action's terms.

Still working out the layer-1 weights, now mapping each row's cells to their input indices.

Still working out the layer-1 weights for the value units, mapping the gating and pull terms row by row.

Still working out the layer-1 weights for the value units, now the pull and danger terms for each unit's neighboring rows.

Still working out the layer-1 weights for the value units, now the combined pull and danger terms on the rows just above and below each unit.

Still working out the layer-1 weights, now checking how a diver or enemy in an adjacent column-2 or column-7 cell interacts with the up and down pull terms.

I'm weighing whether to block danger on columns 2 and 7 using the enemy-only channel, but that can't be separated from divers, so I'm considering treating any object there as danger instead, which costs a little hunting range.

I'm weighing whether to treat enemies in columns 2 and 7 as danger too, since the diver-only subtraction would make diver and enemy entries in those cells behave differently. That would block entry at the center columns and only leave the edge columns open for engaging enemies.

Still working out the layer-1 weights, now deciding whether enemies in columns 2 and 7 should count as danger, since a single rule for both bullets and enemies there would be simpler.

Still working out the layer-1 weights, now settling on treating enemies and bullets alike in columns 2 to 7 of the adjacent rows as danger, with the pull applied across all columns.

Still working out the layer-1 weights for the value units, now the diver-row sign terms and the bias for the zero-row unit.

Still working out the layer-1 weights for the value units, now the danger and pull terms for the rows just above and below each one.

Still working out the weights for the threat units and the diver units, now the first layer-1 unit that combines the cell channels across the whole grid...

Still working out the layer-1 weights for the unit that combines the sign-alternating and column-weighted terms across all rows...

Still working out the layer-1 weights, now the unit that flags the leftmost-and-rightmost lit cells in row 8 and the bias for the fire-two unit.

Still checking the orientation unit: I'm confirming the sign works out so that the back-cell parity matches the front-cell pattern, using a concrete case with the sub facing right.

I'm checking the facing-left case with the back cell at 5, where the sign terms cancel and the left unit fires. Next I'm verifying a front at 3 facing left with back cell 4, which also cancels to zero and gives left. Then the facing-right case with back cell 3 gives a total of -2, so the right unit fires at tanh(4).

Still working out the layer-1 weights, now checking that the signs on the fish trail cancel out and the orientation unit comes out right.

Checking the threat unit's bias and the diver sign convention against the turning logic, I'm confirming that a diver to the right while facing left triggers the turn-right action.

Now I'm checking the case where the sub sits in the bottom row: pressing down there does nothing, so a threat should push only upward. The pull and danger terms for row 8 don't yet block that downward move, so I'm thinking about adding a constant offset to the row-8 value unit to discourage going down.

Still working out the layer-1 weights for the row-8 case, now handling the downward move without losing the upward pull.

Still working out the layer-2 wiring, now adding a row-8 indicator so the down move gets blocked only when the sub is in the bottom row.

Still checking the row-8 case, where the threat push and the downward move interact, and I'm confirming the sub's position gating still holds for the threat unit.

Still working out the layer-1 weights, now checking whether the pull toward targets in row 1 can be kept without letting the threat logic override it.

Working out the day-zero case now: with the row-0 base of 1.5, the value unit is already fairly active before any danger shows up. Next I'm computing the down-move logit at row 0 with no danger present, starting from its bias and the value and danger terms.

Checking the downward-move logit at row 0 with no danger present: starting from its bias and the value and danger terms, the arithmetic comes out to about +1.65, but then I'm recomputing it carefully and getting roughly -0.38 before the last term.

Checking the down-move logit at row 0 again, I'm getting about +1.64 after folding in the row-8 indicator's contribution, so the surface-and-pull terms still dominate there. Next I'm considering the case where the sub sits between rows with a target in its row, where firing takes priority, and the surface push adds a bit more upward pressure during ascent.

Now I'm thinking about how a noop-as-default policy might leave the sub idle for long stretches when no targets are around. I'm also considering that idling at row 1 after the initial dive could be wasteful, so a central resting row might cut down on travel once pulls appear.

Now I'm adding a small central bias to the value units so the idle sub drifts toward the middle rows instead of parking near the surface. The offsets shrink toward row 4.5, so rows 1 through 3 lean downward and rows 5 through 8 lean upward.

I'm settling on a mild central bias for the idle sub: positive for rows 1 to 3 to pull it down, negative for rows 6 to 8 to pull it up, and neutral in rows 4 and 5. That should keep it from bouncing between the middle rows, and I'm wondering whether spawns spread evenly across the rows justify centering it vertically.

I'm settling on the base bias for the value units, which pulls rows 1 to 3 downward and rows 6 to 8 upward. The pull terms could push the total past a hard threshold, but it looks like it stays just under the saturation point, so I'm moving on to checking how the threat term interacts with the value units at row 5.

I'm checking that firing when the cooldown isn't ready does nothing, which makes it the same as noop, and then I'm looking at a target that's aligned with the sub so I can confirm when a shot will connect.

Checking the case where a diver approaches in the same row a real enemy is coming from the other side. Both pull into the same unit, so the sub may keep firing at the diver and wait to turn toward the enemy until it's closer, with cooldown possibly tied up by those diver shots.

I'm checking for a deadlock where the sub keeps pressing right, since a persistent orientation misread would drift it toward {5,6} and {6,7}; the centering term should pull it back left, so there's no runaway. Once it's at {4,5} facing right with a target on the right, it fires. I'm also turning to the oxygen question, since with no divers collected the sub would run out of air around step 200.

I'm checking the surfacing condition: the sub surfaces only when oxygen is below 60 and at least one diver is held. Then I'm working through the six-diver edge case, where the held count hits the cap before oxygen runs low, so pickups stop and the surfacing bonus could leave the count negative and the gauge stuck empty.

Now I'm working out whether the surfacing bonus can drive the diver count negative, and what that does to the gauge. Then I'm looking at how the ramp-up of enemy speed changes spawn timing, since more enemies bring more points but also more danger.

Checking the bias numbers at the extremes: row 8 with a -0.5 base and upward pulls still lands near -0.9 after the squash, so the down logit is only slightly affected there. At row 1 the +0.5 base plus downward pulls stays under the saturation point, so the up move remains blocked as intended.

Checking the threshold on the value unit at row 1 with the new target weight, I'm finding that a far target still gives a firing signal above the threshold, so turning toward it is justified. I'm also confirming that the threat-blocking unit at row 8 properly stops downward movement.

I'm checking the sub's ascent past row 2 when danger sits above and below: the upward block at row 1 holds, and the downward block at row 2 catches anything coming from below. Row 1 has nothing further up to worry about.

Checking whether the sub's firing and centering terms still hold together at row 2 when the next move is up. I'm also thinking about how the sub would handle a hazard appearing in the row above it.

Next I'm checking the threat term at row 1 during the dive: it feeds the threat-blocking unit, which holds back the upward move while the downward one stays available. I'm also noting that if the sub sits in row 1 with no surfacing active and danger below, it could get stuck, though that case looks rare. Surfacing is only enabled once oxygen drops below the threshold with a diver held, so I'm checking that the oxygen-refill step turns surfacing off again when the sub reaches row 0.

Now I'm laying out how the weight-index ranges map onto each row and channel, so the writeup can list them cleanly.

Now I'm mapping out the weight index ranges for the value units, working out the flat offsets for each row and channel so the setup is laid out cleanly.

Still setting up the value unit weights, now the per-row entries for the second unit.

Still writing out the value-unit weights, now the pull terms for the third unit and the danger entries above row 1.

Still writing the value-unit weights for the third unit, now the entries for its pull terms and the danger cells on either side.

Still writing out the value-unit weights, now the pull terms and danger cells for the fifth unit.

Still writing out the value-unit weights, now the pull terms and danger cells for the sixth unit.

Still writing out the value-unit weights, now the pull terms and danger cells for the eighth unit.

Still writing out the value-unit weights, now the pull terms and danger cells for the last rows.

Still writing out the weight slices, now the first channel for the zeroth unit.

Still writing the weight slices for the diver and threat units, now the per-row channel ranges for those.

Still writing out the weight slices, now the second channel for the diver and threat units.

Still writing out the weight slices, now the remaining rows of the second channel for the threat units and the setup for the final unit's per-column weights.

Still writing out the value-unit weights, now the final column-wise entries for the last unit's bias and pattern values.

Still filling in the per-column weights for the last unit, working through the slice index for each channel.

Still filling in the weight slices, now the unit with its pull terms and the fixed offsets for the last few units.

Still writing out the layer-2 weights, now the bias and weight entries for the first few units of the second layer.

Still writing out the layer-2 weights, now the bias and weight entries for the fire and turn units.

Still writing out the layer-2 weights, now checking the firing and turning units against the facing direction.

Still checking the bias values for the second layer, now the fire and turn units' weights, and working through the threat unit's inputs next.

Still writing out the output weights, now the entries for the fire and turn units in the third layer.

Still writing out the output weights, now the turn and threat units' entries and the bias terms for the output layer.

Now I'm checking the output biases for each action: the up, down, right, and fire logits all come out negative once their terms are summed. I'm also confirming that a plain idle state gives the no-op logit a value of zero.

Checking the signed output logits for each action: left comes out to -2, up to about -1.0, right to -2, and down to about -1.0. The fire logit is still being summed.

Checking the sub's output logits for a threat case: with a hazard in view, the no-op logit drops, the side moves go negative, and the up and down logits climb, so the sub would drift away from the danger.

Now I'm checking the sub's behavior in rows 1 and 2 once surfacing is involved: the surfacing unit is only on when the fire target is missing, so the upward move stays off while firing. Then I'm running the scenario with the sub at row 4 facing left, and the fish in row 6 pulling it leftward.

Checking the sub's pull toward the fish: at row 5 the pull from row 6 gives a downward logit of about 0.68, so it should keep sinking. Once it reaches row 6, I'll look at the danger term there, since the fish is at column 9 and not directly below.

Checking the turn-right case with the fish at column 9: the right logit comes out near 3.9, so the sub should turn and then fire toward the fish.

Now I'm working through the scenario where the sub sits in row 4 and sees a threat at row 3 on the left, so I'm checking the pull toward row 3 and whether it fires back before moving on.

Now I'm checking the diver case: it's at column 2 on the left, so the sub would turn left, but firing there is wasted. If the diver keeps moving right, it reaches column 4, which is the right spot to pick it up whichever way I'm facing.

Now I'm checking the danger-avoidance edge case: a bullet sitting in the adjacent row near the edge could pull the sub back and forth, but once it's back in the original row the danger term blocks the move.

I'm checking how the danger term behaves when the sub drifts over to columns 3 and 4, since a target just to its right at column 5 could still pull it the wrong way.

Checking the sub's pull toward the fish in row 6 once it reaches the middle columns, since the diver and threat terms could still pull it the wrong way near the edges.

Now I'm checking the pull toward the middle rows: the base pull fades as the sub moves down, so it should settle around row 4 and stay there.

Checking the danger term and the orientation signals for the sub's sides, and confirming that row 9 never gets activated by any of the input channels.

Now I'm checking how the sub's own trail sits in its back cell: if another entity's trail lands on the same cell, the two merge in that channel, so the back cell only counts once.

Checking the threat threshold again: with a diver-only reading the threat value sits at -1, which pushes the threat unit's pre-activation to about -9, so it stays off, and with no threat at all it comes to -3, which is also effectively off.

I'm weighing the upward and downward move terms next, and checking whether the bias on those outputs can be left as is, since the value-based estimate for each unit is still to be summed.

Now I'm checking whether an inactive threat unit could still leak a meaningful output: with four bullet cells in view its pre-activation lands at +1, which would be too large to ignore.

Switching the threat units' gating to weight 15 with bias -33, so that four stray bullet cells can't push an inactive threat unit positive. Next I'm checking whether the same problem shows up in the danger units' inactive rows.

Setting the gating weights on the danger and threat units higher, so inactive ones can't leak false positives.

Still writing out the weight entries for the second value unit's input row, now the third value unit.

Still writing the weight entries for the third value unit's input row, now the last of its bias and gating terms.

Still writing the weight entries for the fourth value unit's input row.

Still writing the weight entries for the fifth value unit's input row.

Still writing the weight entries for the sixth value unit's input row.

Still writing the weight entries for the eighth value unit's input row.

Still writing the weight entries for the ninth value unit's input row.

Still writing the weight entries for the fifth danger unit's input row.

Still writing the weight entries for the threat units' input rows.

Still writing the weight entries for the threat units' input rows.

Still writing the weight entries for the first value unit's paired columns.

Still writing the weight entries for the first value unit's paired columns.

Still writing the weight entries for the second danger-unit's columns, now the middle of the column pairs.

Still writing the weight entries for the unit 26 input column pairs, the fills that scale with each column's position.

Still writing the weight entries for the sign-flipped unit, then the constant and sum-check units.

Still writing the remaining weight entries for the fill-in units and the layer-two outputs.

Still writing the layer-two output weights, now the bias and gating entries for the outputs.

Still writing the layer-three weights, filling in the output rows for the next set of units.

Still writing the layer-three weights and the bias entries for the output units...

Still writing the weight entries for the fire and turn units, checking how a diver in the sub's row might keep the fire unit active while it drifts away.

Weighing whether the fire unit should key on the second channel alone: a diver in the row would keep the sub firing until it passes or leaves, but enemies elsewhere would stay ignored, and I'd rather not trade that for the cancellation problem of mixing the channels.

Now I'm weighing the second option: mixing the diver channel in at half weight, so that a lone diver no longer triggers firing. The catch is that an enemy on one side with a diver on the other could cancel out, though as the enemy gets closer its pull grows enough to clear the threshold again.

I'm weighing the diver-versus-enemy cancellation problem, and it's worse if the diver channel is mixed in at half weight, since an approaching enemy could go unshot. Keeping the sub's firing keyed only to the enemy channel looks safer, so divers would just add targets without suppressing fire. When an enemy and a diver sit on opposite sides, I'd face whichever is closer, and once the diver is picked up the enemy alone drives the turn and fire.

Still writing the weight entries for the danger units, now deciding how much the bullet channel should count toward firing.

Still working out the threshold for the layer-two units: I'm raising the cutoff to 0.5 so that a lone bullet at a distance stays below it, while a diver or enemy still clears it at range, and then I'll recompute those biases.

Still writing the bias terms for the fire and turn units, with the threshold now at 0.5.

Still checking the cancellation case: I'm reconsidering the danger units' channel-one weights, which should be half the proximity weights so an enemy keeps dominating over a diver on the other side.

Still checking the sub's fire and turn behavior, now with the enemy channel weighted higher than the diver channel so an approaching enemy isn't drowned out.

Weighing whether the sub can stay in the operating zone at rows 3 and below, with rows 1 and 2 used only to pass through, since targets in row 2 are rare and each upward move carries a small sticky-action risk. The chance of drifting up through row 2 is only a few percent per episode, so I'll keep the current layout.

Now checking the oxygen threshold: the sub starts with 200 and only surfaces when it drops below 60, so the timing of that trigger still needs confirming.

Checking the sub's position at the edge of the grid, I'm weighing how the centering term behaves when it sits at columns 3-4 or 5-6 and whether the facing logic still holds there.

Now I'm checking how the sub's position at the edge of the grid affects the facing check, specifically when it's on the far side with the enemy channel still feeding into the turn decision.

Checking the spawn edge cases now: an entity sitting at column 0 for a few steps can throw off the orientation estimate when it overlaps with another one leaving the grid, so I need to see whether those errors cancel or stack up.

Now I'm checking whether bullets at the edge columns can threaten the sub, and I'm deciding whether the danger units should watch them too.

Now I'm checking the sub's surfacing logic when it's active at row 2, to make sure that danger above it still blocks the upward move.

Checking whether the sub can still be pushed up by a threat when it's at row 3, and it looks like moving up to row 2 stays allowed in that case.

Checking the fire and turn logic once more: a bullet in the sub's row coming toward it triggers the threat unit and pushes the decision to fire, and the threat wins. The remaining hidden units are unused, so they add nothing, and the oxygen-value unit stays saturated near its inactive value.

Checking the pull weights for the V_1 unit next, including the danger in row 2 and how the enemy there cancels its pull, then confirming the slice indices for the row-2 pull entries.

Checking the slice indices for the danger units now, covering the ch2 and ch1 entries for each row and confirming the counts come out to ten each.

Still writing the slice indices for the danger units, now the diver channels for each row.

Still checking the danger slices for rows 5 and below, confirming the same six-step pattern holds.

Still checking the danger slices for the rows below, and confirming the indices step by six columns from column 2 to column 7 hold for each one.

Checking the cases where an enemy at column 8 is approaching, I'll need two steps to turn and fire, and I'm treating the danger-channel edge cases as acceptable risks.

Checking the row-0 case, the vertical value there comes out negative and blocks the down move, so the sub mostly idles and only occasionally strafes left or right. The up-blocking rule at row 2 still holds when the surface signal is off, and the rule at row 8 keeps the sub from pushing further down. I'm also noting that the facing term does nothing to firing while the sub sits at row 0.

Checking the threat case at row 2 with danger below: the up move is blocked, so the sub mostly holds still, with a slight pull back down and the fire and strafe options pushed well below.

Checking the row-2 case again: if the sub is pushed up by a threat while danger sits below, the up move scores about -5, which beats staying put at -6, so it will often rise to row 1. From row 1 it can still come back down, though the sticky-action chance adds a small risk, and that is acceptable given that staying in the bullet's path is just as dangerous.

Checking the threat-in-row case once more: the bullet is treated as a danger, and I'm recalculating the logit for moving left or right at -8 with the turn bonus bringing it to -2.

Now I'm weighing a timing problem: if the sub keeps dodging bullets before it ever fires, it may never get a shot off, since the enemy fires about every 11 steps and the bullets take a few steps to arrive.

Next I'm checking the friendly bullet case: if one is already in flight when I dodge, it keeps going and can still hit the sub, so that risk stays. I also want to confirm the list lengths in the W3 row, making sure the six-element slice holds.

Checking the unit indices for the friendly pull, the danger units, and the threat units now, confirming each slice lines up with its channel.

Checking the sub's position relative to the enemy trail, I'm working through how a trail cell landing on the sub's front would shift the parity sum, and whether the entity term cancels that shift.

Still checking the bias values for the V units, working through each one from V_0 up to V_8 and the groups after them.

Now I'm double-checking the bias for the surfacing unit, which comes out to -4, and the sub's left and right weights for the scaled coupling term.

Next I'm laying out the bias values for the V units and the sub's surfacing and coupling terms, then settling how divers are handled once the pickup cap of six is reached.

Working out the per-column weights for the two pull units next, which will take a while since there are around sixty entries across both, and I'm writing the unit C coupling term afterward.

Setting the weights for the first layer's vertical preference unit now, gating it on the submarine's row.

Still writing the per-column weights for the V units, filling in the bias values as I go.

Now I'm setting the danger-unit weights for each vertical preference unit: a bonus for moving up when danger sits just above, and a penalty when it sits just below.

