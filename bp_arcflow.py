import sys
import time
from collections import Counter

from bp_approx import ffd, parse_args, read_instance, report, validate
from bp_exact import l2

MAX_ARCS = 500000
MAX_CAPACITY = 100000

def solve(C, w, limit=600.0):
    began = time.monotonic()
    validate(C, w)
    if not w:
        return [], "OPTIMAL"
    start, lb = ffd(C, w), l2(C, w)
    if len(start) <= lb:
        return start, "OPTIMAL"
    skipped = (start, "SKIPPED (model too large)")
    if C > MAX_CAPACITY:
        print(f"capacity {C} too large for the arc-flow graph", file=sys.stderr)
        return skipped
    try:
        from ortools.linear_solver import pywraplp
    except ImportError:
        print("ortools is not installed: pip install ortools", file=sys.stderr)
        sys.exit(2)
    demand = Counter(w)
    mask, reach = (1 << (C + 1)) - 1, 1
    for size, count in demand.items():
        for _ in range(count):
            reach |= (reach << size) & mask
    loads = [u for u in range(C + 1) if reach >> u & 1]
    reachable = set(loads)
    nodes = sorted(reachable | {0, C})
    arcs = []
    for size in sorted(demand, reverse=True):
        for u in loads:
            if u + size > C:
                break
            if u + size in reachable:
                arcs.append((u, u + size, size))
        if len(arcs) > MAX_ARCS:
            print(f"graph too large ({len(arcs)}+ arcs)", file=sys.stderr)
            return skipped
    arcs += [(a, b, 0) for a, b in zip(nodes, nodes[1:])]
    ub = len(start)
    solver = pywraplp.Solver.CreateSolver("SCIP")
    flow = [solver.IntVar(0, ub, "") for _ in arcs]
    z = solver.IntVar(lb, ub, "z")
    balance = {u: solver.Constraint(0, 0) for u in nodes}
    cover = {s: solver.Constraint(d, d) for s, d in demand.items()}
    for var, (u, v, s) in zip(flow, arcs):
        balance[u].SetCoefficient(var, -1)
        balance[v].SetCoefficient(var, 1)
        if s:
            cover[s].SetCoefficient(var, 1)
    balance[0].SetCoefficient(z, 1)
    balance[C].SetCoefficient(z, -1)
    solver.Objective().SetCoefficient(z, 1)
    solver.Objective().SetMinimization()
    where = {arc: i for i, arc in enumerate(arcs)}
    nxt = dict(zip(nodes, nodes[1:]))
    hint = [0] * len(arcs)
    for b in start:
        u = 0
        for x in sorted(b, reverse=True):
            hint[where[(u, u + x, x)]] += 1
            u += x
        while u != C:
            hint[where[(u, nxt[u], 0)]] += 1
            u = nxt[u]
    solver.SetHint(flow + [z], hint + [ub])
    remaining = limit - (time.monotonic() - began)
    if remaining < 1:
        return start, "NOT PROVEN OPTIMAL"
    solver.SetTimeLimit(int(remaining * 1000))
    status = solver.Solve()
    proven = "OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "NOT PROVEN OPTIMAL"
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return start, "NOT PROVEN OPTIMAL"
    left = [round(v.solution_value()) for v in flow]
    leaving = {}
    for i, (u, v, s) in enumerate(arcs):
        leaving.setdefault(u, []).append(i)
    bins = []
    for _ in range(round(z.solution_value())):
        u, b = 0, []
        while u != C:
            i = next(i for i in leaving[u] if left[i] > 0)
            left[i] -= 1
            u = arcs[i][1]
            if arcs[i][2]:
                b.append(arcs[i][2])
        bins.append(b)
    bins = [b for b in bins if b]
    if sorted(x for b in bins for x in b) != sorted(w):
        return start, "NOT PROVEN OPTIMAL"
    return (bins, proven) if len(bins) <= len(start) else (start, "NOT PROVEN OPTIMAL")


def main():
    show, nums = parse_args(sys.argv[1:])
    try:
        limit = float(nums[0]) if nums else 600.0
    except ValueError:
        print("invalid time limit", file=sys.stderr)
        sys.exit(1)
    C, w = read_instance()
    bins, status = solve(C, w, limit)
    report(status, bins, C, show)


if __name__ == "__main__":
    main()
