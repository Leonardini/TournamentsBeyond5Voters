# Why the certificate blocks were re-issued as CERT-v2

*2026-09-28.* Every certificate here now ships in two forms: the published
**CERT-v1** block, unchanged, and a **CERT-v2** block beside it. v2 differs in
one respect that matters — it binds the host by the **sha256 of its adjacency**
rather than by the name of its construction.

## The problem with `q=19`

A v1 block opens `q=19`, and its remaining fields are `base=0,1,2,3,4,11`,
`arc=0,1`, `non=2,1`. Those are **vertex labels**. `q=19` is not: it names an
isomorphism class, which fixes no labelling for them to refer to.

This is not a hypothetical gap. `cube_sat.paley(q)` orients `i -> j` iff
`(j - i) mod q` is a quadratic residue. The other standard sign convention gives
the **converse**, which is equally entitled to be called Paley(19):

    our paley(19)   9729da99a13d3e6ea0d4984f5330e7675acc5daa2c6ecd3de25c5dda0420ebbe
    its converse    31e4fce02812a37fb134d5bb32bb6c78f28fb0c5e9cfb83a82ebe1ab4b38c6a1

`adj[0][1]` differs between them, so `arc=0,1` denotes a different arc under each
and `base=0,1,2,3,4,11` a different induced subtournament. Someone who
reimplements with the other convention **reproduces the verdict** — every
quantity in this work is converse-invariant — and then obtains a different cube
set, a different ROOT (CNF), and so a different `CERT (portable)`. The mismatch
would be manufactured entirely by the certificate's own under-specification, and
it would look exactly like a failed reproduction.

The package already argues this for its data. `CLAIMS.md` closes with it: *"the
numbering is the reason tournaments ship as bit strings rather than being rebuilt
from their constructions. Two of the four 21-vertex tournaments are not in the
canonical labelling a fresh enumeration produces."* The certificate blocks were
simply not holding themselves to the same standard.

## And most hosts have no `q` at all

`h02_f00` is a 21-vertex tournament. 21 is not a prime power, there is no
Paley(21), and no value of `q` describes it. A block that identifies its host by
`q` cannot be written for it — which is why `sat/certroot.py` could not emit one
until now.

## What v2 says instead

    CERT-v2 portable
    host_name=h02_f00
    host_bits=../../tournaments/vt21_arcflip/h02_f00.bits
    host_sha256=a67aa2882d4353ca71ccadd0b59184ff3e5e146eb52bbd37d699d8102e575a64
    host_n=21
    origin=h02 with arc 0->1 reversed ...
    k=5
    margin=exact
    base=0,1,2,3,7,10
    anchoring=none
    cubes=202129
    search_root_cnf=...
    split_cover_cnf=...

* **`host_sha256` is the identity.** It is the sha256 of the host's canonical
  bit string — the upper triangle in `(0,1),(0,2),...,(n-2,n-1)` order, `0`/`1`
  characters only, no trailing newline. Stripping whitespace before hashing makes
  the value a property of the tournament-with-labelling rather than of a file's
  line endings, so a `.bits` file saved with or without a final newline gives the
  same value. `sat/certroot.py --v2` computes it; `tools/check_cert_portable.py`
  re-derives it from the shipped `.bits` and fails if it disagrees.
* **`host_bits`** is a relative path from the block's own directory to a local
  copy, so a reader can check `host_sha256` without reconstructing anything.
* **`host_n`** is recovered from the bit-string length, not asserted.
* **`origin`** carries the provenance in words. `q` survives here, as
  annotation — `origin=paley(19), quadratic-residue convention of
  sat/cube_sat.py paley()` — where it can no longer be mistaken for an
  identifier.
* **`anchoring`** is explicit, and general. See below.

## `anchoring=` — what it is, and why it earns a field

The anchoring representatives do **exactly one thing**: they filter the
enumerated base states down to the live ones. In `sat/certify_d6.py` that is a
single line,

    live = [c for c in cubes if any((B[pi[0]], B[pi[1]]) in PAIRS for pi in c)]

and they reach neither `build()`, nor the CNF, nor `cube_units`. So anchoring
changes *which* subproblems were solved and nothing about any one of them —
which is precisely why the certificate has to record it. Without it, `cubes=22876`
is unexplained, and the search half looks inconsistent with a coverage half that
ranges over all 142,251 base states.

Section 2 gives **two** anchorings, alternatives rather than a sequence, each
without loss of generality on its own, and which is better depends on whether the
host has fewer vertex orbits or fewer ordered-pair orbits:

| lemma | representatives | field |
|---|---|---|
| **Lemma 2.1**, ordered-pair anchoring | one ordered pair from each `Aut`-orbit on ordered pairs; some voter's top two is one of them | `pair-orbit(p1=0,1;p2=2,1)` |
| **Corollary 2.2**, vertex anchoring | one vertex from each `Aut`-orbit on vertices; some voter ranks one of them first | `vertex-orbit(v1=0;v2=3;v3=7)` |
| neither | every base state is live | `none` |

Both take **any number** of representatives. The v1 blocks could express only
the two-representative case, as `arc=`/`non=`, because every host certified so
far was Paley — whose ordered-pair orbits are exactly the arcs and the non-arcs,
so `m = 2`. That is a theorem about Paley, not a property of the format, and a
host with three ordered-pair orbits had no way to say so.

`h02_f00` is rigid: neither lemma applies, all 202,129 base states were run, and
its block reads `anchoring=none` — **a shorter trust chain, stated in the
certificate rather than in a README.**

### Every representative must lie inside the base

The filter reads a *base state*, which knows only each voter's order restricted
to `B`. A representative outside `B` therefore matches nothing: an anchored
witness is filtered **away**, and the refutation goes vacuous — in the direction
that makes a run finish sooner and look like a success.

Nothing checked this before 2026-09-28. Both published Paley certifications
satisfy it — `{0,1} ∪ {2,1} ⊂ {0,1,2,3,4,11}` and `{2,6} ∪ {1,6} ⊂ {0,1,2,5,6,3}`
— which is why it never bit. `sat/certroot.py` and `sat/certify_d6.py` now both
refuse an out-of-base representative, and gate check 3e is the control.

What is **not** checkable from shipped bytes is orbit *completeness* — that the
representatives meet every orbit. The manuscript flags it ("Lemma 2.1 must be
given the full set of orbits") and it stays a human obligation, like the lemma
itself. Recording the representatives in the hashed block is what makes it
auditable instead of implicit. For a pair representative the gate does check the
one thing the host now makes decidable: whether it is an arc or a non-arc,
recomputed from the `.bits`. Under v1's `q=`, it was not decidable at all.

## v1 is frozen

Published v1 values must stay byte-identical, so this is a version bump and not
an edit to how a v1 block is emitted. `p19_cert.portable.txt` still hashes to
`8eb20a1d…` and `p23_cert.portable.txt` to `ff60539e…`; `sat/certroot.py
--from-v1` rebuilds each from its own contents and `--expect-portable` asserts
the published value. Both versions ship, and the gate checks both.

    p19      CERT-v1 portable 8eb20a1d…   CERT-v2 portable 21d94257…
    p23      CERT-v1 portable ff60539e…   CERT-v2 portable b2b5ed32…
    h02_f00  (v1 not expressible)        CERT-v2 portable 0e5da399…

A v2 value is **not** comparable with a v1 value for the same instance: they
hash different blocks, and are meant to.

## Rebuilding them

No solving is involved — every input is a recorded hash or a shipped file:

    python3 sat/certroot.py --v2 --from-v1 certificates/p19cert_d6/p19_cert \
        --host-bits tournaments/p19_paley.bits --host-name p19_paley \
        --origin 'paley(19), quadratic-residue convention of sat/cube_sat.py paley()' \
        --out certificates/p19cert_d6/p19_cert.v2

`--from-v1` lifts `k`, the margin, the base, the anchoring pair, the cube count
and all four component hashes out of the published v1 pair, **after verifying
that both v1 blocks hash to the values they state**. Nothing is retyped, so the
two versions cannot drift apart.
