import sys, json; sys.path.insert(0, '.')
import search_pacman as S
for kw in json.loads(sys.argv[1]):
    s = S.summarize(S.stats(kw, "sample", 32, 400, 1), 0, 0); r = S.summarize(S.stats(kw, "random", 64, 150, 2), 0, 0)
    print("S pel %.1f len %.1f die %.2f clr %.2f | R pel %.2f len %.1f die %.2f | implied %s | %s" % (*s, *r[:3], S.implied(kw, 32, 300), kw), flush=True)
