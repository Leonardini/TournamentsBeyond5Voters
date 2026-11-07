# N11Census — every 11-vertex tournament is 5-inducible (N(5) >= 12)

The literature has no exhaustive n = 11 verification (the census of Bachmeier
et al. 2019 stops at n <= 10), so we ran one. Built 2026-07-22.

## Pipeline (streaming, per gentourng res/mod slice; no tournament file ever
## materialized)

1. `gentourng -q 11 RES/MOD` (nauty 2.8.6, ARM build at
   `~/Downloads/DownloadedSoftware/nauty2_8_6/gentourng`): all 903,753,248
   tournaments in 48 s single-core; res/mod slicing partitions the generation
   tree, so slice totals summing to D_11 is the completeness identity.
2. `margin1_scan 11 emitn` (triple-local 4-label CSP, ~34 us/tournament):
   3-inducible => 5-inducible, done. ~49.9% survive to stage 3.
3. `cert_m1k5 11` (unit-margin five-voter CSP over the 10 dissent pairs,
   ~276 us/instance): SAT => 5-inducible with every arc 3:2; emits the full
   labeling as a witness.
4. `verify_m1k5 11` (independent verifier, this campaign): rebuilds the five
   voters from each witness, checks acyclicity of every backward set and
   re-counts every arc at exactly 3:2. Aborts the slice on any failure.
5. Residual (cert-UNSAT) lines -> ILP stage (feas5-style cplexAPI with
   scheme-A symmetry breaking) — **empty on all validation runs so far**.

## Validation (known-answer, before the full run)

- n = 9: stage 2 reproduces 173,608 / 254 / 17,674 exactly (the census table of the companion paper);
  all 17,674 non-3-inducibles are unit-margin 5-SAT, all witnesses verified.
- n = 10: stage 2 reproduces 6,812,906 / 89,686 / 2,830,464 exactly
  (the companion paper's census table); stage-3 run over the 2,830,464 in progress.
- n = 11 slice 137/4096 (246,829 tournaments): 118,463 / 5,119 / 123,247;
  all 123,247 unit-margin 5-SAT, all verified, residual 0.

## Running

Local (as launched 2026-07-22, ~5.5 h wall, 8 cores, ~10 MB RSS/worker):

    seq 0 255 | xargs -P 8 -I{} bash n11_worker.sh {} 256 results bin \
        ~/Downloads/DownloadedSoftware/nauty2_8_6/gentourng
    bash n11_aggregate.sh results 256

JZ fallback: `n11_census.slurm` (array 0-63; workers generate their own
slices on the node — nothing to rsync). Copy this directory + an x86 build of
the three `bin/` tools + gentourng to `$WORK/n11_kit` first.

The aggregator names missing workers, checks every per-slice tally chain
(margin1_scan vs cert vs verifier vs residual file), and asserts the slice
totals sum to exactly D_11 = 903,753,248.

## Sources

`margin1_scan.c`, `cert_m1k5.c` live in `Paley23Decide/` (manuscript Section G.3 /
the A(3) campaign); `verify_m1k5.c` is new (this directory's `bin/` holds ARM
builds of all three).
