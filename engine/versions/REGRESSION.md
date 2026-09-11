# The consolidated engine against the versions that produced the results

`REPRODUCE.md` closes by citing this file, and until 2026-09-11 it did not
exist: the node-for-node agreement it promised had never been run, let alone
recorded. This is that run.

## What is compared, and why it is the node counts

`kinduce.c` is a **consolidation**. Not one published number in the paper was
produced by it — each result names its original version in `REPRODUCE.md`, and
those 24 sources are in this directory. *Verdicts* would agree under any correct
implementation, which is the claim the paper actually makes, so agreeing on
verdicts alone would be weak evidence that the consolidation preserved the
search. The node counts are the sharper test: they pin the tie-breaking rule,
the dynamic variable order and the incremental domain refinement, any of which
can differ silently between two programs that reach the same verdict.

So every counter on the `RESULT` line is compared except `time=` — `nodes`,
`sols`, `base_states`, `dom_calls`, `dom_nodes`, `mrv_fails`, `top0_fails`,
`bound_fails`, `fas_fails`, `refine_tuples` — together with the `SLICE` line's
`capped=`, and `BATCH_SUMMARY` for the batch-mode case.

Each case is the **published command line of `REPRODUCE.md`** with its
base-state range narrowed. Narrowing is sound because base states are
independent: that is the same fact every distributed run in this project rests
on. Where an anchor kills every base state in the cheap window, the comparison
is still substantive, because `dom_nodes` and `top0_fails` then carry it — the
P23 anchor-A case does 2,281,621 domain nodes while returning `nodes=200`.

## How to re-run it

    sh regression.sh            # all eleven cases, about nine minutes
    sh regression.sh --fast     # the five that finish in about a second

In the reproduction package the script is `engine/regression.sh`; in the working
repository it is `KInduceDFS/regression.sh`. It resolves the engine source and
the `.bits` hosts from either layout and says which it could not find rather
than letting the compiler report `no input files`.

`tools/check_package.sh` check 12 runs the fast subset on every gate pass.

## The run

Recorded 2026-09-11, Apple M-series laptop, `cc -O2` (with `-w` for the
historical sources, several of which predate a warning-free build).

```
consolidated kinduce.c vs the version that produced each published result
compared: every counter on the RESULT line except time=, plus capped=

  ok    P23 anchor A, N(5) <= 23                 kinduce16
          capped=0
          RESULT UNSAT nodes=200 sols=0 base_states=8031 dom_calls=3600 dom_nodes=2281621 mrv_fails=0 top0_fails=200 bound_fails=0 fas_fails=0/0 refine_tuples=0 
  ok    P23 anchor B, a different break          kinduce22
          capped=0
          RESULT UNSAT nodes=184 sols=0 base_states=16118 dom_calls=3360 dom_nodes=1978560 mrv_fails=0 top0_fails=184 bound_fails=0 fas_fails=0/0 refine_tuples=0 
  ok    P27 not 5-inducible                      kinduce22
          capped=0
          RESULT UNSAT nodes=4 sols=0 base_states=8031 dom_calls=88 dom_nodes=54049 mrv_fails=0 top0_fails=4 bound_fails=0 fas_fails=0/0 refine_tuples=0 
  ok    P31 not 5-inducible                      kinduce22
          capped=0
          RESULT UNSAT nodes=90560 sols=0 base_states=21009 dom_calls=78 dom_nodes=43794 mrv_fails=166766 top0_fails=13931 bound_fails=0 fas_fails=0/0 refine_tuples=289821205 
  ok    P43 - v, not vertex-critical             kinduce24
          capped=0
          RESULT UNSAT nodes=1030175 sols=0 base_states=8031 dom_calls=37 dom_nodes=21949 mrv_fails=2117729 top0_fails=66375 bound_fails=0 fas_fails=0/0 refine_tuples=6775141947 
  ok    P31 - v, not vertex-critical             kinduce24
          capped=0
          RESULT UNSAT nodes=651014 sols=0 base_states=8031 dom_calls=25 dom_nodes=14054 mrv_fails=1373156 top0_fails=16376 bound_fails=0 fas_fails=0/0 refine_tuples=1865128969 
  ok    P19 unit margin, certified half          kinduce24
          capped=0
          RESULT UNSAT nodes=20243855 sols=0 base_states=2200 dom_calls=140 dom_nodes=52947 mrv_fails=29564583 top0_fails=0 bound_fails=0 fas_fails=0/0 refine_tuples=4499596203 
  ok    dr19_g2 unit margin                      kinduce24
          capped=0
          RESULT UNSAT nodes=12432866 sols=0 base_states=2200 dom_calls=140 dom_nodes=52689 mrv_fails=17591286 top0_fails=0 bound_fails=0 fas_fails=0/0 refine_tuples=2704652476 
  ok    margin-1 family, P23 - v cell            kinduce24
          capped=0
          RESULT UNSAT nodes=7019826 sols=0 base_states=4677 dom_calls=340 dom_nodes=95796 mrv_fails=9776186 top0_fails=0 bound_fails=0 fas_fails=0/0 refine_tuples=2321116768 
  ok    P23 - v IS 5-inducible (witness)         kinduce21
          capped=0
          RESULT SAT nodes=8507042 sols=1 base_states=8031 dom_calls=17 dom_nodes=8590 mrv_fails=16120409 top0_fails=1120359 bound_fails=0 fas_fails=0/0 refine_tuples=8829045374 
  ok    regular n=15, batch mode                 kinduce20
          BATCH_SUMMARY n=15 K=5 margin=exact1 order=mrv instances=40 SAT=40 UNSAT=0 ABORTED=0 

passed 11   failed 0   skipped 0
```

## Coverage of the versions

Five distinct historical versions produced the paper's results, and all five are
exercised above:

| version | results it produced | cases here |
|---|---|---|
| `kinduce16` | Paley(23), anchor A | 1 |
| `kinduce20` | the regular-tournament batch sweeps | 1 |
| `kinduce21` | the Paley(23) − v witness | 1 |
| `kinduce22` | Paley(23) anchor B, Paley(27), Paley(31) | 3 |
| `kinduce24` | Paley(43) − v, Paley(31) − v, the margin-1 family, dr19_g2 | 5 |

`kinduce25.c` is **excluded from the reproduction package** and from this table:
its `--pin` machinery produced no published result, and the consolidated engine
was built from `kinduce24` rather than by stripping it.

## The one positive case

Ten of the eleven comparisons are refutations, and a bug that lost witnesses
would agree with itself across all ten. The `P23 - v IS 5-inducible` case is
there for that reason: it is the slice, `[6560,6564)`, that actually produced the
published Paley(23) − v witness, and both binaries must find it and report the
same 8,507,042 nodes on the way.
