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
* **`anchoring`** is explicit. v1 always had `arc=`/`non=` because every
  certified host so far was Paley, whose automorphism group is transitive on arcs
  and on non-arcs; that is what licenses running only the live cubes (HUMAN LEMMA
  L1). `h02_f00` is rigid, L1 does not apply, and all 202,129 base states were
  run, so its block reads `anchoring=none` — **a shorter trust chain, stated in
  the certificate rather than in a README.**

## v1 is frozen

Published v1 values must stay byte-identical, so this is a version bump and not
an edit to how a v1 block is emitted. `p19_cert.portable.txt` still hashes to
`8eb20a1d…` and `p23_cert.portable.txt` to `ff60539e…`; `sat/certroot.py
--from-v1` rebuilds each from its own contents and `--expect-portable` asserts
the published value. Both versions ship, and the gate checks both.

    p19      CERT-v1 portable 8eb20a1d…   CERT-v2 portable 989ab618…
    p23      CERT-v1 portable ff60539e…   CERT-v2 portable 4f266045…
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
