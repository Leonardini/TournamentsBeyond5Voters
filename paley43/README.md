# Paley(43) is not 5-inducible  (`paley43/`)

**What it does.** Proves the paper's Paley(43) theorem, **N(5) ≤ 43**: the Paley tournament
Paley(43) is *not* 5-realizable (it is the Kemeny median of no multiset of five linear orders) —
**end-to-end from a single script**. Proof skeleton: MAS(Paley43) = 543 is barely above 3C/5, so any
5-realization must use two voters at level δ ≤ 1 ⇒ the co-backing lemma forces the five voters'
double-back sets to be pairwise disjoint, so those two δ ≤ 1 orders would have *disjoint* double-back
sets ⇒ `razor_screen` shows exhaustively that **no two level-≤ 1 orders have disjoint double-back
sets** ⇒ contradiction. The full mathematics is in
[`PALEY43_NONREALIZABLE.md`](PALEY43_NONREALIZABLE.md).

**Files.**
- `reproduce_paley43.sh` — the driver; builds the tools and runs the proof in guarded, resumable
  stages 0–4 (self-documenting header: proof skeleton + resource envelope).
- `dp43.c` — the MAS engine (the dynamic program of the paper's MAS appendix): certifies MAS(Paley43) = 543, builds the δ ≤ 2 layer
  tables, and joins/enumerates the level-≤ 1 shell; also carries a `selftest` mode.
  To save memory, `dp43` drops layer records that cannot lie on an order with at least τ forward
  arcs (τ = 541 in the certifying run), so in general a table stores a lower bound on g(S), the
  exact value of the paper's recurrence. **In the certifying run this pruning removed no whole
  Aut-orbit:** every layer L0–L22 reaches its full orbit count, which the code computes by
  Burnside's lemma (the `-> N reps (burn N)` line of each layer in the run log; e.g. L22:
  1,165,060,668 of 1,165,060,668). The pruning test is monotone in the stored value, so whenever a
  set survives, its best record survives too; with every orbit present, each stored value equals
  g(S), and the tables are exactly those of the DP that the paper describes.
- `canon_reps.c` — canonicalizes and dedups the enumerated orders into Aut-orbit representatives,
  and validates completeness against the census orbit count (must equal 1,841,303).
- `razor_screen.c` — the co-backing screen: proves no two δ ≤ 1 orders have disjoint double-back sets.
- `realize5_cpsat.py` — auxiliary OR-Tools CP-SAT 5-inducibility encoder (not on the proof path);
  `--gauntlet` self-checks it against known answers.
- `d0_reps.txt` — the one committed input: the δ = 0 (MAS) orbit representatives (~2.2 MB seed).
- `PALEY43_NONREALIZABLE.md` — the mathematical write-up of the proof.

**Dependencies.** A C compiler (`cc -O3`) for `dp43`, `canon_reps`, `razor_screen`; Python 3 with
Google OR-Tools CP-SAT (`ortools`) for the auxiliary `realize5_cpsat.py` check. Versions and
installation are in the [top-level README](../README.md#building). **None require CPLEX** — the
proof is solver-free, and the auxiliary realize5 check uses free CP-SAT.

**How to run.**

```sh
# full proof, one command (stages 0–4)
./reproduce_paley43.sh

# resume from a stage (optional arg; default 0). E.g. skip the expensive layer build:
./reproduce_paley43.sh 3

# quick sanity check WITHOUT the expensive stages: build dp43, then run the DP self-tests
cc -O3 -march=native -pthread -o dp43 dp43.c
./dp43 selftest 7  /tmp/st7      # q=7  DP pool == brute force
./dp43 selftest 11 /tmp/st11     # q=11 DP pool == brute force

# auxiliary: validate the CP-SAT 5-inducibility encoder against known answers
python3 realize5_cpsat.py --gauntlet
```

**What to expect.**

*On a machine with under ~32 GB of RAM*, run `CHUNKMB=2 ./reproduce_paley43.sh`: the default chunk size puts
~6.4 GB into buffers and peaks near 26 GB at layer 20, while `CHUNKMB=2` completed the same layers at ~9 GB.

- **Full `reproduce_paley43.sh`.** Documented envelope: **≤ 8 threads, ~5 GB peak RAM, ~50 GB scratch
  disk** (layer tables). Stage 2 ("`STAGE 2  q=43 delta<=2 shell layer tables [EXPENSIVE ~hours,
  ~48 GB]`") is the expensive one — approximately hours per the script header. Each layer prints its
  `L%02d: parents ... reps ... Ns` summary on stdout when it completes, and while a layer is still
  running `dp43` prints a heartbeat on stderr every 30 s
  (`L07: 41156608/98304000 parents dispatched (42%), ... 612s`), so a long layer is visibly
  progressing; `PROGRESS=0 ./reproduce_paley43.sh` turns the heartbeat off. Stage 3 runs
  `join(542) → enum(542) → canon_reps` and enforces the **census identity check**: the δ ≤ 1 orbit
  count must equal **1,841,303**, else it dies with "enumeration incomplete". Stage 4 runs the screen
  (a δ = 0 sanity pass that must report `TRUE_DISJOINT=0`, then the real δ ≤ 1 pass), ending in the
  banner:

  ```
  PROVED: no two delta<=1 orders of Paley(43) have disjoint double-back sets.
  By co-backing + fwd-counting, Paley(43) is NOT 5-realizable  =>  N(5) <= 43.
  ```

  (Timings are approximate; only the "~hours / ~5 GB / ~50 GB" envelope is documented in the header.)

- **The `dp43 selftest 7/11` path.** Runs in ~seconds with no large disk footprint. It re-implements
  the canonicalization independently and checks it (fast == slow, idempotent, Aut-invariant), then
  verifies the DP order-pool equals brute force at several τ — printing lines like `selftest: q=7
  tau=… (delta=…) … pool == brute force (… orders) OK` and finishing with `selftest q=7 PASSED` /
  `selftest q=11 PASSED`. This self-check has been run and passes.

- **`realize5_cpsat.py --gauntlet`.** Prints `GAUNTLET (known answers):` and finishes `GAUNTLET: PASS`
  (checks ce1068 k=3 infeasible, ce1068 k=5 feasible, Paley(11) k=5 feasible).
