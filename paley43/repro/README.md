# `repro/` — the reproduction harness

Added by the independent reproduction of arXiv 2607.26690 (see the top of the
[root README](../README.md)). It does not change any proof code in this package.

Every experiment node runs one fixed command — `bash repro/run.sh` — and the environment is a
fixed contract too. Only `run.sh` varies from node to node, so results stay comparable.

| file | role |
|---|---|
| `env.sh` | the fixed contract: `THREADS` cap (8), the nauty `gentourng` and McKay-catalogue paths, `claim`/`metric` log helpers, and a watchdog that samples the run's own RSS and kills it if *it* grows swap by more than 3 GB. Identical on every branch. |
| `run.sh` | the per-node script. Present on each `orx/*` experiment branch, not on `main`, because it is the one thing each node changes. |
| `verify_d0.c` | independent re-derivation of the Paley(43) level-0 premises from the one committed input `paley43/d0_reps.txt`: rebuilds the tournament from quadratic residues, checks all 19,651 representatives have fwd = 543, have trivial stabiliser, and lie in distinct orbits. Shares no code with `dp43.c` / `canon_reps.c`. |
| `verify_ginv.c` | independent check of the one lemma the screen's factor-903 reduction rests on: recomputes G's action on the 3311 cyclic triangles and verifies \|DB(σO₁) ∩ DB(σO₂)\| is invariant over **all 903 σ**, plus the triangle orbit structure. |
| `figures/make_figures.py` | regenerates the report figures from numbers transcribed out of the run logs. |

Both verifiers are standalone:

```sh
cc -O3 -march=native -pthread -o verify_d0   repro/verify_d0.c
cc -O3 -march=native            -o verify_ginv repro/verify_ginv.c
./verify_d0   paley43/d0_reps.txt 8     # ~1 s
./verify_ginv paley43/d0_reps.txt 60    # ~1 s
```

The watchdog's threshold is on swap **growth** measured from the run's own start, not absolute
swap: the laptop this ran on idles at 17–18 GB of swap in use by unrelated applications, so an
absolute threshold fires immediately on a run using 10 MB.
