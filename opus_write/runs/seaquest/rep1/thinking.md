I'm designing a hand-built policy network for MinAtar Seaquest and want to know first what a sensible policy can realistically score. I'm recalling reported baselines, where DQN lands somewhere in the mid-teens to around thirty on this game, and I'm not certain of the exact figure.

I'm trying to pin down the actual DQN number for MinAtar Seaquest, which I think is somewhere around 10 to 25, though I'm unsure. I also recall PPO getting noticeably higher with longer training. The main game mechanic to plan around is oxygen: it drains only while the sub is below the surface, so a policy that stays shallow avoids that clock, but surfacing without divers ends the episode.

I'm working out that a surface-hugging policy is safe from enemies, since enemies only spawn in rows 1 through 8, but it would never score, so I have to descend to shoot anything. From a fixed row, enemies approach from either side, and facing and firing toward the incoming direction determines whether the bullets hit them or whether the sub gets struck from behind.

I'm working through how the enemy subs fire: they shoot every ten steps, and their bullets travel one cell per step, so they can't be shot down by the sub's own bullets. I'm working out how fast the enemies move relative to the spawn timing.

I'm now tracing when the enemy sub's movement timer fires, starting from its spawn at x=0. Its counters begin at 5 for movement and 10 for shooting, and each step decrements them, so I'm counting how many steps until the first move.

I'm tracing the enemy sub's timers from spawn: it moves every six steps and fires every eleven, so its first shot lands at x=1 and the bullet immediately advances one cell per step. I'm working out how the bullet's path lines up with where the sub would be.

I'm checking the shooting cooldown: after the sub fires, the next shot is blocked for five steps, so the fire key does nothing while the timer is still counting down.

I'm checking whether an enemy can slip between my bullets, since I fire every five steps and bullets move one cell per step, while the enemy only advances one cell every six steps.

I'm checking whether an enemy bullet and an enemy sub can pass through each other, and they can't: whichever moves first lands on the other's cell and the collision registers. So firing steadily along a row means any incoming enemy in that row gets caught before it can reach me.

I'm checking whether firing every five steps from x=5 facing left can reach an enemy sub spawned at x=0 before its first shot at t0+10. A bullet fired at time t moves one cell per step, so it lands at x=4 right away and reaches x=1 within about four more steps.

I'm checking that a bullet fired every five steps keeps some shot in the enemy's path at all times, so an enemy spawned at x=0 gets hit before its first shot at t0+10.

I'm checking the case of enemies coming from behind, spawning at x=9 and moving left toward my position, where they'd still be able to shoot me even while I keep firing forward.

I'm weighing two ways to handle an enemy coming from behind: turning to face it, which costs a move and leaves no shot that step, or dodging vertically into a row with no threats. Since each row's enemies all travel the same direction, I can dodge when a row is clear.

I'm working out how divers keep the oxygen clock running: they spawn about every 30 steps, drift one cell every six steps, and with roughly two on screen at once, collecting them is the way to keep surfacing points coming.

I'm noting that divers only get collected while there are fewer than six aboard, so any extra divers just pass by. Bullets can't hit divers and enemies can't either, so the diver check is the only thing that matters for them. I'm now sketching a plan that hunts divers and enemies, surfaces when oxygen runs low with at least one diver, and avoids collisions. I'm also trying to recall the MinAtar paper's reported Seaquest numbers for DQN and actor-critic, though I'm unsure of the exact values.

I'm trying to recall the published MinAtar Seaquest numbers, which I think put DQN somewhere in the teens to twenties and PPO higher, though I'm not sure of the exact values. I'm also weighing how a trained network of this architecture might compare against those baselines.

I'm picturing a small two-layer network of 32 units per layer that reads the 600 grid inputs, and I see that a linear first-layer unit can't represent "a danger in the sub's row" on its own. To get that conjunction I'd dedicate a group of units to each row, each one firing when the sub and a danger share that row, which comes to roughly eight rows times a few features.

I'm weighing a fixed-position strategy that keeps the sub in a known row, so the features only need to check a few specific cells. Staying near the surface seems like a candidate, since it avoids oxygen pressure, but then nothing would get scored, so I'd have to dive to shoot.

I'm noting that the surface only counts as a safe return once I've picked up a diver, so the first descent is effectively committed. The plan then is to go down, grab divers, shoot what comes at me, and head back up when oxygen runs low while carrying at least one.

I'm noting that divers come every 30 steps and oxygen lasts 200, so I could keep surfacing if I grab a couple each cycle. Each surfacing ramps up enemy spawns and speed, which makes long runs harder but also gives more targets. Collecting six divers for the surface bonus is the other option, and I want to estimate how many points a simple patrol-and-shoot approach would bring in.

I'm working out the enemy spawn timing: the spawn timer starts at 20, and when it hits zero the next enemy appears and the timer resets, so the gap between spawns comes out to about 20 steps.

I'm estimating how many enemies spawn over a run, roughly one every twenty steps, and noting that only a fraction of them will ever cross my row. To catch more of them I'd need to move into their rows, which means I have to think about how a small network could represent that.

I'm thinking about how a small network could tell whether an enemy sits in the sub's row, which needs a separate unit per row to capture that conjunction. Fixing the sub at the screen edge would put every enemy in its row in front of it, though I still need to check what happens at x=-1.

I'm checking the edge case where the sub sits at x=9 facing left, since the back cell would then land at column 10, which is outside the grid and might raise an index error. I'm also noticing that a negative back index at x=0 wraps around to column 9, so the back cell could appear on the far side of the screen.

I'm checking which edge positions the sub can actually reach, and it turns out x=9 can only be reached by moving right, so the sub always faces right there. Likewise x=0 is only reached by moving left, so the sub always faces left. That means the back cell never falls off the grid or wraps around at the edges, but it also means the sub can never be at an edge facing inward.

I'm checking the edge cases again: at x=0 I can only be facing left, toward the wall, so a shot fired there leaves the grid immediately and does nothing. Pressing left at the edge just keeps me in place. The more pressing issue is that an enemy spawning at x=0 in my row would land directly on the sub and end the episode.

I'm checking whether a shot fired from column 1 facing left can reach an enemy at column 0, and it can, since the bullet lands there before leaving the grid. The catch is timing: an enemy spawned at x=0 gets about six steps before it reaches me, and I can only fire every five steps, so I'd need to shoot right away or on the next available cycle.

I'm checking the timing for enemies spawned at the far end: they'd need around 48 steps to reach my column, and enemy subs could fire from farther back, with their bullets taking several more steps to arrive.

I'm settling on a turret-style plan: hold one row and column, face left, and fire constantly, so that I catch everything that comes from the left. Enemies arriving from the right in that row would still need dodging, which means stepping off the position for a moment.

I'm weighing whether to shoot enemies from a fixed row or to move vertically, since a single row yields almost no kills over one oxygen cycle. Enemies move slowly, so I could line up with them and fire.

I'm considering a tracking approach where the sub moves toward the nearest enemy's row and fires along it. The difficulty is that telling whether an enemy is above or below me means comparing its row to the sub's row, which a single first layer can only do through a weighted sum over row positions.

I'm noting that the vertical comparison also reduces to a linear expression, so the sign of "enemy row minus sub row" would tell me which way to move. With several enemies the sum blends their positions, so I might end up hovering between two of them, though that could still be workable. Horizontal alignment would presumably work the same way, using column differences.

I'm checking how the sub's orientation is encoded: both the front and back cells are marked in the first channel, and only the back cell also shows up in the trail channel, though enemy and diver trails could muddy that.

I'm working out how to tell which way the sub is facing: the trail channel marks the back cell, but enemy and diver trails can contaminate it. Summing column indices over the first channel only gives front plus back, which isn't enough to recover the orientation on its own.

I'm working out how to tell which way the sub faces: summing column indices over channel 0 gives only front plus back, which is ambiguous between facing left and facing right. I'll need the trail channel or some other per-cell signal to resolve it, and I'm considering whether a unit that combines channel 0 with channel 4 could do that.

I'm noting that channel 4 also picks up enemy and diver trails, so a plain column-weighted sum over it would be contaminated. I'll try to find a way to read the sub's orientation from the observation without relying on that channel alone.

I'm weighing whether to lock the sub into a fixed column and oscillate its orientation, or to fix a row and move horizontally, since the network could then treat those positions as known. A fixed row only covers about an eighth of the enemies, though, so that trade-off is what I need to settle.

I'm considering a vertical alignment approach, where the network linearly computes the row difference to the target and moves up or down to line up. Once aligned with an enemy, I'd need to know which side it's on relative to my facing, which needs extra units. I'm thinking about whether restricting the sub to middle columns would make those side checks simpler.

I'm going to think about how to pull the danger signals into per-row units, splitting enemies into a left half and a right half of the grid, which would take 16 units plus the orientation handling. Then I want to sketch the overall behavior: diving to hunt and collect divers, surfacing when oxygen runs low with a diver in tow, and avoiding enemy bullets and enemies that approach along the sub's row.

I'm weighing whether to stay on the surface row to avoid oxygen loss, but the problem is that scoring requires diving, and surfacing again costs a diver.

I'm now listing the ways danger can reach the sub: enemies in its row, enemy bullets flying toward it, and the timing of how often enemies step forward.

I'm checking the collision timing for the sub moving vertically into a row where a bullet is passing through its column, since the bullet hits it if it lands on the sub's cell before or after the bullet moves.

I'm now checking how a fish or sub gets hit by my shots, and whether an enemy sub that has been shooting for a while can still be taken out before its bullets reach me. Its bullets fly one cell per step, so I'd need to close the distance quickly while dodging them.

I'm now reasoning that enemies heading toward the sub in its row, or enemy bullets moving its way, are the real threats, whereas enemies moving away are harmless since their shots go in their own direction.

I'm realizing enemies can be handled by facing whichever side they're approaching from and firing. The trail channel tells me their direction, and an enemy moving toward me is one that sits on the side it came from. Since spawns prevent enemies from coming from both sides at once, facing the approaching side should cover every threat.

I'm reasoning that in any given row all enemies move the same way, since the spawn rule forbids opposite directions there, so the dangerous side is always the one they're coming from. The part I'm still unsure about is whether bullets left flying after their sub died could ever meet a new enemy coming the other way, because the spawn check ignores bullets entirely.

I'm settling on a rule for each row: whichever way the enemies there are moving tells me which side is dangerous, so I should face that side and fire. Enemies moving away from me, along with their bullets, can't reach me, so they don't need a response. The trail cell behind each enemy should reveal its direction, though divers' trails could blur that reading.

I'm checking whether a linear function over the trail and danger channels can tell an enemy moving right, since its trail sits one cell behind it. The difference between the position-weighted sums of those two channels would come out to −1 for that case, though divers also leave trails and could muddy the reading.

I'm checking whether an enemy's direction can be read from a single position, and the answer looks like no: an enemy at the edge has no visible trail, so position alone won't tell me if it's approaching. I'm now asking whether the danger that matters is just whether an enemy to my side is closing in.

I'm weighing a simpler design where the sub stays in a fixed middle column and just faces whichever side enemies are on, since shooting either side still scores. The catch is that when enemies appear on both sides, only the approaching side is dangerous, so I'd still need direction information to decide which way to face. I'm also starting to think about the overall policy and which simplifications keep it robust.

I'm settling on a fixed footprint: the sub never leaves columns 4 and 5, flipping between them when it turns. Facing left puts the front at column 4 with the back at column 5, and facing right reverses that. Either way the sub occupies both cells in its row, so its orientation can be read directly from which of those two cells is the front.

I'm checking whether the sub's orientation can be read from the trail channel at its row, but enemy and diver trails in the neighboring columns make a global linear sum unreliable. That leaves me needing a per-row check, which is harder to express with simple features.

I'm considering whether the sub could occupy a different pair of columns depending on its facing, so that the orientation shows up in the danger/trail channel at fixed columns. Moving right twice from facing left would put the front at column 6 and the back at column 5, which would make column presence alone reveal the direction.

I'm weighing whether the sub really needs to know its facing at all: if I just alternate between turning and firing, I could cover both sides without tracking orientation, though pressing a turn key while already facing that way would move the sub instead.

I'm weighing whether the sub's facing can be read from the trail at column 5 versus column 4 in its row, but trails from other enemies and divers in those columns could throw off a global sum.

I'm working out how to tell an enemy's trail apart from a diver's in columns 4 and 5, since each entity's trail sits at a predictable offset from its position depending on its direction.

I'm now working out the trail geometry: an entity at a given cell leaves its trail one cell behind it, so the trail at column 4 or 6 in the sub's row points back to where an enemy came from. Columns 3 through 6 near the sub would also be collisions or near-misses, which makes that region hard to read. I'm considering whether to drop per-entity direction tracking and instead split the state into per-row units.

I'm considering per-row units that AND the sub's row with a row-local feature, with a second layer aggregating across rows. But global quantities like oxygen, diver count, and vertical target position need their own units, and the budget is tight. A purely linear first layer can't capture the "enemy in the sub's row" interaction, so that AND has to be built in.

I'm breaking down the features needed per row: whether danger is approaching from the left, from the right, and which way the sub is facing. Since the sub's columns are fixed, enemies on either side are easy to separate, and each row only needs to know which side is coming.

I'm settling on per-row units: one for a threat on the left side of the sub's row and one for a threat on the right side, each gated by whether the sub is in that row. Orientation would need its own per-row unit as well, which I'm still working out.

I'm checking whether a diver at the sub's edge column would leave a trail that lands in the sub's own cells, which would contaminate the back-cell orientation signal.

I'm weighing whether the sub's orientation can come from a single global linear sum over both trail and body channels at columns 4 and 5 across all rows. The contamination from other rows is the worry, so I'm considering whether per-row units would be cleaner, though that costs eight more units.

I'm considering a different encoding: moving the sub's footprint so that facing left and facing right occupy different column pairs, which would make orientation visible in the columns alone. The tradeoff is that switching direction then takes two presses and passes through an intermediate position whose footprint looks like the other facing.

I'm noticing that the footprint alone is ambiguous: a {4,5} footprint could mean either facing left with the front at 4, or facing right with the front at 5, so I can't tell from the columns which way I'm pointed.

Still weighing a per-row check on the sub's back cells, since a global sum over the trail channel gets contaminated by enemies in other rows.

I'm considering whether the sub's orientation could come from a single global sum over the trail channel, but enemies in other rows make that unreliable. Per-row units would fix it, though they cost more budget. I'm also looking at whether our own bullets could reveal facing, and that doesn't hold up since they only show where we last fired.

I'm thinking the sub's orientation could simply be left to the policy: if it always presses 'l' when the threat is on the left, the sub drifts that way, and alternating 'l' with firing might be enough. Another option is reading the sub's x-position linearly from channel 0, since a weighted column sum would give it directly.

I'm considering whether the sub's orientation can be encoded in a per-row unit alongside the left and right threat units, which would bring the total to 24 and leave only 8 for oxygen, diver count, and vertical target.

I'm setting up per-row units that AND the sub's row with threat-left, threat-right, and facing-right, then summing across rows to get global threat and facing signals.

I'm checking whether a single global orientation sum over the back-cell channel would hold up, or whether the contamination from other rows forces per-row units after all.

I'm checking whether the trail left behind by an entity could be told apart from the sub's own back cell, which would let the contamination from other rows be cancelled out.

I'm checking whether a trail at column 4 could be told apart by its source: an entity at column 3 moving left and one at column 5 moving right both leave a trail there, so subtracting entity positions at columns 3 and 5 would cancel some cases but not the case of an entity at column 3 moving right, which leaves no trail at column 4. That means the subtraction doesn't fully remove the contamination. I'm also noting that enemies show up in the danger channel while divers don't, so that distinction doesn't help here.

I'm considering whether orientation could be folded into the per-row threat units, so that one unit encodes both threat side and facing. A single tanh unit only yields a threshold on one linear combination, though, so it can't reliably carry two separate bits.

I'm weighing whether a unit could cover two rows at once, but that would fire on a threat in one row while the sub sits in the other, so the per-row AND has to stay. I'm also thinking about which survival threats matter most, starting with enemies.

I'm listing the survival threats in priority order: enemies approaching in the sub's row, which I have to kill or escape, and enemy bullets in that row, which I can't shoot down so I have to leave the row. Then I'm noting the vertical dangers, oxygen running out before a surface with at least one diver, and surfacing empty-handed, which is fatal. On the scoring side, each kill is worth one point and surfacing with six divers gives up to ten more.

I'm wondering whether the sub could just start from the surface and stay there, since row 0 is completely safe and oxygen doesn't run down while it sits there. I'm thinking about whether dipping to row 1 and back might be a way to farm kills without risking the sub.

I'm weighing the surfacing trade-off: returning to row 0 from row 1 costs a diver, so a dive-to-shoot-and-return pattern is only sustainable while I still have divers in hand. Waiting at the surface looks safe and cheap, but the timing of diver pickups versus enemy spawns makes a hover-at-row-1 plan look unattractive.

I'm working out how the oxygen gauge is drawn on row 9 of channel 5: each cell covers 20 steps of oxygen, and the diver count fills cells from the right, so the two bars can overlap when they're both long.

I'm checking how the oxygen and diver bars share row 9 of channel 5: the oxygen bar fills from the left and the diver bar from the right, so when oxygen is high they overlap and the diver count disappears. When oxygen is low, the two bars stay separate and both are readable.

I'm working out how the oxygen and diver bars share column 2 and beyond: column 2 can only be lit by the oxygen bar, since the diver bar never reaches that far left, so lit column 2 means oxygen is at least 60. From there I'm reading off the diver count from column 8, which is lit either by the diver bar or by oxygen near full.

I'm settling on a threshold for the oxygen warning: column 2 of channel 5 going dark means oxygen has dropped below 60, which leaves enough steps to climb back, though I'm leaning toward column 1 at below 40 to keep the trigger later and avoid false alarms.

I'm checking whether diver count stays readable at low oxygen: with oxygen under 180, column 8 of row 9 in channel 5 can only be lit by the diver bar, so it reliably signals at least one diver.

I'm now thinking about how to hunt divers: they move one cell every six steps, so the sub needs to line up in their row and approach from the side they're crossing toward, with the front cell at column 4 or 5 depending on facing.

I'm settling on a vertical strategy with the sub fixed in its column: since divers and enemies both drift across the rows, I can collect or shoot them by moving to their row and waiting for them to reach the front cell. The open question is how to pick which row to move toward when several targets are present.

I'm stuck on the vertical targeting: picking a row needs the product of the sub's row and the number of targets, which a single linear layer can't compute, and a tanh approximation with limited units looks hard. So I'm considering per-row comparison units that count targets above the sub instead.

I'm trying a different angle on the vertical targeting: instead of a single linear weighted sum, I'd compare each row's target presence against the sub's position, so the "targets above" count doesn't need a product of the sub row and the number of targets.

I'm checking whether a per-row linear feature could give the sub-to-target direction, but summing over several targets mixes their rows together and loses the sign, so a single weighted sum doesn't work here.

I'm considering a sweep pattern for the sub instead of targeting, moving down to row 8 and back up, and I'm wondering whether the oxygen level could serve as the clock that tells it which way to go.

I'm considering a time-based sweep instead: the oxygen bar's length, which drops one level every 20 steps, could set which row the sub hovers in, moving it down toward row 8 and then surfacing once oxygen runs low. It's non-reactive, but each row would still get shot at whatever passes through it.

I'm estimating how often the sub would meet an enemy if it sat in each row for about 20 steps, weighing the spawn rate against how long enemies stay on screen and how many rows there are.

I'm estimating how many divers would pass through a row while the sub sits there, and it looks like a diver in the same row only crosses the front cell in a short window, so catching one by chance is fairly unlikely.

I'm estimating the expected diver pickups from a fixed schedule, which comes to about one per cycle and isn't reliable. Reactive targeting would work better, so I'm now looking at how to move vertically toward the nearest target with limited units, starting from the idea of detecting the sub's row implicitly through linear features.

I'm laying out the next step as layer-1 units: one "sub row ≥ k" feature for each k from 2 to 8, plus one "target present in row r" feature for each of the 8 rows. Layer 2 can then combine them into "a target lies above the sub" by checking each row for a target while the sub sits below it.

I'm trying to express "a target lies above the sub" as a single layer-2 unit, but a plain weighted sum over the per-row target flags and per-row sub-position flags can't represent the AND between them. I'm considering a threshold on the combined sum instead, so that the unit fires only when some target sits in a row above the sub.

I'm working out whether the topmost target row can be encoded by weighting each row's target flag with a rapidly decreasing power of two, so a single sum tells me whether the nearest target sits above the sub. The idea is that the sum's magnitude would reveal the topmost target row, and comparing it against a threshold tied to the sub's row would give the "target above" test.

I'm checking whether the weighted sum can carry the comparison: powers of two per row would make the total reveal the topmost target row, and the sub's position would set the threshold. The open point is whether counting target cells, rather than just their presence, would still keep that ordering intact.

I'm checking whether using base 5 weights instead of base 2 keeps the ordering intact even when a row holds several targets, since counts up to about four would otherwise break the power-of-two bound. Then I want the threshold for "topmost target is above the sub" to come out to 5^(9−s), which only holds if the sum stays inside that range.

I'm checking the bound on the weighted sum: with base-5 weights and up to four targets per row, the total stays under the next power of five, so the ordering holds. The catch is the dynamic range, since the weights reach about 390,000, and I'm wondering whether the smallest terms stay distinguishable near the threshold.

I'm checking the margin: at the smallest scale, the difference between the sum and the threshold can be only about one unit, which isn't enough for tanh to saturate. So I'd scale all the weights up by a factor of 3 to widen the margin. That pushes the largest weight past the limit I want to stay under, so I'm switching to base 4 with at most 3 targets per row, which keeps everything within bounds.

I'm weighing whether a target could be above me and how I'd choose between targets above and below, leaning toward the ones above since they're closer to the surface.

I'm now checking whether the topmost target can be the rule: if one sits above the sub, move up, and if one shares its row, stay and shoot. That leaves the case where every target is below, which means moving down. The worry is that the sub may keep chasing upper targets and never reach enemies lower down.

I'm now weighing a different layer-1 design, where thermometer-style units encode the sub's row and a cheaper per-row feature handles same-row danger, since a second layer can supply the extra nonlinearity.

I'm checking whether one linear unit can single out the case where the sub and a danger share a row, and it looks like a plain weighted sum can't pick out only the diagonal pairs.

I'm checking whether one threshold unit can detect a danger sharing the sub's row, and it turns out it can't, since the diagonal match can't be separated by a single linear sum. I'm considering two units per feature instead, one testing "danger row at or above the sub" and one testing "at or below," with their conjunction giving the equality, though that only holds cleanly when there's a single danger.

I'm settling on a strategy that needs few interaction features: a column sweeper that keeps the sub in the middle columns and moves vertically toward target rows. When an enemy approaches in a row, the sub would face it and fire. The concern is that moving vertically through rows exposes the sub to enemies or bullets at the destination cell, though enemies are slow and bullets fast enough that this is manageable.

I'm now checking whether a danger directly above the sub can be detected cheaply: that would mean a per-row AND between the sub's row and the danger cells in the adjacent row, which costs about one unit per row again.

I'm weighing whether a single unit can flag danger in the column band just above the sub, but multiple entities spread across rows break the one-threshold idea. Estimating the risk from vertical movement instead, I'm looking at how likely an enemy is to sit in the sub's column in a given row at any moment.

I'm estimating the collision risk from passing through rows: with a few enemies on screen and the sub crossing about four rows, the chance an enemy sits in the front column of a row is small but adds up, and enemies just about to step into that column add a bit more.

I'm weighing the collision risk from moving vertically through rows: even a small per-row chance of an enemy in the front column adds up over many crossings, so I need a check on the destination cell before each vertical move.

I'm wondering whether the sub could hold a safer spot, maybe at the edge columns, but enemies spawn right there and would kill it on arrival. Staying in the top row and only diving briefly looks risky too, since each surfacing costs a diver. I'll see what trained MLP agents usually reach on this game before settling on a target.

I'm recalling rough figures for Seaquest on MinAtar: DQN and actor-critic agents land somewhere around 10 to 30 after millions of steps, and MLP PPO agents plausibly reach 10 to 40. So a hand-written policy that scores around 10 would be a respectable target.

I'm working out the play policy in layers: first a survival check when oxygen runs low and divers are on hand, then fire-or-wait behavior in the sub's row, and finally moving vertically toward a target row. The row-level threat detection is the hard part, so I'm simplifying it to just "danger on the left or right of my row" for now.

I'm noting that the sub's footprint could drift from columns 4 and 5 through sticky actions, which would throw off the orientation and side features, so I'd need some way to pull it back toward the center.

I'm working out a drift-correction rule: summing the column-weighted ch0 gives the sub's footprint position, so pressing right or left when it falls outside the expected range keeps it near the center. The orientation feature for each row still needs to be settled, since the back column tells me which way the sub faces.

I'm checking the footprint drift case: if the sub sits at columns 3 and 4, pressing right gets it back to 4 and 5, so the corrective move overrides the orientation check there. The orientation feature only means anything when the footprint is {4,5}, since in the drifted positions the same column reads as the opposite facing.

I'm laying out the per-row layer-1 units: for each row, one unit for danger on the left half, one for danger on the right half, and one for the sub facing right, which comes to 24 units and leaves 8 for oxygen and diver counts.

I'm trying to fold the left and right danger units for each row into a single unit with a sign, gating it on whether the sub sits in that row so that it reads as constant when the sub is elsewhere.

I'm trying to compress a single unit per row into a three-way signal: when the sub is in that row, the output sums to 2 for a left-only threat, 1 for none or both, and 0 for right-only. The catch is that this loses the distinction between "no threat" and "threats on both sides."

I'm considering whether the orientation bit can ride along in the same per-row unit as the left and right threat signals, using graded output levels so that each combination of inputs maps to a distinct value. Since rows outside the sub's own row sit at a fixed saturated constant, only that one row's levels would vary, and a second layer could read them off with thresholds.

I'm checking whether the sub's facing bit and the threat side can share one value, so the next layer can read off the cases with thresholds: 3 means turn left, 2 means fire, and 1 or 0 covers the remaining combinations.

I'm checking whether the sign-combined threat units can be decoded cleanly, but counts of dangers rather than yes/no flags make the thresholds fragile, since two dangers on one side push the level past what a single unit can separate. Clipping inside one layer isn't possible, so I'm considering whether to reduce the per-row structure altogether instead.

I'm trying to avoid one unit per row for each danger side, since that's too many units. Because the sub occupies only one row at a time, I'm wondering whether a single trick can capture the sub-row-and-danger AND across all rows without spending a separate unit on each combination.

I'm considering whether to cut down the number of rows the sub can occupy, say to a few fixed rows, which would shrink the per-row unit count. The trade-off is that enemies in rows the sub can't reach would go unanswered. I'm also wondering whether it would be better to think about the problem over time rather than as a single snapshot.

I'm settling on a simpler survival design: enemies in a row all move the same way, so a sub that faces the incoming direction and keeps firing can clear them before they reach it. The remaining worry is enemy subs that shoot before dying, which I still need to account for.

I'm checking the timing against the enemy sub: it spawns at the left edge and fires once it reaches column 1, while my bullets fired every 5 steps from column 4 reach the edge in that same window. Working through the offsets, every 5-step window should see exactly one of my bullets arrive at the edge, so a sub kills anything that spawns in its line of fire before it can shoot twice.

I'm checking that the enemy sub's timing holds: the bullet visits at the edge line up with the spawn window, so it dies before it can fire, as long as the sub keeps firing on its cooldown. The remaining worry is that softmax sampling might pick another action on a ready-cooldown step, which would break the every-5-steps rhythm.

I'm now thinking about how to tell which direction enemies in the sub's row are coming from, since facing the wrong way is what would get it killed.

I'm weighing whether to commit to a single row and turn toward incoming enemies, or to move between rows, since one row alone yields too few points.

I'm now picking which row to move toward, using the second channel so that divers count as targets too, while keeping the first channel for anything that can hurt the sub.

I'm weighing whether divers are worth chasing at all, since one moving away from my column can't be reached with a fixed footprint. Their spawn rate is steady, though, so I'm checking how many would actually be catchable.

I'm working out how to pick a target row: I'll look for divers or enemies that are still approaching the center, since everything spawns at an edge and moves inward, and treat anything past the center as receding.

I'm now setting up the vertical navigation signals: whether a target sits above the sub's row, below it, or in its own row, with the "above" check built from a weighted sum of target rows.

I'm setting up the threshold for the topmost-target check: with a base-B weighted sum over target rows, the test for "some target sits above the sub's row" reduces to comparing that sum against B raised to 9 minus s.

I'm setting the upward check as a threshold on the weighted row sum, with a half-step margin and a scaling factor so the output saturates cleanly. Next I'm building the matching downward signal from the bottommost target row.

Now I'm working out a signal for whether any target sits below the sub's row, using a weighted sum over target rows that compares against B to the power s. For the in-row case, I'm weighing whether to test for a target in row s directly, or derive it from the above and below signals, since the two can conflict when targets sit both above and in the sub's own row.

Still working out whether a single unit can detect that the topmost-target row sits exactly at the sub's row, since the threshold trick only separates "above" from "not above."

I'm checking whether a single unit can flag a target sitting in the sub's own row, since the above and below signals alone can't settle that case. Testing per-row units for danger on each side would cover enemies and bullets in that row, but divers would still be missed.

I'm weighing whether a single unit can flag danger directly above the sub in a column band, since the same trick could cover threats from above without per-row units.

I'm checking whether one weighted sum over the danger cells in the band can tell me if something sits directly above the sub, since a plain threshold only separates "above" from "not above" and can't isolate the row just above.

I'm now checking whether a single unit can flag danger directly above the sub, since a weighted sum over the band can't isolate the row just above. The bottommost-danger trick only works if I can drop the rows at or below the sub, and that restriction isn't linear. So for the most important interactions I'll likely have to fall back on per-row units.

I'm estimating the risk of moving vertically: each step up or down exposes the sub to enemies and bullets in the destination row, and with roughly three enemies alive that's a fairly small per-move chance of collision.

I'm estimating the collision risk for a vertical move: roughly 5% per step, counting enemies in the destination row and enemy bullets near the sub's column. Across ten vertical moves per oxygen cycle, that adds up to a meaningful chance of dying.

I'm now weighing how often vertical moves put the sub at risk. Each step exposes it to enemies and bullets in the destination row, so I'll need a safety check on the cell above or below before moving.

I'm trying to cut the unit count down, since the per-row checks for danger above and below the sub already push past the 32-unit budget. One option is limiting the sub to fewer rows, another is folding the band checks into the left, right, and orientation units. A third is using a threshold-style trick to find the nearest band danger above the sub's row.

I'm checking whether layer-two units built from thermometer codes of the sub's row and per-row band-danger presence could flag danger directly above the sub.

I'm trying to see whether a single unit can flag danger directly above the sub by combining a thermometer code of the sub's row with per-row band-danger presence, but an OR over rows of ANDs isn't linear, so that route doesn't work. I'll consider splitting the check across pairs of rows instead.

I'm weighing whether to give each row its own danger-detection unit for the sub's position, since a single weighted sum can't isolate the row directly above or below. I'm also looking at whether one unit could cover the left and right threats in the sub's row together, with the direction handled elsewhere.

I'm now considering whether to lay out the sub's threat checks per row, since the remaining features (side threats, orientation, band danger above and below, and diver presence) all depend on which row the sub sits in. I'm also weighing whether the action choice could be spread across per-row units, or whether reducing the number of rows the sub can occupy would free up enough units.

I'm weighing whether the band-danger check can be split across pairs of rows and merged into the left and right units, since per-row units for each neighboring row would exceed the unit budget. Coarse pairings look like they'd produce false positives when dangers sit in more than one group, so I'm leaning away from them.

I'm weighing a hugging-the-surface strategy against a turret in one row, since staying near the top keeps threats limited to row 1, though oxygen drains whenever the sub is below the surface.

Checking how the surface routine handles a full set of divers: it sets the count back to zero, but the line after that subtracts one more, which would push the count below zero.

I'm tracing through the surfacing routine and noticing that when the diver count hits 6, it resets to 0 and then the decrement pushes it to −1. That means the terminal check for zero divers wouldn't fire, and the count keeps drifting negative on later surfacings.

The surfacing logic is the sticking point here: once six divers are aboard, the reset leaves the count at zero and the decrement then drops it to −1, so the zero-diver check never fires afterward. Surfacing again just keeps pushing the count further negative. That means after one full-capacity surface I could keep refilling oxygen without losing divers, but collecting a diver at the wrong moment could bring the count back to zero during a surface and end the run.

I'm now checking the surfacing logic: with six divers, the count resets to zero and then the decrement pushes it to −1, so the zero-diver terminal check stops firing. That makes it possible to keep surfacing for oxygen, as long as the count never lands on exactly zero at a surface.

I'm checking how the surface routine behaves at different diver counts, and whether running it repeatedly lets the sub keep refilling oxygen. The count-reset quirk aside, each surfacing with a few divers costs one diver and restores full oxygen, so collecting about one diver per 200 steps would keep the run going. I also want to see how the spawn and movement speeds ramp up with each surfacing.

Now I'm looking at how the surfacing ramp speeds up enemies and spawns with each refill, so the late-game gets much harder even though the points come faster.

I'm now considering whether the sub should hold a column at the far right instead, facing the wall, but the left edge is out because enemies spawning at x=0 would hit it right away. Column 1 facing left looks workable: it covers spawns from the left in front of the sub, and threats from the right approach over a longer stretch, so I'd handle those by turning around.

I'm settling on a column-1 turret facing left, so the orientation stays fixed and I never have to sense it. Threats coming from the right would be the ones to dodge by moving vertically.

I'm settling on enemies from the left as the ones to shoot, since at column 1 only the cell at column 0 is in front of the sub. Enemies from the right would have to be dodged by moving to a safer row, and I only have about five steps to get clear when something spawns at x=0 in a different row.

I'm now considering the column-8 option facing left, where enemies approaching from the left stay in front of the sub for a long stretch. Enemies coming from the right would hit the sub quickly, so those would mean leaving the row, while receding enemies to the left are still valid targets.

I'm weighing column 9 facing right, but its bullets would go off-screen, so that's out. Staying at column 8 facing left, the only real danger is an enemy spawning at x=9 in my row, which reaches my front cell within a few steps, so I'd need to leave the row quickly.

I'm settling on column 8 facing left as the fixed spot, reached by moving right and then turning back. The main risk there is an enemy spawning at x=9 in my row, which would reach me in about six steps. Enemies that approach from the left can be shot, though bullets from subs that are already moving toward me could catch me before mine land.

I'm working out what a sub at column 8 facing left would face: enemies in its row to the left can be shot, while the main threat is something spawning right behind it at x=9. Divers moving left get collected once they reach the front cell.

I'm checking the consequences of the column-8 spot facing left: divers spawning at x=9 in my row would reach me within six steps and get collected, while threats from behind are limited to that one cell. Staying put and never turning right keeps the orientation fixed.

Working out how the sub can drift back to column 8 facing left: from column 7, two rights reach column 9 facing right, and one left then lands on column 8 facing left.

I'm distinguishing the two positions by checking the back cell in the sub's row: column 8 facing right would have its back at 7, column 9 facing right has its back at 8, and column 8 facing left has its back at 9, so the footprints overlap but the back cell tells them apart.

I'm working out a global feature for the sub's back cell: each row contributes a +1 when there's a trail at column 9 and a -1 when the trail sits at column 8, which separates facing-left at column 8 from the other positions.

I'm checking whether the footprint alone can tell a column-9 facing-right sub from a column-8 facing-left one, since both occupy cells 8 and 9. The back cell would separate them, but reading it means looking at trails in each row, which other entities can also produce. So I'm weighing whether a global count can work or whether that ambiguity is too risky.

I'm weighing whether to avoid the {8,9} footprint ambiguity by choosing column 7 facing left, reached by moving from column 8 facing right and then pressing left, though that footprint overlaps other states too.

I'm weighing whether a global feature can tell orientation apart when footprints overlap, since any position facing left shares its two cells with the position one column right facing right. Reading the back cell in the sub's row would settle it, but that means checking per-row trails, and I'm looking for a linear count that avoids that.

I'm testing whether a single linear unit could flag the sub as facing left at column 8 by summing the column-9 cells, but other rows' trails at column 9 could cause false positives, so I'd end up firing uselessly if I was really at column 9 facing right.

I'm checking whether the orientation can be read from a single global feature, since the contamination from other rows would only ever delay a false "facing left" reading rather than cause a false "facing right" one. The remaining question is why orientation needs checking at all, which comes down to drift: after a correction press of 'r', the sub could end up at column 9 facing right, so I'd want to know which footprint means which position.

I'm checking whether a single global count of column-9 and back-cell readings can flag facing-left at column 8, and where the drift-correction conditions would come from.

I'm settling on a fixed home at column 8 facing left, where the back cell at column 9 won't collide with anything, so the main vertical-move risks are enemies at columns 7 and 9 and bullets in neighboring rows approaching column 8.

I'm listing the per-row checks I'd need: whether a threat is coming from behind while the sub sits in that row, and whether an enemy bullet is approaching in that row. Telling bullets from enemies with a single linear sum runs into trouble, since divers muddy the count.

I'm now weighing whether a bullet can be told apart from an enemy by its cell, since bullets and divers can overlap and muddy a simple per-cell difference.

I'm considering how an enemy sub moving right in my row would fire bullets straight at my column, since bullets go in the shooter's direction and I can't see their trails. Once one is fired, it will reach me in a handful of steps, so I'd need to spot it early and move up or down to dodge.

I'm weighing whether enemy subs can be told apart from fish, since they look the same in the input, so any approaching enemy might be a sub. The plan is a turret at column 8 facing left that keeps firing, with vertical moves to dodge bullets fired along its row.

I'm settling on the vertical-movement rules for the turret: fire whenever nothing else needs doing, move toward rows with targets at columns 7 or less, and avoid rows where something sits at column 9 or where a bullet is coming. Bullets have no trail, so I can't read their direction, and I'm leaning toward ignoring bullets that look like they're moving away.

I'm checking whether a bullet in my row at columns 5 to 7 is coming toward me, but the bullet itself has no trail, so its direction isn't visible. Subs moving left in my row would have had to pass through my column to get there, so a bullet to my left most likely comes from a sub moving away, which doesn't put me in danger.

I'm wondering whether a central home with turning would beat a fixed column-8 position facing left, since enemies moving left and spawning at column 9 would be behind me at first but could be shot once they recede in front.

Enemies moving right are the ones that will close in on the turret, and they can be shot as they approach. An enemy at col 9 that is about to leave is harmless. Receding enemies to the left are free shots from the turret's home position.

Checking whether the danger at column 9 in the sub's row can be read from the sub's back cell, since that is where the danger would sit when the sub is at column 8 facing left.

I'm checking the danger at column 9 with a single global sum over that column, but other rows' spawns and exits there would cause false alarms. A per-row unit that requires both the danger and the sub's back cell in the same row would be exact.

I'm weighing per-row units that check the sub's row together with danger at columns 7 to 9, so each row's threat is tied to whether the sub sits there. Checking the rows above and below would mean conditioning on the sub's row offset, so I'm working out whether that stays linear.

I'm now trying a vote-style setup instead, where each row's unit checks whether the sub is in that row and whether danger sits in a neighboring row near column 8, so the result tells the sub which way not to move.

I'm weighing whether the per-row danger units should also feed the target logic, since an enemy in my row at columns 7 or less would be something I can shoot.

I'm weighing whether the navigation units alone can cover "stay and fire." If only UP and DOWN exist, a target in my own row gets overridden whenever another target sits above or below, so I'd need a separate HERE signal to keep the turret firing in place.

I'm working out a navigation signal that only goes down when no target sits above, so a target in my own row isn't overridden by one below. The rule would be: down only if some target exists and the topmost target lies below my row, which I can express with the counts of targets above and below.

I'm now checking whether the "move toward the topmost target" policy works, which would take only about three units: one for a target strictly above, one for a target at or above my row, and one for any target existing at all. The topmost-target idea would have the sub settle in the highest row with a target and stay there until it's cleared, then move on to the next one.

I'm noting that the topmost-target policy would send the sub toward enemies at column 9, which are actually threats behind it. So the target definition should leave out column 9, and probably column 8 too, and only count enemies at columns 0 to 7 as things to chase.

I'm thinking about whether divers should count as targets at all. A diver moving right takes a long time to reach my front, and one moving left never does, so if I treat divers like other enemies I could end up parked in a row waiting for something that won't come. Divers near column 9 are probably better handled on their own rather than as things to chase.

I'm now defining the topmost-target signal as a total over columns 0 to 7 with bullets and divers counted once and enemies counted twice, so the per-row counts stay below the base needed for the geometric comparison, though this mixes the categories.

I'm weighing which cells should count as targets: enemies at columns 0 to 7 are shootable, but bullets are threats and divers only matter when they approach. Using one channel alone mixes enemies with either bullets or divers, and a per-cell AND isn't linear, so I'm stuck on how to isolate enemies cleanly.

I'm trying to get a threshold of 2 per row so that a lone bullet doesn't count as a target, since enemies contribute 2 to the channel sum and bullets only 1. The question is whether a comparison like V ≥ 2·B^{9−s} keeps the geometric ordering intact for the leading row.

I'm checking whether the geometric encoding can detect "a target exists above" when a single bullet in a higher row would falsely trigger it. A lone bullet contributes a weight that can dominate the comparison, so the sum alone can't distinguish a real target from noise.

I'm still trying to get a channel combination that picks out enemies alone, since bullets and divers would otherwise get treated as targets too. Subtracting the channels zeroes enemies but gives divers a positive weight and bullets a negative one, which breaks the geometric trick, so I'm considering simply counting divers as targets as well.

I'm sorting out which cells count as targets: divers at column 9 are useful to collect since they reach column 8 quickly, while enemies at column 9 are dangerous.

Next I'm planning the unit budget for the topmost-target navigation: a couple of geometric units for targets above and at or above my row, plus per-row danger units for the current, upper, and lower rows, an oxygen-low unit, a diver-count unit, and drift corrections at the edges.

I'm checking the start position: from (5, row 0) I need four steps right to reach column 9 and then one step left to settle at (8, L). Row 0 is the surface, so it's safe there, but I'll have to pick up a diver before I surface again, and the oxygen gauge only counts down once I descend.

I'm checking the oxygen gauge thresholds: the first column lights when oxygen is at least 40, so it going dark means I'm under 40, and the second column going dark means under 60. The surfacing rule is that low oxygen with at least one diver collected sends the sub up row by row to the surface, where the diver is spent and oxygen refills, so it can dive again right away.

I'm checking the oxygen gauge again: column 8 of the bottom row lights when there's a diver aboard, so below 60 oxygen it tells me exactly whether I'm carrying one. The start is the hard part, since I have no diver yet and must not surface empty-handed, so the topmost-target navigation has to keep me in the rows where enemies are rather than drifting up toward the surface.

I'm checking the surfacing risk: if the sub drifts to row 1 with no diver aboard and the 'u' choice comes up, it would surface empty-handed and die. So I need the 'u' logit strongly suppressed whenever the sub is in row 1 and no diver is carried, and I'm also noting that pressing 'u' at the surface does nothing.

I'm noting that sticky actions could carry the sub from row 2 up into row 1 and then into the surface, which would be fatal with no diver aboard. So I'm considering blocking entry to row 1 when no diver is carried, or accepting that risk only once a diver is aboard.

I'm now thinking about how sticky actions could push the sub around at the edges, since a repeated 'l' might overshoot to column 7 and need a couple of 'r' presses to correct. I'll keep the allowed rows at 2 through 8 whenever no diver is aboard, so that an accidental move into row 1 can't end in an empty-handed surfacing.

I'm checking how enemies and bullets in the sub's row would move relative to my position at column 8. Enemies spawning at column 9 need about six steps to reach me, so I have time to leave, and I'm now timing the bullet travel from column 8 across the row.

I'm checking when the enemy at column 0 gets hit: bullets reach column 0 every five steps, so one of them should catch it before it moves on.

I'm working out how an enemy sub that's been drifting right would react once I enter its row: my first bullet needs about four steps to reach it, and in that window it has roughly a one-in-three chance to fire back, sending a bullet that would reach column 8 in about four more steps.

I'm checking whether a bullet in the destination row near column 8 would hit me on arrival, since approaching enemy subs there could also fire. Receding enemies are fine to enter and shoot, but approaching ones are risky.

I'm weighing how risky it is to enter a row where an enemy sub is approaching from the left: my first bullet needs about four steps to reach it, and during that window it could fire back, with a bullet that would reach column 8 quickly.

I'm weighing whether to only target receding enemies, since approaching ones could fire a bullet back at me before my shots arrive. The risk is roughly proportional to distance, so entering a row with a distant approaching enemy is the dangerous case.

I'm working out how to tell receding enemies from approaching ones by their trails: a trail one cell ahead of an entity means it's moving away, one cell behind means it's coming toward me. A spawned entity at column 0 has no trail yet, so it needs separate handling.

I'm working out how to weight the trail-based direction sum so that a just-spawned enemy at the left edge doesn't come out as a strong signal, and I'm checking the sign convention on the edge cases.

I'm settling the per-row direction score: each trail cell adds its weight, and each entity cell subtracts its weight, so a leftward enemy scores +1 and a rightward one (including a fresh spawn at column 0) scores −1. Divers in the row will add their own ±1 on the same scale, and I'm noting that several enemies moving the same way simply stack.

I'm stuck on whether per-row signed direction scores can be combined with the geometric targeting, since those need nonnegative values per row. One option is to compute row features separately in the first layer, so the second layer can AND them with the sub's row position.

I'm weighing whether a single layer-1 unit could cover two rows at once, firing when the sub is in either row of a group and that row's feature holds, to save units over one unit per row.

I'm checking whether one layer-1 unit could cover a group of rows, but a single halfspace can't tell "sub in row r1 and feature in row r2" apart from matching rows, since the required inequalities contradict when summed. So each row needs its own unit for the AND, and the geometric trick would have to work around that.

I'm checking whether a per-row "danger one row away" test can be built from the geometric trick: "some danger above" and "some danger below" don't combine into "some danger exactly adjacent," so the adjacency check would need its own unit per row.

I'm checking whether a danger check for the row directly above can be built from weights that favor lower rows, but rows at or below the sub would still dominate that sum, so the geometric trick doesn't isolate the row I need.

I'm checking whether moving vertically is safe by looking at the rows directly above and below, but a per-row adjacency test doesn't reduce to simple halfspaces. I'm also considering whether to stay pinned at the right edge, though an enemy spawning right beside me would be fatal.

I'm now looking at whether the danger checks for the rows above and below can share per-row units with my own row's threat check, since each row's danger band around column 8 would be the same signal.

I'm now listing the per-row units I'd need: one for a threat behind the sub in its own row, plus one each for danger in the rows directly above and below, about 22 units in total. I'm also considering whether bullets approaching in the sub's row could be folded into the first of those checks.

I'm checking whether a bullet at columns 6 or 7 in the sub's row counts as danger to dodge, which means treating bullets as positive and divers as negative in the per-cell sum.

I'm considering bullets moving left in my row at columns 6 and 7, but a receding sub would have fired them from behind its own position, so those shots are moving away from me and aren't a threat to dodge.

I'm checking bullets in my row at columns 6 and 7, since a bullet at column 7 would reach me on its next move and I'd need to dodge right away. A bullet further out gives me a little more warning, and a leftward one from a receding sub is a false alarm but harmless.

I'm also checking the windows for bullets in my row: cols 5–7 give a bit more warning, though each extra column picks up some harmless bullets from receding subs. Then I'm turning to targeting, where the question is which encoding gives the unit for enemies and divers ahead of me.

I'm tallying the remaining units: oxygen-low, a diver check, two drift corrections for the left edge and column 9, and two row checks for surfacing, which brings the total to 30.

I'm now checking whether a "HERE" signal can come from the two top-target units: the sub is in the topmost target row exactly when the at-or-above check holds but the strictly-above one does not. That adds one more unit, bringing the total to 31. The sub should stay put and fire while it's in that row, but divers moving left at columns 7 and under may just drift out of view, so the sub could wait up to 48 steps for nothing.

I'm checking whether moving back into the target row right after dodging could run into a bullet still traveling along it. The vertical safety check should block that move while a bullet is in the row I'd re-enter.

I'm checking how the band check handles an approaching enemy at column 7 in the target row: it counts as danger, so I wouldn't enter that row, and once it passes column 8 the row would be clear. Then I need to decide how to dodge when a threat appears, moving up or down whichever row is safe and closer to the targets or the surface, though I haven't settled the case where both neighboring rows are blocked.

I'm settling on the fire rule: when no move is needed, the sub stays in the target row and keeps firing, even when no targets are currently visible in that row.

I'm weighing whether the vertical-move checks for the rows above and below can be merged, since navigation up needs the row above clear and navigation down needs the row below clear, and each dodge needs one of those two.

I'm weighing whether to keep the two adjacent-row safety checks separate or merge them into one per-row unit to save budget, since a combined check would freeze both vertical directions whenever either side is unsafe.

I'm now counting the per-row units: one for threats in my own row, and for the adjacent rows I need checks for danger above and below, which comes to 22 in total. The top row never has enemies, so the above-check can skip row 1, and the bottom row can't be descended into, so that check can skip row 8. When I'm at the surface and about to dive, I still need the check for the band in row 1.

I'm settling the vertical-move budget: 8 units for the danger-below checks, bringing the total to 23. Navigation takes three more units for targets anywhere, strictly above, or at-or-above. At the surface those above-checks are always false, so any target sends the sub down to dive.

I'm weighing whether to surface at under 60 oxygen instead of under 40, since the refill is the same either way and the extra margin covers the 8 moves up plus any waits for safe rows, though it costs a little oxygen per cycle.

I'm now working out the drift correction: if the sub's footprint sits left of columns 8–9, I'd press right, and if it's at column 9 facing right, I'd press left. I still need a way to tell whether the front or back of the sub is at column 9.

I'm working out how to tell whether the sub's front or back sits at column 9, since both leave lit cells there. Checking the back-cell columns for each facing and position suggests a rough test for whether a rightward nudge is needed.

I'm checking whether the sub has drifted left by seeing if any lit cell sits in columns 7 or below. If it has, I'd press right, but after two steps right the footprint sits at columns 8–9 and that test goes false, so I still need a way to tell that position apart from the one one step earlier.

I'm checking whether a rightward-facing sub at column 9 can be told apart from one at column 8, since both leave similar trails. Trail columns for the back cell differ between the two, but summing those across all rows is only a rough signal and gets muddied by entity trails. I'm considering a global count of column-8 versus column-9 trail cells as an approximation for facing.

I'm checking whether the drift test still holds with a couple of contaminating trails at column 8: two of them would push the rightward-facing score to 2 and flip the test, so the sub would press left and drift back toward column 7.

I'm checking whether the drift test still holds when the trail columns get contaminated: a single extra trail at column 8 leaves the score under the threshold, but two would flip it and make the sub press left toward column 7. I'm also considering that a contaminating trail at column 9 could make the sub miss a move back to the home position, though that clears once the entity passes.

I'm settling the start route: from the surface at column 5 I'd move right to column 9 and then step back left to the home column 8, and the drift correction would handle each step before I dive.

I'm weighing whether drift corrections underwater are worth the risk, since pressing right or left can carry the sub into an enemy's path, though such moves should be rare. If I drift left to column 7 while at home, I'd need up to three steps to recover, which is a minor exposure I can accept.

I'm wondering whether keeping the sub strictly at home is worth it, since drifting one column left to (7,L) would leave a threat at column 8 unseen by the column-9 check. I'll keep it strict, because the home position makes the front-region and danger-band logic consistent. The surface case needs its own check too: before diving from row 0, I still have to confirm the band in row 1 is clear.

I'm checking how divers behave in the topmost target row, since they could mean long waits: approaching ones get collected in about 48 steps, and receding ones leave the same way, while enemies are caught quickly by bullets.

I'm weighing whether exclusively chasing enemies, and collecting divers only when they happen to line up with my row, would be better than targeting divers too. Opportunistic pickup looks like it would only net around one diver per oxygen cycle, so I'm not sure I can drop divers as targets without running short on oxygen.

Now I'm weighing whether to tell divers apart from enemies by the difference between the two channels, since a diver shows up only in one and an enemy in both. That works per cell, but a row holding only bullets gives a negative count, which could push the total below the thresholds I'm relying on.

Weighing whether to chase enemies or divers first: a row holding a diver and a bullet cancels out in a combined count, so the detector can miss divers, and bullet-only rows push the total negative. I'm considering separate navigation for divers and enemies, but I have only one or two spare units to spend on that.

I'm weighing whether to pick targets by their topmost row or by distance, and I'm leaning toward topmost since it's deterministic and avoids oscillating between rows, though targets lower down will only get attention once the upper ones are cleared.

I'm weighing whether to keep the sub at row 1 or back off, since with no diving buffer (d=0), a sticky 'u' could carry it all the way to the surface and end the run.

I'm considering excluding row 1 from the targets entirely, so the sub only passes through it when surfacing or diving. A sticky 'd' from row 1 would just carry it to row 2, which is safe, but a sticky 'u' near the surface with no diver to spare would end the run.

I'm now worried about the sub drifting up to row 1 with a sticky 'u' and no diver to spare, so I'll try to keep row 1 out of the target set. I still need a per-row unit for the row-1 case, plus a suppression on 'u' there when d=0.

I'm settling the per-row units: row 1 only matters in transit, since surfacing needs a check on row 1 and diving needs one on row 2. I'll keep the row-1 units but won't treat it as a regular target row. The rest of the plan is intricate and hand-computed, so I'll need to check each piece carefully.

I'm working through how enemy subs behave when they spawn in our row: an enemy at column 0 gets shot down before its first bullet, as long as our shots reach that column in time. I'm estimating the timing, since a bullet fired from column 8 needs about 8 steps to get there, and we fire every 5 steps.

I'm checking the timing of bullets against an enemy that spawns at column 0, to make sure one of our shots reaches it before its first shot. The bullet columns repeat on a five-step cycle, so I'm working out which columns are covered at each step.

I'm checking the bullet timing against column 0 and column 1, which are hit on different phases of the five-step cycle. An enemy sitting at column 0 for five or more steps should get hit before it can fire, so spawns from the left look covered.

I'm checking how enemies in our row behave once we enter it: an enemy at column 6 moving right could be caught by our next bullet, so the danger band around columns 6 to 9 matters. I'll let the band check stop us from entering rows where threats sit in that zone, even though it also flags harmless receding enemies.

I'm checking how enemy bullets reach the sub in our row: an enemy bullet at column 5 would take about three steps to reach column 8, but I can dodge it since I move before bullets update. So a bullet at columns 4 through 9 counts as a danger when I'm deciding whether to enter the row.

I'm weighing whether to fold cols 4..5 into the entry check for bullets, since a bullet there reaches us in a few steps, but enemies at those columns are exactly the targets I want to shoot, so blocking entry on them would be counterproductive.

I'm settling on using the combined channel difference for the outer columns 4 and 5, since enemies there are exactly the targets I want, and plain enemy detection for columns 6 through 9 where approaching enemies could collide with me as I enter.

I'm checking whether an enemy sub at column 9 moving left could hit me before I can react. Its first shot doesn't come until about ten steps after it spawns, and by then it has already moved on to column 8, so the threat at column 9 on spawn is not an immediate hit.

I'm checking whether a sticky threat in my row can reach me while I'm still firing, and the bullets at columns 5 through 7 are the ones I'd need to dodge. Enemies sitting at columns 6 and 7 will get shot before they matter, so they aren't a reason to move, but a gap in the bullet stream could leave one of them alive where it's a problem.

I'm checking whether enemies approaching from the left could threaten me while I'm dodging vertically: if I leave the row because of a bullet, the enemy keeps coming in that row, so I'll only return once the band is clear.

I'm checking whether enemy bullets from receding subs in our row could trigger a false dodge: a sub at column 7 moving left fires a bullet that lands at column 6 on the same step, so my bullet check would misread it as a threat.

I'm now looking at the danger checks for when the sub is in its target row: if no immediate threat, it fires, and if a dodge is needed it moves up when that's safe, down when it isn't, and otherwise stays and fires.

I'm weighing dodging down by default, since moving up from row 2 could push the sub toward the surface with a sticky 'u' and no diver to spare. I'm considering a rule that allows dodging up only when the sub is at row 3 or deeper, or when a diver is available.

I'm weighing a simpler rule for the dodge direction: dodge down when that's safe and the sub isn't on the bottom row, and dodge up only when it's safe and the sub is deep enough or a diver is available. If the sub is on row 8, there's no room below, so I'd need a special case there.

I'm settling on a single combined check for the outer columns: the sub's own unit fires when it's in row 2 and there's danger in row 1 or no diver is available, so the dodge can't push it toward the surface with a sticky 'u'.

I'm now testing whether the diver gauge can be read reliably from column 9 alone: col 9 is lit only when oxygen is high, so the diver bar's position has to come from the cells just left of it.

I'm realizing that when oxygen is 180 or higher, the diver count can't be read from the bar, since it's hidden by the oxygen display. So right after a surfacing I have to assume the diver count might be zero, which means no upward dodges near the top rows.

I'm settling on a rule that the sub only dodges upward when it's surfacing, since oxygen above 180 hides the diver count and a stray 'u' could take it into rows 0 or 1. So for now the sub stays in rows 2 through 8, and I still need separate checks for when it's in row 1 and row 2.

I'm settling on a sub-in-rows-1-2 check, which suppresses 'u' presses so the sub never climbs toward the surface outside of a surfacing move. At the surface, I'll wait for targets to appear before diving, since staying there costs no oxygen.

I'm checking the row-8 case: the sub can't dodge down from there, so a "dodge down if safe" rule would press a no-op key and leave it exposed. I need either a special unit for row 8 or a rule that blocks the down-dodge preference when the sub is already on the bottom row.

Now I'm settling the up-blocking units for the lower sub rows: the bottom row gets a block that stops downward dodges, and the upper rows get checks that keep the sub from climbing toward the surface.

I'm working out the surfacing case now: when oxygen is low and a diver is available, the sub moves upward as long as it's safe, and reaching the surface refills oxygen and uses up one diver. The open question is what happens when oxygen is low but there's no diver left.

I'm checking what happens if the diver count reads as zero after a bonus surface: the gauge goes blank at -1, so my detector would wrongly conclude there are no divers and never surface again, leaving the sub to run out of oxygen.

Working out the diver count after a bonus surfacing: the gauge goes to -1 and then shows nothing, so my detector would read zero divers and I'd stop surfacing. Once divers are collected again the count climbs back toward a visible value, and it looks like the gauge stays consistent for surfacing decisions as long as it reads one or more.

I'm checking whether a diver count of 6 can be seen on the bar when oxygen is high, since the oxygen display overlaps the same columns. Surfacing at 6 divers could pay out a bonus of up to 10 points, so it's worth working out how to detect that state.

I'm working out whether a diver count of 6 can be told apart from 5 on the gauge. When oxygen is 5 or higher, the oxygen and diver bars overlap in the same columns, so the pattern looks identical, and I can only read the diver count exactly when oxygen is very low.

I'm checking whether a diver count of 6 can be picked out of the bar at low oxygen: column 3 is lit only for six divers when oxygen is below about 80. The bonus from surfacing at that point is small, so I'm skipping special bonus logic and letting the normal surfacing handle it.

I'm checking whether the diver count can be trusted after a bonus surfacing: the gauge drops to -1 and shows nothing, so my policy would read zero divers and avoid surfacing even when it's actually safe. That only costs me if I fail to collect two more divers before oxygen runs out, and I can't tell the two states apart from the observation, so I'll leave it alone. I also still need to account for the diver loss on each surfacing.

I'm estimating how often divers actually get collected: the ones spawning at column 9 and drifting left only become reachable once they reach column 8 or 7, and by then the sub often can't get to their row in time. The ones entering from column 0 are the ones I can plausibly chase, so the collection rate depends mostly on those.

I'm considering whether divers at column 9 could also count as targets, using the difference between the two channels so that enemies there are excluded, though a bullet could cancel a diver's signal.

I'm weighing the trade-off in using the col 9 channel difference to catch divers before they reach column 8, but a bullet there would subtract from the sum and could flip a row's threshold, so it would only cause brief errors.

I'm weighing whether receding divers should count as targets at all, since only approaching ones are worth going for, and I'm considering whether a direction-sensitive trail channel could tell them apart. Enemies are worth chasing in either direction, so the value of a row depends on what's there. I'm going to keep that trade-off in mind as I think about which row is most worth moving toward.

I'm weighing whether to target divers too, since the receding ones waste time, but using the difference between channels to catch them at column 9 risks bullets distorting the row sums.

I'm turning over whether receding divers should be excluded from the targets, using a per-cell trail signal to tell direction apart. A plain sum over the trail channel won't separate the two directions, so that idea doesn't work as a linear feature.

I'm weighing whether to start from the middle column instead, since divers always drift inward first and a central home might catch more of them as they pass.

I'm weighing a home at the far right column, since divers spawned at column 0 would then approach it for their whole crossing and the sub could collect them on the way.

I'm weighing a home at the right edge against a central one: divers spawning at column 9 would only be approachable for about six steps there, while a home at column 8 gives divers from column 0 a long approach, and a center home would catch divers from both sides for longer but adds threats from behind.

I'm weighing a home in the center with turning in place: the footprint stays at columns 4 and 5 while the front flips between them, which would let the sub cover divers from both sides. The catch is that threats can then come from behind, so I'd need to keep track of which way it faces.

I'm sorting out how to orient the sub in a center home: enemies on each side of a row either approach or recede depending on their direction, so facing the approaching side is the key, and the trouble comes when enemies sit on both sides at once.

I'm settling on a home at (8,L) because its fixed orientation keeps the per-row feature count low, and I'm dropping the center home since it would need about 40 features. Divers at column 9 might still be worth targeting if I can count them without bullets distorting the signal, but I'm not sure yet how to do that cleanly.

I'm thinking through whether divers at column 9 should count as targets too: the safety check on entering a row already keeps the sub clear of enemies there, so including them shouldn't cause dangerous moves, and divers in that column could still be collected once they drift to column 8.

I'm settling on targeting every diver channel entry across all columns and rows 2 to 8, since the band check uses the enemy channel and won't block those moves. Entities at column 9 can't cause dangerous entries, so including them just means the sub waits for them to drift closer.

I'm treating the topmost target row as the sub's goal, with targets being divers and enemies in rows 2 to 8 across all columns. If an enemy is still at column 9, the entry check keeps the sub out of that row until the enemy works its way left, which is fine.

I'm weighing a "nearest target" rule against the topmost-row rule, since the topmost one could leave lower-row enemies unattended while a slow diver holds the upper rows. I'm checking whether the distance to the nearest target above and below can be expressed with the same indicator features.

I'm trying to express "a target exists above the sub within j rows" as a linear feature, but a bottom-weighted geometric sum picks up targets below as well, so restricting to rows above doesn't work directly. I'm considering pairing an upward-looking indicator with a separate one to isolate the nearest target on each side.

I'm now settling the policy for choosing a direction: I'd check whether any target sits above the sub, prefer going up in that case, and otherwise fall back to a rule that also counts targets in the sub's own row.

I'm weighing a "target in my own row" unit against the topmost-target rule, since preferring up could leave an enemy in the current row ignored while a diver far above pulls the sub away. Per-row units for that would cost seven or eight more features, which doesn't fit the budget alongside the safety checks.

I'm checking whether a topmost-target rule causes oscillation when a target sits just above in a blocked band, and concluding the sub just holds and fires, so there's no loop.

I'm checking the case where a target in my own row triggers a dodge: after I step away, the top target is still in that row, so navigation sends me back up, but the band check blocks it and I just wait until the danger clears.

I'm settling the action priority: surfacing comes first when oxygen is low, and I'd hold off on drift correction until the threats are handled, since it rarely matters underwater.

I'm settling the dodge and navigation rules: dodge down if that's safe, otherwise up if that's safe, and otherwise fire. Navigation then goes up when a target sits above, and down when targets are only below, with rows 1 and 2 handled as special cases.

I'm settling the navigation rule: if a target sits above, go up unless the band blocks it, otherwise go down when only targets below remain, and fire by default. The up-move from row 2 stays blocked unless I'm surfacing, and dodges and drift correction come ahead of navigation.

I'm checking that row 0 is always safe to surface into, since no enemies spawn there. Then I'm working through the start position: the sub begins at column 5 facing left, and I'd need a few right-moves to drift off the edge before it settles at a home.

I'm writing out the frame-right detection as a sum over trail channels, subtracting the col-9 contributions and adding a bias, though the col-8 trails from other rows will leak into that total.

I'm checking whether the far-right indicator still works when the sub's back sits on column 8 facing right, since trails from other rows could leak into the total and make the signal unreliable.

I'm checking the far-right detection against the sub's footprint: when it's at column 9 facing right, the front trail there gives the signal, and when it drifts left the signal goes off. I'm now looking at how to express each row's occupancy using the sub's column-8 and column-9 trail channels.

I'm setting the unit so the output is positive only when the row is occupied and there is at least one danger cell: summing the row's sub-occupancy, adding each danger, and subtracting a threshold of 2.5.

I'm settling the danger unit with a per-row sum, using a factor of 2 on the row's occupancy and a threshold of 4.5, so it only fires when the sub is in the row and at least one danger cell is present. I'll tune the steepness afterward, since a sharper tanh gives a cleaner margin around the threshold.

I'm defining the threat-in-row unit: it fires when the sub is in row r and either an enemy sits at column 9 or a weighted count of enemies and divers in columns 5 to 7 is at least one.

I'm checking how a bullet at column 7 in my own row should be handled: one moving right would hit me on the next step, so that case calls for an immediate dodge.

I'm now working out the up-blocked condition for each row: the sub can't move up into row r−1 if that row's band holds a danger, with the band covering the right-side columns plus the left-side columns where bullets and divers count differently. Rows 1 and 2 still need the rule that 'u' is suppressed unless I'm surfacing.

I'm counting the units: 8 for row-threat, 7 for up-blocked, and 9 for down-blocked, plus three, one, one, one, one and one more. That totals exactly 32, which is tight, so I'm looking for any that could be dropped or merged, starting with whether the row-8 down-block is needed.

I'm now checking whether the down-block for row 8 is needed: if the sub is there with an up-block, pressing 'd' does nothing, so I'd rather prefer up and see if the extra unit can be dropped to fit the budget.

I'm dropping the separate down-block for row 8, since preferring an up-dodge covers that case. The sub at row 1 still needs its own threat check, because it moves in and out of the surface band during a dive or surfacing.

I'm dropping the separate threat check for row 1 if it would cost a unit, since the sub only sits there briefly during a dive or surfacing. Next I'm reconsidering whether the "any target exists" flag is needed, because without it the sub would simply head down to row 8 when no targets remain.

I'm weighing whether to keep the "any target exists" flag: without it the sub would drop to row 8 when the screen is empty, which is far from the surface, so I'd rather it stay put.

I'm checking whether the "any target exists" flag can be folded into the down-move: I'd need a second unit to separate targets below from none at all, and I'm looking for a cheaper way to express that.

I'm working out the navigation with a few special-case units: an up-move from row 2 stays blocked unless I'm surfacing, and the bottom-heavy count tells me whether a target lies below. The problem is that a bare "target below" check would make the sub drop away from a target sitting in its own row, then climb back, and oscillate. So I need the at-or-above flag to decide whether to hold or go down.

I'm working out whether a single unit can capture "some target lies at or below the sub" without needing both the at-or-above and no-targets checks separately. A two-sided band condition would take two units, so I'm looking for a formulation that keeps the total within 32.

I'm tallying the units so far: the threat, up-block and down-block groups, plus the three navigation flags, come to 31, leaving one spare. I'm also checking whether the separate row 1–2 "no up" rule can be folded into the up-block units instead of costing its own.

I'm checking whether the row-1 check for 'u' can be dropped, since at row 1 the sub should only go up when surfacing, and I'm weighing whether a single row-2 block can cover that case without its own unit.

I'm checking whether the row-1 and row-2 cases can be handled by baking the "no up" rule into the up-block units for those rows, so that no separate suppression unit is needed.

I'm checking whether the "surfacing" exception can be folded into the row-2 up-block unit: a single unit that fires when the sub is at row 2 and either row 1 holds a danger or the oxygen-not-low and no-diver conditions hold, so no separate suppression unit is needed.

I'm checking whether the separate row-2 check can absorb the surfacing exception, so that no extra unit is needed for rows 1 and 2. A unit that fires on the sub being at row 2 plus any of danger in row 1, oxygen not low, or no diver would cover it, but the negative weights on the divers' columns could make that OR-style unit fail to fire, so I'm weighing whether to keep a separate suppression unit instead.

Now I'm moving on to layer 2: the decision logic will be built from these 31 units. I'm treating each layer-1 output as a near-binary value and summing the target-threat indicators across rows.

I'm now expressing the decision as a combination of the layer-1 units: the threat count, up-block, and down-block sums, plus the three navigation flags. Since each unit outputs roughly ±1, I can recover the total threat count linearly from the sum, with biases absorbing the constants. The question I'm turning to is how upward movement is allowed, which depends on the up-block sum and on whether the sub is near the surface with surfacing conditions met.

I'm settling the action priority now: the drift correction ('r' or 'l') goes near the top, though I'm still deciding whether it should sit above the threat dodge or yield to it when the sub is in surfacing mode.

I'm writing the action priority as a decision chain: first drift correction, then a threat dodge that prefers up and falls back to down, then a surfacing rule that climbs when oxygen is low and a diver is present, and finally navigation that goes up toward targets or down only when nothing is at or above.

I'm settling on the action logic at the layer-2 level now, with separate triggers for each move: drift-right when DL is set, drift-left when FR is set without DL, and up when nothing blocks it and there is a threat, surfacing, or a target above. Down is the one I'm still working out.

Now I'm defining the decision for drifting left and dodging: drift-left is blocked when drift-right is active, and a downward move happens only when down is allowed and either a threat sits in my row with up blocked or nothing threatens and nothing is above me. Writing these as conjunctions of the layer-1 booleans, with the threshold units still to be sorted out.

I'm working out the up-allowed condition for the up move: it's blocked by the up-block units and only passes in rows 1–2 when the surfacing condition holds. Next I'm combining that with the threat and navigation terms to see what the up-move conjunction reduces to.

Next I'm splitting the upward-move condition into two layer-2 units. The first covers the surfacing case with oxygen low and a diver present. For the second, I'm checking whether one threshold unit can express "not drifting, no danger above, not in rows 1–2, and either a threat in my row or a target above," since the OR inside may need its own unit.

Checking that the two OR-style units combine correctly: the 'u' logit is just the sum of U2a and U2b, so either one firing is enough. Now starting on the down-move condition, D2, with the drift-exclusion terms first.

I'm writing the down-move trigger D2a as the drift exclusions plus the danger-below check, with the threat-in-row case and the blocked-up condition, which expands to danger above or the surface band with no surfacing.

I'm splitting the down-dodge into two units: one for when danger sits above in the up-block band, and one for rows 1–2 when surfacing doesn't apply, with the "not surfacing" part handled as a small OR-style threshold.

I'm settling the down-move condition next, splitting it into a case for a threat in my row that can't go up and a case for the navigation-down rule. The second needs the surfacing check, so I'm weighing whether to write it as a separate unit based on oxygen low and no diver present.

I'm writing the navigation-down unit D2b as the drift exclusions, no threat in my row, no danger below, and a target at row 0 but none above row 2, with the surfacing check left as an OR of oxygen-not-low or no-diver.

I'm now setting the output logits so fire is the default with a margin over the others, and each action's logit rises above fire when its trigger unit is active.

I'm checking how a random slip of 'u' near the surface would play out: at row 1 it could take the sub to the surface, and the chance per step is small but it adds up if the sub lingers there.

I'm estimating that a logit margin of about 8 keeps the chance of an accidental 'u' near row 2 very small, since e^-8 is around 0.0003 per step. I'm also noting that the no-op action should sit far below the others.

Now I'm checking the navigation-down case and the tanh saturation margins, and the per-row unit families still need sorting out.

Checking the sum for the row-0 case: when the sub sits at the surface, every row's threat and up-block units read −1, so the layer-2 sum just lands on a constant, and I still need to see what the danger-below unit at row 0 contributes.

I'm laying out the geometric units A0, A1, and A2 now, starting with the target counts per row for rows 2 through 8.

I'm checking how the bound for the row-count coefficients works out: each row can hold up to B−1 targets before the sum overflows, so with B = 4 it's three per row. I'm also noting that rows 2 through 8 give exponents 0 through 6, which puts the largest base term at 4096.

Working out the geometric units A1 and A2 now, I'm setting the per-cell weight to β·B^(8−r) with B = 4 and β = 6, so a target in row 2 carries 24576. For the sub's row threshold I'm subtracting β·B^(9−s) spread over its two footprint cells, which gives −12288 per cell at row 3, and I'm checking what the same term looks like for A1 when the sub is at row 2.

Checking the s ≤ 2 cases for the geometric units: since targets only sit in rows 2 through 8, A1 can be forced false for those sub rows by using the s = 2 threshold, and the largest value any sum can reach stays under that bound.

Now I'm setting the A0 unit for the any-target check: its pre-activation is β times the target count minus one half, so it fires whenever a target exists in rows 2 through 8. That makes DOWN equal to A0.

Now I'm checking that the target-cell weights and the sub's threshold terms stay within bounds, and both do, so the geometric units are numerically safe.

I'm working out how to decide when the oxygen counts as low, and weighing whether the sub can realistically climb back from row 8 before running out, since each upward step can be blocked by danger in the band above.

Weighing whether to surface at oxygen below 60 or below 40: the sub often sits in upper rows, so surfacing should be quick, but a looser threshold leaves more slack.

Weighing the oxygen threshold again: whether to surface at 60 or 40 depends on how many divers the sub can realistically pick up in the time left. I'm leaning toward 60 for the extra slack, though the sub may pick up a diver late and surface right away anyway.

I'm weighing col 1 (oxygen under 40) against col 2 (under 60) for the surfacing trigger, since a lower threshold leaves more time to rise from row 8 but cuts the slack for blocked steps. Even if the sub gets stuck, the margin of 39 steps should cover the eight rows up in most cases, so I'm leaning toward the stricter threshold.

I'm weighing whether the oxygen threshold should be 60 or 40, and I'm worried that an enemy sub sitting in the band above could hold the sub in place for a long stretch, potentially longer than the margin allows. I'm going with 60 for safety.

I'm reconsidering the band check, since it may be too conservative for enemies moving away from column 8 in the row above. An enemy at column 9 that is about to exit blocks the step for only a few moves, while one at column 7 moving left blocks it until it clears the band.

I'm checking the case where an enemy sits at column 7 in the row above and moves right: if my shot cooldown is still running, I can't clear it before it steps into column 8, so that case counts as dangerous. I'm now going to look at the enemy at column 6 moving right.

I'm now looking at the enemies in the band just above the sub's entry point, separating those that are about to reach column 8 from those moving away, and I'm weighing how far each one can get before I can clear it.

I'm checking the bullet cases now: a bullet at column 7 moving right reaches column 8 on the same update that I move in, so entering then is fatal, while bullets further left just force a dodge on the next step. A bullet at column 9 is exiting and harmless, but one sitting at column 8 means I'd be stepping into its cell.

I'm now checking the enemy at column 6 moving right: it needs a few steps to reach column 8, and a shot fired after I enter should catch it before it gets there, so I'm treating it as only slightly risky rather than blocking.

Checking the enemy at column 6 moving right: it needs a couple of moves to reach column 8, and firing right after I enter should clip it on the way, so it's only a mild risk.

I'm checking the entry band for the sub: enemies at columns 7 through 9 block the step, and bullets at columns 4 through 6 that are moving right do too, since a diver in the middle could cancel one out. I'm still weighing whether to use the bullet threshold directly rather than a difference.

I'm weighing how to handle bullets and enemies in the entry band: enemies at columns 4 to 6 are fine to ignore since I can shoot them down in time, while bullets there should block the step. For the threat check in my own row, I'm looking at whether enemies at column 9 can be ignored since they're leaving, and whether a bullet at column 5 to 7 should force a dodge, though an enemy at 7 moving right is still a concern.

I'm checking whether an enemy at column 7 moving right should block entry, since its bullets might not get there in time, and I'm also weighing whether bullets can clear it before it steps into column 8.

I'm noting that enemies can't reach column 7 alive while I keep firing, so I'll leave them out of the threat check. The only gap is if I entered when an enemy was at column 6 and it stepped to column 7 before my first shot; that's low risk, so I'm moving on to the bullet band for the destination row.

I'm now checking whether an enemy sitting at column 9 in my row, moving right, should trigger a dodge, since it is exiting and harmless, and I'm noting that my back cell overlaps it visually.

I'm checking that a bullet from an enemy sub at column 5 or 6 gives me enough steps to dodge before it reaches column 8, so entry is safe even when the enemy shoots first.

I'm checking how likely an enemy sub at column 6 is to shoot before my bullet reaches it, since if I enter right then it only has about one chance to hit me.

I'm now widening the entry check: enemies at columns 6 through 9 block the step, while bullets at columns 4 and 5 do so only when a diver isn't cancelling them out. For the threat check in my own row, I'm watching column 9 and bullets at columns 5 through 7.

I'm checking whether an enemy sub in my row that is moving left, at column 7, would fire a bullet toward me, since that bullet would appear at column 6 and force a dodge.

I'm sorting out which rows need which checks: the threat check for each row, the up-dodge for rows 2 through 8, and the down-dodge for rows 0 through 7, which comes to 23 units in total. Adding the eight global flags brings it to 31, which leaves one spare unit that I might use for the bottom row.

I'm still settling the spare unit: a surface-row check would not help, since at row 8 the fallback is a no-op either way. I'm also considering whether an early surfacing bonus can be detected from the oxygen columns, but the column-3 signal overlaps with the oxygen lighting, so it doesn't separate the two cases.

I'm checking whether the oxygen bar and the diver bar can be told apart at the surfacing threshold, since both light up column 3 once the diver count reaches six. Column 3 alone doesn't separate them, so an early-surfacing signal from the oxygen columns doesn't look workable.

I'm weighing whether to use the spare unit on something useful, and I'm going through the candidates: direction-aware targeting, early surfacing, and a two-level oxygen signal. Early surfacing is ruled out because the oxygen and diver bars light the same columns in different combinations, and the other options don't add anything I need.

I'm reconsidering the row-1 threat unit: a sub sitting at row 1 happens when the danger band below it blocks diving. In that case it can't go up or down, so it just has to fire back.

I'm deciding whether the row-1 threat unit is worth keeping, since a sub at row 1 is stuck and can only fire back, and surfacing happens through rows 1 and 0 regardless. Dropping it would free a unit for the layer-2 logic, so I'm weighing that trade-off against what I still need to encode.

I'm settling the layer-2 encoding now: the row-1 threat unit is effectively the only thing left to decide, and the reset signal DL can feed straight into a layer-2 unit as a plain pass-through.

I'm wiring up the layer-2 units now: one for the pass-through of the reset signal, one for the lift-off condition, and a handful of combined gates for the up-dodge, down-dodge, and fallback cases.

I'm settling the layer-2 units for the down-dodge and navigation cases: the navigation-down unit should only fire when no threat is present, since otherwise the dodge logic has to take over.

I'm verifying that the surfacing case works when a blocked-above state holds: if there's a threat I dodge down where possible, and otherwise the navigation-down and up-navigation units stay off, so the sub just fires and waits.

I'm checking the edge cases now: a threat at row 8 with the upward move blocked just leads to a downward dodge that does nothing there, so the sub stays put and gets hit either way. For rows 1 and 2, a threat without surfacing sends it down if the cell below is clear, and with surfacing active and the cell above free it goes up instead. When surfacing and the cell above is blocked, it dodges down only if that is clear, otherwise it holds and fires.

I'm checking that the up-dodge and down-dodge units are mutually exclusive: each one needs a condition the other rules out, so they never both fire. The navigation and surfacing units also exclude each other the same way. The last point is that the reset signal and the forward-movement units cannot both be active, since every dodge and navigation unit already requires the reset to be off.

I'm writing out the output logits for each action, with the layer-2 booleans mapped onto the ±1 encoding, and the up-dodge and down-dodge units each collect their two contributions. Where both up-dodge units fire, the logit doubles, which is fine.

I'm settling the output logits now: fire is the default, and each action gets a bonus when its condition holds. With a margin M of 8, the constants work out to C = 8 and W = 16, so a triggered action beats fire and the rest stay well below it. Fire is harmless even when it does nothing, since that matches a no-op.

Now I'm checking the start-of-game case: the sub sits at row 0 with full oxygen, so the surfacing signal stays off and diving is the only move once targets appear.

Now I'm turning to the early game: the sub starts at the surface with full oxygen, fixes its drift first, and then waits and fires until a target appears in rows 2 through 8, at which point it dives.

Now I'm checking the navigation case at row 2, where the target has to be somewhere above the sub for the up-move to matter.

Checking the row-1 transit case next: with the sub moving down, the threshold A2 is false there since no target sits at or above row 1, so the dive goes ahead. I'm now turning to the geometric thresholds, which read the two ch0 cells in the sub's own row. For each row I'm defining the weights for A1 and A2 against a threshold that shifts with the row.

Writing the threshold weights as powers of 4 now, so each row's contribution to V is spaced out in a way that keeps the A2 check at row 8 clean.

I'm checking the per-row thresholds: the sub's two cells in row s each carry a weight of −β·Θ(s)/2, with a bias of +0.5β, while A0 has no cell weights and a bias of −0.5β. With β = 6, every pre-activation lands at least 3 away from zero, which keeps the comparisons clean.

I'm checking whether the ch0 cells appear anywhere besides the sub's own two cells in its row, and they don't. Entity rows 1 through 9 are where the counts come from, so I'm now checking whether a row can hold four or more entities, which would push the sum past the bound I've set.

Checking whether a row with four or more entities would push the count past the bound: at row 5, four entities give 256, which reads like a target in row 4, so the sub could drift up there with nothing actually present. I'm treating that as rare and acceptable. Next is the oxygen-low check, where the threshold on column 9 flips the sign of the pre-activation.

I'm checking the drift-left condition next: it should count the sub's cells in columns 7 or below, which at home position means ch0 is zero there and the pre-activation sits at −3.

I'm checking the forward-drift condition: with the sub at (9,R), the counts give +0.5 and it fires correctly, but with a stray trail in column 8 at (8,L) it still reads as the right answer, while two such trails would flip it.

I'm weighing whether the foreground trails at column 9 could make the forward-facing check misfire, since the sub is exposed at that edge. The contamination from entities crossing columns 8 and 9 is what makes the sign of that formula unreliable, so I'm considering an alternative formulation.

I'm working out the sensor thresholds for the sub's own row and checking the forward-facing condition. The next step is the surface-warning weight, which should be +6 when the sub is in rows 1 or 2 and −6 otherwise.

I'm writing the per-row unit for row r: its pre-activation combines the sub's cells in that row with a count of nearby entities and trails, so it reads +0.5β only when at least one such entity is present.

I'm working out the drift-left and forward-facing sensor formulas, and the trade-off is that a bullet in column 6 combined with a diver in column 7 cancels out and would miss a shot. I'm settling on a weight of 3 for the per-row sum so the unit stays off when the sub isn't in that row.

Now I'm setting the upward-danger check for each row: it sums the danger cells in the row just above and adds a weight of 4 for the sub's own row, so the unit fires only when both hold.

Now I'm setting up layer two, where each unit takes ±1 inputs and computes an AND over its literals.

I'm working through the layer-two units now: each AND unit's pre-activation is scaled so that all literals true gives +0.5κ and any single false literal gives −0.5κ, with κ = 6 putting the values at ±3. For the units that include an OR of two terms, I'm weighting the OR so it still reaches the threshold when at least one of those terms holds and all the AND literals do.

Now I'm converting the layer-two literals into the h-domain: each b_i becomes (h_i + 1)/2, so a coefficient c on b_i turns into c/2 on h_i plus a matching bias shift, and a negated literal flips the sign of that weight.

Now I'm mapping the layer-1 units to their indices, so each family of threshold units lines up with a fixed slot in the second layer.

Now I'm working out the layer-two unit that flags the left-facing drift case: it should fire only when the forward-facing sensor is on and the drift-left sensor is off, so I'm setting its weights on those two first-layer units with a scale of 3.

Now I'm setting the weights for the M2 unit, which requires the sub to be clear of the drift-left and forward-facing signals, no upward danger, oxygen low, and a diver present.

I'm now expressing the layer-two literals in terms of the h values, so the remaining terms for the M2 unit (the sum of the drift-left, forward-facing, upward-danger, oxygen, and diver literals) are being put into the same form.

I'm finishing the M2 unit's weights in the h-domain: the literal for oxygen-low and diver-present each add a positive coefficient on their h-values, while drift-left, forward-facing, and the upward-danger units enter with negative coefficients, which gives the pre-activation as −30 plus a weighted sum. Setting W2 for drift-left to −3 is the first of those entries.

Now I'm checking the h-domain weights for the M2 unit: the drift-left and forward-facing inputs and the upward-danger inputs get −3 each, while oxygen-low and diver-present get +3, with a bias of −30. With all literals true that gives 33 and with one false it gives 27, so the sign stays correct.

Now I'm writing the weights for the M3 unit, which needs the drift-left, forward-facing, upward-danger, and surface-warning signals all off, plus either a per-row T unit or the A1 unit on, so I'm converting its literals into the h-domain.

I'm combining the h-domain terms for the M3 unit: the inner sum comes out to −2 − h_DL − h_FR − Σh_UB − h_S12 plus half the sum of the T-unit outputs, with a constant of 4 added on.

I'm checking the M3 unit's combined expression: the AND literals and the OR over T and A1 reduce to a constant of −36 plus weighted h-terms, and with all AND literals true and the T and A1 units off, the total comes out to 0, which is the boundary case I need to resolve.

Now I'm working on the M4 unit, which needs the drift-left and forward-facing signals off, the down-danger signal off, and both the T and UB signals on.

I'm combining the drift-left, forward-facing, down-danger, T, and upward-danger terms for the M4 unit, which gives a sum of 5.5 plus half of the combined h-values with the appropriate signs.

I'm checking the M4 unit's threshold for the case where T is false: the combined sum drops to −3, which pushes the pre-activation negative, so it stays off.

Checking the M5 unit's combined expression, so I'm working out its literals in the h-domain next.

Now I'm working out the M5 unit's pre-activation: the AND literals combine into a sum over the drift-left, forward-facing, down-danger, T, and surface-warning terms, and the OR of the oxygen-low and diver-present negations is folded in with a constant of −27.

Checking the M5 unit's pre-activation: with all the AND literals true and at least one OR term true, it comes out to +3, so it fires, and with both OR terms false it drops to −3, so it stays off.

Now I'm writing out the M6 unit, which needs the drift-left, forward-facing, and down-danger signals off, the T-units off, A0 on, A2 off, and the oxygen-low or diver negation on.

Now I'm simplifying the sum for the M6 unit's AND literals, collecting the h-terms and their signs.

Now I'm checking the M6 unit's sum with all AND literals true, which gives 120, and then the OR terms, where the oxygen-low negation is false and the diver term can vary.

Now I'm settling the output layer: with the hidden units at roughly ±1, each logit reduces to a constant plus a term proportional to the M-unit activation, so the scaling works out to cancel the offset.

Now I'm settling the output logits: each one reduces to a bias plus a multiple of the relevant unit activations, and the scaling makes the on and off cases come out at roughly +M and −M.

Checking the output logits: with the hidden units at roughly ±1 and M = 8, each action logit lands at about ±8, so the fire action wins by a wide margin when nothing else is active.

I'm now checking the failure cases, starting with diving with no divers in sight, which leads to running out of oxygen, and then the surfacing path, which climbs through rows 2, 1, and 0 without needing extra safety conditions.

I'm checking the remaining failure cases in the navigation: a bullet from the left could still reach me while both adjacent rows are blocked, and an enemy approaching from the right is covered by the blocked-row rule. Entering a clear row with an enemy moving toward me from the left is fine since I can shoot it, but a bullet already in flight at the left edge could catch me before the threat check triggers.

Checking the dodge logic: when a bullet or enemy threatens, the sub tries to move up unless that puts it in rows 1 or 2, otherwise it moves down. Once the threat clears from the lower band, navigation brings it back toward the target row, and it fires at anything in the row it's waiting in.

I'm going through the remaining edge cases for the sub: a drift that is rare, and the case of being at row 1 during surfacing with a threat at column 9, which the surfacing rule still handles by moving up. I also note that once surfaced the surface signal is off because oxygen is full, and that oxygen can't drop while at the surface, so the low-oxygen case there doesn't arise. I'm starting to check the initial state at row 0, column 5, facing left, where the drift-left rule would fire a rightward move.

I'm stepping through the opening moves from the start: the sub is at row 0, column 5, facing left, so the drift rule fires a rightward move, and the sub keeps going right until it reaches column 9, where the forward-facing check flips it back left and it returns home.

Next I'm checking the case where an enemy sits at column 9 in our row while we're still at home. The trigger fires and we dodge, and since the enemy takes several acts to move, there's plenty of time to react.

Next I'm checking how the sub handles divers and bullets approaching its front: divers moving left from column 9 reach column 8 after one move, while divers moving right from the left reach it eventually. The sub's front edge is where the collection happens, so I'm working out how that interacts with the threat checks.

I'm checking the edge case where a diver moves left from column 9 and reaches the sub's front, and then the case of an enemy sitting at column 9 in the sub's own row, which should trigger a dodge.

Now I'm checking the case of a bullet fired by an enemy sub at column 9 moving left, which the same trigger should also catch.

Now I'm checking whether enemy bullets fired from col 9 could hit me at col 8, and I note that the enemy sub placed in my row gets to move before its first shot, so those cases are covered. I'm also looking at whether bullets from enemy subs approaching from the left are caught by the threat check at cols 5 to 7, which it should be.

I'm thinking through the scoring: the sub mostly stays in the topmost row with targets, shooting what's in front of it, and the question is whether travel and kill time per target keeps up with spawns, with divers taking longer to collect.

Now I'm weighing whether to keep divers as targets at all, since a sub waiting on a receding diver can waste many steps while higher-row targets pile up.

I'm wondering whether a receding diver in row 2 could tie the sub up for dozens of steps while higher-row targets pile up, which would make including divers costly. Dropping them entirely would hurt collection, though, so I'm considering a direction-aware rule that only counts divers heading toward the sub's front.

I'm weighing whether a direction-based rule could separate divers approaching the sub's front from those drifting away, since trails alone don't tell the two apart.

I'm weighing a left-half target window, where right-movers are still far enough out to wait for and left-movers will exit soon. I'm also thinking about weighting divers by how far left they sit, since those furthest out take longest but are guaranteed to reach the sub.

I'm considering a variant where the target set is the diver cells on the left half of the sub's row, minus the trails shifted one column over, so that divers moving toward the sub count while those drifting away mostly drop out. The sum still mixes both directions, though, so I'm checking whether the subtraction really separates them.

I'm trying to isolate only the divers moving toward the sub's front by subtracting trails, but the offset for left-movers and right-movers doesn't cancel cleanly, so a plain shifted subtraction still leaves some noise from the right-movers near the left edge.

I'm checking whether assigning weights to the trail and entity cells can make left-movers cancel to zero while right-movers come out positive, and it looks like a weight of c+1 on the entity and c on the trail works, though other trails in the row could still interfere.

I'm considering whether the per-row weighted sum stays a clean nonnegative count, since overlapping trails and the sub's own back cell near the edge could push it off, but I think those cases are rare enough to accept.

I'm trying to make the per-row value stay small by giving each entity a contribution of 0 or 1, since a single linear unit can't threshold per row, so the base has to be kept small. I'm considering a design where left-movers contribute zero and right-movers contribute one.

I'm weighing whether bullets and enemies moving in either direction should count as targets too, which would mean adding weighted terms for the enemy channel. The worry is that bullets would pull the sub toward rows where they're flying, and that could be dangerous.

I'm checking whether the negative trail term can be made to work with these weights, since it still needs to stay nonnegative per row. With B = 6 and β = 6 the numbers fit under the 10^6 limit, so the design looks numerically feasible.

I'm noticing that right-movers at cols 8 and 9 would subtract a trail from a column the sub's own weighting doesn't account for, which could push the row value negative, so I'm considering restricting which entities get the positive weight in those edge columns.

I'm checking whether the weights for the rightmost columns can be set so that right-movers there still come out nonnegative, which would require either dropping the trail at column 9 or assigning weight to columns 8 and 9 directly.

I'm checking whether the right boundary breaks the design, since counting trails at the edge columns without their matching entities would push right-movers negative. Truncating the trail range keeps the sum nonnegative, but then the edge entities need their own handling.

I'm checking the right boundary again: counting trails at the edge columns without their matching entities pushes right-movers negative, and I'm weighing whether to accept a small negative term from right-movers at cols 8 and 9, since those are rare and short-lived.

I'm checking whether the negative terms from right-movers near the right edge can be bounded, since a row-9 entity would subtract a large amount from rows below it. Even if those errors are transient, they could mislead navigation for a handful of steps, so I'm weighing a simpler alternative to the weighted trail design.

I'm considering a simpler target set: enemies and bullets across the left columns, plus divers only in the first few columns, though right-movers there are far from the sub and left-movers are about to leave. I'm also going back to the trail-weighted design, looking for a per-row value that stays between zero and the base limit.

I'm sketching a per-row score that adds up the enemy and bullet cells across the left columns and then a diver term built from the trail cells, aiming to keep divers approaching the sub counted while the others drop out.

I'm checking whether adding weighted terms for the right-hand columns 8 and 9 can cancel the negative contributions from right-movers there, so the row value stays nonnegative.

I'm considering whether to offset the sub's own back cell with a term from ch0, so the trail weighting doesn't distort the sub's row value.

I'm adding a +7 term from the channel-0 cell at column 9 in each row, which cancels the sub's own back cell when it's at home. The transient case, where the sub sits at column 9 with its back at column 8, leaves a small net error that I'll set aside for now. I'm also looking at how enemies and divers entering from column 9 get counted, since the weighting there is uncertain.

I'm now checking the left-movers at columns 0 through 7, where each one's entity weight is offset by the trail weight at the next column, so the contribution comes out to zero.

I'm checking the left-movers at column 8 and 9, where their entity weights line up with the trail weights and cancel to zero, though at column 9 they're left uncancelled and count positive. For the right-movers, column 0 gives a value of 1 with no trail, columns 1 through 7 come out at 2, and the two edge columns 8 and 9 both net to zero.

I'm now checking the contributions for the right-movers and left-movers at each column, and finding that right-movers at cols 0 to 7 count between 1 and 3 while left-movers at 0 to 7 mostly drop out. I'm also adding a plain +1 for enemies and bullets across the left columns, since that gives the enemies a value in every direction.

I'm now trying a bounded version: enemies at the left columns count regardless of direction, divers only when they approach, and the base is kept small enough to fit under the numeric limit.

I'm weighing a simpler target set of enemies and divers in the front columns, since the weighted trail design keeps producing boundary errors at the edges. The fraction of time the topmost target is a receding diver seems small enough that the cost of the simpler approach may be acceptable.

I'm settling on a simpler target set: enemies and divers in columns 0 through 7 in any row, which means roughly one in five times the sub might idle on a receding diver, but the boundary errors in the weighted design aren't worth fixing. I'm leaving divers at column 9 out of the target set for now, since reaching them takes several steps and the sub will often be in a different row by then.

I'm weighing whether to include the far-right columns too: entities at columns 8 and 9 moving right are already leaving, and enemies at column 9 moving left can't be entered yet, but divers at column 9 moving left would reach the sub's zone within a few steps and are worth counting.

I'm weighing whether to add the col 9 divers through a diver-only term, since enemies there cancel out but bullets would subtract, and a bullet there could briefly pull the row value below zero.

I'm checking whether bullets at column 9 could briefly push a row's value negative and mislead the threshold check for the topmost target, weighing whether that one-step error is acceptable.

I'm weighing whether a half-weight term for divers at column 9, offset by bullets there, could keep the per-row counts workable without breaking the integer margins I'm relying on.

I'm settling on targets as the top-band cells in columns 0 through 7 plus a diver-only check at column 9, and I'm thinking about whether to add column 8 too, since left-movers there are about to recede into the target zone.

I'm settling on B = 5 as the base, since with the per-row counts capped at 4 the geometric weights still fit under the numeric limit. Now I'm working out the threshold for the sub's second check, Θ2(s).

I'm settling the threshold for the sub's second check, and I'm keeping the other rows' bullets from pushing the score negative by letting the base stay at 5.

Now I'm checking the sub's own row, where the middle band of columns 5 through 7 is compared against the sub's position, and an enemy sitting at column 6 cancels out to zero there. I'm also keeping track of two spots where the weighting could drift: the front and back columns of the transit unit, and the global bullet check at columns 8 and 9.

I'm now checking the destination row for danger: an enemy at column 8 blocks the move, and so does one at column 7 that's about to advance into column 8.

I'm checking the destination row for hazards: an enemy or bullet at column 7, 8 or 9 would be a collision, and bullets still a few columns away would reach the sub in a few steps, so the band covers those columns too.

Next I'm checking the vertical moves for safety, and I've decided that staying put is covered by the column 9 check and the bullet check. Enemies coming at me from the left in my row get shot, so I'm not worried about them there. I'm also wondering about an enemy at column 7 in my own row moving right while I've been busy moving, since that's the case where the band might not catch it in time.

I'm checking the destination row for hazards before moving, and if the enemy or bullet that just triggered the dodge is now sitting in that band, the move is blocked.

I'm sketching the dodge logic: moving up when a threat is in the destination band, and checking the sub's row and the bullet exiting at column 9 before deciding to step back down.

I'm picturing the diver odds over 200 steps and thinking navigation will probably collect at least one diver, after which I'd surface once oxygen drops low. I'm also considering whether to use the spare unit for something else, like keeping the sub out of row 8, but I'm leaning toward leaving it alone.

I'm checking the diver bar and the oxygen threshold: the DIVER flag sits at column 8 once oxygen is high enough, and OXLOW at column 2 flips when oxygen drops below 60, so surfacing only triggers at low oxygen. I'm also confirming that the combined condition for the dive and surface checks reduces to not surfacing, and I'm about to test whether the sub could deadlock while surfacing.

I'm checking whether the sub could get stuck surfacing, since an enemy crawling left along the row above could hold it under the surface and burn oxygen while it waits, though the topmost-target navigation should keep the surfacing distance short.

I'm checking whether a threshold of 80 would work better, but col 3 is lit by the diver bar once six divers are collected, so OXLOW would never trigger there. I'm sticking with the column 2 check, which means oxygen below 60, and I'm wondering whether the sub might stall while surfacing if the path above stays blocked.

I'm checking the oxygen cutoff at zero and how the sub's row-0 checks stay off, then wondering whether surfacing could stall too long.

I'm checking the surface case: if the sub is at row 0 with targets but the dive is blocked, it waits and keeps firing, and the bullets it sends along row 0 are harmless. Next I'm confirming that the row-1 rule holds when a threat is present, since the dive stays off and the sideways dodge takes over in the same direction.

I'm estimating how often the sub might drift into row 2 and then slip up on a noisy 'u', since that would lead toward the surface and possibly a death if no diver has been collected.

I'm settling on a logit margin of 10 for the policy, since the softmax noise at that size drops to around 4.5e-5, small enough to ignore.

I'm now worried about the sticky action: a 10% chance the previous move repeats, so after a vertical dodge the sub could slide again into a row I haven't checked, and over many vertical moves that small risk adds up.

I'm estimating the danger from stickiness: roughly 6% chance that the destination band holds an enemy or bullet, so about 0.6% risk per vertical move, which adds up over the ~30 vertical moves in an oxygen cycle to something like 17% death from that alone. I'm wondering whether fewer vertical moves could cut that down, since the topmost-target navigation keeps shifting the sub up and down.

I'm weighing whether the stickiness of the policy makes the rare drift corrections risky too, since a repeated 'l' after a correction can push the sub one column further left before it recovers.

I'm checking the sub's leftward and rightward moves at the edge, where stepping to column 9 is safe, and noting that a sideways step at column 9 simply holds position.

I'm checking the case where the sub ends up at the far right underwater, since a sticky move could leave it facing right at column 9 with firing doing nothing. In that spot an enemy spawning in its own row would be an immediate collision, though I'm treating that risk as small.

I'm settling the fire-or-stay case: if the sub is in a row with a target and the dive is blocked, it just keeps firing from where it is. Even with no targets in the usable rows, it simply holds position. I'm also checking that it won't get stuck deep down, since a new target above should pull it back up.

I'm noting that right-moving enemies in my row should already have been shot before reaching column 8, and that I shouldn't have entered with one sitting at column 9, so those cases are rare. The real triggers are left-movers spawning at column 9 in my row and incoming bullets, plus a few stray bullets near the edge.

I'm checking the band test for up and down moves: a bullet at column 4 or 5 blocks, while a diver there subtracts from the count, so I'm making sure a diver can't hide a danger in the same row.

I'm wondering whether a diver sitting in cols 4–5 could mask a real danger further right, since subtracting divers from the band count would hide it. To avoid that, I'm considering treating anything in cols 4–5 as blocking, so entry waits until the column clears even if it's just a slow enemy.

I'm weighing whether a diver in cols 4–5 could cancel out a real danger further right, so I'm considering weighting the band so that any danger at cols 6–9 still clearly blocks entry.

I'm settling the band weights so that a diver in cols 4–5 can't cancel a real danger at cols 6–9: I'm giving cols 6–9 weight 2 and cols 4–5 weight 1 with divers at −1. That puts the maximum band score at 10, so I'm working out the threshold for the AND with the sub's own row.

I'm setting the band weights for the terms: cols 6–9 get weight 2 and the diver-subtracted cols 4–5 stay at 1, so the total for the up/down blocking check comes out at 10. I'm working out the threshold from that, and the same kind of weighting for the topmost-target check is next, with the col 9 enemy term at weight 2 so a diver in cols 5–7 can't mask it.

I'm worried that a diver sitting in columns 5 to 7 could hide a bullet in the same row, since subtracting divers from the count cancels out the danger. I'm checking whether that masking is actually a problem for the topmost-target check when I'm waiting on a diver.

I'm checking whether a diver in columns 5 to 7 could mask a bullet, and weighting those columns so a bullet still registers. An approaching enemy sub in that range would then trigger a dodge too, which costs a kill but keeps me safer.

I'm worried a diver in cols 5–7 could mask a bullet, but giving those columns extra weight would also make me dodge receding enemies and oscillate. I'm working out how to tell bullets apart from enemies on that side.

I'm trying per-cell weights instead: a bullet counts 3, an enemy 1, and a diver −2, so a diver can't cancel a bullet, and a threshold of 2 would catch bullets while letting enemies through.

I'm running into the same masking problem again: a diver's negative weight can cancel out a real bullet in the same window. Since divers are common, I'm considering whether to drop the negative term altogether and use enemy trails instead, since bullets have no trail while enemies do.

I'm checking whether a diver's trail cancels a bullet's signal in the same window, and it does: a bullet at col 4 with a diver at col 6 nets to zero. I'm wondering if I can skip the trail-based approach and just treat any enemy approaching at cols 5–7 as a threat, accepting extra dodges in exchange for not missing real bullets.

I'm now checking the case where a diver in columns 5 to 7 could mask a bullet, and I'm weighing whether dodging an approaching enemy there is worth the cost. Enemies rarely reach those columns in my row while I'm firing, so the masking risk is probably small.

I'm now checking the case where a bullet could reach me unseen: a bullet at column 5 isn't caught until it reaches column 6, leaving two steps to dodge. With a sticky move succeeding only about 10% of the time, I'm estimating the chance of failing both attempts as very small, so I'm continuing with that window.

I'm now looking at the right-side window: a bullet at column 6 or 7 should still trigger a dodge even if a diver sits at column 5, so I'm weighting those columns at 2 and the column 5 term at 1 to keep a diver from cancelling it.

I'm settling on a weighted band for the topmost-target check: cols 6, 7 and 9 count double, col 5 counts once, and a diver at col 5 subtracts from that single term. Then I'm working out the threshold so a bullet at col 6 or 7 still triggers a dodge even with a diver present, while divers in row alone don't.

I'm checking the band weights for the topmost-target check, and whether a bullet entering at col 5 or 6 gets caught in time.

I'm still going through the band term for the up/down check, where the diver in cols 4–5 gets subtracted so it can't hide a real bullet further right.

I'm now setting the upper band's threshold at 6 units of weight, which makes the combined score 12, and working out the offset so a single danger still clears the cutoff.

I'm now writing out the layer-1 weights as a formula over the input index, with a helper that maps each row, column and channel to a position in the input vector.

Writing out the per-row weights for the threshold units: each row's unit takes the sub's row signal at weight 4, bullets and enemies at columns 5 to 9 at weight 2 or 1, and a diver at column 5 subtracted, with a bias that puts an empty row at −3.

Setting up the upper-band units now, each with the sub's row at weight 6 and every column's channel 0 wired in.

