import sys
import time
from collections import Counter

from bp_approx import ffd, parse_args, read_instance, report, validate
from bp_exact import l2

MAX_ARCS = 500000
MAX_CAPACITY = 100000


def reachable_loads(C, demand):
    mask = (1 << (C + 1)) - 1
    bits = 1
    for size, count in demand.items():
        for _ in range(count):
            bits |= (bits << size) & mask
    return [load for load in range(C + 1) if bits >> load & 1]


def item_arcs(C, demand, loads):
    reachable = set(loads)
    arcs = []
    for size in sorted(demand, reverse=True):
        for load in loads:
            if load + size > C:
                break
            if load + size in reachable:
                arcs.append((load, load + size, size))
        if len(arcs) > MAX_ARCS:
            return None
    return arcs


def hint_flows(packing, arcs, nodes, C):
    index = {arc: i for i, arc in enumerate(arcs)}
    next_node = dict(zip(nodes, nodes[1:]))
    flows = [0] * len(arcs)
    for b in packing:
        load = 0
        for item in sorted(b, reverse=True):
            flows[index[(load, load + item, item)]] += 1
            load += item
        while load != C:
            flows[index[(load, next_node[load], 0)]] += 1
            load = next_node[load]
    return flows


def rebuild_bins(arcs, flows, bin_count, C):
    left = list(flows)
    leaving = {}
    for i, (start, end, size) in enumerate(arcs):
        leaving.setdefault(start, []).append(i)
    bins = []
    for _ in range(bin_count):
        load = 0
        items = []
        while load != C:
            i = next(i for i in leaving[load] if left[i] > 0)
            left[i] -= 1
            load = arcs[i][1]
            if arcs[i][2]:
                items.append(arcs[i][2])
        bins.append(items)
    return [b for b in bins if b]


def solve(C, w, limit=600.0):
    began = time.monotonic()
    validate(C, w)
    if not w:
        return [], "OPTIMAL"

    start, lb = ffd(C, w), l2(C, w)
    if len(start) <= lb:
        return start,"OPTIMAL"

    too_large = (start, "SKIPPED (model too large)")
    if C > MAX_CAPACITY:
        print(f"capacity {C} too large for the arc-flow graph", file=sys.stderr)
        return too_large

    try:
        from ortools.linear_solver import pywraplp
    except ImportError:
        print("ortools is not installed: pip install ortools", file=sys.stderr)
        sys.exit(2)

    demand = Counter(w)
    loads = reachable_loads(C, demand)
    nodes = sorted(set(loads) | {0, C})
    arcs = item_arcs(C, demand, loads)
    if arcs is None:
        print(f"graph too large (over {MAX_ARCS} arcs)", file=sys.stderr)
        return too_large
    arcs += [(a, b, 0) for a, b in zip(nodes, nodes[1:])]

    upper = len(start)
    solver = pywraplp.Solver.CreateSolver("SCIP")
    flow = [solver.IntVar(0, upper, "") for _ in arcs]
    bins_used = solver.IntVar(lb, upper, "bins")

    balance = {node: solver.Constraint(0, 0) for node in nodes}
    cover = {size: solver.Constraint(count, count) for size, count in demand.items()}
    for var, (a, b, size) in zip(flow, arcs):
        balance[a].SetCoefficient(var, -1)
        balance[b].SetCoefficient(var, 1)
        if size:
            cover[size].SetCoefficient(var, 1)
    balance[0].SetCoefficient(bins_used, 1)
    balance[C].SetCoefficient(bins_used, -1)

    solver.Objective().SetCoefficient(bins_used, 1)
    solver.Objective().SetMinimization()
    solver.SetHint(flow + [bins_used], hint_flows(start, arcs, nodes, C) + [upper])

    remaining = limit - (time.monotonic() - began)
    if remaining < 1:
        return start, "NOT PROVEN OPTIMAL"
    solver.SetTimeLimit(int(remaining * 1000))
    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return start, "NOT PROVEN OPTIMAL"
    label = "OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "NOT PROVEN OPTIMAL"

    values = [round(var.solution_value()) for var in flow]
    bins = rebuild_bins(arcs, values, round(bins_used.solution_value()), C)

    if sorted(x for b in bins for x in b) != sorted(w):
        return start, "NOT PROVEN OPTIMAL"
    if len(bins) > len(start):
        return start, "NOT PROVEN OPTIMAL"
    return bins, label


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
