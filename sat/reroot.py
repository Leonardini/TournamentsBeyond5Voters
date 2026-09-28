#!/usr/bin/env python3
"""Retro-fit the timing-free ROOT (proofs) onto a completed certification.

The proofs root used to hash  f"{ci} {cnf_h} {lrt_h} VERIFIED {dt:.3f} {dc:.3f}"
-- wall-clock included -- so it differed between two identical runs and could
never be reproduced.  The fix removes the timings.  A finished run can be
upgraded WITHOUT RE-SOLVING, because log/k*.log preserved every per-cube
sha256(CNF) and sha256(LRAT) even though the proofs themselves were discarded.

VALIDATION FIRST, then the new value: we rebuild the OLD hashes from the same
log lines and require them to match done/*.json exactly.  If they do, the parse
is faithful and the timing-free variant computed the same way is trustworthy.
If they do not, nothing is emitted.

TWO CHUNK-HASH CONVENTIONS, AND IT MUST NOT ASSUME EITHER.  Runs from before
2026-09-05 wrote the timing-inclusive record into `chunk_hash`; runs after it
write the timing-free one, because that is now what certify_d6 hashes.  This
script originally asserted the OLD convention, so it rejected the parse of every
certificate produced after the fix and reported it as "ROOT does not rebuild" --
a false alarm on correct evidence.  It now DETECTS the convention per chunk and
requires all chunks to agree; a mixed directory is genuine corruption and is
still refused.

  usage: reroot.py <certdir> [expected_cnf_root] [expected_proof_root]
"""
import sys, os, json, glob, hashlib

d = sys.argv[1]
exp_cnf = sys.argv[2] if len(sys.argv) > 2 else None
exp_prf = sys.argv[3] if len(sys.argv) > 3 else None
logs = sorted(glob.glob(os.path.join(d, 'log', '*.log')))
dones = sorted(glob.glob(os.path.join(d, 'done', '*.json')))
print(f"  {d}: {len(logs)} chunk logs, {len(dones)} chunk records")
if len(logs) != len(dones):
    sys.exit("  chunk log/record counts differ -- refusing to proceed")

r_cnf = hashlib.sha256(); r_old = hashlib.sha256(); r_new = hashlib.sha256()
ncube = bad = 0
seen = set()
for lg in logs:
    key = os.path.basename(lg).replace('.log', '.json')
    dn = json.load(open(os.path.join(d, 'done', key)))
    h_cnf = hashlib.sha256(); h_old = hashlib.sha256(); h_new = hashlib.sha256()
    for line in open(lg):
        if line.startswith('#'):
            continue
        rec = line.rstrip('\n')
        p = rec.split()
        if len(p) < 4:
            continue
        ci, cnf_h, lrt_h = p[0], p[1], p[2]
        h_cnf.update((f"{ci} {cnf_h}\n").encode())
        h_old.update((rec + "\n").encode())                       # as originally hashed
        h_new.update((f"{ci} {cnf_h} {lrt_h} VERIFIED\n").encode())  # timing-free
        ncube += 1
    if h_cnf.hexdigest() != dn['chunk_hash_cnf']:
        bad += 1
        if bad <= 3:
            print(f"    PARSE MISMATCH {key}: chunk_hash_cnf")
    elif h_old.hexdigest() == dn['chunk_hash']:
        seen.add('timing-inclusive')
    elif h_new.hexdigest() == dn['chunk_hash']:
        seen.add('timing-free')
    else:
        bad += 1
        if bad <= 3:
            print(f"    PARSE MISMATCH {key}: chunk_hash under either convention")
    r_cnf.update(h_cnf.hexdigest().encode())
    r_old.update(h_old.hexdigest().encode())
    r_new.update(h_new.hexdigest().encode())

print(f"  cubes {ncube:,}   chunk parse mismatches {bad}")
if bad:
    sys.exit("  PARSE NOT FAITHFUL -- no new root emitted")
if len(seen) != 1:
    sys.exit(f"  chunks disagree on the hashing convention ({sorted(seen)}) -- "
             "this directory mixes two runs and no root is meaningful")
conv = seen.pop()
print(f"  chunk_hash convention: {conv}")
# The proofs root that this directory's OWN records commit to.  Naming it from
# the detected convention keeps the comparison honest: a post-2026-09-05 run
# must be checked against its timing-free value, not against one it never wrote.
r_prf = r_old if conv == 'timing-inclusive' else r_new
ok = True
if exp_cnf:
    m = r_cnf.hexdigest() == exp_cnf; ok &= m
    print(f"  ROOT (CNF)  rebuilt  {r_cnf.hexdigest()}  {'MATCHES' if m else '*** DIFFERS'}")
if exp_prf:
    m = r_prf.hexdigest() == exp_prf; ok &= m
    print(f"  ROOT (proofs) rebuilt {r_prf.hexdigest()}  {'MATCHES' if m else '*** DIFFERS'}")
if not ok:
    sys.exit("  rebuilt roots do not match the recorded ones -- no new root emitted")
if conv == 'timing-inclusive':
    print(f"  ROOT (proofs) NEW    {r_new.hexdigest()}   <- timing-free, reproducible on this build")
