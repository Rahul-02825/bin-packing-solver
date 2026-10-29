import sys
import time
from bisect import bisect_left

from bp_approx import ffd, parse_args, read_instance, report, validate
from bp_exact import l2


def empty_bin(C, bins, t, deadline):
    loads = [sum(b) for b in bins]
    while bins[t]:
        if time.monotonic() >= deadline:
            return False
        for x in sorted(bins[t], reverse=True):
            fits = [j for j in range(len(bins)) if j != t and C - loads[j] >= x]
            if fits:
                j = min(fits, key=lambda j: (C - loads[j], j))
                bins[t].remove(x)
                bins[j].append(x)
                loads[t] -= x
                loads[j] += x
                break
        else:
            swap = None
            for x in sorted(set(bins[t]), reverse=True):
                for j in range(len(bins)):
                    for y in bins[j] if j != t else ():
                        if y < x and C - loads[j] + y >= x:
                            if swap is None or (y, -x, j) < swap[:3]:
                                swap = (y, -x, j)
            if swap is None:
                return False
            y, x, j = swap[0], -swap[1], swap[2]
            bins[t].remove(x)
            bins[t].append(y)
            bins[j].remove(y)
            bins[j].append(x)
            loads[t] += y - x
            loads[j] += x - y
    return True


def improve(C, bins, deadline):
    bins = [list(b) for b in bins]
    progress = True
    while progress and time.monotonic() < deadline:
        progress = False
        for t in sorted(range(len(bins)), key=lambda j: (sum(bins[j]), j)):
            if empty_bin(C, bins, t, deadline):
                del bins[t]
                progress = True
                break
    return [b for b in bins if b]


def mbs_prime(C, w, deadline, cap=1000):
    rest = sorted(w, reverse=True)
    bins = []
    while rest:
        if time.monotonic() >=deadline:
            return None
        head = rest.pop(0)
        cand = [x for x in rest if x <= C - head]
        neg = [-x for x in cand]
        best = {"room": C - head, "set": [], "steps": 0}

        def search(i, room, chosen):

            best["steps"] += 1
            if room < best["room"]:
                best["room"], best["set"] = room, list(chosen)
            if room == 0 or best["steps"] >= cap:
                return
            for j in range(bisect_left(neg, -room, i), len(cand)):

                if j >i and cand[j] == cand[j - 1]:
                    continue
                chosen.append(j)
                search(j +1, room - cand[j], chosen)
                chosen.pop()
                if best["room"] == 0 or best["steps"] >= cap:
                    return

        search(0,C -head, [])
        items = [cand[j] for j in best["set"]]
        for x in items:
            rest.remove(x)
        bins.append([head] + items)
    return bins


def solve(C, w, limit=10.0):
    validate(C, w)
    if not w:
        return [], True
    deadline = time.monotonic() + limit
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(w) + 100))
    w = sorted(w, reverse=True)
    n, S, minw = len(w), sum(w), w[-1]
    base, alt = ffd(C, w), mbs_prime(C, w, deadline)
    start = alt if alt is not None and len(alt) < len(base) else base
    best, lb = improve(C, start, deadline), l2(C, w)
    a = [0] * n

    def feasible(k):
        r = [C] * k
        slack = k * C - S
        nodes = [0]
        def dfs(i, dead):
            nodes[0] += 1
            if nodes[0] % 1024 == 1 and time.monotonic() >= deadline:
                raise TimeoutError
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

    while len(best) > lb:
        try:
            if not feasible(len(best) - 1):
                return best, True
        except TimeoutError:
            return best, False
        bins = [[] for _ in range(len(best) - 1)]
        for i in range(n):
            bins[a[i]].append(w[i])
        best = [b for b in bins if b]
    return best, True


def main():
    show, nums = parse_args(sys.argv[1:])
    try:
        limit = float(nums[0]) if nums else 10.0
    except ValueError:
        print("invalid time limit", file=sys.stderr)
        sys.exit(1)
    C, w = read_instance()
    bins, proven = solve(C, w, limit)
    report("OPTIMAL" if proven else "NOT PROVEN OPTIMAL", bins, C, show)


if __name__ == "__main__":
    main()
