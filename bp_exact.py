import sys
from bisect import bisect_left, bisect_right

from bp_approx import ffd, parse_args, read_instance, report, validate


def l2(C, w):
    ws = sorted(w)
    P = [0]
    for x in ws:
        P.append(P[-1] + x)
    h = C // 2
    mid = bisect_right(ws, h)
    best = 0
    for alpha in {0} | {x for x in ws if x <= h}:
        hi = bisect_right(ws, C - alpha)
        n2, s2 = hi - mid, P[hi] - P[mid]
        s3 = P[mid] - P[bisect_left(ws, alpha)]
        extra = max(0, -(-(s3 - (n2 * C - s2)) // C))
        best = max(best, len(ws) - hi + n2 + extra)
    return best


def solve(C, w):
    validate(C, w)
    if not w:
        return []
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(w) + 100))
    w = sorted(w, reverse=True)
    n, S, minw = len(w), sum(w), w[-1]
    best = ffd(C, w)
    a = [0] * n

    def feasible(k):
        r = [C] * k
        slack = k * C - S

        def dfs(i, dead):
            if i == n:
                return True
            seen = set()
            for j in range(k):
                if r[j] < w[i] or r[j] in seen:
                    continue
                seen.add(r[j])
                nr = r[j] - w[i]
                nd = dead + (nr if nr < minw else 0)
                if nd > slack:
                    continue
                r[j] = nr
                a[i] = j
                if dfs(i + 1, nd):
                    return True
                r[j] += w[i]
            return False

        return dfs(0, 0)

    for k in range(l2(C, w), len(best)):
        if feasible(k):
            bins = [[] for _ in range(k)]
            for i in range(n):
                bins[a[i]].append(w[i])
            return [b for b in bins if b]
    return best


def main():
    show, _ = parse_args(sys.argv[1:])
    C, w = read_instance()
    report("OPTIMAL", solve(C, w), C, show)


if __name__ == "__main__":
    main()
