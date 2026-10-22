# Witness extension at 21 vertices (Appendix G, the 19 classes of group `extension19`)

For each open 21-vertex class T and each vertex c, the child T - c is a settled 20-vertex
class.  Its witness (banked, or a settled 21-vertex witness restricted to it) is mapped onto
T - c through an explicit isomorphism (nauty canonical forms to find the class, VF2 for the
map, orders reversed for a converse match), and `extend.c` tries every insertion of c into the
five orders, keeping a hit only if every arc at c has a majority.  This is phase 1 of
Appendix C.2 applied to one fixed witness.  Iterated to a fixed point it settled 15 + 3 + 1
classes; the 19 witnesses are in `evidence/n21_level_witnesses.tar.zst` (group
`extension19`) and are checked by the gate like every other 21-vertex witness (check 8d).

    cc -O2 -o extend extend.c
    python3 drive.py 10            # round 1: banked 20-vertex witnesses
    python3 drive.py 10 --from21   # later rounds: also restrictions of settled 21-vertex witnesses

`drive.py` reads the package's level files and witness archives by absolute path; edit `R`.
