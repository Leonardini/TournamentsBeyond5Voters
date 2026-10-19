# d000_mv09 majority certification -- hash evidence

`d000_mv09` is **not 5-inducible**, machine-verified on both halves. It is the
third 22-vertex obstruction behind N(5) <= 22. The search half solved 1,611
cubes, about 732 laptop-equivalent core-hours (Appendix A.6 of the manuscript
explains the conversion of the cluster's share).

The host is the doubly regular tournament `d000` on 23 vertices, line 1 of
McKay's `drtourn23.txt` and `tournaments/drt23/d000.bits`, with vertex 9
(0-based) deleted and the remaining vertices kept in order. The file is
`tournaments/drt23_del/d000_mv09.bits`. The manuscript calls it Delta_1 - 10,
counting both the catalogue line and the vertex from 1.

The margin is plain majority. Every arc of this host lies in a directed
triangle, so by the 3-cycle bound majority equals margin <= 3 here; `VERDICT.txt`
states this in full.

    log/k*.log    one line per cube: index, sha256(CNF), sha256(LRAT proof),
                  verdict, solve seconds, check seconds
    done/k*.json  per chunk of five cubes: cube count, rolling hashes over the
                  CNF hashes (chunk_hash_cnf) and over full records (chunk_hash),
                  timings
    VERDICT.txt   the verdict as the prover wrote it
    coverage/     the coverage CNF and its LRAT refutation (the split half)

The search proofs were verified and discarded. To re-derive both roots from
these files, with no solving:

    python3 sat/reroot.py certificates/d000mv09cert_d6 \
        73f97259ae040e5d6e948417f59aabf79c7dd0b846f3c3dd13f8e72241b9e57a \
        82784e3056e17fd8f300496905126df4f6b90e88e76d012900c3581c275db82c

## One cube per orbit: the quotient, and no anchoring

The automorphism group of `d000_mv09` has order 55. The automorphism

    h = (0,8,7,10,1,2,4,3,9,6,5,20,15,14,18,17,12,21,11,19,13,16)

(h(i) is the i-th entry) has order 5 and maps the base `{11,13,14,18,20}` onto
itself, so it permutes the 8,031 base states, and by Corollary 2.5 it suffices
to solve one per orbit: 1,611. `certify_d6.py --quotient` chose the
representatives. No anchoring is used, so the trust chain holds Corollary 2.5
and Corollary 2.4 (voters may be lex-ordered) and no anchoring lemma; the block
records `anchoring=none` and the `quotient=` line, and
`tools/check_cert_portable.py` checks that h is an automorphism of the host
that maps the base onto itself (`certificates/CERT-v2.md`). The base is
{y1, y3, y4, y5, y9} in the manuscript's labelling of Figure 1, the five
in-neighbours of y0 in Y; it is a different base from the depth-first search's
of Section 3.2, so the two refutations are independent in base as well as in
method.

## How it ran

Chunks of five cubes, CaDiCaL with `--lrat=true --seed=3`, each proof checked by
lrat-trim and then deleted. 140 chunks were solved on the laptop and 183 on the
cluster; a chunk's markers are the same wherever it ran. On 19 October a full
disk corrupted the proofs of two cubes, 638 and 1602, mid-write; lrat-trim
rejected both, so nothing unverified was banked. Their chunks were rerun on the
laptop, the second one cube at a time (`certify_d6.py --only`, folded into its
chunk by the working repository's `assemble_chunks.py`, which reproduces
the chunk hashes exactly). The roots above rebuild from the shipped files, so
none of this history needs to be trusted.

## The split half

    coverage/d000_mv09_cover.cnf    sha256 34e9a46a702dd2860a93c9899075e0500739a917d0ed180f828fe6edd1d6d6cf
    coverage/d000_mv09_coverage.lrat sha256 044ea82bbf3d29e45a31a80484fa59aeb90dceb03c9425db52ed48bbd8e87eb4

The CNF is F_B (200 clauses), the voter lex-ordering (236), and the negation of
every one of the **8,031** base states (not only the 1,611 solved), over 90
variables. It is UNSAT, so the base states cover every lex-ordered base
assignment; Corollary 2.5 is the step from the 8,031 to the 1,611. Unlike the
other certificates here, both coverage files are small enough to ship:

    lrat-trim certificates/d000mv09cert_d6/coverage/d000_mv09_cover.cnf \
              certificates/d000mv09cert_d6/coverage/d000_mv09_coverage.lrat

prints `s VERIFIED`.

## The joint certificate

    CERT-v2 portable  25a3f1da4666cf2138ff7e8822dab81446f0c4e46f3f7be5a6b5cba083447ee4
    CERT-v2 full      5e46c16b2b354d17d5209d35e5cbc0d195825c32e76193d648caef35e35300ac

in `d000mv09_cert.v2.portable.txt` and `d000mv09_cert.v2.full.txt`, committing
to the host

    host_sha256 = 83091cadc92537d59b3944cc48573a7c449e682213ae8e8ff7fce27b18c1f97f
