"""Ceiling for MinAtar Breakout under the paper's protocol (sticky 0.1, 10,000-step cap): the score of episodes in which
the simulate-the-source player never loses the ball, i.e. reaches the step cap. Also the bricks-per-step rate.
Usage: python -I max_score.py [episodes]"""
import sys, numpy as np
from multiprocessing import Pool
sys.path.insert(0, ".")
from scripted_breakout import episode
if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    with Pool(16) as p:
        res = np.array(p.map(episode, [("simulate_landing", 10_000 + s) for s in range(n)]))
    cap = res[res[:, 1] >= 10000]
    print(f"episodes {n}, mean score {res[:,0].mean():.1f}, capped {len(cap)} ({len(cap)/n:.0%})")
    print(f"score when the ball is never lost (capped episodes): mean {cap[:,0].mean():.1f}, sd {cap[:,0].std():.1f}, min {cap[:,0].min():.0f}, max {cap[:,0].max():.0f}")
    print(f"bricks per step over all episodes: {res[:,0].sum()/res[:,1].sum():.4f}")
