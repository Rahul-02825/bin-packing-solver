import argparse
import importlib.util
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))


def load(path):
    cases = []
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#"):
            name, expected, data = [p.strip() for p in line.split("|", 2)]
            cases.append((name, expected, data))
    return cases


def lower_bound(data):
    try:
        t = data.split()
        n, C = int(t[0]), int(t[1])
        return -(-sum(int(x) for x in t[2:2 + n]) // C)
    except (ValueError, IndexError, ZeroDivisionError):
        return None


def run_one(script, args, data, timeout):
    start = time.monotonic()
    try:
        p = subprocess.run([sys.executable, os.path.join(ROOT, script), *args], input=data,
                           capture_output=True, text=True, timeout=timeout or None)
    except subprocess.TimeoutExpired:
        return {"state": "TIMEOUT", "secs": timeout}
    secs = time.monotonic() - start
    out = p.stdout.split()
    if p.returncode != 0 or not out:
        return {"state": "REJECTED" if p.returncode == 1 and not out else "ERROR", "secs": secs}
    try:
        return {"state": "OK", "bins": int(out[-1]), "label": " ".join(out[:-1]), "secs": secs}
    except ValueError:
        return {"state": "ERROR", "secs": secs}


def judge(expected, r, lb):
    if expected == "invalid":
        if r["state"] == "REJECTED":
            return "REJECTED PASS", True
        return (f"ACCEPTED {r['bins']} FAIL" if r["state"] == "OK" else f"{r['state']} FAIL"), False
    if r["state"] != "OK":
        return r["state"], None if expected == "unknown" else False
    if r["label"].startswith("SKIPPED"):
        return f"{r['label']}, FFD gave {r['bins']}", None
    tag = {"OPTIMAL": "", "APPROXIMATE": "", "NOT PROVEN OPTIMAL": " [NOT PROVEN]"}.get(r["label"], "")
    if expected == "unknown":
        return f"{r['bins']} (LB {lb}){tag} {r['secs']:.2f}s", None
    gap = r["bins"] - int(expected)
    verdict = "PASS" if gap == 0 else f"FAIL ({gap:+d})"
    return f"{r['bins']} {verdict}{tag} {r['secs']:.2f}s", gap == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="?", default=os.path.join(ROOT, "testcases.txt"))
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--budget", type=float, default=5.0)
    ap.add_argument("--arcflow-limit", type=float, default=600.0)
    ap.add_argument("--only", default="", help="comma-separated programs to run: exact,approx,hybrid,arcflow")
    a = ap.parse_args()
    programs = [("exact", "bp_exact.py", []), ("approx", "bp_approx.py", []),
                ("hybrid", "bp_hybrid.py", [str(a.budget)])]
    if importlib.util.find_spec("ortools"):
        programs.append(("arcflow", "bp_arcflow.py", [str(a.arcflow_limit)]))
    if a.only:
        programs = [p for p in programs if p[0] in a.only.split(",")]
    rows, score = [], {p[0]: [0, 0] for p in programs}
    for name, expected, data in load(a.cases):
        lb = lower_bound(data)
        row = [name, expected]
        for pname, script, args in programs:
            cap = a.timeout and (max(a.timeout, a.arcflow_limit + 120) if pname == "arcflow" else a.timeout)
            cell, ok = judge(expected, run_one(script, args, data, cap), lb)
            if ok is not None:
                score[pname][1] += 1
                score[pname][0] += ok
            row.append(cell)
        rows.append(row)
        print(f"done: {name}", file=sys.stderr)
    head = ["case", "expected"] + [p[0] for p in programs]
    widths = [max(len(str(r[i])) for r in rows + [head]) for i in range(len(head))]
    fmt = lambda r: "  ".join(str(c).ljust(w) for c, w in zip(r, widths)).rstrip()
    text = [f"run: {datetime.now():%Y-%m-%d %H:%M:%S}   cases: {os.path.basename(a.cases)}   "
            f"timeout: {'none' if not a.timeout else format(a.timeout, 'g') + 's'}   hybrid budget: {a.budget:g}s   arcflow limit: {a.arcflow_limit:g}s   python: {sys.version.split()[0]}", "",
            fmt(head), fmt(["-" * w for w in widths])] + [fmt(r) for r in rows] + ["", "Summary (passed / judged):"]
    text += [f"  {k}: {v[0]}/{v[1]}" for k, v in score.items()]
    text += ["", "PASS = bin count equals the expected optimum. FAIL (+n) = n bins above it.",
             "approx is a heuristic, so a FAIL there is expected. exact should never FAIL unless it times out."]
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    path = os.path.join(ROOT, "results", f"results_{datetime.now():%Y%m%d_%H%M%S}.txt")
    with open(path, "w") as f:
        f.write("\n".join(text) + "\n")
    print("\n".join(text))
    print(f"\nsaved to {path}")


if __name__ == "__main__":
    main()
