import sys; sys.path.insert(0, '.')
import numpy as np
exec(open('pm_probe.py').read().split("names='0^v<>'")[0])
names='0^v<>'
# effect of a single ghost anywhere on the action at pac (1,1) and (4,1) with full pellets
for pac in [(1,1),(4,1),(8,4),(3,4)]:
    base=pr(obs(pac,[])); print('pac',pac,'base',names[base.argmax()],np.round(base,2))
    for r in range(1,9):
        row=''
        for c in range(1,9):
            if pacman.WALLS[r,c] or (r,c)==pac: row+=' #' if pacman.WALLS[r,c] else ' P'; continue
            p=pr(obs(pac,[(r,c)],prevg=[(r,c)])); row+=' '+names[p.argmax()]
        print(row)
