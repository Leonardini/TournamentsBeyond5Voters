# h02_f00 unit-margin certification -- hash evidence

`h02_f00` is **not 5-inducible at unit margin**, machine-verified on both
halves. Run of 2026-09-27/28, 202,129 cubes, 224.4 core-h on 9 workers
(217.1 solve + 7.3 check, 25.09 h wall).

The host is the 21-vertex obstruction `h02` with the single arc `0 -> 1`
reversed -- orbit 00 of its ten arc orbits, `tournaments/vt21_arcflip/h02_f00.bits`
and the `h02_f00` row of `tournaments/vt21_arcflip/manifest.tsv`. It is the
first letter of the `h₂` spectrum string `USUSSUUSSU` in `CLAIMS.md` row F2:
that letter was established by the DFS engine, and is now re-established with
proofs.

    log/k*.log    one line per cube: index, sha256(CNF), sha256(LRAT proof),
                  verdict, solve seconds, check seconds
    done/k*.json  per chunk: cube count, rolling hash over CNF hashes
                  (chunk_hash_cnf) and over full records (chunk_hash), timings
    VERDICT.txt   the verdict as the prover wrote it

The proofs themselves were verified and discarded. To re-derive both roots from
these files -- no solving, seconds:

    python3 sat/reroot.py certificates/h02f00cert_d6 \
        f99d11d9c443859fbb1d14bf18fea991bcb46160740265258937f3657c366dfa \
        e64aa8ce5d0062665035d40d1cba5ab00ef9c0b5e7f3a6341acde5a885e59994

    root_cnf = sha256 over chunk_hash_cnf, chunks in ascending `lo` order
    root_all = sha256 over chunk_hash,     same order

This run writes the **timing-free** `chunk_hash` (artifacts only, no stopwatch),
so its ROOT (proofs) is reproducible on a fixed cadical build -- unlike the
pre-2026-09-05 Paley runs, whose archives hold the timing-inclusive variant and
whose published proofs root was retro-fitted. `reroot.py` detects which
convention a directory uses and refuses one that mixes both.

## Two things are shorter here than for Paley(19)

**No anchoring, so no anchoring lemma is in the trust chain.** Both forms buy a
reduction only when `Aut` has few orbits -- Lemma 2.1 needs one representative
ordered pair per orbit on ordered pairs, Corollary 2.2 one vertex per orbit on
vertices. `h02_f00` is **rigid**, so every orbit is a singleton, a full set of
representatives is everything, and neither lemma removes a single base state.
**All 202,129 were run**, roughly six times the cube count a Paley-style
two-orbit break would have given. Only Lemma 2.3 (voters may be lex-ordered)
remains human. The block records this as `anchoring=none`, which is a statement
that the lemma is ABSENT from the chain, not merely satisfied.

**No `q`.** 21 is not a prime power, so no CERT-v1 block can be written for this
host at all; see `../CERT-v2.md`. This certificate exists only in v2.

    CERT-v2 portable  0e5da399d031c20dcf73b3ccd71ab41d4b15af97241015858c54056241d95f1c
    CERT-v2 full      e6dd99e3879e0a8f8310d8366d5c76f9d05fd1a5d12f46f301a51cc76a568115

in `h02f00_cert.v2.portable.txt` and `h02f00_cert.v2.full.txt`, and the host it
commits to is

    host_sha256 = a67aa2882d4353ca71ccadd0b59184ff3e5e146eb52bbd37d699d8102e575a64

`CERT (portable)` commits to the host's adjacency, the instance, ROOT (CNF) and
the coverage CNF -- all regenerable from this repository's code with no solver,
so anyone must obtain it. `CERT (full)` adds ROOT (proofs) and the coverage
proof, which are cadical-build-specific.

## The split half

Certified separately and bound in by `split_cover_cnf` / `split_cover_proof`;
the verification output is `../h02f00_coverage_cert.txt`. The coverage CNF and
proof are bulk and regenerable and are not kept here, which is the same policy
`../p19_coverage_cert.txt` records for Paley(19).

## One thing the negative control did NOT cover

`cover_check.py --drop` was deliberately not run. Coverage UNSAT already
establishes that nothing bypasses the cubes; the control's only role would be to
exclude a vacuous certificate, and vacuity here would require `F_B & SB` to be
unsatisfiable -- i.e. the 6-vertex base not 5-inducible -- contradicting
N(5) >= 12. `VERDICT.txt` states this in full.

## A stale line in VERDICT.txt, deliberately not edited

`VERDICT.txt` is reproduced as the prover wrote it, and it contradicts itself
once: the closing "Remaining HUMAN lemmas" list names both L1 and L2, while its
own `anchoring` line five lines above correctly says L1 **is not used** here.
That list was unconditional boilerplate. `sat/certify_d6.py` now builds it from
what the run actually did, so a future rigid-host verdict says
"NO anchoring lemma is used"; this file is left alone because re-stamping it
would rewrite a prover's output after the fact. The `anchoring` line and this
README are right, and `anchoring=none` inside the CERT-v2 block is the value
that is hashed.
