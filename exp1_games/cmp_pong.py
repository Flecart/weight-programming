import sys, json; sys.path.insert(0,'.')
from common import *; import pong
net=Net('pong'); ref=reference('pong')
print('ref', {k:(round(v,3) if isinstance(v,float) else v) for k,v in ref.items()})
for line in sys.stdin:
    kw=json.loads(line)
    rep=full_report(lambda rng: pong.Env(rng,**kw), net, n_envs=64, n_steps=500)
    print({k:(round(v,3) if isinstance(v,float) else v) for k,v in rep.items()}, kw, flush=True)
