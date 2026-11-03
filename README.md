# Weight Programming

Replication and stress tests of *Sparks of Weight Space Programming: LLMs can understand and write neural
network weights* ([post](https://rikiyat.github.io/blog/weight-space-programming/),
[logs](https://github.com/RikiyaT/lm_understand-logs)), and a companion blog post.

To rerun anything that reads the paper's networks, clone its log repo into `repo/`:

```
git clone https://github.com/RikiyaT/lm_understand-logs repo
```

| Folder | What it holds |
|---|---|
| `blog/` | The companion post (`companion_post.md`) and its figures (`image/blog/`) |
| `minatar/` | Experiment 5 validation: Astra's hand-written networks on official MinAtar 1.0.15, with episodes |
| `exp1_games/` | Rebuilt Experiment 1 games (Breakout, Freeway validated; Pong, Pac-Man approximate), checked with the released critic |
| `exp4_kinetix/` | Experiment 4 validation in the real Kinetix environment, with episodes |
| `astra_eval/` | Which-game harness for gpt-6-astra: rescaling, graded obfuscation, and rule-defined permutations (Kt sweep) |
| `opus_write/` | Experiment 5 repeated with Claude Opus 5.5, with a verified edits applier |
| `faith_fate_probe/` | Faith and Fate tasks (multiplication, DP) pushed to Astra's breaking point |
| `critique/` | Scripted Breakout players and the score ceiling |
| `prefix_probe/` | Prefix-completion memorisation test of the released weights |
| `breakout_recon/` | First attempts at reconstructing the Experiment 1 Breakout |
| `novel_games/` | Designs for three unseen games (training was stopped) |
| `site/` | Scripts for the replay page, the obfuscation GIF and the operations-vs-tokens chart |

API keys are read from local `.env` files at run time and are not part of this repository.
