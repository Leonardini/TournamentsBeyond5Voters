# The two 22-vertex obstructions

The hosts behind **N(5) <= 22**: each is a one-vertex deletion of a 23-vertex
doubly regular tournament, and each is NOT 5-inducible at majority on a
**complete, uncapped cover** of all 8,031 base states.

    d005_mv04   d005 minus vertex 4    UNSAT  8031/8031  1551.2 core-h  2026-09-26
    d027_mv04   d027 minus vertex 4    UNSAT  8031/8031  1537.7 core-h  2026-10-09

`UNSAT` here is `jz_sweep1/aggregate.sh`'s word, and it is not a summary: its awk
emits it only when the markers tile `[0, base_states)` exactly AND `capped == 0`
on every chunk, so the cover is complete and no chunk was budget-limited.

**Why they are copies and not the originals.** `registry.py` indexes whole
directories, and `jz_sweep1/hosts/` mixes orders 21, 22, 25 and 26 -- adding it
wholesale would enter a dozen classes that have no verdict. These two files are
byte-identical to their sources, which `check.sh` asserts.

**Triangle load 5, and it could not be anything else.** A DRT(23) has load 6, a
deletion drops the minimum by at most 1, and the ceiling at n = 22 is 5
(mean load 3*c3/C(22,2) = 5.714), so both are pinned at 5 from both sides.
See `../triangle_load/FINDINGS.md`.

**The two parents are independent**, so these are two separate witnesses to the
bound rather than one result counted twice; their largest common subtournament is
18 of 22, which `../common_subdigraph/` shows is ordinary for the family.
