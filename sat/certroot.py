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

  usage: certroot.py --dir D --cover-cnf F --cover-proof F --q .. --k .. \
                     --margin .. --base .. --arc .. --non .. --cubes N \
                     --root-cnf HEX --root-proofs HEX [--out PREFIX]
"""
import argparse, hashlib, os, sys

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 22), b''):
            h.update(blk)
    return h.hexdigest()

a = argparse.ArgumentParser()
for f in ('dir', 'cover-cnf', 'cover-proof', 'margin', 'root-cnf', 'root-proofs', 'out'):
    a.add_argument('--' + f)
a.add_argument('--q', type=int); a.add_argument('--k', type=int)
a.add_argument('--cubes', type=int)
a.add_argument('--base', nargs='+', type=int)
a.add_argument('--arc', nargs=2, type=int); a.add_argument('--non', nargs=2, type=int)
a = a.parse_args()

for p in (a.cover_cnf, a.cover_proof):
    if not p or not os.path.exists(p):
        sys.exit(f"missing coverage artifact: {p}")
cov_cnf_h = sha256_file(a.cover_cnf)
cov_prf_h = sha256_file(a.cover_proof)

portable_block = (
    "CERT-v1 portable\n"
    f"q={a.q}\nk={a.k}\nmargin={a.margin}\n"
    f"base={','.join(map(str, a.base))}\n"
    f"arc={a.arc[0]},{a.arc[1]}\nnon={a.non[0]},{a.non[1]}\n"
    f"cubes={a.cubes}\n"
    f"search_root_cnf={a.root_cnf}\n"
    f"split_cover_cnf={cov_cnf_h}\n")
cert_portable = hashlib.sha256(portable_block.encode()).hexdigest()

full_block = (
    "CERT-v1 full\n"
    f"cert_portable={cert_portable}\n"
    f"search_root_proofs={a.root_proofs}\n"
    f"split_cover_proof={cov_prf_h}\n")
cert_full = hashlib.sha256(full_block.encode()).hexdigest()

print(portable_block + f"=> CERT (portable) {cert_portable}\n")
print(full_block + f"=> CERT (full)     {cert_full}")
if a.out:
    open(a.out + '.portable.txt', 'w').write(portable_block + f"CERT_PORTABLE={cert_portable}\n")
    open(a.out + '.full.txt', 'w').write(full_block + f"CERT_FULL={cert_full}\n")
    print(f"\nblocks written: {a.out}.portable.txt  {a.out}.full.txt")
