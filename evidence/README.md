# Run evidence, 2026-09-02/03

Chunk-level logs for every verdict claimed in `../README.md`, plus the
measurement records behind each configuration choice.  The logs compress ~100x
(they are highly repetitive), so the archives are small enough to track.

## Verdict evidence

| archive | claim it supports |
|---|---|
| `rerun1_p23_majority.tar.zst` | 2nd refutation of Paley(23): 2008/2008 UNSAT, 34.0 core-h |
| `anchor2_p23_majority.tar.zst` | 3rd, **base-independent** refutation: 4030/4030 UNSAT, 43.8 core-h |
| `n22_p23minusv.tar.zst` | Paley(23)−v: SAT in 62 s, so n=22 does not improve the bound |
| `p27_majority.tar.zst` | Paley(27): 2008/2008 UNSAT, 31.0 core-h, 1.14e8 nodes |
| `p31_majority.tar.zst` | Paley(31): 5253/5253 UNSAT, 26.9 core-h, 3.43e9 nodes |
| `p43_majority.tar.zst` | Paley(43): 2008/2008 UNSAT, 22.9 core-h, 1.43e9 nodes — cross-method confirmation |

Each `c_LO_HI.log` carries the engine banner (base, break, base-state slice), a
`SLICE` line, and a `RESULT` line with verdict, nodes, capped count and time.
To re-audit one:

    zstd -dc run_evidence/p27_majority.tar.zst | tar -xOf - \
      | grep -h '^RESULT' | awk '{print $2}' | sort | uniq -c

(No `--wildcards`: that is GNU tar and silently matches nothing under the BSD
tar on macOS, which is how a first version of this file came to claim a
verification it had not performed.)

Coverage must also be checked, since a verdict is only as good as the union of
its slices: extract `base_state_slice=[a,b)` and confirm they tile [0, N).
Re-audited from these archives:

| archive | verdicts | capped | coverage |
|---|---|---|---|
| rerun1 | 2008 UNSAT | 0 | to 8031, no gaps |
| anchor2 | 4030 UNSAT | 0 | to 16118, no gaps |
| p27 | 2008 UNSAT | 0 | to 8031, no gaps |
| p31 | 5253 UNSAT | 0 | to 21009, no gaps |
| p43 | 2008 UNSAT | 0 | to 8031, no gaps |
| n22 | 1 SAT | 0 | to 7976, **10 gaps -- CORRECT** |

**The n22 gaps are by design.**  That run is a witness SEARCH and stops at the
first verified witness, so it never visits the remaining slices.  Partial
coverage there is success, not incompleteness -- do not apply the refutation
checklist to it.  For the three UNSAT archives, complete coverage is exactly
what makes the refutation valid.

The Paley(19) certification's per-cube hashes are NOT here -- they are tracked
uncompressed in `../p19cert_d6/`, because they are the evidence chain behind a
machine-verified theorem and should be readable without unpacking.

## Measurement records

`measurements/` holds the JSON behind every configuration decision:

| file | what it settled |
|---|---|
| `t6census.json` | margin-1 bases for all 56 six-vertex tournaments |
| `break6.json` | live cubes after Aut reduction, top 5 base classes |
| `chosen_config.json` | the winner by live x MEASURED s/cube |
| `maskprobe.json` | 4.5x spread across masks on the SAT route |
| `probe2_results.json` | mask vs Aut-orbit, 61x between/within (DFS route) |
| `probe3_results.json` | five breaks with equal survivors differ 1.81x in cost |
| `price27.json` | Paley(27) priced; its +32% was NOISE, not bias -- see below |
| `p31cfg.json` | a class-76 Paley(31) configuration; superseded, NOT the one run |
| `price31.json` | the Paley(31) configuration competition, 230 single-base measurements over 11 arms |
| `p31_result.json` | the audited Paley(31) verdict: coverage, nodes, core-h |
| `price43_series.json` | the 27/31/43 paired cost series on bit-identical base states |
| `p43_result.json` | the audited Paley(43) verdict; priced 22.9 core-h, ran 22.865 |

Four rankings have now inverted when measured, so none of the cheap proxies is
safe: raw base states, then live cubes, then live x s/cube, and at q=31 the
BASE COUNT itself -- class 12 (4,007 survivors) beat class 76 (2,537) because
each of its bases is ~2x cheaper.  Only `bases x measured s/base` is the
objective.  Details in `../RESEARCH_LOG.md`.

**On `price27.json` reading 32% high.**  That protocol is NOT biased.
Bootstrapping the exact 2008-chunk P27 cost vector gives mean 0.999 of truth at
k=60, but a 90% CI of [0.66, 1.35], because the estimate is dominated by how
many LIVE chunks (674 of 2008) the sample happens to draw.  The +32% was
sampling noise -- which is precisely why price27's RATIO was right while its
ABSOLUTE was not.  Since the base-state list depends only on the labelled mask
and the survivor set only on the reps' within-base indices, mask 217 gives a
bit-identical base-state list and survivor set on every Paley host, so the right
estimator is a cost-weighted PAIRED RATIO against a completed run.  Beware that
single-base probes run under PARTIAL pool load and under-price a saturated run
by ~1.35x; the paired ratio is immune.

## Not tracked

`certs/cover_p19_d6.{cnf,drat,lrat}` (34 MB / 383 MB / 224 MB) are gitignored
and regenerable; their verification output is preserved in
`../p19_coverage_cert.txt`.  The ~440 GB of per-cube LRAT proofs were verified
and discarded by design.
