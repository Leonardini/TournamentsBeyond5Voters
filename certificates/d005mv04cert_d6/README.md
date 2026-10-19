# d005_mv04 majority certification -- hash evidence

`d005_mv04` is **not 5-inducible**, machine-verified on both halves, so
N(5) <= 22. The run took 742,374 cubes and 1,292.7 core-h on 11 workers
(1,254.9 solve + 37.8 check, about 118 h of wall clock over three
invocations).

The host is the doubly regular tournament `d005` on 23 vertices, line 6 of
McKay's `drtourn23.txt` and `tournaments/drt23/d005.bits`, with vertex 4
(0-based) deleted and the remaining vertices kept in order. The file is
`tournaments/drt23_del/d005_mv04.bits`. The manuscript calls it Delta_6 - 5,
counting both the catalogue line and the vertex from 1.

The margin is plain majority (every arc carried by at least 3 of 5 voters). By
the 3-cycle bound every arc of this host lies in a directed triangle, so no arc
can be unanimous and majority equals margin <= 3 here. `VERDICT.txt` states
this in full.

    log/k*.log    one line per cube: index, sha256(CNF), sha256(LRAT proof),
                  verdict, solve seconds, check seconds
    done/k*.json  per chunk: cube count, rolling hash over CNF hashes
                  (chunk_hash_cnf) and over full records (chunk_hash), timings
    VERDICT.txt   the verdict as the prover wrote it

The proofs themselves were verified and discarded. To re-derive both roots from
these files, with no solving, in seconds:

    python3 sat/reroot.py certificates/d005mv04cert_d6 \
        f5ea8bf78c29405bdcd0c685ef032bf5ab01a6885d699b05b53e5d6abc386266 \
        6e20fa618d3a139fcbc0e6668f87c6ed64e65d8fd3e31a8276f0087923ac96fe

This run writes the timing-free `chunk_hash`, so its ROOT (proofs) is
reproducible on a fixed cadical build.

## No anchoring, so no anchoring lemma is in the trust chain

`d005_mv04` has no non-trivial automorphism, so every orbit is a singleton and
neither Corollary 2.2 nor Corollary 2.3 removes a single base state. **All 742,374
base states of the base `{0,1,2,3,11,17}` were run.** Only Corollary 2.4 (voters
may be lex-ordered) remains human, and the block records `anchoring=none`.
The same rigidity is why this is the most expensive of the four certificates
here, although its host is smaller than Paley(23).

## The joint certificate

    CERT-v2 portable  043a6488483235bb447a9073a153b178eea2ce4cf7b34970c1597567ba0c1a11
    CERT-v2 full      915c06d23d0b4b817dafc6ea837657a6081d78d0f61469f1ba270fd0b96725b6

in `d005mv04_cert.v2.portable.txt` and `d005mv04_cert.v2.full.txt`, committing
to the host

    host_sha256 = d7c871ea57c9e5cbf5938eeb86a61c7475738c1a740fd7aef0e937b6de8e179d

There is no CERT-v1 block: 22 is not a prime power, so no `q` names this host.
`CERT (portable)` commits to the host's adjacency, the instance, ROOT (CNF) and
the coverage CNF, all regenerable from this repository's code with no solver.
`CERT (full)` adds ROOT (proofs) and the coverage proof, which are
cadical-build-specific.

## The split half

Certified separately and bound in by `split_cover_cnf` / `split_cover_proof`:
743,080 clauses (350 base constraints + 356 symmetry breaking + 742,374 negated
cubes), UNSAT in 82.81 s on one core, a 422 MiB LRAT proof verified by
`lrat-trim`. The verification output is `../d005mv04_coverage_cert.txt`. The
coverage CNF (183 MB) and proof (442 MB) are regenerable in about 7 minutes and
are not kept, the policy `../p19_coverage_cert.txt` records for Paley(19).

## Two lines in VERDICT.txt to read with care

The `wall 73.55 h ... CUMULATIVE over all invocations` line covers the third
invocation only. The wall total is banked when a run completes, and the first
two (about 0.6 h and 44.4 h, the second ended by a laptop restart) never did.
The core-hours are summed from the 3,712 chunk records and are complete;
1,292.7 / 11 = 117.5 h agrees with the true total of about 118 h.

The `--drop` negative control was deliberately not run, for the reason
`VERDICT.txt` gives: vacuity would need the 6-vertex base itself to be
non-inducible, contradicting N(5) >= 12.
