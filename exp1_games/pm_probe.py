import sys; sys.path.insert(0, '.')
import numpy as np
from common import *
import pacman
net = Net('pacman')
def obs(pac, ghosts, prevpac=None, prevg=(), pellets=None):
    o = np.zeros((10,10,5), np.float32)
    o[pac[0],pac[1],0]=1
    for g in ghosts: o[g[0],g[1],1]=1
    P = np.zeros((10,10),bool)
    if pellets is None:
        for p in pacman.OPEN: P[p]=True
        P[pac]=False
    else: P=pellets
    o[...,2]=P; o[...,3]=pacman.WALLS
    if prevpac: o[prevpac[0],prevpac[1],4]=1
    for g in prevg: o[g[0],g[1],4]=1
    return o.reshape(-1)
def pr(o):
    z=net.logits(o[None])[0]; p=np.exp(z-z.max()); return p/p.sum()
names='0^v<>'
# ghost at distance k in direction of each free neighbor, approaching or receding
stats={}
for pac in pacman.OPEN:
    for di,(dr,dc) in enumerate(pacman.DIRS):
        for k in (1,2):
            g=(pac[0]+dr*k,pac[1]+dc*k)
            if not all(not pacman.WALLS[pac[0]+dr*j,pac[1]+dc*j] for j in range(1,k+1)): continue
            for mode,pg in (('approach',(g[0]+dr,g[1]+dc)),('recede',(g[0]-dr,g[1]-dc)),('none',None)):
                prevg=() if pg is None or pacman.WALLS[pg] else (pg,)
                if mode!='none' and not prevg: continue
                p=pr(obs(pac,[g],prevg=prevg))
                stats.setdefault((k,mode),[]).append(p[di+1])
for k,v in sorted(stats.items()): print(k, 'P(move toward ghost) mean %.3f n %d'%(np.mean(v),len(v)))
# baseline without ghost: prob of each direction
print('policy map, no ghosts, full pellets:')
for r in range(1,9):
    row=''
    for c in range(1,9):
        if pacman.WALLS[r,c]: row+='  #   '; continue
        p=pr(obs((r,c),[])); a=int(p.argmax()); row+=f' {names[a]}{p.max():.2f}'
    print(row)
print('policy map, no ghosts, no pellets:')
for r in range(1,9):
    row=''
    for c in range(1,9):
        if pacman.WALLS[r,c]: row+='  #   '; continue
        p=pr(obs((r,c),[],pellets=np.zeros((10,10),bool))); a=int(p.argmax()); row+=f' {names[a]}{p.max():.2f}'
    print(row)
o=obs((1,1),[]); print('V full pellets at (1,1)', net.value(o[None]))
for pac in [(1,1),(8,8),(4,1),(1,4),(6,4),(8,4)]:
    print(pac,'V full', net.value(obs(pac,[])[None])[0], 'V empty', net.value(obs(pac,[],pellets=np.zeros((10,10),bool))[None])[0])
