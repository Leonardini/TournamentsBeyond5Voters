# The nine obstructions on 22 vertices

The hosts behind **N(5) <= 22** (the manuscript's subsection "Eight tournaments on 22 vertices that
five voters cannot produce" and its appendix "The obstructions on 22 vertices").  Eight are one-vertex
deletions of a 23-vertex doubly regular tournament, and the ninth is Delta_1 - 10 with one arc
reversed.  Each is NOT 5-inducible at majority on a **complete, uncapped cover** of its base states
(or of their orbit representatives, where a symmetry reduction applies), and each is vertex-critical.

    host             paper            cover                              core-h       where
    d005_mv04        Delta_6 - 5      8031/8031                          1551.2       cluster
    d027_mv04        Delta_28 - 5     8031/8031                          1537.7       cluster
    d000_mv09        Delta_1 - 10     1611/1611 reps (|Aut| 55)            96.9       laptop
    d000_mv00        Delta_1 - 1      1611/1611 reps (|Aut| 5)            485.6       cluster
    d000_mv01        Delta_1 - 2      1611/1611 reps (|Aut| 5)            436.3       cluster
    d010_mv01        Delta_11 - 2     1611/1611 reps (|Aut| 5)            108.5       laptop
    d010_mv04        Delta_11 - 5     1611/1611 reps (|Aut| 5)            335.2       cluster + laptop
    d010_mv19        Delta_11 - 20    1611/1611 reps (|Aut| 5)            332.3       cluster (state 382 also on the laptop)
    d000mv09_r01_02  Delta_1 - 10,    8031/8031 (rigid)                  2063         cluster + laptop
                     arc 1->2 reversed

`dNNN` is line NNN+1 of McKay's drtourn23.txt and `mvVV` deletes 0-based vertex VV, so the paper's
Delta_i - v is `d(i-1)_mv(v-1)`.  The three deletions of d000 = Delta_1 cover its three vertex orbits
(sizes 11, 11, 1), so every one-vertex deletion of Delta_1 is an obstruction.  Cluster core-hours are
about 3.55 laptop core-hours each for these searches (measured on 355 base states of d010_mv04 run on
both machines); the paper reports laptop-equivalents.

In this package the hosts are `../../tournaments/drt23_del/<host>.bits`, and the marker archives are
the `*markers.tar.zst` files of `../../evidence/` (d027_mv04's markers stay on the cluster).
`tools/check_package.sh` checks these hosts and their covers in its sections 8d, 8e, 8f and 8j.

`seconds` in `verdicts.tsv` is the sum over the markers (for d010_mv04, the faster marker where both
machines ran a state).  These nine rows are the source of the nine 22-vertex classes of
`../verdict_ledger.tsv`, each `majority UNSAT` and therefore `margin1 UNSAT`.

For d005_mv04 and d027_mv04, `UNSAT` is the cluster roll-up's word, and it is not a summary: the
roll-up emits it only when the markers tile `[0, base_states)` exactly AND `capped == 0` on every
chunk, so the cover is complete and no chunk was budget-limited.

**Triangle load 5, and it could not be anything else.** A DRT(23) has load 6, a
deletion drops the minimum by at most 1, and the ceiling at n = 22 is 5
(mean load 3*c3/C(22,2) = 5.714), so all nine are pinned at 5 from both sides.

**The parents d005 and d027 are independent**, so these are two separate witnesses to the
bound rather than one result counted twice; their largest common subtournament is 18 of 22.
