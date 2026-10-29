# Bin packing

The problem statement is **bin packing**: pack a set of items into as few fixed-size bins as possible. Bin packing has many variants (1D, 2D, 3D, with extra constraints). I chose to solve the **one-dimensional** variant, where each item has a single size, its weight.

In that variant you have `n` items with integer weights and an unlimited supply of identical bins of capacity `C`. Every item goes into exactly one bin, no bin may be overfilled, and the goal is to use as few bins as possible. Think of loading boxes into identical vans and hiring as few vans as you can.  I did not attempt the 2D or 3D variants.

This project implements four solvers for 1D bin packing, from a fast approximation to provably exact methods, so you can compare them. The techniques come from the bin packing literature (see [Where the ideas come from](#where-the-ideas-come-from)); the code and the way the pieces are combined are my own.

## The four programs

| Program | Idea | Can you trust the number? | Best for |
|---|---|---|---|
| `bp_exact.py` | Branch-and-bound that tries bin counts upward from a lower bound | Always the proven minimum, if it finishes | Small inputs (roughly up to 40-50 items) |
| `bp_approx.py` | First Fit Decreasing (FFD) | A valid packing, **not always the best** | Very large inputs, instant answers |
| `bp_hybrid.py` | Best of FFD and MBS′, local search, then time-limited branch-and-bound | `OPTIMAL` only when proven, otherwise `NOT PROVEN OPTIMAL` | Mid-to-large inputs with a time budget |
| `bp_arcflow.py` | Arc-flow model solved by Google OR-Tools (SCIP) | `OPTIMAL` only when the solver proves it | Hard instances where `bp_exact.py` is too slow |

`bp.py` is the default entry point. It runs the exact solver and prints only the bin count. `bp_arcflow.py` is the only program that needs a third-party package; the others use the standard library only.

## Why one solution is not enough

Bin packing is NP-hard in the strong sense, so no known algorithm is both guaranteed optimal and fast on every input. Each approach gives something up, which is why this project ships several and does not pick one:

- **Exact search (`bp_exact.py`)** gives the proven minimum but its running time can grow exponentially. On  62-item `planted_20` case it produced no answer in 120 s.
- **FFD (`bp_approx.py`)** is almost instant (about 0.06 s for 5000 items) and always valid, but it can use more bins than necessary. On small cases it matched the optimum on 16 of 27.
- **The hybrid (`bp_hybrid.py`)** spends a time budget to improve on FFD and proves optimality only when it can. On a 5000-item benchmark it went from 1527 bins (FFD) to 1505, with a lower bound of 1499, so the optimum is still unknown.
- **Arc-flow (`bp_arcflow.py`)** can be far stronger on structured instances (`planted_20` solved in 0.2 s), and planted_40 got solved in around 400 s.

Which one to use depends on the use case:

| Situation | Reasonable choice |
|---|---|
| Few items and you need a certified minimum | `bp_exact.py` |
| Huge input, or a real-time answer, and a few extra bins are acceptable | `bp_approx.py` |
| Medium or large input, a time budget, and you want the best answer found plus an honest label | `bp_hybrid.py` |
| Hard instance where you can install OR-Tools and wait minutes | `bp_arcflow.py` |

The `OPTIMAL` and `NOT PROVEN OPTIMAL` labels exist for this reason: when a problem is this hard, the solver should say whether its answer is proven.

## Input and output

Every program reads `n C w1 w2 ... wn`, whitespace-separated, until the end of input. Empty input means zero items.

Output is `<status> <bins>`, where the status is `OPTIMAL`, `APPROXIMATE` (FFD), `NOT PROVEN OPTIMAL`, or `SKIPPED (model too large)` (arc-flow only). `bp.py` prints just the number. Add `--show` to also print the packing, one line per bin. Invalid input (an item larger than `C`, a non-positive weight or capacity, a wrong item count) prints `invalid input` to stderr and exits with code 1.

## Quick start

```bash
echo "5 10 1 2 3 4 5" | python3 bp.py              # 2
echo "5 10 1 2 3 4 5" | python3 bp_exact.py        # OPTIMAL 2
echo "5 10 1 2 3 4 5" | python3 bp_approx.py       # APPROXIMATE 2
echo "5 10 1 2 3 4 5" | python3 bp_hybrid.py       # OPTIMAL 2
echo "5 10 1 2 3 4 5" | python3 bp_hybrid.py 2     # same, with a 2 second search budget (default 10)
echo "5 10 1 2 3 4 5" | python3 bp_hybrid.py --show
```

For the arc-flow solver, create a virtual environment first (Homebrew Python blocks system-wide installs):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install ortools
echo "9 20 9 6 19 8 6 17 5 4 17" | .venv/bin/python bp_arcflow.py     # optional argument: time limit in seconds (default 600)
```

Greedy is not enough. On capacity 20 with weights `9 6 19 8 6 17 5 4 17`:

```bash
echo "9 20 9 6 19 8 6 17 5 4 17" | python3 bp_approx.py     # APPROXIMATE 6
echo "9 20 9 6 19 8 6 17 5 4 17" | python3 bp_exact.py      # OPTIMAL 5
echo "9 20 9 6 19 8 6 17 5 4 17" | python3 bp_hybrid.py 0   # NOT PROVEN OPTIMAL 6 (no time to search)
```

## Where the ideas come from

The main building blocks are published techniques. The table says which source each one comes from and how much of that source was actually read. A number of the papers were not available in full text, and this is marked.

| Technique | Source |
|---|---|
| **Branch-and-bound** that sorts items in descending order and places each item into an open bin or a new bin, using depth-first search (the structure of `bp_exact.py`) | Martello and Toth's MTP algorithm, as described in [Delorme's PhD thesis](https://amsdottorato.unibo.it/id/eprint/7828/1/Mathematical%20Models%20and%20Decomposition%20Algorithms%20for%20Cutting%20and%20Packing%20Problems.pdf), Section 2.5.1. The thesis notes that the results of Chapter 2 appear in the survey by Delorme, Iori and Martello, [EJOR 255(1), 2016](https://doi.org/10.1016/j.ejor.2016.04.030). |
| **L2 lower bound** | Martello and Toth, *Discrete Applied Mathematics*, 1990. |
| **First Fit Decreasing (FFD)** and its guarantee of at most \(11/9 \cdot OPT + 6/9\) bins | Dósa, "The Tight Bound of First Fit Decreasing Bin-Packing Algorithm," ESCAPE 2007, LNCS 4614, pp. 1–11. |
| **MBS′** (fills one bin at a time, starting with the largest remaining item and selecting the remaining items to minimize unused capacity) | Gupta and Ho, *Production Planning & Control* 10, 1999 (MBS); Fleszar and Hindi, *Computers & Operations Research* 29(7), 2002 (MBS′). |
| **Local search improvements** (emptying a bin and redistributing its items, and swapping items to improve bin utilization) | Alvim, Ribeiro, Glover and Aloise, *Journal of Heuristics* 10(2), 2004; Falkenauer's grouping genetic algorithm. Also discussed in Levine and Ducatelle, *JORS* 55(7), 2004, Section 4.6. |
| **Arc-flow formulation** (nodes represent bin loads, and arcs represent items) | For example, [Brandão and Pedroso, arXiv:1310.6887](https://arxiv.org/pdf/1310.6887). my implementation uses the basic formulation without the paper's graph compression. |


**What is done**

- The code, the input and output format, the labelling rules, and the way the pieces are combined into the hybrid.
- The dead-space pruning and the skipping of bins with identical remaining space in the search. These are standard ideas but were written here, not taken from a paper we read.
- The move-and-swap local search. It follows the idea described by Levine and Ducatelle but is a different, simpler procedure.
- Parameters and limits: the cap of 1000 search steps per bin in MBS′, the size limits of the arc-flow model, and the time budgets.
- The "planted" test instances and the test runner.

## How the hybrid works

1. Build two quick packings, FFD and MBS′, and keep the one with fewer bins (FFD wins ties).
2. Improve it: repeatedly try to empty the least-full bin by moving its items into other bins, or swapping them for smaller ones.
3. Compute the L2 lower bound, the fewest bins any packing could possibly use.
4. If the packing already uses that many bins, it is proven optimal. Stop with `OPTIMAL`.
5. Otherwise, within the time budget, search for a packing with one bin fewer. If one is found it becomes the new best and the search repeats. If the search shows none exists, the current packing is optimal (`OPTIMAL`). If time runs out, it returns the best packing so far as `NOT PROVEN OPTIMAL`.

A timed-out answer is never presented as optimal. The true minimum is somewhere between the lower bound and the number printed.

## Test cases

Test cases are plain text, one per line: `name | expected | n C weights`. `expected` is the known optimum or `invalid`.

- **`testcases.txt`** has 27 cases: small named cases (empty input, an item equal to the capacity, repeated weights, a case where FFD loses), six small cases where FFD uses one bin too many (optimum checked by brute force), four medium cases, and five invalid inputs.
- **`testcases_large.txt`** has two "planted" cases. Each is built by filling `k` bins exactly to capacity, cutting every bin into pieces, and shuffling all the pieces together. The total weight is exactly `k` times the capacity, so the optimum is known to be exactly `k`. `planted_20` has 62 items with capacity 100, and `planted_40` has 120 items with capacity 1000. Larger planted cases (100 and 300 bins) were dropped because none of the solvers here could prove an answer on them.

Run them with the runner, which tests each program on each case and saves a results table:

```bash
python3 run_cases.py                                    # testcases.txt
python3 make_large.py                                   # regenerates testcases_large.txt (fixed seeds)
python3 run_cases.py testcases_large.txt
.venv/bin/python run_cases.py testcases_large.txt       # adds the arcflow column
.venv/bin/python run_cases.py testcases_large.txt --only arcflow
```

Options: `--only exact,approx,hybrid,arcflow`, `--timeout` (seconds per program per case, default 600, `0` for no limit), `--budget` (hybrid search time, default 5) and `--arcflow-limit` (default 600). Each run saves `results/results_<date>_<time>.txt` with the settings at the top. A program passes a case when its bin count equals the expected optimum, so failing some cases is expected for FFD. The exact solvers should pass every case they finish within the time limit.

There is no unit-test suite; correctness is checked with these case files.

## Results (measured)


### Small cases (`testcases.txt`, 27 cases)

| Program | Passed | Note |
|---|---|---|
| `bp_exact.py` | 27 / 27 | proven optimal on all |
| `bp_hybrid.py` | 27 / 27 | 5 s budget |
| `bp_approx.py` | 16 / 27 | all 11 misses were exactly 1 bin over the optimum |

`bp_arcflow.py` was not in that run. It was checked separately against the exact solver on 150 random small instances and a few of the cases above, with no differences.

### Large cases (`testcases_large.txt`, optimum known by construction)

| Case | Program | Output | Time |
|---|---|---|---|
| `planted_20` (optimum 20) | `bp_exact.py` | no result, stopped at 120 s | 120 s |
| | `bp_hybrid.py 5` | NOT PROVEN OPTIMAL 21 | 5.0 s |
| | `bp_arcflow.py` | **OPTIMAL 20** | 0.2 s |
| `planted_40` (optimum 40) | `bp_arcflow.py` | **OPTIMAL 40** | 406 s |

On `planted_40`, arc-flow with a 60 s limit stopped at 41 (not proven). With the 600 s limit it reached 40 and proved it, in 406 s. The exact solver and the hybrid were not run on `planted_40`.


## Limits

- The exact solver is exponential in the worst case. On hard inputs, such as the planted cases, it may not finish for a very long time.
- `NOT PROVEN OPTIMAL` means exactly that: the packing is valid and probably good, but nobody has shown it cannot be beaten.
- The arc-flow program is a basic version. If the graph would need more than 500,000 arcs, or the capacity is above 100,000, it skips the solver and returns the FFD packing labelled `SKIPPED (model too large)`.
- The 1000-step cap per bin in MBS′ and the other limits above are my own choices, not values from the papers.
