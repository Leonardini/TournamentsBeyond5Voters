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

  usage: reroot.py <certdir> [expected_old_cnf_root] [expected_old_proof_root]
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
    if h_cnf.hexdigest() != dn['chunk_hash_cnf'] or h_old.hexdigest() != dn['chunk_hash']:
        bad += 1
        if bad <= 3:
            print(f"    PARSE MISMATCH {key}")
    r_cnf.update(h_cnf.hexdigest().encode())
    r_old.update(h_old.hexdigest().encode())
    r_new.update(h_new.hexdigest().encode())

print(f"  cubes {ncube:,}   chunk parse mismatches {bad}")
if bad:
    sys.exit("  PARSE NOT FAITHFUL -- no new root emitted")
ok = True
if exp_cnf:
    m = r_cnf.hexdigest() == exp_cnf; ok &= m
    print(f"  ROOT (CNF)  rebuilt  {r_cnf.hexdigest()}  {'MATCHES' if m else '*** DIFFERS'}")
if exp_prf:
    m = r_old.hexdigest() == exp_prf; ok &= m
    print(f"  ROOT (proofs) old    {r_old.hexdigest()}  {'MATCHES' if m else '*** DIFFERS'}")
if not ok:
    sys.exit("  rebuilt roots do not match the recorded ones -- no new root emitted")
print(f"  ROOT (proofs) NEW    {r_new.hexdigest()}   <- timing-free, reproducible on this build")
