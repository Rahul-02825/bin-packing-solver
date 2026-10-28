import sys


def solve(C, w):
    if C <= 0 or any(x <= 0 or x > C for x in w):
        raise ValueError("invalid instance")
    if not w:
        return 0
    w = sorted(w, reverse=True)
    n, S, minw = len(w), sum(w), w[-1]
    ffd = []
    for x in w:
        for j in range(len(ffd)):
            if ffd[j] >= x:
                ffd[j] -= x
                break
        else:
            ffd.append(C - x)

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
                if dfs(i + 1, nd):
                    return True
                r[j] += w[i]
            return False

        return dfs(0, 0)

    for k in range(-(-S // C), len(ffd)):
        if feasible(k):
            return k
    return len(ffd)


def main():
    data = sys.stdin.read().split()
    if not data:
        print(0)
        return
    try:
        n, C = int(data[0]), int(data[1])
        w = [int(x) for x in data[2:]]
        if n < 0 or len(w) != n:
            raise ValueError
        print(solve(C, w))
    except (ValueError, IndexError):
        print("invalid input", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    main()
