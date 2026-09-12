# Independent reproduction on the cluster

## Why

On 2026-09-05 several things in the certification workflow changed: a dead
constant removed from `cubes.py`, a stale label fixed in `cover_check.py`,
wall-clock timings removed from the hashed records, a streaming path added to
`cover_check.py`, and an unearned coverage claim removed from the verdict
template. Each was validated locally — but local validation of a local change is
weak evidence. Different hardware and a different compiler is the real test.

## One driver, instance as data

Everything that differs between campaigns — size, margin, base, arc/non,
expected roots, cost — lives in `instances/<name>.conf`. Nothing in the scripts
knows about Paley(19) or Paley(23) specifically, so **adding Paley(27) or
Paley(31) is a new conf file and nothing else**.

    run.sh <instance> <stage>

| stage | what it does | needs a solver? |
|---|---|---|
| `root` | regenerate every cube CNF, assert ROOT (CNF) | **no** |
| `coverage` | build and solve the split-half CNF, assert UNSAT + verified | yes |
| `cert` | bind split + search into the two combined roots | no |
| `recertify` | full re-solve of every cube (see `SOLVE_CORE_H`) | yes |
| `all` | root, coverage, cert | yes |

Every expected value is **asserted**, not printed for a human to compare. An
empty expectation in the conf means "record what you observe" — never "assume it
passed". Both confs are now fully populated: `COVER_CLAUSES`, `COVER_CNF_SHA`
and `CERT_PORTABLE` are all present, so every stage asserts and none merely
reports. `COVER_CNF_SHA` was added on 2026-09-11 — before that the coverage
stage printed the hash instead of checking it, which is how the cluster's
coverage comparison came to be made by eye.

## Tier 1 — cheap (~1 core-h, no cube solving)

    KInduceDFS/jz_reproduce/check.sh          # every instance
    KInduceDFS/jz_reproduce/check.sh p19      # just one

ROOT (CNF) commits to the CNF *files*, which this repository's Python generates,
so regenerating and hashing them involves **no solving at all** — the check costs
minutes rather than the hundreds of core-hours the original runs took, and needs
only Python. That is the check that would catch a real encoding change. If the
toolchain isn't built yet, the `root` stage still works.

## Tier 2 — full re-certification (the gold standard)

    INSTANCE=p19 sbatch KInduceDFS/jz_reproduce/recertify.slurm    # ~24 core-h
    INSTANCE=p23 sbatch KInduceDFS/jz_reproduce/recertify.slurm    # ~228 core-h

Re-derives each verdict from scratch and compares ROOT (CNF), exiting non-zero on
mismatch. It does **not** compare ROOT (proofs): a different cadical build may
emit a different, equally valid proof, so a difference there is expected.

**A SAT cube would be a witness and a major result.** The run stops and keeps the
instance as `STOP_SAT`. Do not dismiss it as a porting artifact.

## Tier 3 — a different solver (strongest)

The method is solver-agnostic; cadical is our choice, not a dependency of the
argument. Any solver emitting DRAT/LRAT can produce the proofs, and any checker
can verify them. Running a sample of cubes under a *different* solver — kissat,
say — tests the result rather than the build: same CNFs, same ROOT (CNF),
different search, different proofs, same verdict.

Point `CAD` in `certify_d6.py` at the other solver and use `--sample N --seed S`
(a uniform sample; `--limit` is a prefix and cube difficulty is heavily skewed,
so it would mislead).

Stronger still on the checking side: `cake_lpr` is formally verified in HOL4,
where `lrat-trim` is merely a different program by a different author.

## What can and cannot be reproduced elsewhere

| | reproducible off the original machine? |
|---|---|
| **ROOT (CNF)**, both campaigns | **yes** — and needs no solver |
| Coverage certificate | **yes** — fresh proof; its CNF hash must match, its proof hash will not |
| **CERT (portable)** | **yes** — built from the two above |
| Known-answer selftests | **yes** |
| **ROOT (proofs)**, **CERT (full)** | **no, by design** — they commit to LRAT bytes |

## Toolchain

    git clone https://github.com/arminbiere/cadical && cd cadical && ./configure && make
    git clone https://github.com/arminbiere/lrat-trim && cd lrat-trim && ./configure && make

`certify_d6.py` and `cover_check.py` expect them at
`~/Downloads/DownloadedSoftware/{cadical/build/cadical,lrat-trim/lrat-trim}`;
edit `CAD`/`LT` at the top of each, or symlink.

**`lrat-trim` exits 20 on success, not 0.** Anything wrapping it must test for
`s VERIFIED` in the output, not the exit code.

## Memory

`cover_check.py` must be run with `--stream` on anything the size of Paley(23).
The in-memory path holds every clause as Python lists — ~9 GB for 3,414,729
negated cubes at 75 literals — and was killed at 8.99 GB. Streaming ran the
Paley(19) instance in 39 MB of Python; cadical's own footprint on the Paley(23)
instance is the part still to be measured, so watch it rather than assume.

Note the coverage instance is **much larger than the search instance**: the
`--arc`/`--non` filter reduces the search half to the live cubes, but coverage
must consider *all* base states — 3,414,729 for Paley(23) against 343,896 live.

## What has actually been reproduced on a second machine

Stated per value, because "the certificate reproduces" is four different claims
and they did not all happen.

| value | asserted by the script? | reproduced on the cluster? |
|---|---|---|
| `ROOT (CNF)`, both instances | yes, `stage_recertify` vs `ROOT_CNF` | **yes** -- `PORTABLE ROOT MATCHES`, jobs 1829004 (p19) and 1919064 (p23) |
| coverage clauses, UNSAT, `CHECK=VERIFIED` | yes, vs `COVER_CLAUSES` | **yes**, both instances, 2026-09-11 |
| coverage CNF sha256 vs `split_cover_cnf` | yes *since 2026-09-11*, vs `COVER_CNF_SHA` | matched, but on the day it was **printed and compared by eye** |
| `CERT (portable)` | yes, `stage_cert` vs `CERT_PORTABLE` | **yes**, both instances -- `slurm/cert_p19.out` and `slurm/cert_p23.out` |
| `ROOT (proofs)` | no, by design | **matched anyway**, both instances, which is stronger than 5.2 claims |
| `CERT (full)` | no, by design | no, and must not be -- it commits to LRAT bytes |

**DONE 2026-09-12.** Both instances have now run `all` to completion, so
`CERT (portable)` is the product of a composition that was RUN, not inferred from
the fact that its two inputs matched. That inference -- true but unearned -- is
the exact failure `certroot.py` exists to end, and it is what the wording here
used to warn against.

The p23 run is the instructive one. `run.sh` prints
`NOTE: search_root_cnf was READ FROM ...` whenever the root came from the conf
rather than from the current run, and the absence of that line in
`slurm/cert_p23.out` is what distinguishes it from `slurm/cert_p23_loginkill.out`,
where the same "CERT (portable) matches the recorded value" was printed with the
root stage SIGKILLed at cube 200 of 343,896. Read the NOTE, not the match.

One thing did not reproduce and must not: `CERT (full)` commits to LRAT proof
bytes, which depend on the solver build. `ROOT (proofs)` matched anyway on both
instances, so the whole of the p23 difference comes from `split_cover_proof`,
for which the conf deliberately records no expectation.

It cost one allocation per instance, because `$W` is `JOBSCRATCH` and is purged
at job end: the coverage CNF and its proof cannot survive to a later `cert` run,
so the two stages must share an allocation.

    KInduceDFS/jz_reproduce/run.sh p19 all      # root + coverage + cert
    KInduceDFS/jz_reproduce/run.sh p23 all      # COMPUTE node, 4 cores, ~5 h

`all` is `root`, `coverage`, `cert` in that order. `root` regenerates the cube
CNFs with no solver; p23's coverage took 41 min of a 2 h wall; `cert` is a hash
of a text block. Both instances now carry `CERT_PORTABLE` in their conf, so
`stage_cert` asserts rather than observes, and a `FAIL` is the outcome to watch
for rather than a line to read.

## Earlier attempts, kept because their failure modes are instructive

`recert_1827897.out` died with `FileNotFoundError` on cadical (step 0 of this
file, skipped); `1828524` and `1829003` were cancelled by signal; `1843769` hit
its wall at 93,400 of 343,896 cubes. Chunk records make a resume cheap, which is
why 1919064 finished the set rather than restarting it. Against the laptop's
25.1 and 236.0 core-hours, the cluster's 70.9 and 567.6 are 2.8x and 2.4x,
inside the 2-5x band Appendix A.3 quotes.
