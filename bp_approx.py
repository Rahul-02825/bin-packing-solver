import sys


def validate(C, w):
    if C <= 0 or any(x <= 0 or x > C for x in w):
        raise ValueError("invalid instance")


def ffd(C, w):
    validate(C, w)
    bins, rem = [], []
    for x in sorted(w, reverse=True):
        for j in range(len(rem)):
            if rem[j] >= x:
                rem[j] -= x
                bins[j].append(x)
                break
        else:
            bins.append([x])
            rem.append(C - x)
    return bins


def read_instance():
    data = sys.stdin.read().split()
    if not data:
        return 1, []
    try:
        n, C = int(data[0]), int(data[1])
        w = [int(x) for x in data[2:]]
        if n < 0 or len(w) != n:
            raise ValueError
        validate(C, w)
    except (ValueError, IndexError):
        print("invalid input", file=sys.stderr)
        sys.exit(1)
    return C, w


def parse_args(argv):
    return "--show" in argv, [a for a in argv if a != "--show"]


def report(label, bins, C, show):
    print(label, len(bins))
    if show:
        for i, b in enumerate(bins, 1):
            print(f"bin {i}: {' '.join(map(str, b))} ({sum(b)}/{C})")


def main():
    show, _ = parse_args(sys.argv[1:])
    C, w = read_instance()
    report("APPROXIMATE", ffd(C, w), C, show)


if __name__ == "__main__":
    main()
