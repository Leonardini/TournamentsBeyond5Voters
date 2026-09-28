#!/usr/bin/env python3
"""Bind the two halves of a cube-and-conquer refutation into ONE certificate root.

The per-cube roots certify the SEARCH (every cube UNSAT); cover_check certifies
the SPLIT (the cubes are exhaustive).  Certified separately, they were tied
together only by a human reading two files and believing they describe the same
run -- so all 343,896 cube proofs could be reproduced, both roots matched, and
nothing would commit to the cube set having been exhaustive.

This keeps the existing roots untouched and ADDS two overall values, one of each
kind, mirroring the component pair:

    CERT (portable)  = sha256 of a block naming the INSTANCE, ROOT (CNF) and
                       sha256(coverage CNF).  Both inputs are regenerable from
                       this repository's code, so anyone must obtain it.
    CERT (full)      = sha256 of a block naming CERT (portable), ROOT (proofs)
                       and sha256(coverage proof).  Proof bytes are build-
                       dependent, so this reproduces on the same setup.

The hashed blocks are written out verbatim: the root is auditable, not a bare
concatenation, and the parameters are inside it so a value cannot be matched
against a different instance's artifacts.

TWO BLOCK VERSIONS.
-------------------
CERT-v1 names its host as `q=<prime power>`, i.e. "Paley(q)".  That is NOT an
identifier: it names an ISOMORPHISM CLASS, and a certificate's remaining fields
-- `base`, `arc`, `non` -- are vertex labels, which only mean something relative
to a labelling.  `cube_sat.paley(q)` orients i -> j iff (j - i) mod q is a
quadratic residue; the other standard sign convention yields the CONVERSE, is
equally entitled to be called Paley(q), and differs in adj[0][1].  A third party
reimplementing with that convention reproduces the VERDICT -- every quantity
here is converse-invariant -- but obtains a DIFFERENT CNF and so a different
root: a mismatch manufactured by the certificate's own under-specification.
It also cannot describe a host with no q at all, which is most of them.

CERT-v2 therefore commits to the ADJACENCY CONTENT.  `host_sha256` is the
sha256 of the host's canonical .bits string -- the upper triangle in
(0,1),(0,2),...,(n-2,n-1) order, `0`/`1` characters only, no trailing newline,
so the value is a property of the tournament-with-labelling and not of a file's
whitespace.  `host_bits` points at a local copy so a reader can check it, and
`origin` says in words what the host is.  `q` survives inside `origin` as
annotation.

**CERT-v1 IS FROZEN.**  Published v1 values must stay byte-identical, so v2 is a
version bump rather than an edit to how a v1 block is emitted.  Re-running this
script in v1 mode on a published instance must still reproduce its published
CERT_PORTABLE, and `--expect-portable` asserts exactly that.

  usage (v1, unchanged):
    certroot.py --cover-cnf F --cover-proof F --q .. --k .. --margin .. \
                --base .. --arc .. --non .. --cubes N \
                --root-cnf HEX --root-proofs HEX [--out PREFIX]

  usage (v2, from a published v1 pair -- no recomputation, and it re-verifies
  the v1 values it lifts):
    certroot.py --v2 --from-v1 certificates/p19cert_d6/p19_cert \
                --host-bits tournaments/p19_paley.bits \
                --host-name p19_paley --origin 'paley(19)' --out PREFIX

  usage (v2, from scratch; coverage artifacts may be given as hashes, because
  the coverage CNF and proof are deliberately not kept in the repository):
    certroot.py --v2 --host-bits H.bits --host-name N --origin TEXT \
                --k .. --margin .. --base .. [--arc u v --non u v] --cubes N \
                --root-cnf HEX --root-proofs HEX \
                --cover-cnf-sha HEX --cover-proof-sha HEX [--out PREFIX]
"""
import argparse, hashlib, os, sys


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 22), b''):
            h.update(blk)
    return h.hexdigest()


def canonical_bits(path):
    """(n, canonical bit string, sha256 of it) for a .bits host file.

    Whitespace is stripped before hashing, so the identity is the tournament's
    orientation vector and not the file's line endings.  n is RECOVERED from the
    length rather than passed in, so it cannot disagree with the content.
    """
    b = "".join(c for c in open(path).read() if c in "01")
    n = int((1 + (1 + 8 * len(b)) ** 0.5) / 2)
    if n * (n - 1) // 2 != len(b):
        sys.exit(f"{path}: {len(b)} bits is not n(n-1)/2 for any n")
    return n, b, hashlib.sha256(b.encode()).hexdigest()


def read_block(path):
    """A published *.portable.txt / *.full.txt, verified against its own hash.

    The file is the hashed block plus one trailing CERT_PORTABLE= / CERT_FULL=
    line, which makes it self-auditing.  Returns the parsed fields plus the
    stated value, and refuses to return anything if the block does not hash to
    what it claims -- lifting fields out of a corrupted block would carry the
    corruption silently into the new certificate.
    """
    txt = open(path).read()
    tag = 'CERT_PORTABLE=' if 'CERT_PORTABLE=' in txt else 'CERT_FULL='
    if tag not in txt:
        sys.exit(f"{path}: no CERT_PORTABLE= or CERT_FULL= line")
    i = txt.index(tag)
    block, stated = txt[:i], txt[i:].split('=', 1)[1].strip()
    got = hashlib.sha256(block.encode()).hexdigest()
    if got != stated:
        sys.exit(f"{path}: block hashes to {got}, file states {stated}")
    fields = dict(l.split('=', 1) for l in block.strip().split('\n') if '=' in l)
    return fields, stated, block.strip().split('\n')[0]


def build_anchoring(a, n, bits_path):
    """The `anchoring=` field: WHICH cubes were solved, and under which lemma.

    The anchoring representatives do exactly one thing in the prover -- they
    filter the enumerated base states down to the live ones (certify_d6.py, the
    `live = ...` line).  They never reach the CNF.  So this field is what
    explains a `cubes=` count smaller than the host's full base-state count, and
    without it the search half and the coverage half appear to disagree.

    Section 2 gives TWO anchorings, alternatives rather than a sequence, each
    without loss of generality on its own:

      LEMMA 2.1 (ordered-pair anchoring)  one representative ordered pair from
        each Aut-orbit on ordered pairs; some voter's top two is one of them.
          pair-orbit(p1=0,1;p2=2,1)
        A Paley host has exactly TWO such orbits -- the arcs and the non-arcs --
        which is the only case the v1 blocks could express, with `arc=`/`non=`.
        The general form takes m representatives.

      COROLLARY 2.2 (vertex anchoring)  one representative VERTEX from each
        Aut-orbit on vertices; some voter ranks one of them first.
          vertex-orbit(v1=0;v2=3;v3=7)

      and, for a rigid host or any unanchored run,
          none

    EVERY REPRESENTATIVE MUST LIE IN THE BASE, and that is enforced here: the
    filter reads a base state, which knows only the order restricted to B, so a
    representative outside B can never match and an anchored witness would be
    filtered away -- unsoundness in the direction that makes a run finish
    sooner.  Orbit COMPLETENESS -- that the representatives meet every orbit --
    stays a human obligation, as the lemma itself is; recording them here is
    what makes it auditable.
    """
    fams = [x for x in (('pair', [tuple(a.arc), tuple(a.non)]) if a.arc else None,
                        ('pair', [tuple(a.pair_anchor[i:i + 2])
                                  for i in range(0, len(a.pair_anchor or []), 2)])
                        if a.pair_anchor else None,
                        ('vertex', list(a.vertex_anchor)) if a.vertex_anchor else None)
            if x is not None]
    if len(fams) > 1:
        sys.exit("Lemma 2.1 and Corollary 2.2 are ALTERNATIVES, each WLOG on its own.\n"
                 "Give at most one of --arc/--non, --pair-anchor, --vertex-anchor.")
    if not fams:
        return "none"
    kind, reps = fams[0]
    if kind == 'pair' and a.pair_anchor and len(a.pair_anchor) % 2:
        sys.exit("--pair-anchor takes a FLAT list u1 v1 u2 v2 ...; got an odd count")
    flat = [v for p in reps for v in p] if kind == 'pair' else reps
    if any(not 0 <= v < n for v in flat):
        sys.exit(f"anchoring names a vertex outside 0..{n - 1}: {sorted(set(flat))}")
    if len(set(reps)) != len(reps):
        sys.exit("anchoring: repeated representative -- one per orbit, no duplicates")
    if a.base is not None:
        outside = sorted({v for v in flat if v not in a.base})
        if outside:
            sys.exit(f"anchoring names {outside}, outside the base "
                     f"{','.join(map(str, a.base))}.  Anchoring is decided from the "
                     "base state alone, so a representative outside the base filters\n"
                     "anchored witnesses AWAY and the refutation is vacuous.")
    if kind == 'vertex':
        return "vertex-orbit(" + ";".join(f"v{i}={v}" for i, v in enumerate(reps, 1)) + ")"
    if any(u == v for u, v in reps):
        sys.exit("anchoring: an ordered pair must have distinct vertices")
    return "pair-orbit(" + ";".join(f"p{i}={u},{v}"
                                    for i, (u, v) in enumerate(reps, 1)) + ")"


a = argparse.ArgumentParser(add_help=True)
for f in ('dir', 'cover-cnf', 'cover-proof', 'cover-cnf-sha', 'cover-proof-sha',
          'margin', 'root-cnf', 'root-proofs', 'out', 'from-v1',
          'host-bits', 'host-name', 'origin',
          'expect-portable', 'expect-full'):
    a.add_argument('--' + f)
a.add_argument('--v2', action='store_true',
               help='emit a CERT-v2 block (host bound by sha256 of its .bits)')
a.add_argument('--q', type=int); a.add_argument('--k', type=int)
a.add_argument('--cubes', type=int)
a.add_argument('--base', nargs='+', type=int)
a.add_argument('--arc', nargs=2, type=int); a.add_argument('--non', nargs=2, type=int)
a.add_argument('--pair-anchor', nargs='+', type=int, metavar='U V',
               help='Lemma 2.1 in general form: a flat list u1 v1 u2 v2 ... of one '
                    'representative ordered pair per Aut-orbit on ordered pairs')
a.add_argument('--vertex-anchor', nargs='+', type=int, metavar='V',
               help='Corollary 2.2 instead: one representative VERTEX per Aut-orbit '
                    'on vertices')
a = a.parse_args()

# ---------------------------------------------------------------- lift v1
# Values published in a v1 pair are the authority for that instance; retyping
# them here would put a second copy of every hash in play.
if a.from_v1:
    pf, p_stated, p_hdr = read_block(a.from_v1 + '.portable.txt')
    ff, f_stated, f_hdr = read_block(a.from_v1 + '.full.txt')
    if ff.get('cert_portable') != p_stated:
        sys.exit(f"{a.from_v1}: the full block names a different portable cert")
    print(f"lifted from {a.from_v1}.{{portable,full}}.txt -- both blocks "
          f"recompute from their own contents")
    print(f"  {p_hdr}  CERT_PORTABLE={p_stated}")
    print(f"  {f_hdr}      CERT_FULL={f_stated}\n")
    if a.k is None:          a.k = int(pf['k'])
    if a.margin is None:     a.margin = pf['margin']
    if a.base is None:       a.base = [int(x) for x in pf['base'].split(',')]
    if a.cubes is None:      a.cubes = int(pf['cubes'])
    if a.root_cnf is None:   a.root_cnf = pf['search_root_cnf']
    if a.cover_cnf_sha is None and not a.cover_cnf:
        a.cover_cnf_sha = pf['split_cover_cnf']
    if a.arc is None and 'arc' in pf:
        a.arc = [int(x) for x in pf['arc'].split(',')]
    if a.non is None and 'non' in pf:
        a.non = [int(x) for x in pf['non'].split(',')]
    if a.q is None and 'q' in pf: a.q = int(pf['q'])
    if a.root_proofs is None:     a.root_proofs = ff['search_root_proofs']
    if a.cover_proof_sha is None and not a.cover_proof:
        a.cover_proof_sha = ff['split_cover_proof']

# ------------------------------------------------- the coverage components
# Hash the artifacts when they are here; take the recorded hash when they are
# not.  The coverage CNF and proof are bulk and regenerable, so the package
# deliberately keeps only their sha256 -- which is precisely enough to rebuild
# the certificate without a solver.
def component(path, given, what):
    if path:
        if not os.path.exists(path):
            sys.exit(f"missing coverage artifact: {path}")
        h = sha256_file(path)
        if given and given != h:
            sys.exit(f"{what}: {path} hashes to {h}, but {given} was asserted")
        return h, f"hashed {path}"
    if given:
        return given, "recorded hash (artifact not shipped)"
    sys.exit(f"need --{what} or --{what}-sha")

cov_cnf_h, cov_cnf_src = component(a.cover_cnf, a.cover_cnf_sha, 'cover-cnf')
cov_prf_h, cov_prf_src = component(a.cover_proof, a.cover_proof_sha, 'cover-proof')

# ------------------------------------------------------------ build blocks
if not a.v2:
    portable_block = (
        "CERT-v1 portable\n"
        f"q={a.q}\nk={a.k}\nmargin={a.margin}\n"
        f"base={','.join(map(str, a.base))}\n"
        f"arc={a.arc[0]},{a.arc[1]}\nnon={a.non[0]},{a.non[1]}\n"
        f"cubes={a.cubes}\n"
        f"search_root_cnf={a.root_cnf}\n"
        f"split_cover_cnf={cov_cnf_h}\n")
    full_header = "CERT-v1 full\n"
else:
    for need, flag in ((a.host_bits, '--host-bits'), (a.host_name, '--host-name'),
                       (a.origin, '--origin')):
        if not need:
            sys.exit(f"CERT-v2 requires {flag}")
    host_n, _, host_sha = canonical_bits(a.host_bits)
    if a.q is not None and host_n != a.q:
        sys.exit(f"--q {a.q} disagrees with the host's n={host_n}")
    # The recorded path is DERIVED from where the block is written, so the two
    # cannot drift; with no --out it is relative to the working directory.
    ref_dir = os.path.dirname(os.path.abspath(a.out)) if a.out else os.getcwd()
    host_ref = os.path.relpath(os.path.abspath(a.host_bits), ref_dir)
    # ...and immediately followed back, so a block never ships a path that does
    # not resolve to the host it commits to.
    if canonical_bits(os.path.join(ref_dir, host_ref))[2] != host_sha:
        sys.exit(f"{host_ref} does not resolve to the host from {ref_dir}")
    if (a.arc is None) != (a.non is None):
        sys.exit("--arc and --non must be given together")
    anchoring = build_anchoring(a, host_n, a.host_bits)
    portable_block = (
        "CERT-v2 portable\n"
        f"host_name={a.host_name}\n"
        f"host_bits={host_ref}\n"
        f"host_sha256={host_sha}\n"
        f"host_n={host_n}\n"
        f"origin={a.origin}\n"
        f"k={a.k}\nmargin={a.margin}\n"
        f"base={','.join(map(str, a.base))}\n"
        f"anchoring={anchoring}\n"
        f"cubes={a.cubes}\n"
        f"search_root_cnf={a.root_cnf}\n"
        f"split_cover_cnf={cov_cnf_h}\n")
    full_header = "CERT-v2 full\n"

cert_portable = hashlib.sha256(portable_block.encode()).hexdigest()

full_block = (
    full_header +
    f"cert_portable={cert_portable}\n"
    f"search_root_proofs={a.root_proofs}\n"
    f"split_cover_proof={cov_prf_h}\n")
cert_full = hashlib.sha256(full_block.encode()).hexdigest()

print(f"coverage CNF   {cov_cnf_h}  [{cov_cnf_src}]")
print(f"coverage proof {cov_prf_h}  [{cov_prf_src}]\n")
print(portable_block + f"=> CERT (portable) {cert_portable}\n")
print(full_block + f"=> CERT (full)     {cert_full}")

# --------------------------------------------------------------- assertions
# A rebuild is only a regression test if it is allowed to fail.
bad = 0
for got, want, what in ((cert_portable, a.expect_portable, 'CERT (portable)'),
                        (cert_full, a.expect_full, 'CERT (full)')):
    if want:
        if got == want:
            print(f"\nOK   {what} reproduces the asserted {want}")
        else:
            print(f"\nFAIL {what} is {got}, asserted {want}")
            bad += 1

if a.out:
    open(a.out + '.portable.txt', 'w').write(portable_block + f"CERT_PORTABLE={cert_portable}\n")
    open(a.out + '.full.txt', 'w').write(full_block + f"CERT_FULL={cert_full}\n")
    print(f"\nblocks written: {a.out}.portable.txt  {a.out}.full.txt")
sys.exit(1 if bad else 0)
