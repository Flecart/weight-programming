## Observations

The rotations must be undone before interpreting a row as a grid cell. For each listed pair, I use
\[
W_{\mathrm{orig},i}=cW_{1,i}+sW_{1,j},\qquad
W_{\mathrm{orig},j}=-sW_{1,i}+cW_{1,j}.
\]
The following are manual spot checks; hidden-unit indices are zero-based.

- **Channel 0 — agent: the clearest learned structure is on the bottom playable row, consistent with a paddle.** At **(8,1)**, input 405, the recovered weight to hidden unit 15 is approximately **+4.07**. This follows from pair `(155,405)`, angle 108°, and shown weights **−3.8498** and **−1.3085**. At **(8,3)**, input 415, the corresponding recovered weight is approximately **−1.86**, using pair `(2,415)` and shown weights **+0.4905**, **−1.7910**. Thus different horizontal positions on the bottom row have substantial, differentiated representations. In contrast, apparent large weights at some higher agent positions cancel: at **(1,1)**, input 55, the recovered unit-5 weight is only about **+0.053**, from shown weights **−1.8969** and **+1.2481** in pair `(55,144)`.

- **Channel 1 — moving objects: strong sensitivity at multiple interior positions, suggesting a ball moving through the field.** At **(2,3)**, input 116, the recovered unit-7 weight is about **−5.49**: pair `(12,116)` combines shown weights **5.1945** and **1.7864**. At **(4,2)**, input 211, the recovered unit-8 weight is about **+6.41**, from pair `(70,211)` and shown weights **−3.3278**, **−5.4790**. These are much larger than the roughly tenth-sized weights of many inactive inputs.

- **Channel 2 — reward targets: substantial structure in the upper three playable rows, characteristic of bricks.** Examples include:
  - **(1,4)**, input 72: recovered unit-1 weight approximately **+1.03**, from shown weights **0.7420**, **0.7222** in pair `(72,207)`.
  - **(2,7)**, input 137: recovered unit-21 weight approximately **−2.42**, from **0.8576**, **2.2614** in pair `(32,137)`.
  - **(3,1)**, input 157: recovered unit-0 weight approximately **−4.81**, from **0.2482**, **−4.8223** in pair `(157,430)`.
  
  Below that region, the checked target inputs are much weaker. The same `(72,207)` calculation gives only about **−0.050** at **(4,1)** for unit 1. At **(6,5)**, input 327, the 90° rotation makes its original row the negative of shown row 133, whose entries are small—for example **−0.121** and **0.130** before negation.

- **Channel 3 — obstacles: the checked interior locations are weak, rather than showing a learned maze or extensive internal hazards.** For example, the recovered unit-1 weights at **(2,4)**, input 123, and **(3,5)**, input 178, are approximately **+0.068** and **+0.022**. These use shown pairs **(0.1835, 0.1899)** and **(−0.0651, 0.1835)**, respectively. The always-present wall border can also provide a constant contribution; its weights alone do not demonstrate active collision reasoning.

- **Channel 4 — previous frame: strong interior structure, consistent with tracking ball motion.** At **(3,8)**, input 194, the recovered unit-7 weight is approximately **−3.69**, using shown weights **2.3772**, **2.8277** in pair `(0,194)`. At **(4,2)**, input 214, the recovered unit-8 weight is approximately **+3.76**, using **−0.5473**, **−3.7227** in pair `(54,214)`. Previous positions therefore matter well above the bottom-row agent.

- **Output layer: left and right are the distinctive control actions.** No-op, up and down often have similar weights, while horizontal actions differ sharply. For example:
  - W3 row 11: **`−0.177, 0.185, 0.450, 4.057, −0.414`**
  - W3 row 22: **`0.376, 0.387, 0.537, −5.336, −1.203`**
  - W3 row 24 gives right **+3.031**.
  
  The output biases are **`1.221, 1.008, 1.024, 0.897, 1.298`**. They are fairly similar and do not themselves suppress vertical actions; the stronger evidence is the learned horizontal differentiation.

## Reasoning

The combination is particularly diagnostic: **a bottom-row horizontally controlled agent, a moving object in the interior, important previous-frame information, and reward targets concentrated near the top**.

A falling-object catching game could explain the bottom-row controller, but not as naturally the substantial upper target field alongside a separate moving-object representation. **Pong** explains a paddle and a tracked ball, but ordinarily lacks a field of reward targets across the upper rows. **Breakout** explains all of these together: the targets are bricks, the moving object is the ball, and the agent is the bottom paddle.

Snake, maze navigation and Pac-Man-like games are poor fits because they normally require agent-position structure throughout the interior and meaningful control along both axes. This is a strong identification by structural evidence, though weights alone do not uniquely establish every game rule.

## Game

**Breakout — a small grid-based brick-breaker, similar to Atari Breakout or Arkanoid.**

## Description

The agent moves a paddle left and right along the bottom to intercept and bounce a moving ball. The ball hits and removes bricks near the top for reward, while the agent tries to prevent it from passing the paddle.

## Confidence

**96%**