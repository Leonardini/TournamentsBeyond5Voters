# n = 11 five-inducibility census — RESULT (2026-07-22)

**Every 11-vertex tournament is 5-inducible, hence N(5) ≥ 12.**

Full run: 256 slices (gentourng `res/mod 256`), local 8-core, ~4.5 h wall.
Aggregate (from `n11_aggregate.sh`, which asserts per-slice internal consistency
and the completeness identity):

```
slices: 256, all present and internally consistent
total tournaments:             903,753,248   (= D_11, completeness check PASSED)
  unit-margin 3-inducible:        362,587,120
  3-inducible, not unit-margin:    20,038,128
  not 3-inducible:             521,128,000
    unit-margin 5-inducible:      521,128,000   (all witnesses independently verified)
    residual (need ILP):                 0
```

Every non-3-inducible tournament admits a **unit-margin** five-voter profile
(witness found by `cert_m1k5`, re-checked by the independent `verify_m1k5`:
five acyclic voters, every arc backed exactly 3:2). The ILP fallback was never
invoked. Empirical corollary: all non-3-inducible tournaments on n ≤ 11
vertices lie in I_{5,1}.

Per-slice artifacts in `results/`: `w_K.tally1` (3-inducibility scan totals),
`w_K.tally2/.tally3` (5-certification/verification counts), `w_K.residual`
(all empty), `w_K.done` (progress + final line). Reproduce any slice with
`n11_worker.sh K 256` (see README.md; binaries rebuild from
`Paley23Decide/{margin1_scan,cert_m1k5,verify_m1k5}.c` and nauty's gentourng).
