# Paley(23) majority certification — hash evidence

Run of 2026-09-05, 343,896 cubes, 228.3 core-h solve + 7.7 core-h check,
21.72 h wall on 11 workers. Verdict and both roots in `VERDICT.txt`.

    log/k*.log    one line per cube: index, sha256(CNF), sha256(LRAT proof),
                  verdict, solve seconds, check seconds
    done/k*.json  per chunk: cube count, rolling hash over CNF hashes
                  (chunk_hash_cnf) and over full records (chunk_hash), timings

The proofs themselves were verified by `lrat-trim` and discarded — the LRAT
bytes were never retained. Their sha256 survives here, which is what makes the
proofs root re-derivable without re-solving.

## Three roots, and what each is worth

    ROOT (CNF)                 7e6c9c26...  setup-INDEPENDENT
    ROOT (proofs, timing-free) 01e52ba5...  same-setup reproducible
    ROOT (proofs, as-run)      fccd41d0...  NOT reproducible — superseded

`ROOT (CNF)` commits to the CNFs, i.e. *which* problems were solved. Anyone
regenerating the cube set must obtain it, on any machine with any
implementation.

`ROOT (proofs, timing-free)` adds the LRAT bytes. cadical is deterministic on a
fixed binary, so a re-run on this build must reproduce it; a different version
or architecture may emit a different, equally valid proof, and a mismatch there
is not an error.

`ROOT (proofs, as-run)` is what the run printed. Its per-cube record folded in
wall-clock timings, so it differs between two *identical* runs — demonstrated,
not merely suspected: the same two cubes solved twice under that code gave
`0e42a231ad0323d8...` and `95315066219b8aa2...`. It is kept only so the
original output can be matched to this archive.

## Re-deriving any of them

    python3 ../reroot.py <certdir> <expected_cnf_root> <expected_old_proof_root>

`reroot.py` rebuilds the two recorded roots from these logs *first* and refuses
to emit the timing-free value unless both match, so a faithful parse is proved
before anything new is claimed. On this archive: 1,720 chunks, 343,896 cubes,
0 parse mismatches, both recorded roots reproduced.

## Not included

`cover.cnf` (~800 MB) is regenerable by `cover_check.py` and is not kept.

## Combined certificate (2026-09-05 18:29) — split AND search in one value

Both halves are established: every cube UNSAT (**search**), and the cube set
exhaustive (**split**). They were previously certified separately and tied
together only by a reader believing two files described the same run.

    CERT (portable) ff60539e16abf2ecdc1fc822dbb2379abe52fe06f076fe4cf1003bb56ec3bb9e
    CERT (full)     0d017c747352bd5ea701e9daafcc48a4378a2eec812096540bec2bc73d43df74

Blocks in `p23_cert.portable.txt` / `p23_cert.full.txt` — read them; the root is
auditable rather than a bare concatenation, and the instance parameters sit
inside, so a value cannot be matched against a different instance's artifacts.

The split half: 3,415,435 clauses = 350 F_B + 356 SB + 3,414,729 negated cubes,
UNSAT in 1,182.95 s, 2.05 GiB LRAT proof verified by lrat-trim, peak RSS 5.6 GB
with swap unmoved. Note it sees **all** base states — the arc/non filter reduces
the *search* half to 343,896 live cubes, but coverage must consider every one of
the 3,414,729, which is the whole point of it.

It needs `cover_check.py --stream`: the in-memory path holds every clause as
Python lists (~9 GB here) and was killed at 8.99 GB.

Coverage CNF and proof are not kept — 0.78 GiB and 2.05 GiB, both regenerable,
and their sha256 are committed inside the cert blocks.

**Total running time on one laptop: 21.72 h (search) + 0.39 h (split) = 22.11 h.**
