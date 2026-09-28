# Paley(19) margin-1 certification -- hash evidence

Per-cube and per-chunk hashes backing the two root hashes in
`../p19_margin1_VERDICT.txt`.  Run of 2026-09-03, 22,876 cubes.

    log/k*.log    one line per cube: index, sha256(CNF), sha256(LRAT proof),
                  verdict, solve seconds, check seconds
    done/k*.json  per chunk: cube count, rolling hash over CNF hashes
                  (chunk_hash_cnf) and over full records (chunk_hash), timings

The proofs themselves were verified and discarded -- ~440 GB was never written.

To re-derive the roots from these files (they must reproduce exactly; this was
checked on 2026-09-03):

    root_cnf = sha256 over chunk_hash_cnf, chunks in ascending `lo` order
    root_all = sha256 over chunk_hash,     same order

ROOT (CNF) is the portable one: regenerate the cube set with certify_d6.py and
you must obtain the same value.  ROOT (proofs) commits to LRAT bytes, which are
NOT portable across solver builds -- a mismatch there is not an error.

## Addendum 2026-09-05 — three roots, and what each is worth

    ROOT (CNF)                 0eeb9dd5...  setup-INDEPENDENT
    ROOT (proofs, timing-free) 8b49aa2d...  same-setup reproducible
    ROOT (proofs, as-run)      ea5f8982...  NOT reproducible — superseded

The as-run proofs root hashed wall-clock timings alongside the proof bytes, so
it differs between two *identical* runs — demonstrated, not merely suspected.
It is kept only so the original output can be matched to this archive.

The timing-free value was recomputed from the per-cube hashes here, with both
recorded roots rebuilt first as a parse check (`../reroot.py`, which refuses to
emit anything unless they match): 115 chunks, 22,876 cubes, 0 mismatches.

ROOT (CNF) was additionally re-derived from scratch by regenerating all 22,876
CNFs (`../verify_p19_root.py`) — 0 per-cube and 0 per-chunk mismatches, root
IDENTICAL. That check needs no solving, so reproducibility costs minutes rather
than the 24 core-h of the original run.

## Combined certificate (2026-09-05) — split AND search in one value

Both halves of the refutation are now established for Paley(19) margin-1: every
cube UNSAT (**search**), and the cube set exhaustive (**split**). Previously
they were certified separately and tied together only by a reader believing two
files described the same run. These two values bind them.

    CERT (portable) 8eb20a1d9e814aabb8782c7d34fd8a436ab52db690852ed856a2b1bbd4c65ffa
    CERT (full)     7e14be9fd4f3d67fdcd383e74383e5244d8f3685f8ff969cdc9159e58af4d894

The hashed blocks are `p19_cert.portable.txt` and `p19_cert.full.txt` — read
them; the root is auditable, not a bare concatenation, and the instance
parameters are inside so a value cannot be matched against a different
instance's artifacts.

`CERT (portable)` commits to the instance, ROOT (CNF), and the coverage CNF —
all regenerable from this repository's code, with no solver involved. Anyone
must obtain it. `CERT (full)` adds ROOT (proofs) and the coverage proof, which
are cadical-build-specific.

The split half was re-established on 2026-09-05 with `cover_check.py --stream`:
143,032 clauses (425 F_B + 356 SB + 142,251 negated cubes), **UNSAT in 7.56 s,
91 MiB LRAT proof verified by lrat-trim**, matching the originally recorded
clause count exactly. The coverage CNF and proof are not kept here — both are
regenerable, and their sha256 are committed inside the cert blocks.

Rebuild with `../certroot.py` (see its docstring for arguments).

## Addendum 2026-09-28 — a CERT-v2 block beside the v1 one

`q=19` names an isomorphism class, not a labelling, while `base`, `arc` and
`non` in the block above are vertex labels. Our `paley(19)` and its converse are
both "Paley(19)" and differ in `adj[0][1]`, so a reproducer using the other sign
convention gets the same VERDICT and a different ROOT. `p19_cert.v2.portable.txt`
closes that by committing to the adjacency itself:

    host_sha256 = 9729da99…  (sha256 of tournaments/p19_paley.bits, canonical
                              bit string, whitespace stripped)
    CERT-v2 portable  989ab61823134ab4ca9ec61a18a9f9466fde69eda259b70a02b5213517278891
    CERT-v2 full      97c6414605d38a1ba72aca789faa98b702c17068c924442a9bcde65ce755eddf

**The v1 values above are unchanged and stay authoritative for anything already
published.** v2 hashes a different block and is not comparable with v1. The
reasoning, and the rebuild command, are in `../CERT-v2.md`.
