# The three 22-vertex obstructions

The hosts behind **N(5) <= 22**: each is a one-vertex deletion of a 23-vertex
doubly regular tournament, and each is NOT 5-inducible at majority on a
**complete, uncapped cover** of its base states.

    d005_mv04   d005 minus vertex 4    UNSAT  8031/8031  1551.2 core-h  2026-09-26
    d027_mv04   d027 minus vertex 4    UNSAT  8031/8031  1537.7 core-h  2026-10-09
    d000_mv09   d000 minus vertex 9    UNSAT  1611/1611    96.9 core-h  2026-10-17

`d000_mv09` is the paper's Delta_1 - 10 (d000 is Delta_1, line 1 of McKay's
catalogue; vertex 10 in 1-based labels).  Its automorphism group has order 55, so
its cover is over the 1,611 orbit representatives of its 8,031 base states under
an order-5 subgroup H that fixes the base (Corollary 2.5), searched with vertex
anchoring on the two H-fixed vertices (Corollary 2.3).  The representatives and
the markers are in `../d000mv09_screen/` (`xbase.py`, `xbase_reps.txt`,
`xsweep_markers_20261017.tar.gz`); `seconds` here is the sum over the markers.

For the first two, `UNSAT` is `jz_sweep1/aggregate.sh`'s word, and it is not a summary: its awk
emits it only when the markers tile `[0, base_states)` exactly AND `capped == 0`
on every chunk, so the cover is complete and no chunk was budget-limited.

**Why they are copies and not the originals.** `registry.py` indexes whole
directories, and `jz_sweep1/hosts/` mixes orders 21, 22, 25 and 26 -- adding it
wholesale would enter a dozen classes that have no verdict. These files are
byte-identical to their sources, which `check.sh` asserts.

**Triangle load 5, and it could not be anything else.** A DRT(23) has load 6, a
deletion drops the minimum by at most 1, and the ceiling at n = 22 is 5
(mean load 3*c3/C(22,2) = 5.714), so all three are pinned at 5 from both sides.
See `../triangle_load/FINDINGS.md`.

**The parents d005 and d027 are independent**, so these are two separate witnesses to the
bound rather than one result counted twice; their largest common subtournament is
18 of 22, which `../common_subdigraph/` shows is ordinary for the family.
