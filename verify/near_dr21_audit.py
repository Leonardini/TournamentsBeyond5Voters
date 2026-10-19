#!/usr/bin/env python3
"""The 25 near-doubly-regular tournaments on 21 vertices that five voters can produce, but
not at unit margin (Section 3.7, Appendix G), audited from the shipped bytes.

    usage: near_dr21_audit.py DIR COVERS.tar.zst [--drop HOST] [--flip HOST]

DIR is verdicts/near_dr21/: one <host>.bits per class and out/<host>.majority.txt, its
majority witness.  COVERS is the archive of each host's unit-margin search: cover/<host>/
REPS.txt, the base states the search had to exhaust, and one marker per state.  For each
host this checks:

  * the host is near-doubly regular: regular, and every two vertices have 4 or 5 common
    out-neighbours;
  * the witness is a majority witness for THIS host (verify_witness_bits.py --majority);
  * the unit-margin search is complete: every state in REPS.txt has a marker reading
    `RESULT UNSAT ... base_states=2200` and `SLICE cleared=1 capped=0`, there is no
    marker for any other state, and REPS.txt has the size its quotient gives: 444 of 2,200
    for the 20 order-5 gluings (Corollary 2.5), all 2,200 for zf21_0 and zf21_1 (no
    quotient), 600 for the three zr21 hosts (the sub-base quotient, Corollary 2.6).

The representative lists come from the campaign's own quotient scripts, shipped beside
the hosts as provenance; this audit does not rerun them.  Controls: --drop HOST removes
one marker of HOST and --flip HOST reverses one arc of HOST; each must make the audit fail.
"""
import io, os, re, subprocess, sys, tarfile, tempfile

args = sys.argv[1:]
drop = flip = None
for opt in ('--drop', '--flip'):
    if opt in args:
        i = args.index(opt); v = args[i + 1]; del args[i:i + 2]
        drop, flip = (v, flip) if opt == '--drop' else (drop, v)
D, arc = args
HERE = os.path.dirname(os.path.abspath(__file__))
expect = lambda h: 444 if h.startswith('g21_') else 2200 if h.startswith('zf21_') else 600

raw = subprocess.run(['zstd', '-dc', arc], capture_output=True, check=True).stdout
tf = tarfile.open(fileobj=io.BytesIO(raw))
cov = {}
for m in tf:
    if m.isfile():
        _, h, f = m.name.split('/')
        cov.setdefault(h, {})[f] = tf.extractfile(m).read().decode()

hosts = sorted(f[:-5] for f in os.listdir(D) if f.endswith('.bits'))
assert len(hosts) == 25, f'{len(hosts)} hosts'
assert sorted(cov) == hosts, 'the archive and the directory name different hosts'
fails = 0
for h in hosts:
    s = ''.join(open(os.path.join(D, h + '.bits')).read().split())
    if h == flip:
        s = ('1' if s[0] == '0' else '0') + s[1:]
    n = 21; A = [[0] * n for _ in range(n)]; k = 0
    for i in range(n):
        for j in range(i + 1, n):
            A[i][j], A[j][i] = (1, 0) if s[k] == '1' else (0, 1); k += 1
    probs = []
    if any(sum(r) != 10 for r in A):
        probs.append('not regular')
    lam = {sum(A[u][w] and A[v][w] for w in range(n)) for u in range(n) for v in range(u + 1, n)}
    if not lam <= {4, 5}:
        probs.append(f'common out-neighbour counts {sorted(lam)}')
    bf = os.path.join(tempfile.gettempdir(), f'near_dr21_{os.getpid()}.bits')
    open(bf, 'w').write(s + '\n')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'verify_witness_bits.py'),
                        os.path.join(D, 'out', h + '.majority.txt'), bf, '21', '5', '--majority'],
                       capture_output=True, text=True)
    os.remove(bf)
    if r.returncode != 0:
        probs.append('majority witness does not verify: ' + r.stdout.strip()[:80])
    c = dict(cov[h])
    reps = [int(x) for x in c.pop('REPS.txt').split()]
    if h == drop:
        c.pop(f'{h}_{reps[0]}')
    if len(reps) != expect(h) or len(set(reps)) != len(reps):
        probs.append(f'{len(reps)} representatives, expected {expect(h)}')
    for x in reps:
        t = c.pop(f'{h}_{x}', None)
        if t is None:
            probs.append(f'state {x}: no marker'); break
        if not (re.search(r'^RESULT UNSAT .*base_states=2200 ', t, re.M) and
                re.search(r'^SLICE cleared=1 capped=0', t, re.M)):
            probs.append(f'state {x}: not an uncapped UNSAT'); break
    if c:
        probs.append(f'{len(c)} marker(s) for states not in REPS.txt')
    if probs:
        fails += 1
        print(f'  FAIL  {h}: ' + '; '.join(probs))
print(f'{len(hosts) - fails} of {len(hosts)} hosts: near-doubly regular, majority witness verified, '
      f'unit-margin search complete with no witness')
sys.exit(1 if fails else 0)
