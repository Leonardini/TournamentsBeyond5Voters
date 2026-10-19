#!/usr/bin/env python3
"""The 25 near-doubly-regular 21-vertex tournaments that five voters can produce, but not at
unit margin (paper 2, Section 3.7 and Appendix G), gathered into one ledger directory.

    python3 near_dr21/build.py          # (re)writes near_dr21/{*.bits, verdicts.tsv, out/, cover/}

Built 2026-10-19 for the reproduction package.  Every fact is re-derived from the campaign
files, nothing is copied as a verdict:

  * unit margin UNSAT -- every queued representative base state of the host has an
    `exhausted` marker that reads `RESULT UNSAT ... base_states=2200` and
    `SLICE cleared=1 capped=0`, and the queue holds exactly the representatives the
    campaign's quotient produced (444 per order-5 gluing under Corollary 2.5; 2,200 for
    zf21_0/1, no quotient; 600 per zr21 host under the sub-base quotient, Corollary 2.6).
    The marker set is copied into cover/<host>/ so the package can re-audit it.
  * majority SAT -- a witness log, re-verified here by verify_witness_bits.py --majority
    against THESE .bits, copied to out/<host>.majority.txt for verdict_ledger.py.
  * each .bits is the campaign's own file (asserted byte-identical after whitespace).

Sources: glue10/lottery21q (unit) + glue10/lottery21maj (majority) for the 20 order-5
gluings; glue10/z3free_full + glue10/z3free_maj for zf21_0/1; glue10/z3free_sub/<h> +
glue10/z3free_sub_maj/zr21_0 + run_evidence/jz21_sporadics_witnesses.tar.gz (zr21_1/2,
found on Jean Zay) for the three zr21 hosts."""
import os, pathlib, re, shutil, subprocess, sys, tarfile

K = pathlib.Path(__file__).resolve().parent.parent
OUT = K / 'near_dr21'
G = K / 'glue10'
VERIFY = K / 'verify_witness_bits.py'


def bits(p):
    return ''.join(open(p).read().split())


def unit_cover(h, qfile, exdir, expect):
    """Representatives of h in the queue, each with a clean exhaustion marker."""
    reps = sorted({int(l.split()[1]) for l in open(qfile) if l.split()[:1] == [h]})
    assert len(reps) == expect, f"{h}: {len(reps)} queued representatives, expected {expect}"
    dst = OUT / 'cover' / h
    dst.mkdir(parents=True, exist_ok=True)
    for s in reps:
        m = exdir / f'{h}_{s}'
        t = open(m).read()
        assert re.search(r'^RESULT UNSAT .*base_states=2200 ', t, re.M), (h, s, 'not UNSAT/2200')
        assert re.search(r'^SLICE cleared=1 capped=0', t, re.M), (h, s, 'not cleared')
        shutil.copyfile(m, dst / m.name)
    with open(dst / 'REPS.txt', 'w') as f:
        f.write('\n'.join(map(str, reps)) + '\n')
    return len(reps)


def witness(h, log):
    dst = OUT / 'out' / f'{h}.majority.txt'
    dst.parent.mkdir(exist_ok=True)
    shutil.copyfile(log, dst)
    r = subprocess.run([sys.executable, str(VERIFY), str(dst), str(OUT / f'{h}.bits'), '21', '5',
                        '--majority'], capture_output=True, text=True)
    assert r.returncode == 0, (h, r.stdout, r.stderr)
    return r.stdout.strip()


# (host, bits source, queue, exhausted dir, representatives, majority witness log)
HOSTS = []
for l in open(G / 'lottery21q' / 'VERDICTS.txt'):
    f = l.split()
    if len(f) >= 2 and f[1] == 'UNIT-INFEASIBLE':
        h = f[0]
        HOSTS.append((h, G / 'lottery21q/hosts' / f'{h}.bits', G / 'lottery21q/queue.txt',
                      G / 'lottery21q/exhausted', 444, G / 'lottery21maj/found' / h))
for h in ('zf21_0', 'zf21_1'):
    HOSTS.append((h, G / 'z3free_full/hosts' / f'{h}.bits', G / 'z3free_full/queue.txt',
                  G / 'z3free_full/exhausted', 2200, G / 'z3free_maj/found' / h))
jz = OUT / 'src_jz'
if not jz.exists():
    with tarfile.open(K / 'run_evidence/jz21_sporadics_witnesses.tar.gz') as t:
        t.extractall(jz, filter='data')
for h in ('zr21_0', 'zr21_1', 'zr21_2'):
    d = G / 'z3free_sub' / h
    wl = G / 'z3free_sub_maj/zr21_0/found/zr21_0' if h == 'zr21_0' else jz / 'results/witness' / f'{h}.log'
    HOSTS.append((h, d / 'hosts' / f'{h}.bits', d / 'queue.txt', d / 'exhausted', 600, wl))
assert len(HOSTS) == 25, len(HOSTS)

rows = ['name\tn\ttmin\tmargin\tverdict\tverified\tseconds']
for h, bsrc, q, ex, nrep, wl in HOSTS:
    b = bits(bsrc)
    assert len(b) == 210, (h, len(b))
    open(OUT / f'{h}.bits', 'w').write(b + '\n')
    n_ok = unit_cover(h, q, ex, nrep)
    v = witness(h, wl)
    rows.append(f'{h}\t21\t-\texact\tUNSAT\t1\tcomplete-cover-{n_ok}-reps')
    rows.append(f'{h}\t21\t-\tmajority\tSAT\t1\twitness')
    print(f'{h}: unit margin {n_ok}/{nrep} representatives exhausted; majority {v}')
open(OUT / 'verdicts.tsv', 'w').write('\n'.join(rows) + '\n')
print(f'{len(HOSTS)} hosts written to {OUT}')
