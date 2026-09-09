# Research log — dynamic-order placement DFS for k-inducibility

_Copy of the session memory note `kinduce-dynamic-order-dfs.md` (2026-09-01/02),
frontmatter removed. `[[double-bracket]]` names refer to other notes in that
memory store, not to files in this repo. This is a chronological log: later
sections correct earlier ones, so read to the end before acting on anything._


**The idea (Leonid's, 2026-09-01)**: the old incremental BFS/DFS
(`ObsoleteSourceFiles/k_realizability_optimized.R`, `three_realizability_*.R`)
fixed the vertex numbering up front (static `optimal_vertex_ordering`: degree
imbalance desc, triangle count asc). Instead pick the next vertex **at each DFS
node** as the most locally-constrained one -- minimum remaining values /
fail-first -- since "the decision only affects the arcs between this vertex and
the previously named ones". **Leonid's caveat: ordering must be dynamic per
BRANCH, not preprocessing-based.** Motivation: P19 (unrestricted) was cracked
historically by placement-DFS, never by ILP -- see [[margin1-uniform-sat-encodings]].

**Why it's sound**: for a fixed choice of v*, every full profile extending the
node has exactly ONE insertion tuple for v*, so branching over D(v*) partitions
the subtree. Hence ANY rule for choosing v* preserves completeness -- caps,
random tie-breaks and cheap heuristics are all free correctness-wise. Only the
*pruning* rules need proving.

**Model**: state = placed set S + the k voter orders restricted to it. Insert v
at slot p_i in voter i; U_i(p_i) = the suffix after that slot, so v <_i u iff
u in U_i(p_i), and c_v(u) = #{i : u in U_i(p_i)}. Then
  D(v|state) = { p in {0..|S|}^k : c_v(u) = (k+1)/2 on Out(v)&S,
                                   c_v(u) = (k-1)/2 on In(v)&S }.
Counts held bit-sliced over 3 planes (one bit per vertex) so each prune is a
few 64-bit ops over all of S. **Key monotonicity**: within a voter, larger p =
smaller suffix, so counts are non-increasing in p -> a lower-bound violation
can never recover (break), an upper-bound one can (continue).

**Code, all in `KInduceDFS/`** (kinduce3.c is the live one; 1 and 2 kept as
reference points, all three build standalone):
- `kinduce.c`  -- base version, auto-base + capped MRV + imbalance tie-break
- `kinduce2.c` -- adds Leonid's forced-last-voter closed form
- `kinduce3.c` -- adds the agreement bound + `--select cheap`
- `base_enum.c`, `dp_check.c` -- the two INDEPENDENT oracles
- `sweep_p19.sh` -- restart-style witness hunt over base states
Flags: `--paley q | --bits F --n N | --batch F --n N`, `--k`, `--margin
exact|majority`, `--order mrv|static`, `--mrv-cap`, `--select exact|cheap`,
`--no-bound`, `--base-size`, `--bs-from/--bs-to` (base-state slice = free
parallelism), `--nodes`, `--time`, `--count`, `--no-symbreak`.

**INITIALISATION (Leonid's spec): 5-vertex base, exhaustively precomputed.**
All sorted (= lex-ordered, the full S_k voter-symmetry break) k-tuples of the
120 orders on 5 vertices, tabulated by induced labelled tournament. For k=5
exact margin-1: **6,225,000 sorted / 735,103,200 unsorted tuples, all 1024
labelled tournaments hit**; the C(124,5)=225,150,024 sweep prunes to 9.8M nodes
(0.34s). kinduce recomputes this per-mask on the fly (<=1024 masks, cached), so
no table file is needed at run time; `base5_exact.tbl` is kept for validation.
**Most restrictive 5-vertex base = the REGULAR tournament on 5 vertices**
(5 three-cycles, |Aut|=5, 24 labelled copies): 2200 base states vs 13,717 for
the transitive one. Restrictiveness is MONOTONE in 3-cycle count (5->2200,
4->2919/2973/3372, 3->4301/4677, 2->6292, 1->8838, 0->13717) though not
determined by it. cnt_sorted IS an isomorphism invariant (sorted tuples =
multisets, and relabelling acts bijectively on multisets). Copies of the
minimal class: Paley(11) 22, DR15-g1/g2 84, **Paley(19) 342**, DR19-g2 360,
Paley(23) 1012. **Paley(7) has NONE** -- all 21 of its 5-subsets are the 2973
class, so it can't use the best base (and it's margin-1 3-inducible anyway, so
it's a smoke test, not a discriminator: SAT in 3 nodes).

**VALIDATION (the main deliverable -- Leonid: "correctness is the main outcome")**
1. Two independent oracles agree on every number: `base_enum.c` (enumerates
   complete order-tuples) vs `dp_check.c` (DP over the vector of per-pair
   support counts, capped at tHI, 4^10 states -- never enumerates a tuple).
   Identical `cnt_all` on ALL 1024 masks; totals 2220 / 811,680 / 735,103,200
   at nb=3/4/5.
2. kinduce reproduces `cnt_sorted` on all 1024 masks (base_sz=5) and `cnt_all`
   on all 12 iso classes (base_sz=1, `--no-symbreak`), in BOTH arms and at
   every mrv-cap -- the second one tests the insertion machinery against the DP.
3. **n=8 exhaustive, k=3: exactly 96 UNSAT of 6880**, matching
   `Counterexamples/Non3RealizableTournaments8.RData` -- and all 96 of those
   come out UNSAT individually. Holds in EVERY mode (mrv caps 1/5/50, static,
   select cheap, bound on/off, both margins). This is the only test that
   validates the **UNSAT direction**, and it also catches over-pruning.
4. **n=9 exhaustive (191,536 tournaments), k=3, reproduces Leonid's stated fact
   from scratch**: 17,674 unrestricted-infeasible, 17,928 margin-1-infeasible,
   **254 margin-1-only** (unrestricted-FEASIBLE but margin-1-infeasible), and 0
   in the impossible direction. At n=8 the same difference is exactly 0. So the
   margin-1/unrestricted separation first appears at n=9, as Leonid said.
5. Every SAT verdict re-verified from scratch inside the binary (`VERIFY
   bad_arcs=0 support_min=3 support_max=3`), independent of the search.
Known-answer decisions all correct: Paley(7) SAT 3 nodes, Paley(11) SAT 7,
DR15-g1 SAT 96, DR15-g2 SAT 77.

**THE HEADLINE MEASUREMENT** (n=9, k=3 exact margin-1, 191,536 **complete**
searches, identical verdicts in both arms):
  dynamic per-node MRV: **1,454,516** nodes | static order: **4,052,393**
  => **2.79x tree reduction**. Wall time identical (847s vs 846s) ONLY because
  each search is ~8 nodes and the fixed per-instance base setup (~4.4ms)
  dominates at that size; the node saving is what carries to large instances.
At n=8 the same comparison is 30,153 vs 38,516 (1.28x) -- too easy to
discriminate.

**Leonid's three refinements, measured on Paley(19) k=5 exact margin-1:**
(a) **Forced last voter** -- after placing v in k-1 voters, exactness forces the
    last: it must contribute tau(u)-s_u in {0,1}, so its suffix is exactly
    R={u : tau(u)-s_u=1}, one candidate slot p=|S|-|R|, valid iff suf[k-1][p]==R.
    Provably equivalent, replaces the whole innermost loop with a few 64-bit
    ops. **Only +22%** (887k vs 733k nodes/60s) -- because the break-on-
    lower-bound already fired immediately at the last level (r=0 makes the
    lower bound BE the deficit condition). Kept: free and exact.
(b) **Per-voter agreement bound** -- A_i(p) = |Out(v) & U_i(p)| + |In(v) &
    (S\U_i(p))|; counting per-arc agreement two ways gives sum_i A_i(p_i) =
    tHI*|S| exactly, so sum_i max_p A_i(p) < tHI*|S| PROVES D(v) empty (and for
    exact margin, sum_i min_p A_i(p) > tHI*|S| does too). O(k|S|) per vertex.
    **VALID BUT USELESS AS A FILTER HERE: catches 1,684 of ~500,000 failures
    (0.19%)** -- the exact domain check already finds essentially all of them.
    NOTE: the bound must use ALL k voters; the "top 3" variant is NOT a valid
    bound (it would under-count capacity and could prune real solutions), it is
    only a selection heuristic.
(c) **Cheap selection** (`--select cheap`, rank by sum of the top tHI values of
    max_p A_i(p), smallest wins, exact-enumerate only the winner) -- **3.3x
    throughput: 48,676 vs 14,750 nodes/s**, but a worse-guided tree. Net effect
    UNRESOLVED: no terminating instance of intermediate difficulty exists to
    settle it (see below).

**PALEY(19) k=5 EXACT MARGIN-1 IS NOT CRACKED BY THIS.** Base state 0 ALONE did
not finish in 600s (6.94M nodes). 2200 base states => >1.5e10 nodes at ~11.5k
nodes/s => **>17 days single-core, and that's a LOWER bound** (state 0 never
completed). Plain DFS has no clause learning, which is exactly what makes CDCL
effective on hard symmetric UNSAT -- honest read: this route is unlikely to
settle P19 margin-1 by refutation. **Leonid doubts it is UNSAT at all**, so
`sweep_p19.sh` (restart-style: sweep all 2200 base states with a node cap, then
raise the cap 4x and re-sweep) was launched as a WITNESS hunt instead, 3
workers x 6h budget, logs `/tmp/p19_sweep_w{0,1,2}.log`.

**BENCHMARKING TRAP -- random tournaments are worthless here**: all 30 random
tournaments at n=9..13 are margin-1 5-SAT, found in the MINIMUM possible n-4
nodes with ~zero backtracking. Hardness is specific to Paley/regular structure.
And there is a benchmark GAP: DR15 is instant, P19 is hopeless, and no Paley or
doubly-regular tournament exists strictly between 15 and 19 (DRTs need
n = 3 mod 4). That gap is why (c) can't be settled.

**Gotchas hit this session** (cost real time):
- **zsh does NOT word-split unquoted `$var`** -- `./prog $args` passes ONE
  argument. Bit me 3x; use `${=args}` or explicit arguments.
- Greedy regex: `sed 's/.*nodes=([0-9]+).*/\1/'` matches **dom_nodes=**, not
  nodes=. Use ` nodes=` with the leading space.
- Python `print` is buffered in background jobs -> logs look empty; use
  `python3 -u` or a shell loop.
- Rebuild to a NEW binary name while jobs are running; overwriting a running
  binary in place can crash it on macOS.


## 2026-09-01 EVENING -- the benchmark gap CLOSED, and the result is decisive

**n=17 regular tournaments do NOT close the gap**: generated 33 of them
(`gen_regular.py`, rotational seed + m random 3-cycle reversals), ALL 33 are
margin-1 5-SAT and easy. Regularity at n=17 is not what makes Paley(19) hard.

**The dial that works: 3-cycle reversals applied to PALEY(19) ITSELF**
(`gen_mix2.py`, `bench19/p19_mix.batch`, 41 instances, m in 0..2000). Reversing
a DIRECTED triangle a->b->c->a to a->c->b->a preserves every out-degree (each of
a,b,c loses one out-arc and gains one) -- reversing a TRANSITIVE triple would
not (it shifts two degrees by +-2). Verified independently on the written files:
out-degrees stay {9}, tournament property holds, and the 3-cycle count is pinned
at 285 for every one of them (= C(19,3) - 19*C(9,2), an invariant of ANY regular
tournament on 19 vertices -- same 285 as in [[margin1-uniform-sat-encodings]]'s
S_2(sigma)+S_2(reverse)=285 identity). **Double-regularity dies after ONE
reversal** (codegree set {4} -> {3,4,5}), yet hardness PERSISTS at m=1 and m=2
(all 8 aborted at 20s) -- so it is proximity to Paley(19) in reversal distance,
not double-regularity per se, that drives difficulty. Transition: m=3 (3 of 4
solve), m=5 (2 of 4), m>=8 all solve.
=> `bench19/p19_solvable.batch` = the 29 terminating instances (all SAT,
28..210k nodes) = **the intermediate-difficulty benchmark that was missing**.
`bench19/p19_hard.batch` = the 12 undecided ones (m=0 Paley19, m=1 x4, m=2 x4,
m=3 x1, m=5 x2).

**THE HEADLINE (29 instances, 20s search cap each, ONLY the next-vertex rule
differs; all 29 are SAT with independently re-verified witnesses):**
| next-vertex rule                          | solved | nodes      |
|-------------------------------------------|--------|------------|
| exact MRV, argmin |D(v)| (capped count)   | **29/29** |    992,378 |
| hybrid: exact fail-first + cheap ordering  |  22/29 |  2,615,546 |
| cheap only: top-3 agreement score          |  20/29 | 11,403,516 |
| static order                               |   5/29 | 20,665,050 |
**Dynamic ordering solves ALL 29 where the static order solves 5** -- far
bigger than the 2.79x measured at n=9. The hybrid row DECOMPOSES why: exact
fail-first alone buys 11.4M->2.6M nodes, and picking the TRUE argmin buys a
further 2.6M->992k. Both matter; the true argmin matters more. So Leonid's
cheap top-3 rule is real (20/29 vs static's 5/29) but the accurate lookahead
clearly earns its cost -- do NOT replace exact selection with it.

**PERFORMANCE BUG FIXED (38x on batch runs)**: the mask -> base-state-count
cache was rebuilt per instance inside `solve_one`, costing **13.7s per n=19
instance**. It depends only on the ABSTRACT 5-vertex tournament, so it is now
`static` and computed once per process. The 6880-instance n=8 batch went
15.4s -> 0.4s. (Leonid: "just cache the size-5 tournaments with their profiles
and do a quick mapping" -- the lookup is by the labelled 10-bit mask directly,
so no degree-sequence matching or isomorphism test is needed.)

**NEXT LEVER, measured and strongly motivated -- Leonid's incremental-domain
idea.** D(v | S+u) is a REFINEMENT of D(v | S): deleting u from each order maps
D(v|S+u) -> D(v|S) (removing u leaves every c_v(w), w in S, unchanged), and
going back, each p in D(v|S) lifts to p'_i in {p_i, p_i+1} per voter -- TWO
choices exactly when p_i = pos_i(u), one otherwise -- then the single new arc
(v,u) filters by c_v(u) = tau(u). So a child's domains are computable from the
parent's in O(sum_v |D(v|S)| * k) instead of a fresh enumeration.
**`--measure-dsz` on Paley(19) says this should win big**: FULL uncapped
|D(v|S)| has mean 64 at |S|=5, **8.2 at |S|=11 (882k samples, where the search
lives)**, 4.8 at |S|=12, and NEVER exceeded 136. So maintaining full domains
costs ~330 ops/node versus the **7,080 lookahead nodes per DFS node** the fresh
enumeration burns now -- a ~20x cut in the dominant cost. It also resolves
Leonid's own caveat ("maybe not so much if we are using the caps") in the good
direction: with incremental maintenance you DROP the caps and still get exact
full sizes, which is exactly the ingredient measured as most valuable.
**This is the first thing to build next session.**

**Binaries** (each kept so results stay reproducible; kinduce7 is newest):
kinduce=base, 2=+forced-last-voter, 3=+bound/--select cheap, 4=+persistent base
cache & flushed BATCH, 5=+`--per-base-nodes` in-process sweep, 6=+`--select
hybrid`, 7=+`--measure-dsz`. All re-validated against the n=5 oracles and the
n=8 exhaustive (exactly 96) after every change.

**LIVE overnight as of 2026-09-01 22:00** (9 cores, ~2GB, swap flat):
- 4 SAT solvers from [[margin1-uniform-sat-encodings]] (2485/2486 Paley19 pinned
  10h31m; 65731/65733 dr19_g2 pinned 8h18m) -- STILL no RESULT line.
- `hunt_p19.sh` x4 workers (`/tmp/p19_hunt_w{0,1,2,3}.log`): Paley(19) margin-1
  WITNESS hunt, exact MRV, disjoint base-state slices of 550, per-base cap 200k
  nodes escalating x4 per pass. **After 15 min: 0 witnesses and 0 base states
  cleared -- every base state hits the 200k cap**, consistent with the >17-day
  refutation estimate. Touch `/tmp/p19_hunt_STOP` to stop between passes.
- `/tmp/p19_hard.log`: the 12 undecided near-Paley instances, 1200s each, to
  calibrate whether Leonid's "settle margin-1 overnight" hypothesis is plausible
  -- if m=1/m=2 fall in minutes it is, if they do not it is not.
**Leonid doubts P19 margin-1 is UNSAT.** Nothing so far confirms or denies it;
note every one of the 29 solved mixed instances was SAT, and no margin-1 UNSAT
instance is known at k=5 for any n (smallest known UNSAT for UNRESTRICTED
5-inducibility is Paley(43) -- do not conflate the two).


## 2026-09-01 ~22:50 -- INCREMENTAL DOMAINS BUILT: ~110x, and Paley(19) became DECIDABLE

`kinduce8.c --inc`. Implements exactly the refinement derived above: child
domains are computed FROM the parent's rather than re-enumerated. Per parent
tuple p and voter i: p_i<q_i -> p'_i=p_i (forced before), p_i>q_i -> p'_i=p_i+1
(forced after), p_i==q_i -> BOTH legal; then the single new arc (v,u) keeps the
lifts with c_v(u) = #{i : v before u} = tau. Domains live in a
stack-disciplined arena (`dompool`, 256MB, `domoff/domcnt[depth][vertex]`),
seeded once per base state by the old fresh enumeration (`init_domains`).
**Caps are GONE**: full |D(v)| is known exactly at every node, so the argmin is
free -- which is the ingredient measured as most valuable.

**VALIDATION -- every previously established number reproduces EXACTLY:**
- n=5 cnt_all vs the DP oracle via the incremental path (base_sz=1, so refine()
  does all the work): 12 iso classes + 147 more masks, PASS.
- n=5 base_sz=3: --inc identical to non-inc on 342 masks.
- n=8 exhaustive k=3: exactly 96 UNSAT, both margins; the 96 known-bad all UNSAT.
- **n=9 exhaustive: 17,674 / 17,928 / 254 and the UNSAT SETS ARE IDENTICAL to
  the non-incremental ones (0 diffs, both margins).**
- **Full solution COUNTS agree at scale: Paley(7) all base states =
  2,145,778 solutions both ways; Paley(11) first 5 base states =
  61,885,077 solutions both ways.**

**SPEED** (same verdicts throughout):
- 29-instance Paley(19)-mixing benchmark: 29/29 both, but **70.56s -> 0.64s
  (110x)** and 992,378 -> 294,964 nodes (3.4x fewer, because the uncapped exact
  argmin beats the cap-5 approximation).
- Paley(11) count, 5 base states: **341.77s -> 6.07s (56x)**.
- n=9 exhaustive sweeps: 1109s/841s -> **13.6s/11.5s**.
- Paley(7) full count: 0.742s -> 0.175s.

**THE PAYOFF: Paley(19) k=5 exact margin-1 is now DECIDABLE.** One base state
went from ">6.94M nodes, unfinished in 600s" to **UNSAT in 3.562s** (1,338,515
nodes). First 8 base states: 40.9s. Whole-instance estimate ~11 core-hours
(later base states are harder than the first 8: a 4-worker run averaged ~17.8s
per base state, not 5.1s).

**LIVE AT SESSION END (2026-09-01 22:51), `decide_queue.sh`, log
`/tmp/p19p23_queue.log`, per-worker `/tmp/p{19,23}_w{0..9}.log`:**
10 workers x 220 base states on **Paley(19)**, no caps, exhaustive; then the
same queued on **Paley(23)**. 10 cores, ~17MB total. Each worker ends in
"WITNESS ..." or "SLICE EXHAUSTED, no witness"; all 10 exhausted with no
witness = a COMPLETE REFUTATION. The script prints a VERDICT line per q.
**Leonid killed the 4 SAT solvers at 22:03** -- Paley(19) pinned ran 10h35m and
dr19_g2 pinned 8h23m, BOTH ENDING WITH NO RESULT LINE (his call: "8h is
sufficient to close and if they haven't they probably won't"). So the SAT route
in [[margin1-uniform-sat-encodings]] is closed out as unresolved, and this DFS
is now the live tool.

**COSMETIC BUG, not affecting results**: in `--batch` mode `main()` runs its
auto-base scan and prints the header BEFORE any instance is loaded, i.e. on an
all-zero OUTM -- so the header line shows a meaningless `base_mask=0
base_states=13717`. `run_batch`/`solve_one` recompute the base correctly per
instance (proved by the exact n=8/n=9 agreement). Worth fixing for clarity.


## 2026-09-01 23:27 -- RESULT: Paley(19) AND Paley(23) ARE NOT MARGIN-1 5-INDUCIBLE

`decide_queue.sh`, 10 workers x 220 base states, exhaustive, no caps:
- **Paley(19), k=5, exact margin-1: UNSAT** -- 22:50:52 to 23:09:49 (19 min),
  3,641,060,754 nodes.
- **Paley(23), k=5, exact margin-1: UNSAT** -- 23:09:49 to 23:27:01 (17 min),
  1,909,597,235 nodes.
Audit of both: 2200/2200 base states cleared, 0 capped, 10/10 slices with
contiguous coverage [0,2200), 10x UNSAT worker verdicts, 0 FATAL/crash.
**Paley(23) is CHEAPER than Paley(19)** -- coherent, not alarming: at larger n
each vertex faces more arcs, domains empty sooner, so refutation gets EASIER as
n grows under exactness (this is a post-hoc explanation, not a prediction).
This closes the question [[margin1-uniform-sat-encodings]] was built for, and
in 19 min where 4 CDCL solvers failed in 10h35m.

**Leonid (important context for why UNSAT is not surprising)**: his expectation
that P19 would be SAT rested on the untested premise that every tournament
below 19 vertices is margin-1 5-inducible. He has since confirmed he tested
this exhaustively **up to AND INCLUDING n=11, all fine** (see the manuscript),
and that beyond n=11 it got hard. So the smallest margin-1-non-5-inducible
tournament has **n >= 12**, and nothing rules out 12..19. Do NOT re-run a k=5
threshold sweep over the n<=11 catalogues -- it is already done and Leonid
cancelled that queued job.

**RUNNING OVERNIGHT (queued, sequential, 10 cores, caffeinate armed):**
1. `confirm.sh` -> `/tmp/confirm.log`: re-decides BOTH instances from DIFFERENT
   base decompositions -- another copy of the same 5-vertex class
   (P19 base 0,1,4,8,12; P23 base 0,1,3,7,15) and then a DIFFERENT class
   entirely (the transitive base, 13717 base states instead of 2200:
   P19 0,1,3,4,9; P23 0,1,2,3,4). The base is an arbitrary starting choice, so
   if UNSAT is real every base must agree; a coverage bug tied to one base
   surfaces here. Prints 4 VERDICT lines and flags any witness as
   CONTRADICTING the first run.
2. `unrestricted.sh` -> `/tmp/unrestricted.log`: **Leonid's next target -- is
   Paley(23) 5-inducible with NO margin constraint? If not, N(5) <= 23**, a far
   more valuable conclusion than the margin-1 one (current bound is 43 via
   [[paley43-proven-nonrealizable]]). CAUTION: majority mode allows c in
   {3,4,5} per arc, so domains are much larger than under exactness -- the very
   thing that made tonight fast is absent. The script therefore runs controls
   first (Paley 7/11, DR15 g1/g2, then **Paley(19) unrestricted which is KNOWN
   SAT with a witness on file**) and ABORTS before q=23 if the P19 control does
   not clear, rather than burning the night.
`witness_watch.sh` + `verify_witness.py`: any witness is re-verified by an
INDEPENDENT script (rebuilds Paley(q) from its quadratic residues, rechecks all
C(q,2) arcs and that each voter order is a permutation) before the remaining
workers are killed; a witness that fails verification kills nothing and is
flagged as a bug. Verifier tested both ways (genuine witness passes, a single
transposition is caught) and supports `--majority`.


## 2026-09-02 morning -- margin-1 results CONFIRMED; a coverage bug caught by Leonid

**CONFIRMED: Paley(19) and Paley(23) are NOT margin-1 5-inducible.** Six
independent COMPLETE refutations, all exhausting with 0 capped:
| run | base | base_states | covered |
|-----|------|-------------|---------|
| P19 main / P23 main | auto (0,1,2,3,5 / 0,1,2,5,11) | 2200 | [0,2200) |
| P19/P23 altsame | 0,1,4,8,12 / 0,1,3,7,15 | 2200 | [0,2200) |
| P19/P23 altclass | 0,1,3,4,9 / 0,1,2,3,4 (TRANSITIVE class) | 13717 | [0,13717) |
The altclass pair partitions the space into 13717 root branches instead of
2200 -- a genuinely different decomposition -- and still exhausts. Audited: in
every run the header's `base_states` equals the top of the covered slice range.

**Unrestricted controls all pass, incl. the one that matters: Paley(19)
UNRESTRICTED is SAT in 147s** (38.3M nodes), witness independently verified.
Its `support_max=4`, i.e. NOT margin-1 -- exactly consistent with P19 being
margin-1-UNSAT but unrestricted-SAT, and proof that majority mode finds
witnesses at n=19.

**BUG (caught by Leonid's question "the unrestricted version should have a lot
more than 2200 realizations right? for the 5-regular tournament"): the number
of base states DEPENDS ON THE MARGIN MODE.** For the regular 5-vertex
tournament it is 2200 under exact margin-1 but **8031 under majority**.
`unrestricted.sh` hardcoded 2200 in its slicing loop (copied from the margin-1
scripts, whose 2200/13717 came from `base5_exact.tbl`, an EXACT-margin table),
so the Paley(23) unrestricted run was covering only [0,2200) of 8031 -- 27% --
and would have DECLARED UNSAT on it. Not a soundness bug in anything computed
(the 1088 finished base states are genuinely refuted, bookkeeping asserted:
cleared == b-lo and capped == 0 for all 10 workers); it becomes unsound only at
the moment of declaring the verdict. **NEVER hardcode base_states -- read it
from the program header, it is margin-mode dependent.**

**RELAUNCHED CORRECTLY (2026-09-02 05:19), running now:** dynamic work queue,
`p23_chunk.sh` + `xargs -P 10`, over the complement of the proven ranges:
1736 chunks x 4 base states = 6943, plus the 1088 already proven = 8031 exactly
(asserted in the generator). Chunk order SHUFFLED so a witness, if one exists,
shows up early instead of after a full sweep. Passing `--base 0 1 2 5 11`
explicitly reproduces the auto-selection (mask 947, 8031 states) so indices
line up with the completed work, and it skips the auto-base scan -- per-chunk
setup is 0.024s, hence fine-grained chunks and near-perfect load balancing for
free. Files: proven ranges accumulate in `/tmp/p23maj2_results.txt` (flock-
protected), per-chunk logs `/tmp/p23c/`, a verified witness lands in
`/tmp/p23maj2_WITNESS.txt` and touches `/tmp/p23maj2_STOP` to halt the queue.
**ETA ~23.5h (avg 122 s/base state from the partial run) => ~05:00 on 09-03.**
Leonid: "if it takes the rest of the day to run, so be it -- we are still
beating Brandt's six weeks by a very strong margin."
**Final aggregation MUST verify the union of proven ranges covers [0,8031)
exactly before any verdict is stated.**

**Load-balancing lesson**: the original 10 equal contiguous slices were badly
imbalanced (per-base cost ranged 86-193s across slices), so the straggler set
the finish time: 8.3h solo vs 4.1h if balanced. Contiguous equal slices are a
bad partition here; the shuffled fine-grained queue fixes both balance and
witness latency.


## 2026-09-02 -- NEGATIVE RESULT: global dissent-budget bounds add NOTHING. Do not retry.

Leonid's idea: at a node, lower-bound each voter's remaining dissents and prune
if the total exceeds the budget. Under margin-1 every arc has exactly tLO
dissenters and under majority at most tLO, so in both cases
    sum_j dissents(sigma_j) <= tLO*|E|   (= 342 for P19, 506 for P23).
Built and validated as `kinduce11/12/13.c` (`--fas`, `--fas2 D`, `--tie-fas`).
All three VALIDATE clean (n=8 exhaustive = exactly 96 both margins, Paley(7)
full count 2,145,778, n=5 vs the DP oracle) -- they are correct, just useless.

**Tier 1 (O(1), `--fas`): minFAS table for ALL subsets** via the subset DP
f(U)=min_v[f(U\v)+|N+(v)&(U\v)|], 2^n*2 bytes, 0.1s at n=23. Test
D_S + K*minFAS(T[F]) > tLO*|E|. **FIRED 0 / 8,039,748 times (P19 margin-1) and
0 / 1,201,670 (P23 unrestricted).** Structurally cannot fire: under exactness
the search already forces every arc inside S to split tLO, so
**D_S = tLO*C(|S|,2) is CONSTANT at a given depth and carries no information**,
and the test then reduces to [5*minFAS(T[F]) - 2|E(F)|] + cross > 0 whose first
bracket is always NEGATIVE (Paley sub-tournaments sit comfortably above 3/5:
-22 at F=V, ~-10 at |F|=5). At S=empty it is exactly the manuscript's
MAS/e >= 3/5 criterion; measured MAS/e = 0.6257 (P19) and 0.6364 (P23), i.e.
slack 22/342 and 46/506 -- close, but the wrong side, always.

**Tier 2 (`--fas2 D`): the EXACT per-voter minimum** m_j(P) over all linear
extensions of pi_j|_S, by a constrained subset DP with state (prefix of the
S-sequence consumed, subset of F placed) -- (|S|+1)*2^|F| states, so it gets
cheaper with depth. **FIRED 0 times at every depth tried** (P19 margin-1 depth
>=14 and >=12; P23 unrestricted depth >=16 and >=14), and cost 8x the runtime
at depth 12 (169s vs 21.8s). Two independent reasons it cannot work:
1. sum_j m_j(P) <= budget holds AUTOMATICALLY at any node with a valid
   completion (the totals are equal at the leaf), so it can only fire on dead
   nodes -- and the per-voter minima are far too slack to get there, because
   each voter minimises INDEPENDENTLY while what actually forces excess dissent
   is the COUPLING (all K must produce the right majority on every arc), which
   the relaxation discards entirely.
2. **There is no deep surface to act on**: only 1,808 of 1,201,670 nodes reach
   depth >=14 (0.15%) and 48 reach depth >=16 (0.004%). The exact-domain
   lookahead kills nodes long before. A perfect depth->=14 oracle could remove
   at most 0.15% of the tree. This kills the whole "oracle on deep-ish nodes"
   framing for this search, independent of which bound is used.

**Tier 3 (`--tie-fas max|min`): DP delta f(F)-f(F\v) as the MRV tie-break.**
Node counts IDENTICAL to the imbalance tie-break to the digit (8,039,748 in all
three arms) -- with exact uncapped domains, ties in |D(v)| essentially never
occur, so any tie-break is irrelevant.

**Vertex-numbering caveat Leonid raised is handled**: the DP indexes subsets by
position in `fv[]` (real ids pulled from the free-set bitmask) and `umask[U]`
translates back to a real vertex bitmask before any OUTM lookup; `fastab` is
indexed by genuine vertex bitmasks. A mapping error would have broken the
n=8/n=9 oracles, which it did not.

**The real lesson**: the exact incremental domains dominate everything. They
kill nodes so early that (a) deep-node oracles have no coverage and (b) argmin
ties are too rare for selection heuristics to matter. Further speedups will
need a STRUCTURALLY different mechanism -- nogood/clause learning, or
exploiting Aut(T) (|Aut(Paley23)| = 253, currently unused; only S_K voter
symmetry is broken) -- not another local or global bound.


## 2026-09-02 morning -- Aut SYMMETRY BREAK WORKS: ~10x on Paley(23) unrestricted

**Leonid's construction (his idea, refined jointly).** Aut(Paley(q)) =
{x -> ax+b : a in QR}, order q(q-1)/2, transitive. For sigma: x -> a(x-t) with
a in QR we get sigma(t)=0 and sigma(s)=a(s-t), and a(s-t) sweeps the WHOLE coset
QR*(s-t) -- so ONE fixed representative per coset suffices, and the two cosets
(s-t a residue or not, i.e. the top-ranked vertex beats the second or not) are
mutually exclusive and exhaustive. Hence the sound constraint (`--top0rr r1 r2`,
kinduce16):
   **SOME voter ranks vertex 0 first AND one of the two fixed reps second.**
Leonid's formulation: ONE search, a profile survives if EITHER condition can
still hold -- avoids any QR/NQR split across branches.
**Why it composes with the base lex-sort (the crux): the condition is
VOTER-INVARIANT, so it survives the re-sorting.** Pinning a PARTICULAR voter's
top vertex does NOT work -- sorting moves that voter. And forcing the partial
numbering to be Aut-lex-min is outright UNSOUND (Leonid caught this): sigma
moves the PLACED SET, so the image node has a different restriction to B and is
not matched in our tree, and the property is not monotone. Voter symmetry is
safe incrementally precisely because permuting voters leaves S untouched.

**Only sound for VERTEX-TRANSITIVE T.** Never use it on the n=8/n=9 catalogues
(Aut trivial there) -- it would manufacture false UNSATs.

**Prerequisite fact (computed): NO 5-subset of Paley(19) or Paley(23) has a
nontrivial setwise stabiliser.** Invariant subset sizes are {0,1,3,4,6,7,9,10,
12,13,15,16,18,19} for P19 (element orders 1,3,9,19) and {0,1,11,12,22,23} for
P23 (orders 1,11,23). So base-stabiliser symmetry breaking is unavailable at
|B|=5 -- that is why the old SAT pin needed a TRIANGLE. P19 could get 3x from a
size-3/4 base; P23 gets nothing that way (3 does not divide 253).

**VALIDATION**: construction verified mechanically (0 failures / 20,000 random
profiles at q=7,11,19,23, including that it survives the base sort); flag OFF
reproduces every oracle exactly (n=8 = 96 both margins, n=9 = 17,674/17,928/254
with UNSAT sets identical, Paley(7) count 2,145,778); flag ON keeps Paley(11)
SAT and still finds a verified witness for Paley(19) UNRESTRICTED (known SAT).
Paley(7) counts: full 2,145,778 -> r=1 598,574 + r=3 137,941 - overlap 27,291 =
709,224 union (3.03x).

**MEASURED SPEEDUP (like-for-like, both chunk orders uniformly shuffled):**
unconstrained 105 chunks mean 646.0s (161.5s/base state) vs Aut-broken 145
chunks mean 64.7s (16.2s/base state) = **~10x**. Beware small biased samples:
base states 0-9 gave only 2.90x and cheap ones 2.2-7.1x -- Leonid predicted the
speedup would be larger on expensive subtrees and was RIGHT.
**Decomposition**: of 8031 base states, **3766 (46.9%) are killed at the ROOT**
by the condition, at zero cost and blind to how expensive the subtree was (two
of the three most expensive base states die instantly: 224.5s->0 and 247.0s->0),
and survivors get a further ~4x from in-search pruning (37.2s vs 161.5s).
**dead_at_seeding = 0** for both P19 margin-1 (2200) and P23 unrestricted
(8031): with only 5 vertices placed, no vertex can have an empty domain, so
Leonid's guess of "a handful" is actually zero. Aut kills 1123/2200 (51.0%) for
P19 margin-1.

**HYBRID COMPLETENESS (this is what let us switch mid-run without redoing
anything)**: ranges already refuted WITHOUT the constraint stay valid (a
stronger statement); the rest are refuted WITH it. Any solution has an image
meeting the condition, whose base state lies in one or the other -- contradiction
either way. `/tmp/p23_proven_snapshot.txt` holds the unconstrained ranges.

**BASE SELECTION, revised (Leonid's point)**: choose the base to minimise
SURVIVING base states, not total. `base_enum2.c --dump` now emits
(mask, sorted, all, surv1, surv2). Kill rate IS class-dependent and monotone in
3-cycle count, confirming Leonid's prediction that transitive bases die more:
margin-1 54.8% (regular) -> 56.3% (transitive); unrestricted 55.0% -> 60.6%.
**But the criterion does not change** -- the regular class has 8031 total /3614
surviving vs the transitive class's 1,151,452 /454,017, so it still wins by
~126x; the 1.1x differential kill is noise against a 143x difference in totals.
**More actionable: the kill rate depends on WHERE the reps sit in the base.**
Our live base {0,1,2,5,11} has reps at base-indices (1,3) -> 46.9% killed, 4265
surviving; a base with reps at (1,2) kills ~55% -> ~3614 surviving (1.18x
better). Paley(23) has 7 such regular-class subsets, e.g. **{0,1,5,6,10}**.
SUPERSEDED -- see the rep-role rule below; the index positions were only a
proxy for a STRUCTURAL property.

**THE CORRECT RULE (Leonid, 2026-09-02) -- choose the Aut reps by their ROLE.**
For B = {0,b1..b4} regular, vertex 0's out-degree inside B is the number of QRs
among the b_i, and regularity forces it to be 2 -- so EXACTLY 2 QRs and 2 NQRs,
giving exactly 4 valid rep choices (any QR works as r_QR, any NQR as r_NQR).
Because the regular 5-tournament is unique up to iso AND vertex-transitive,
fixing vertex 0 plus the reps' structural roles determines the configuration up
to iso, so **the surviving-base count is UNIVERSAL -- the same for every regular
base containing 0.** Verified across 8 bases, one count per role combination:
| out-rep role | in-rep role | alive of 8031 |
|--------------|-------------|---------------|
| beats        | beats       | 4265  (what the live 2026-09-02 run used) |
| beats        | loses       | 4663 |
| **loses**    | **beats**   | **2591  <- BEST** |
| loses        | loses       | 3104 |
So: **pick the out-neighbour of 0 that LOSES to its sibling, and the
in-neighbour that BEATS its sibling.** 1.65x better than the live run.
Strikingly the best BASE is the same subset {0,1,2,5,11} we were already
running -- only the REPS change (2,5 instead of 1,5), since 2 is the
out-neighbour that loses to 1. Placement/subset choice was a red herring;
220 regular 5-subsets contain 0 and all admit this pattern.


## 2026-09-02 10:23 -- RESULT: Paley(23) is NOT 5-INDUCIBLE (unrestricted) => N(5) <= 23

**Coverage exactly [0,8031): all 8031 base states refuted, 0 double-counted, 0
chunks with capped!=0, 0 SAT verdicts in any chunk log, witness file empty.**
Aggregate with `python3 KInduceDFS/aggregate_p23.py` (reads the per-chunk logs
in /tmp/p23c and /tmp/p23c2 -- one file per chunk, so no shared-file race;
macOS has no flock and the shared results file was written unsynchronised, hence
the aggregator ignores it). This improves the N(5) bound from 43
([[paley43-proven-nonrealizable]]) to **23**.

**LEONID'S FRAMING: this is TIME TO DISCOVERY, NOT PROOF.** The claim will be
verified multiple ways before being made. Publication plan (his): present the
overall argument GENERICALLY (base-state decomposition + symmetry breaking),
then implement it TWO ways -- once with SAT, once with the bespoke DFS --
"a convergent result plus a DRAT is our proof".

**Strength of evidence right now**: the margin-1 results (P19 and P23) have SIX
independent complete refutations across three base decompositions; this
unrestricted result has ONE. So the more valuable result is currently the weaker
one. Also note 1508 of the 8031 bases were refuted with NO Aut break at all
(the run was a hybrid), so part of it is already unconditional.

**LIVE NOW: `rerun1.sh` -> `/tmp/p23_rerun1.log`, per-chunk `/tmp/p23r1/`.**
Clean from-scratch re-decision, same base {0,1,2,5,11} but the BEST ANCHOR
(reps 2 and 5, the "out-nbr that loses / in-nbr that beats" role pair) => 2591
live bases instead of 4265, expected ~2.7h, 10 workers. It is both a
different-decomposition cross-check and the single-configuration timing datum
the hybrid run could not give. Witness detection + independent verification are
wired in (`/tmp/p23r1_WITNESS.txt`, `/tmp/p23r1_STOP`); the detector was tested
end-to-end on a known-SAT instance and does fire, verify and halt.

**NEXT STEPS, in Leonid's order:**
1. Let rerun1 finish; confirm the same verdict from the different anchor.
2. A further anchor (or a 4-three-cycle-class base, ~6.4h) for more convergence.
   NOT the transitive class -- Paley(23) does have 1518 transitive 5-subsets but
   they carry 1,151,452 bases / ~454,017 live, i.e. hundreds of core-hours.
3. **SAT cubing for DRAT certificates.** `KInduceDFS/cube_sat.py` is WRITTEN and
   smoke-tested (Paley(7)/(11) SAT in both margins): a fresh, independent
   dissent-boolean encoder (deliberately NOT adapted from
   Paley23Decide/margin1_dissentbool_sat.py, so agreement is real
   corroboration), with `--margin majority|exact`, `--cube "o1;o2;o3;o4;o5"`,
   `--proof`. Triple rule re-derived independently and matches.
   **KEY INSIGHT: the Aut symmetry break is fully ABSORBED into which cubes you
   run.** A base state is exactly C(|B|,2)*K = 50 unit literals (the dissent
   pattern on B's internal arcs pins each voter's order on B), so restricting to
   the 2591 live bases IS the symmetry break -- the SAT side needs no
   symmetry-breaking clauses, and both implementations inherit ONE shared
   mathematical argument. Leonid was rightly sceptical that cubing helps
   ("P23 with 5 vertices determined is about as hard as a full P19 run"), but a
   cube pins far more than 5 vertices' membership. UNTESTED: per-cube CDCL time
   -- that is the go/no-go, test one cube first.
   **BLOCKER: no DRAT checker on the machine** (drat-trim, cadical, kissat,
   minisat all absent as standalone binaries). pysat DOES support
   `with_proof=True` + `get_proof()`, so traces are obtainable, but a checker
   must be built before proofs mean anything. Also plan check-and-discard:
   2591 proofs could be hundreds of GB.
4. The 12..18 gap: Leonid's exhaustive margin-1 result reaches n<=11, so the
   smallest margin-1-non-5-inducible tournament has n>=12 and 12..18 is open.
   Restrict to (semi)regular; `regulartournaments13.RData` and 11/12 are already
   on disk, and the incremental engine does 191,536 instances in 11.5s.

## 2026-09-02 (afternoon) -- the Aut break family is EXHAUSTED

`kinduce22.c` adds `--toppair u1 v1 u2 v2`: "SOME voter's global (top, second)
is (u1,v1) or (u2,v2)". This is the general form of the break; `--top0rr r1 r2`
is the special case where both reps start at vertex 0.

**Why two reps, stated without cosets.** |Aut(P_q)| = q(q-1)/2 equals the number
of arcs, and the action on arcs is transitive, hence **regular**: exactly one
automorphism carries any given arc to any other. So the q(q-1) ordered pairs
form exactly TWO orbits -- agrees / disagrees with T's arc -- and a complete
break picks one representative from each. Proof: take any voter with top two
(u,w); if u->w then sigma carries (u,w) to (u1,v1), else to (u2,v2); applying
sigma to the whole profile preserves T. Voter-invariant, so it composes with the
base lex-sort. **This is the phrasing to use in the paper** -- it needs no QR
language, only "fix an arc and a non-arc", instantiated as "(0,2) is an arc of
Paley(23), (0,5) is not". Cosets were only ever how sigma gets EXHIBITED, which
the proof does not need. `--toppair` REFUSES same-orbit rep pairs (unsound).
Same regularity also gives: P_q minus one vertex and P_q minus two vertices are
each unique up to isomorphism, the latter with trivial Aut.

**Exhaustive optimisation over all 100 complete two-rep breaks** with both
coordinates in the base (survivors of the base-state list):

| overlap of the two reps | P23 majority min/mean | P19 margin-1 min/mean |
|---|---|---|
| 0 vertices (disjoint) | **2537** / 3509 | **781** / 951 |
| 1 vertex | 2587 / 3651 | 809 / 1001 |
| 2 (same unordered pair) | 2591 / 3717 | 811 / 1019 |

Less overlap is better in both min and mean, and the optimum needs all four of
u1,v1,u2,v2 distinct. The optimum is attained EXACTLY 5 times on both
instances, each using 4 of the 5 base vertices -- one per choice of omitted
vertex. But the spread WITHIN an overlap class (2537..4452) dwarfs the spread
BETWEEN classes (2537 vs 2591), so "make the reps disjoint" is a weak rule of
thumb; the specific pair dominates. **In use (0,2)+(0,5) = 2591 is within 2.1%
of the 2537 optimum, so there is nothing left here -- do not revisit.**

**Negative result: the "easy to explain" (0,1)/(1,0) rule is much weaker.**
Taking both orders of ONE unordered pair is the worst class (P23: 4842 of 8031,
1.87x the work; P19 margin-1: 1227 vs 809). It DOES fire far more deeply --
measured on P19 margin-1 base states [0,12): 1,436,856 top0_fails vs 250,702,
5.7x more -- and is still 5.7x slower (24.1s vs 4.19s, 8.6M vs 1.5M nodes).
Deeper firing does not compensate, because the base filter is a multiplicative
factor over independent subtrees whereas deeper firing only trims inside
subtrees already entered. CAVEAT on that 5.7x: base states [0,12) are
unrepresentative (the (0,5) reps kill 9 of those 12 outright while (0,1) kills
none); the honest general factor is the base ratio 1227/809 ~ 1.5x. Sample
randomly, not by prefix -- which is why rerun1.sh shuffles its chunks.

Trap for the next person: the `--toppair` orbit-validity check must live in
`main()`. Inserted before the FIRST `make_static_order()` it lands inside
`solve_one` and then only runs in `--batch` mode, silently doing nothing on
single-instance runs.

## 2026-09-03 (overnight) -- a formally verified theorem, and Paley(27) settled

**Paley(19) is NOT margin-1 5-inducible -- MACHINE-VERIFIED.**  22,876 live
cubes, every one UNSAT, every proof produced by cadical in LRAT and checked
INDEPENDENTLY by lrat-trim (different program, different author; cadical's
`--checkproof` disabled so it never validates its own work).  24.3 core-h solve
+ 0.8 core-h check, 2.64 h wall on 10 workers.

    ROOT (CNF)    0eeb9dd53956fec2c77b752d74b89b12c7d1dddd6dc4047405ecb7907896a78a
    ROOT (proofs) ea5f8982abc24b3366d50c1899813d3f8e793920ed3fffac7fac0491561ab27a

Coverage certified separately: 143,032 clauses UNSAT in 8.5 s, 401 MB DRAT
verified by drat-trim in 124.5 s with **0 RAT lemmas in core** (pure
resolution).  Cubes are base states of a 6-vertex base, so `deepen.py` -- whose
splitting is uncertified, `cover_deep.py` being broken -- is not in the trust
chain at all.  What remains human is exactly two lemmas: arc-orbit anchoring is
WLOG, and voters may be lex-ordered WLOG.

**Paley(27) is NOT 5-inducible (unrestricted).**  2008/2008 chunks UNSAT, 0
capped, coverage [0,8031) with no gaps, no witness, 31.04 core-h, 1.14e8 nodes.
Host = the GF(3^3) build (`p27_paley.bits`, = McKay DRT27 #371).  This does NOT
improve N(5) <= 23: non-inducibility propagates upward, so non-inducible
tournaments already exist at every n >= 23.  Its value is method reach -- 27
vertices decided in half a night on a laptop, where SAT and ILP cannot go.
It is a COMPUTATION, not a certificate; a DRAT for it is out of reach at
roughly 20x the Paley(23) proof volume.

**THE COST SCALING IS FLAT FROM 23 TO 27**, which was the surprise.  Per
SURVIVING base state:  P23 47.3 / 47.7 s (two completed runs), P27 44.0 s
(31.04 core-h / 2537).  The earlier 2.2x-per-vertex model was junk -- it came
from comparing P19 margin-1 against P23 majority, which are not comparable.
The sampled price27 protocol read 57.8 s and so ran ~32% high; its control arm
read 58.0 s where the truth was 47.5, so the bias is in the protocol, not the
instance.

**NEXT: price Paley(31).**  Configuration already found and recorded:
base {0,1,6,13,19}, mask 217 (regular class, the same mask used for the P23 and
P27 measurements so the comparison is controlled), 8,031 base states, **2,537
survivors** under `--toppair 0 19 6 1`.  Note 31 is prime, so `--paley 31` is
valid (unlike 27).  IF the flat scaling holds, 2537 x ~45 s = ~32 core-h -- a
laptop job.  That is an extrapolation across a gap where extrapolation has
already failed once today, so MEASURE it before believing it.

## 2026-09-03 (morning) -- Paley(31) settled, and the cost series turns DOWNWARD

**Paley(31) is NOT 5-inducible (unrestricted).**  5253/5253 chunks UNSAT, 0
capped, coverage [0,21009) with no gaps, no witness, **26.89 core-h**, 3.43e9
nodes, 2 h 43 m wall on 10 workers.  Host `p31_paley.bits`: verified a
tournament, all out-degrees 15, every ordered pair with exactly 7 common
out-neighbours (doubly regular), and |Aut| = 465 = the number of arcs, so Aut
acts REGULARLY on arcs and `--toppair` is a complete case split.  The tracked
bits file is the engine's own `--paley 31` build: identical node counts
(823423 / 728580 / 1437525) on three base states.  As with P27 this does NOT
improve N(5) <= 23 -- non-inducibility propagates upward -- and its value is
method reach.

**The configuration was chosen by competition, and ranking by base count would
have been wrong again.**  Leonid's rule: compete on `bases x MEASURED s/base`,
never on bases alone.  Winner was class 12, base {0,1,2,3,6}, mask 499,
`--toppair 2 3 0 3`, 21,009 base states, **4,007 survivors** -- beating class 76
(2,537 survivors, mask 217) even though it carries 58% MORE bases, because each
base is ~2x cheaper.  Cost per surviving base: 23.4 s (class 12) vs ~42 s
(class 76).  Also measured: within class 76 the five labelled masks differ by
up to **1.65x** at identical base counts, so the embedding matters as much as
the class.

**The arc-and-reverse `--toppair` warning is now quantified.**  Taking both
orders of one unordered pair (class 10, `--toppair 5 2 2 5`) gave the LOWEST
per-base cost of any arm -- 2.57x cheaper than class 76, the deeper firing is
real -- but retained 2.90x more bases.  Net **1.13x worse**.  The two effects
very nearly cancel, so this break is never a win and never a disaster either.

**CORRECTION to the 2026-09-02 claim that "the bias is in the price27
protocol".**  It was not biased.  Bootstrapping the exact 2008-chunk P27 cost
vector gives mean 0.999 of truth at k=60 -- but a 90% CI of [0.66, 1.35],
because the estimate is dominated by how many LIVE chunks (674 of 2008) you
happen to draw.  The +32% reading was ordinary sampling noise, which is exactly
why price27's RATIO was right (1.00x per vertex) while its ABSOLUTE was 32%
high.  **Report ratios; anchor absolutes to a completed run.**

**New pricing protocol, and the trap it exists to avoid.**  `base_survivors.py`
shows the base-state LIST depends only on the labelled mask and the survivor SET
only on the reps' indices WITHIN the base.  So mask 217 with reps at index
(0,4)+(2,1) gives a bit-identical base-state list and survivor set on Paley(23),
(27), (31) and (43) -- verified by hash (`aca0e59525a20e27` /
`e855c30ec80223d6`).  Chunk i is then literally the same four base states on
every host, so hosts can be priced by a cost-weighted PAIRED RATIO against a run
that actually completed.  Known-answer control: the same estimator applied
naively to P27, whose truth is 31.04 core-h, read -23% at n=10 and -8% at n=40.
**The trap: single-base probe runs execute under PARTIAL pool load** -- short
jobs leave workers idle -- and so under-price a saturated run by ~1.35x.  The
winning arm probed at 17.0 s/base and ran at 23.4 s/base.  The paired ratio is
immune, which is why the class-76 figure (29.5 core-h, anchored) held and the
class-12 probe figure did not.  Pre-registered prediction for the run that was
launched: ~26 core-h; actual 26.89, i.e. accurate to 3%.

**THE COST SERIES IS NOT FLAT -- IT DECREASES IN q.**  On 24 bit-identical
mask-217 base states, measured on one core alongside a saturated pool (the P27
control arm reading 0.98-1.04 against its own full run):

| ratio | time | nodes | us/node |
|---|---|---|---|
| 31/27 | 0.933 | 0.614 | 1.521 |
| 43/31 | 0.746 | 0.385 | 1.935 |
| 43/27 | 0.739 | 0.237 | 2.94 |

Two steep opposing trends, not a plateau: node counts fall like ~n^-3 (a larger
Paley graph is MORE constrained, so refutation fires higher in the tree) while
per-node work rises like ~n^+2.3.  The fall keeps winning.  It CAN win because
the outer loop is q-INDEPENDENT: mask 217 has 8,031 base states and 2,537
survivors for every q, that being a property of the 5-vertex base pattern rather
than the host.  **Paley(43) therefore prices at ~22.9 core-h -- cheaper than
Paley(31)** -- and is running as an independent confirmation of the 2026-07-10
co-backing screen (a SAT there would mean a bug in one of the two methods, not a
new theorem).

**n=43 engine validation, SAT side**, every witness re-checked by
`verify_witness_bits.py`: transitive on 43 vertices -> SAT, 39 nodes, 0.221 s;
locally transitive circulant C_43(1..21) -> SAT, 39 nodes, 0.018 s, and with
`--top0` also SAT at 0.006 s.  Locally transitive is a PROVEN 3-inducible class,
so UNSAT there would have been a proven bug.  **Random majority-of-5 tournaments
are useless as controls at this size** and worse than the earlier "found in the
minimum possible number of nodes" note suggests: with the auto-selected
most-restrictive base one did NOT find its own witness in 900 s, nor in 400 s
with a hand-picked base.  This is a REFUTATION engine; witness-finding at n=43
needs structure.  Note `--top0` is sound only for VERTEX-TRANSITIVE hosts, so
3-cycle rotations of a circulant make it INVALID -- to perturb a circulant and
keep the break legal, reverse whole JUMP CLASSES, which yields another circulant.

## 2026-09-03 (midday) -- Paley(43) reconfirmed by a second, independent method

**Paley(43) is NOT 5-inducible -- now by DFS as well as by the co-backing
screen.**  2008/2008 chunks UNSAT, 0 capped, coverage [0,8031) with no gaps, no
witness, **22.87 core-h**, 1.43e9 nodes, 2 h 19 m on 10 workers.  Host
`p43_paley.bits` verified doubly regular (out-degrees 21, every ordered pair
with exactly 10 common out-neighbours), |Aut| = 903 = the arc count, so
`--toppair 0 10 2 1` is a complete case split.  Base {0,1,2,3,10}, mask 217 --
chosen so the decomposition is bit-identical to the P27 and P31 mask-217 runs.

This is a genuine CROSS-METHOD agreement, not a repetition: Theorem 10.1 got
there through alpha* and co-backing, this through placement DFS, sharing no
code and no argument.  It does not improve N(5) <= 23.

**The paired-ratio pricing was accurate to 0.2%** -- predicted 22.9 core-h from
R(43/27) = 0.7025 measured on 24 bit-identical base states, actual 22.865.  With
P31 (predicted ~26, actual 26.89, +3%) that is two consecutive pre-registered
predictions inside 3%, on a protocol whose predecessor was out by 32%.  The
difference is entirely the paired ratio plus a completed-run anchor.

**Confirmed: sweep cost DECREASES in q over 27 -> 31 -> 43**, now from FULL runs
rather than samples, on the identical mask-217 decomposition (2,537 surviving
base states at every q):

| q | core-h | nodes | s/surviving base |
|---|---|---|---|
| 27 | 31.04 | 1.14e8 | 44.0 |
| 43 | 22.87 | 1.43e9 | 32.5 |

(P31 ran the cheaper mask-499 decomposition, so it is not directly comparable in
this table; its mask-217 paired ratio against P27 was 0.9505.)  Node counts rise
while total time falls -- per-node work is what shrinks relative to the tree.
The mechanism remains that the outer loop is q-INDEPENDENT while the per-base
DFS gets easier as the host becomes more constrained.

**n=43 SAT-side validation** (see the morning entry) passed on transitive and on
the locally transitive circulant C_43(1..21), both with independently verified
witnesses, the latter being a proven 3-inducible class so an UNSAT there would
have been a proven bug.

## 2026-09-03 (afternoon) -- arc-criticality: Paley(19) YES, Paley(23) open

**Exactly one tournament per q, up to isomorphism, from a single arc reversal.**
`Aut(Paley(q))` is regular on arcs for prime `q`, hence transitive, so all
reversals are isomorphic.  Verified constructively, not merely from the group
order: for all 171 (`q=19`) and 253 (`q=23`) arcs the explicit affine map
carrying `(0,1)` to that arc carries the reversed tournament onto the reversed
tournament.  0 failures.  **The reversal destroys all symmetry: `|Aut| = 1` for
both**, so `--toppair`/`--top0`/`--toporb` are UNSOUND on these hosts and only
the voter lex-sort applies.

**Paley(19) with one arc reversed IS margin-1 5-inducible** -- witness in ~50 s,
independently re-verified (`all 171 arcs at exactly 3:2`), saved to
`WITNESSES_paley_arcrev.md` at the moment of discovery.  So **Paley(19) is
ARC-CRITICAL for margin-1 5-inducibility**, complementing its known
vertex-criticality.

**THEOREM (Leonid): arc-criticality implies vertex-criticality.**  If `T` is not
`k`-inducible and for every vertex `v` SOME arc `e` incident to `v` has `T^e`
`k`-inducible, then `T - v` is `k`-inducible for all `v`.  Proof:
`k`-inducibility is hereditary, `T^e` `k`-inducible gives `T^e - v`
`k`-inducible, and `T^e - v = T - v` because `e` is destroyed by deleting its own
endpoint.  Holds for margin-1 too (restriction preserves the exact 3:2 margin).
So **arc-criticality is the STRONGER notion** -- reversing one arc is a far
smaller repair than deleting a vertex, which drops `n-1` arcs at once.
Verified constructively: restricting the P19 arc-reversal witness to either
endpoint of the reversed arc yields margin-1 witnesses for `Paley(19) - v` on the
ORIGINAL host (153 arcs, all at exactly 3), while restricting to a NON-endpoint
fails on exactly one arc -- the reversed one, at support 2 -- exactly as the
proof predicts.  That also re-derives a `Paley(19) - v` certificate by a second
route.

**Calibration on a known object: `G_8` (denoted `H_8` in earlier accounts) is
arc-critical for 3-inducibility.**  All 20 single-arc reversals become
3-inducible, minFAS dropping 7 -> 6 in every case (`3 x 6 = 18 <= 20`, clearing
the counting obstruction), and NONE is isomorphic to `G_8`.  Tested by real
3-inducibility -- three linear orders with pairwise disjoint backward sets, found
over all `8!` orders reduced to the 278 inclusion-minimal backward sets -- not
merely by the failure of a certificate.  The degenerate escape route (a reversal
isomorphic to the original) is therefore worth checking and was empty in all
three cases here.

**Paley(23) arc-criticality is OPEN**, with the routes priced and a reduction
recorded; see `WITNESSES_paley_arcrev.md`.  Headlines: the blind `T^e` scan is
**253 core-h** (113 s per base state measured, and all 8031 are live without the
break); enumerating `Paley(23) - v` witnesses is ~220 core-h and so buys
correctness, not speed (10 of 12 probed base states are barren; base state 6560
alone holds 3,068,928); **5,928,928 witnesses scanned with 0 single-arc
extensions**.  The best next step is Leonid's **defect-1 reformulation** -- run
the original `Paley(23)` search with the symmetry break intact but accept
exactly one under-supported arc -- because the `--toppair` WLOG survives the
relaxation (`Aut` acts on relaxed solutions carrying the defect along), which
restores the 8031 -> 2537 reduction.  Break-even is 7.5x the defect-0 cost of
48 s/base, so expect 2-5x; still cluster-shaped.  **The defect budget belongs in
the incremental-domain refinement, where soundness lives, so re-run the whole
regression suite before trusting any verdict from it.**

New tools: `kinduce23.c` (`--emit`: stream every witness under `--count` instead
of halting; regression-checked at 96/6880, n=8 k=3), `insert_scan.c` (exhaustive
`23^5` re-insertion, exact min distance), `insert_stream.c` (streaming version
with defect-2 pruning, ~153x fewer insertions; its distance-1 test is exact but
its reported minimum is NOT, being an upper bound over unpruned leaves).

## 2026-09-03 (afternoon) -- the two WLOGs compete, and the defect-1 route LOSES

Leonid's question: with the base's first five vertices fixed and the `--toppair`
renumbering in force, may we ALSO assume the reversed arc is spent somewhere
other than the base's 10 internal arcs?  **No -- and the group-theoretic reason
is exactly the one that makes `--toppair` a complete break in the first place.**

### The group budget (the answer, stated once)

`|Aut(P_q)| = q(q-1)/2` equals the number of arcs and the action is transitive,
hence **regular**, hence `Stab(ordered pair) = 1`.  `--toppair` normalises some
voter's `(top, second)` to an orbit representative, and by regularity there is
**exactly one** `g` per voter doing so -- so the entire set of admissible
relabellings is `{g_1..g_5}`, at most five elements, with **no residual
subgroup**.  Nothing is left to move the defect with.  Under an independence
heuristic the loss is `(10/253)^5 ~ 1e-7` per solution orbit, which is fine for
a HUNT (a witness found is still a witness) and worthless for the negative
direction -- and the heuristic is itself suspect, the base being chosen as the
MOST CONSTRAINED 5-subset, i.e. a priori where a one-arc repair buys most.

Holding the base fixed and being honest is expensive.  Base `{0,1,2,5,11}`,
reps `(0,2)/(0,5)`, majority, counted exactly by mirroring `brec()`:

| base target on S | base states | toppair survivors |
|---|---|---|
| exact `H|_S` | 8,031 | **2,591** |
| the 10 in-base flips, summed | 185,635 | **65,169** |

25x the work, on less constrained hosts -- so "enumerate all 11 base targets"
is not the fix.

### Two sound repairs

**(a) case split with a re-chosen base.**  The base is only our choice of which
five vertices go first, and may differ per branch, PROVIDED both branches use
the same reps (else the normaliser differs and the two conditions do not
partition).  Branch A: `g(e) not in arcs(S)`, base `S`, 2,591 survivors.
Branch B: `g(e) in arcs(S)`, base `B2` with `|B2 & S| <= 1` so `arcs(B2)` misses
`arcs(S)` and its target is exact too; best such `B2` containing 0 is
`{0,3,4,7,10}`, 8,031 states / 6,408 survivors (the reps span `0,2,5 in S`, so
`B2` holds at most one rep vertex and the filter degrades to the `u placed
only` form -- which is exactly the `--top0` filter).

**(b) spend less of the group, and the assumption becomes a THEOREM.**

> With `--top0` ("some voter's global top is 0", a `q`-fold break) one may
> additionally assume the defect lies in a set `R` of `q` arcs fixed in advance
> to miss the base.  Proof: the `--top0` normalisers form a coset of
> `G_0 = Stab(0)`, cyclic of order `(q-1)/2`, which acts FREELY on arcs -- a
> non-identity `x -> ax` fixes only 0, so it fixes `{u,v}` setwise only if
> `au=u, av=v` (forcing `u=v=0`) or `au=v, av=u` (forcing `a^2=1`, so `a=1`).
> All orbits therefore have size `(q-1)/2`, while a 5-vertex base spans only
> `C(5,2) = 10` arcs, so for `(q-1)/2 > 10` -- i.e. `q >= 23` -- no orbit fits
> inside the base and reps outside it always exist.  Within the coset exactly
> one element carries `e` into `R`. QED

Total break `= |Aut|` either way; the `(q-1)/2` multiplier is simply spent on
root pinning (`--toppair`) or on defect localisation (`--top0 + R`), never both.

**`q = 23` is the first Paley prime where this works**: `q = 19` gives orbits of
size 9 < 10 and the counting argument fails (it happens to hold there anyway,
checked directly, which is what makes the P19 known-answer test below possible).
At base size 6 or 7 the counting also fails, but a direct check over ALL
`C(23,6) = 100,947` and `C(23,7) = 245,157` subsets finds **no trapped orbit at
all** (max orbit-overlap with a base 5 and 6, against orbit size 11), so base
size is a free parameter for route (b).  `defect_set.py` emits `R` and reports
the hypothesis it is relying on.

### `kinduce24.c`: `--defect FILE`, and its regression suite

Defect budget 1, confined to `R`, implemented where soundness lives -- the
incremental domain refinement.  `RM[v]` holds `v`'s R-neighbours; every pair is
constrained exactly once (in `dom_rec` while the base is seeded, else in
`refine` when the later endpoint is placed), so a tuple carries the number of
defects it spends in byte `DFB = MAXK-1`; `insert_v` adds it to `defect_used`,
`remove_v` restores it, every test demands `<= 1`.  Pruning is relaxed only on
R-pairs and only while the budget is unspent.  The lookahead is a RELAXATION,
not exact -- two unplaced vertices can each be kept alive by the same unit of
budget -- which is sound (domains over-estimated) and caught when either is
placed.  `main()` REFUSES an `R` meeting the base, `--batch`, `--fas`/`--fas2`
(the minFAS dissent budget is computed for the unreversed `T`) and `K >= MAXK`.

1. **Inert without `--defect`**, matching `kinduce22` exactly: 96/6880 (n=8 k=3,
   both margins), 17,928 / 17,674 (n=9, separation 254), regular n=11 48/1175
   at k=3 and 1223/0 at k=5.
2. **Single-arc `R` agrees with the direct reversed-host run** on three
   non-3-inducible n=8 hosts x 28 arcs x 2 margins: 84 tests each, 0 failures,
   and the single reversals split 149 SAT / 67 UNSAT, so both directions bite.
3. **Multi-arc `R` (|R|=18) is SAT iff some single reversal is**, 12 hosts x 2
   margins, 0 failures.
4. **The budget is TIGHT**: 25 triples `(H, f, g)` per margin where `H`, `H^f`,
   `H^g` are all non-inducible but `H^{f,g}` is inducible -- all correctly
   UNSAT, so nothing leaks to two defects.
5. **End to end on the real configuration**: `--paley 19 --margin exact --top0
   --defect p19_defectR.txt` returns **SAT in 118 s** on base state 3, one
   clean reversal (arc `0->4` at support 2) inside `R`, and
   `verify_witness_bits.py` confirms independently against the reversed host:
   *all 171 arcs at exactly 3:2*.  This is the SAT direction of exactly the
   combination P23 would use, which is the direction that matters -- the failure
   mode of an unsound break is a FALSE UNSAT.

### The price, measured -- and route (b) LOSES

Paired probes on 8 random base states (never a prefix), all arms at the same
8-way load, because a single-base probe under partial load under-prices a
saturated run -- here by 2x, not the 1.35x recorded earlier.

| configuration | s / base state | over 8031 |
|---|---|---|
| defect-0, `--top0` (23-fold break) | 66.4 | **148 core-h** |
| `--top0` + defect on 1 arc (`r_1 = 1.35`) | 89.6 | 201 core-h |
| `--top0` + defect on all 23 (`r_23 = 4.94`) | >= 328.2 | **>= 732 core-h** |
| blind `T^e` scan, no break | 224.1 | **500 core-h** |

**So the defect-1 reformulation costs ~1.5x MORE than the blind arc-reversed
scan it was meant to beat, and the earlier "expect 2-5x better" is refuted.**
The relaxation factor is remarkably stable across base states (3.93..5.93,
cost-weighted 4.94) and the figure is a LOWER bound: 2 of 8 probes hit the
600 s cap.  `r_1 = 1.35` vs `r_23 = 4.94` says the 5x is the intrinsic price of
23 simultaneously-live defect positions rather than loose bookkeeping -- and
splitting `R` into `g`-sized groups is worse still, `(23/g) x r_g` being
minimised at `g = 23` since `r` grows sublinearly.  Perfect global budget
propagation is bounded below by `r_1`, so at best it could reach ~296 core-h;
not worth building for a 1.7x that may not materialise.

**Also re-priced by the same protocol: the blind scan is 500 core-h, not the
253 recorded above** -- the old figure was a partial-load single-probe reading,
the very trap `pricing-protocol-paired-anchor` warns about.  Both routes are
cluster-shaped; the blind scan is the cheaper one, needs no group theory, and is
already implemented (`kinduce22 --bits p23_arcrev.bits --n 23`).

New tools: `kinduce24.c` (`--defect`), `defect_set.py` (emits `R`, proves or
checks the hypotheses), `jz_n15/probe_rate.sh`.

### Route (a) priced too, and the load story corrected

Same protocol, same 8-way load.  **Branch A had to be re-sampled among the
2,591 SURVIVING base states**: a uniform sample of 8 indices put 7 of them in
the 68% that the full break kills at the root, leaving the estimate resting on
one probe.  Sampling survivors and scaling by 2,591 is the low-variance
estimator, and `base_survivors.py`'s index convention was checked against the
engine's own root-kills on four indices first.

| piece | measurement | total |
|---|---|---|
| branch A control (`--top0rr 2 5`, defect off) | 46.3 s / surviving base state | **33.3 core-h** |
| **branch A** (defect free over the other 243 arcs) | >= 913 s, `r_243 >= 19.7`, **8/8 capped at 900 s** | **>= 657 core-h** |
| branch B control (base `{0,3,4,7,10}`, defect off) | 57.4 s mean over all 8031 | 128 core-h |
| **branch B**, free defect over the 10 base arcs | `r_10 = 5.20`, 1/8 capped | **>= 666 core-h** |
| **branch B**, Leonid's variant: defect spent IN THE BASE | 44-53 s / survivor, i.e. `r ~ 1.0` | **~851 core-h** |

**Route (a) >= 1,320 core-h, both terms lower bounds** -- against >= 732 for
route (b) and 500 for the blind scan.  The structural point needs no branch A
at all: **branch B alone, built either way, already costs more than the whole
blind scan.**

*Leonid's variant does exactly what it promises* -- spending the defect in the
base restores full-strength pruning below it, and the measured per-survivor
cost (44-53 s) is indistinguishable from the defect-0 control's 46.3 s.  It
just pays 25x in base states (65,169 against 2,591), and 25 > 5.2, so it lands
1.28x above the free-defect version -- within the noise of 8 probes, so the two
formulations are really equivalent at ~700-850 core-h.

*The premise it was offered under is false, though the identification is right.*
`P23|_{0,1,2,5,11}` IS the regular tournament on 5 vertices, but `|Aut(R_5)| = 5`
against 10 arcs, so R_5 is **NOT arc-transitive**: two arc-orbits of size 5,
`{(0,1),(1,2),(2,5),(5,11),(11,0)}` and `{(0,2),(1,5),(2,11),(5,0),(11,1)}`.
The flip table above already showed it -- five flips give 16,118 base states and
five give 21,009, partitioned exactly along those orbits.  And the two classes
buy no work: **`Stab_{Aut(P23)}(T) = 1` for every one of the 33,649 five-subsets
`T`** (253 = 11 x 23, and neither prime-order subgroup fixes a 5-set), so the
R_5-isomorphism between two flips does not extend to the host and the ten flips
stay ten separate subproblems below the base.  Choosing the shared reps jointly
to minimise both branches -- they MUST be shared or the split is not a
partition -- gains 3%: 1,465 core-h at the optimum `(0,2)/(5,1)` (2,537 exact /
62,961 flip survivors) against 1,508 for the in-use `(0,2)/(0,5)`.

**Correction to the entry above: there is no 2x load penalty.**  The branch A
control reproduces the independently recorded 47.5 s per surviving base state
at **46.3 s under the same 8-way load** -- a clean known-answer anchor for this
whole pricing protocol.  So the blind scan's recorded 113 s against the 224.1 s
measured here is a genuine disagreement between samples, not load; the old
figure was most likely taken by prefix rather than at random, the very trap
`rerun1.sh` shuffles its chunks to avoid.  The ranking is unaffected.

### The margin split at the flipped arc: correct, cheap to test, and it loses

Leonid's last idea: don't treat the defect pair as unconstrained, exploit the
fact that its support still has a VALUE.  Under majority with `K=5` the flipped
arc's support in `T`'s own direction is in `{0,1,2}`, so split

  * **case A**, support exactly 2 -- the flipped arc goes 3:2.  Equivalently a
    UNIVERSAL lower bound of 2 on every arc, with at most one arc below 3.
  * **case B**, support in `{0,1}` -- the flipped arc goes 4:1 or 5:0.

`kinduce24 --defect-support LO HI` implements the window, default `[0,tLO]`
being the old behaviour exactly.  Case A is contiguous with `[tHI,K]`, so the
R-pair domain gains ONE support value instead of three and the monotone `break`
survives; case B is NOT convex, so a lower-bound failure at an R-pair can
recover at a larger `p` and those pairs take `continue` instead -- getting that
wrong would silently lose solutions.  Validated: default window inert
(96/6880 both margins, 17,928 / 17,674, regular n=11 48/1175); budget still
tight on the 25 double-reversal triples; and the SPLIT IS COMPLETE on 84
single-arc tests, which stress it properly -- 51 came back A-only, 9 both,
24 neither, matching the reversed host every time, 0 failures.

| arm | `r` vs defect-0 | over 8031 |
|---|---|---|
| union `[0,2]` (as before) | 4.94 (LB, 2/8 capped) | >= 732 core-h |
| **case A, 3:2** `[2,2]` | **4.56** (LB, 2/8 capped) | >= 675 core-h |
| **case B, 4:1 / 5:0** `[0,1]` | **2.48** (none capped) | **368 core-h** |
| **split total A + B** | **7.04** | **>= 1,043 core-h** |

**Case B behaves exactly as predicted -- the stronger restriction does prune a
lot, halving the relaxation and finishing every probe uncapped.  Case A does
not: pinning the defect to a single support value buys only 7.7%.**  So the
split costs 1.4x the union it replaces.

*And it cannot be rescued, for a reason worth recording.*  Both sub-searches
accept a zero-defect profile, so each explores at least the entire defect-0
tree and `r >= 1` for either.  The split therefore beats the union only if
`r(A) < r(union) - 1 = 3.94`, and `r(A) = 4.56`.  The union already IS the
shared merge of the two cases; splitting can only duplicate the common part.

The deeper reason case A disappoints: the relaxation's cost is driven by the
NUMBER of live R-pairs, not by the width of the window at each -- which is what
`r_1 = 1.35` against `r_23 = 4.94` was already saying.  Narrowing 23 windows
from three values to one is a second-order effect; removing 22 of the 23 live
pairs is a first-order one, and the group argument fixes `|R| = q`.

Residual value: case B is a **complete 368 core-h slice** of the open question.
Run alone it either settles Paley(23) arc-criticality outright or narrows it to
"the flipped arc goes exactly 3:2" -- a genuine strengthening of the open
statement, though not a cheaper route to the full answer, which remains the
blind `T^e` scan at 500 core-h.

## 2026-09-03 (evening) -- Paley(23) is NOT arc-critical at margin 1

**Complete, and cheap: 2.79 core-h of search.**  `Paley(23)` with any one arc
reversed is not margin-1 5-inducible.  All 2200 base states refuted, coverage
`[0,2200)` exact with no gaps or duplicates, 0 leftover logs, 0 witnesses.
`Paley(23)` itself is not margin-1 5-inducible either (immediate: margin-1
restricts majority, majority already refuted), so **the reversal repairs
nothing at margin 1 -- the opposite of `Paley(19)`, which IS margin-1
arc-critical.**  Full statement, evidence and caveats in
`m1_arcrev/VERDICT.md`; per-base-state times in `m1_arcrev/base_state_times.txt`.

Known-answer gate: the same binary and configuration on `p19_arcrev.bits`
returns SAT in 444.6 s with `VERIFY bad_arcs=0 support_min=3 support_max=3 OK`.

**It settles nothing about MAJORITY.**  `minFAS(Paley(23)^e) = 91`, so total
dissents `>= 455` against a budget of `2 x 253 = 506`: **slack 51**, i.e. up to
51 of the 253 arcs may sit above 3:2.  Majority does not collapse to margin-1
here, and the blind majority scan (500 core-h) still carries almost all the
probability mass.  New tool `minfas_bits.c` computes minFAS and that slack for
any `.bits` host.

### Why margin-1 was worth trying first, and the trap it exposed

`--margin exact` on `T^e` needs 2200 base states against majority's 8031, and
runs at 4.56 s each against 224.1 s -- **50x cheaper for a complete answer**,
and `margin-1 SAT => majority SAT` would have settled the whole question.

**The trap: `RESULT ... time=` EXCLUDES setup.**  A one-process-per-base-state
harness pays ~12 s per process at `n=23` for the auto-base scan over all
`C(23,5) = 33,649` subsets -- **73% of the cost when the search itself is
4.6 s**.  Reading the engine's own timer said 2.8 core-h; the wall clock said
10.2 (1,096 base states in 2,286 s on 8 workers = 16.7 s each).  The wall clock
was right.  **Fix: name the base.**  `--base 0 1 2 6 15` is exactly what the
auto-selector picks and is bit-identical (654,513 nodes on base state 1852
either way); it cut the sweep from 16.7 s to 6.4 s per base state.  Every future
run should name its base rather than re-deriving it 2200 times.

*And it was NOT a sampling problem*, which was my first explanation and wrong:
the margin-1 cost distribution is tight (mean 4.56, sd 1.11, range 1.76-8.47,
correlation with base-state index `r = +0.036`), and a bootstrap over the 2200
measured values puts an 8-probe mean inside `[0.86x, 1.15x]` at 90% with
`P(>= 2x high) = 0.000`.  The +12 s is additive, so it distorts a cheap arm and
not an expensive one: 5% on the 224 s blind scan, 3.7% on route (b), but 73%
here.  It also means the earlier "clean anchor" claim (46.3 s against the
recorded 47.5 s per surviving base state) was too quick -- mine carried setup
the completed run amortised over 4 base states per chunk.

## 2026-09-03 (late) -- the margin hierarchy, and one dead mechanism

`kinduce24 --max-margin M` implements the rungs directly: a pair is admissible
iff its support lies in `[(k-M)/2, (k+M)/2]`, so for `k=5` M=1 is `--margin
exact`, M=5 is `--margin majority`, and M=3 forbids unanimous arcs.  It gates
itself -- M=1 and M=k reproduce the two existing modes EXACTLY on the n=8 and
n=9 catalogues (6784/96 and 173,608/17,928; 6784/96 and 173,862/17,674).

**First half of the paper's conjecture, self-contained.**  `Paley(23) - v` is
margin-1 infeasible (complete sweep this evening) and its stored majority
witness has support histogram **208 arcs at 3:2, 23 at 4:1, 0 at 5:0** --
re-derived from quadratic residues, 231 arcs, 0 violations.  So it is
5-inducible at margin <= 3 and not at margin <= 1.

**The clean reformulation.**  With `B_i` the backward-arc set of voter i,
support `= k - #{i : e in B_i}`, so
  margin <= k    : every arc in at most `(k-1)/2` of the `B_i`
  margin <= k-2  : ... and in at least one -- **the `B_i` must COVER E**
  margin <= 1    : every arc in exactly `(k-1)/2`
The open half therefore asks for a tournament whose five near-optimal orders
can never cover every arc.

**A sound screen for it, and why it is asymptotically toothless.**  Let
`f(e)` = min FAS over orders putting `e` backward (the same subset DP with one
precedence constraint; `minfas_arc.c`).  Covering `e` needs a voter with
`FAS >= f(e)`, every voter costs `>= minFAS`, and the total is `<= tLO*|E|`, so

    margin <= k-2 inducible  ==>  f(e) <= tLO*|E| - (k-1)*minFAS  for every arc.

A single violating arc PROVES the tournament needs a unanimous arc.  **It fires
nowhere in the Paley family** -- slack 22/27/31/57 for P19, P19^e, P19-v, P23-v
against `max_e f(e) - minFAS` of 0/2/0/0.  And it cannot fire for large n:
reversing any arc costs at most `n-1` extra feedback arcs (lift one endpoint
over the other), so `f(e) - minFAS = O(n)`, while the slack
`tLO*|E| - k*minFAS` is a roughly constant FRACTION of `|E|` on near-threshold
hosts (10/55, 22/171, 46/253 ~ 0.15) hence `Theta(n^2)`.  **So the obstruction
can only fire when `MAS/|E|` is within `O(1/n)` of `3/5`.**  The screen is
one-sided, so silence proves nothing -- but the OBVIOUS mechanism for forcing a
unanimous arc is ruled out, and a separator must fail margin <= 3 for a finer
reason than "some arc is too expensive to reverse".  Leonid reports that at
k = 3, reversing a "blocking" arc often forces a unanimous arc; that does not
reproduce here -- the reversed arc of `Paley(19)^e` has `f(e) = 65` against
`minFAS = 63`.

## 2026-09-04 07:40 -- P43-2v priced: 229 core-h, and WHY it costs more than P43-v

**P43-2v is unique up to isomorphism.** |Aut(Paley(43))| = 43*21 = 903 = #arcs,
so Aut is REGULAR on arcs, hence transitive on 2-subsets: every P43 minus two
vertices is the same tournament. No choice of pair to make.

**It admits NO symmetry break.** The setwise stabiliser of every one of the
C(43,2) pairs is trivial (checked exhaustively). Pointwise fixing u and v forces
a = 1; swapping them needs a = -1, a NON-residue mod 43 (43 = 3 mod 4). So
`--toporb` would need all 41 reps, which is no break at all.

Contrast P43-v, where `--toporb 0 1` IS sound: p43_minus1v.bits is Paley(43)
less vertex 0, Stab has order 21, and it splits the 42 survivors into exactly
two orbits of size 21 (the QR / non-QR cosets) with 0 and 1 in different ones.
Verified, not assumed. The check is conservative in the safe direction: Stab is
a SUBGROUP of Aut(P43-v), so its orbits refine the true ones and a rep set
meeting every Stab-orbit meets every Aut-orbit.

### Paired-anchor price (12 base states, index-for-index against the live hunt)

Base states are identical: base {0,1,2,3,10}, 8031 states, for BOTH n=42 and
n=41 -- the outer loop is q-independent, so the whole difference is per-base.

| n | mean | median | sd | aggregate |
|---|---|---|---|---|
| 12 | 1.194 | 1.191 | 0.072 | **1.204** |

    P43-2v = 85.2 s x 1.204 = 102.6 s/base x 8031 = 229 core-h = 22.9 h on 10 cores
    (P43-v, for comparison: 190 core-h = 19 h)

**Losing the break costs MORE than dropping a vertex saves** -- +20% net. This is
the exact opposite of the margin-1 finding from 03:36, where the same style of
orbit break was worth 0.0007% of nodes. At margin<=1 the margin constraint
already prunes everything the orbit test would; at margin<=3 the search is wide
enough that Aut-breaking genuinely pays. Do not carry the margin-1 rule of thumb
across rungs.

All 12 probe base states came back UNSAT (12/8031 of P43-2v swept, no witness).

### CAUTION on sequencing

A margin<=3 refutation of P43-v does NOT show P43-v fails at MAJORITY, so it
does not settle whether Paley(43) is vertex-critical. Per one.sh's own header
the M=3 refutation only becomes a result when paired with an M=5 witness
(strict hierarchy). Deciding vertex-criticality needs P43-v at MAJORITY; the
P43-2v descent question is only well-posed once that is known.

## 2026-09-04 08:30 -- THE 3-CYCLE BOUND: majority == margin<=3 on every regular tournament

### Lemma (3-cycle bound)

Let u->v->w->u be a 3-cycle of T and let c(e) = #{voters agreeing with e}.  Any
LINEAR order agrees with at most 2 of the 3 arcs of a cyclic triangle, so
summing over the k voters

        c(u,v) + c(v,w) + c(w,u)  <=  2k.

Under majority every term is >= tHI = ceil((k+1)/2), hence every single support
obeys

        c(e)  <=  2k - 2*tHI        ( = 4 when k = 5 ).

So for k=5 an arc lying in ANY 3-cycle can never exceed support 4: **the top
margin rung is unreachable, and majority collapses onto margin<=3.**
(General k: majority == margin <= k-2, the rung k being unreachable.)

### Corollary 1

If EVERY arc of T lies in a 3-cycle then, at k=5, T is 5-inducible at majority
iff it is 5-inducible at margin<=3.  The two questions are the SAME question.

### Corollary 2 -- and this is the wide one

**Every REGULAR tournament has every arc in a 3-cycle.**  For an arc u->v we
have u notin N+(v) and v notin N-(u), so both sets lie inside V\{u,v} of size
n-2 and each has size (n-1)/2.  Inclusion-exclusion:

        |N+(v) & N-(u)|  >=  (n-1)/2 + (n-1)/2 - (n-2)  =  1.

Tight: the value 1 is attained (checked on rotational tournaments n=7..21).
Hence **for every regular tournament, majority == margin<=3 at k=5.**

### Measured, all hosts (arcs lying in NO 3-cycle)

| host | min 3-cycles per arc | arcs in no 3-cycle |
|---|---|---|
| Paley(43) | 11 | 0 |
| Paley(43)-v | 10 | 0 |
| Paley(43)-2v | 9 | 0 |
| Paley(23) | 6 | 0 |
| Paley(23)-v | 5 | 0 |
| Paley(19) | 5 | 0 |
| dr19_g2 | 5 | 0 |
| transitive n=8 (CONTROL) | 0 | 28 |

The control fires, so the test discriminates rather than being vacuously true.

### Consequences

1. **The live P43-v margin<=3 hunt IS deciding majority.**  If it completes
   UNSAT then P43-v is not 5-inducible at majority, hence **Paley(43) is NOT
   vertex-critical**, with no follow-up run.  This RETRACTS the caution logged
   at 07:40 ("a margin<=3 refutation leaves vertex-criticality open") and the
   41-case pinned split proposed to repair it.  There is no gap to repair.
2. **Explains the all-zero 5:0 column** in WITNESSES_margin_hierarchy.md for
   Paley(19), Paley(23)-v and dr19_g2.  Not three coincidences -- forced.
3. **The OPEN half of the margin-hierarchy conjecture is IMPOSSIBLE on this
   whole family.**  It asks for a tournament 5-inducible unrestricted but not at
   margin<=3; on any host where every arc lies in a 3-cycle the two coincide.
   So `minfas_arc.c` "firing nowhere in the Paley family" is not weakness of the
   screen -- the target does not exist there.  A separation REQUIRES a host with
   an arc e = u->v having N+(v) & N-(u) = empty, which by Corollary 2 forces the
   host to be IRREGULAR.  That is the redirection: stop screening regular and
   doubly-regular families for the second half.
4. The 41 arc-orbit classes of Aut(P43-v), and the 5x5 base cover computed for
   them, are correct but MOOT for this purpose.  Kept in git for a future host
   that actually admits a unanimous arc.

### Engine work (kinduce25.c)

- `--pin u v` forces arc u->v to unanimity.  Enforced in all three places the
  margin is: `brec` (base-INTERNAL pins, filters base states), `dom_rec`
  (initial domains) and `refine` (the --inc path).  Base-internal and off-base
  are the SAME constraint -- the pin is invariant under permuting voters, so it
  composes with the base lex-sort; only the moment it bites differs.  Unlike
  `--defect` a pin does not alter T, so it is safe inside the base.
- Guards, all tested and all firing: pin a non-arc; pin combined with
  --top0/--toporb/--toppair (spends Aut twice -- the g moving a K:0 arc to its
  representative is unique when Aut is free on arcs, so no residual survives);
  pin under --max-margin < K (unsatisfiable by construction); and **pin on an
  arc lying in a 3-cycle** (the Lemma -- refuses rather than emit a vacuous
  UNSAT, because 41 vacuous UNSATs look exactly like 41 real ones).
- Positive control: a transitive n=8 host, arc 0->7 in no 3-cycle, returns SAT
  with `PIN arc 0->7 support=5 of 5 (unanimous, OK)`.
- Fixed a real gap inherited from kinduce24: `--max-margin` capped arc support
  during insertion but NEVER for base-INTERNAL arcs, so margin<=3 enumerated a
  strict superset.  UNSAT stayed sound (a superset refutation implies the
  subset), but a SAT needed an independent histogram -- neither the engine's own
  VERIFY (`c < tHI` only) nor verify_witness_bits.py checks the upper cap.  By
  the Lemma the gap is VACUOUS on every host here, which is why it never bit.
- Regression: margin-1 on dr19_g2, bs[0,24), gives node-for-node identical
  output to kinduce24 (31,850,161 nodes, same dom_calls, same refine_tuples).

## 2026-09-04 09:40 -- P43-2v contains NO known obstacle: the free screen fails

Before spending 229 core-h on P43-2v, screened it for an induced copy of a
tournament already KNOWN not to be 5-inducible.  5-inducibility is hereditary on
vertex subsets, so one induced copy would settle P43-2v for free.

    Paley(23): NO induced copy   (complete, 19 phi(0) choices, 11,711 nodes)
    Paley(27): NO induced copy   (complete, 15 choices,          8,268 nodes)
    Paley(31): NO induced copy   (complete, 11 choices,          5,911 nodes)

(Paley(43) itself does not fit in 41 vertices.)  Leonid predicted this.

`embed_screen.py`.  Propagation is the tournament analogue of kinduce's
incremental domains: once t pattern vertices are mapped, every unmapped pattern
vertex has a DETERMINED t-bit arc signature against them and a host candidate
must match it exactly.  Signatures go near-unique after ~log2(n) placements, so
the search collapses -- hence the tiny node counts.

**Sound symmetry cut.**  Aut(Paley(q)) is transitive on VERTICES, so if any
embedding phi exists then phi o alpha is one too and (phi o alpha)(0) =
phi(alpha(0)) ranges over ALL q host vertices in the image.  So at least q of
the nh host vertices work as phi(0), and testing any nh - q + 1 of them is
COMPLETE.  This is exact, not heuristic.
  TRAP: it needs the PATTERN vertex-transitive.  It would be UNSOUND for e.g.
  Paley(23)-v, whose Aut has order 11 with two orbits of 11 -- there the cut
  nh-q+1 = 2 would discard genuine embeddings.  Only use it for Paley patterns.

**Positive controls** (`embed_screen_control.py`) -- a screen that only ever
answers NO is worthless:
    Paley(19) into itself                  FOUND (20 nodes)
    Paley(23) into itself                  FOUND (24 nodes)
    Paley(23) planted in a random n=41 host FOUND (59 nodes), recovered set
                                           EQUALS the planted set
### What the screen does NOT rule out

Only the KNOWN non-5-inducible tournaments were tested, because those are the
only ones we have.  N(5) >= 12 means everything on <= 11 vertices IS
5-inducible, so an unknown obstacle inside P43-2v would have to live on 12..23
vertices -- exactly the range the open N(5) question is about.  So the screen is
as complete as current knowledge allows, and no more.

**Conclusion: P43-2v is genuinely open and the 229 core-h is not avoidable by
this route.**

## 2026-09-04 15:40 -- arc-reversal does NOT escape the 3-cycle bound; and a stale price

**Stale figure flagged.** Line ~880 of this log records the blind `T^e` scan at
**253 core-h** (113 s/base).  That was SUPERSEDED by the re-pricing at line
~1024: **500 core-h** (224.1 s/base).  The 253 came from a probe under partial
load and under-priced by **1.98x** -- worse than the 1.35x the pricing protocol
warns about.  Use 500 core-h (= 50 h on ten cores).  WITNESSES_paley_arcrev.md
line 136 already has the correct number; only this log carried the stale one.

**Arc-reversed hosts are irregular but still 3-cycle-saturated.**  Reversing one
arc of Paley(q) breaks regularity -- out-degrees become {(q-1)/2 -1, (q-1)/2,
(q-1)/2 +1} -- so Corollary 2 (regular => every arc in a 3-cycle) no longer
applies.  Measured anyway:

| host | out-degrees | min 3-cycles/arc | arcs in NO 3-cycle |
|---|---|---|---|
| Paley(19)^e | {8,9,10} | 4 | 0 |
| Paley(23)^e | {10,11,12} | 5 | 0 |
| Paley(27)^e | {12,13,14} | 6 | 0 |
| Paley(43)^e | {20,21,22} | 10 | 0 |

Consequences:
1. **No saving for the P23 arc-criticality scan.**  majority == margin<=3 on
   `T^e` as well, so running at `--max-margin 3` is the SAME computation, not a
   cheaper one.  500 core-h stands.
2. **The arc-reversed family is barren for the hierarchy's open half.**  Do not
   screen it.

### Necessary condition for a 3-cycle-free arc (the open half's real target)

An arc u->v lies in no 3-cycle iff `N+(v) & N-(u) = empty`.  Both sets live in
`V\{u,v}` of size n-2, so this forces

        d+(v) + d-(u) <= n-2,  i.e.  d+(v) + (n-1-d+(u)) <= n-2,
        hence   d+(u) >= d+(v) + 1.

**The TAIL must out-rank the HEAD in out-degree.**  In a regular tournament that
is impossible (re-deriving Corollary 2).  A single arc reversal DOES satisfy it
-- for the new arc v->u we get d+(v)=12 >= d+(u)+1=11 at q=23 -- and yet the
intersection is still 5, not 0.  So the degree inequality is necessary and very
far from sufficient: you need the two neighbourhoods to be exactly
complementary, which needs a genuinely lopsided tournament, not a perturbed
regular one.  That is where the open half has to be hunted.
