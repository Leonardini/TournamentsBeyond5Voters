#!/usr/bin/env python3
"""Three near-doubly-regular families on 21 vertices from Appendix G's table, gathered for the
reproduction package: each family's hosts and one verified witness per witnessed host.

    python3 near_dr21/build_families.py     # (re)writes near_dr21/families/<family>/{HOSTS.tsv, witness/}

  random   the 78 rigid near-doubly regular tournaments drawn at random (near_drt/HOSTS_near21*.tsv;
           witnesses in near_drt/results*/witness)
  bisector the 50 order-5 gluings with a bisector (glue10/O5_HOSTS21.tsv; unit-margin witnesses in
           glue10/lottery21q/found and glue10/lottery21/found, majority witnesses in
           glue10/lottery21maj/found for the 20 that need one)
  z3free   the 60 classes with a fixed-point-free automorphism of order 3 (glue10/Z3FREE_CLASSES.tsv);
           only the 5 tested here are witnessed (near_dr21/out/), the other 55 are on the cluster

Every witness is re-verified with verify_witness_bits.py --majority against the host's bits before
it is copied; a unit-margin witness is a majority witness.  HOSTS.tsv is `name<TAB>bits`."""
import pathlib, shutil, subprocess, sys

K = pathlib.Path(__file__).resolve().parent.parent
OUT = K / 'near_dr21' / 'families'
VERIFY = K / 'verify_witness_bits.py'


def rows(path, col):
    for l in open(path):
        if l.strip() and not l.startswith('#'):
            f = l.rstrip('\n').split('\t')
            yield f[0], f[col]


def build(fam, hosts, wdirs):
    d = OUT / fam
    (d / 'witness').mkdir(parents=True, exist_ok=True)
    with open(d / 'HOSTS.tsv', 'w') as f:
        for h, b in hosts:
            assert len(b) == 210, (fam, h)
            f.write(f'{h}\t{b}\n')
    nw = 0
    for h, b in hosts:
        src = next((p for w in wdirs for p in (w / h, w / f'{h}.log') if p.is_file()), None)
        if src is None:
            continue
        bf = d / f'.{h}.bits'
        bf.write_text(b + '\n')
        r = subprocess.run([sys.executable, str(VERIFY), str(src), str(bf), '21', '5', '--majority'],
                           capture_output=True, text=True)
        bf.unlink()
        assert r.returncode == 0, (fam, h, r.stdout)
        shutil.copyfile(src, d / 'witness' / f'{h}.log')
        nw += 1
    print(f'{fam}: {len(hosts)} hosts, {nw} witnesses verified and copied')


G = K / 'glue10'; N = K / 'near_drt'
build('random', [r for s in ('', 'a_leftover', 'b', 'c') for r in rows(N / f'HOSTS_near21{s}.tsv', -1)],
      [N / f'{r}/witness' for r in ('results', 'results_a3', 'results_b', 'results_c')])
build('bisector', list(rows(G / 'O5_HOSTS21.tsv', 4)),
      [G / 'lottery21q/found', G / 'lottery21/found', G / 'lottery21maj/found'])
z = list(rows(G / 'Z3FREE_CLASSES.tsv', 1))
build('z3free', [(f'z3c21_{i:02d}', b) for i, (_, b) in enumerate(z)], [])
# the 5 tested Z3-free hosts carry their own names; match them to the 60 by isomorphism in the audit
