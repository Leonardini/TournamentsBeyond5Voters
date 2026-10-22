#!/usr/bin/env python3
"""Do any banked 20-vertex witnesses extend to an open 21-vertex class?  (His idea, 2026-10-22.)

For every open 21-vertex class T (HOSTS_level2 minus SETTLED) and every vertex c of T, the child
T - c is a 20-vertex class that is settled (all 28,724 are), so some banked witness covers it, up
to isomorphism and converse.  We find that class by nauty canonical form, map its witness onto
T - c through an explicit isomorphism (VF2; orders reversed if the match is with the converse),
and ask extend.c whether c can be inserted into the five orders so that every arc at c keeps a
majority.  Any hit is a 5-voter witness for T, written to found/<T>.log and checked by an
independent verifier before it is counted.

usage: drive.py WORKERS"""
import io, multiprocessing as mp, os, re, subprocess, sys, tarfile
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher
H = os.path.dirname(os.path.abspath(__file__))
R = '/Users/lchindelevitch/Downloads/NonPriority/Conjectures/TournamentsBeyond5Voters/'
sys.path.insert(0, os.path.join(H, '..')); from level_coverage import canon, digraph6
LABELG = '/Users/lchindelevitch/Downloads/DownloadedSoftware/nauty2_8_6/labelg'


def load(b):
    n = int(round((1 + (1 + 8 * len(b)) ** .5) / 2)); A = [[0] * n for _ in range(n)]; k = 0
    for i in range(n):
        for j in range(i + 1, n): A[i][j] = int(b[k]); A[j][i] = 1 - A[i][j]; k += 1
    return A


def rows(p):
    return {l.split('\t')[0]: l.split('\t')[4].strip() for l in open(p) if l.strip() and not l.startswith('#')}


def conv(A): return [list(r) for r in zip(*A)]


def iso(A, B):
    """a map f with A[i][j] == B[f(i)][f(j)], or None."""
    GA = nx.DiGraph((i, j) for i in range(len(A)) for j in range(len(A)) if A[i][j])
    GB = nx.DiGraph((i, j) for i in range(len(B)) for j in range(len(B)) if B[i][j])
    m = DiGraphMatcher(GA, GB)
    return next(m.isomorphisms_iter(), None)


def job(args):
    tname, tb, c, wname, wbits, worders, flip = args
    T = load(tb); n = len(T); rest = [u for u in range(n) if u != c]
    C = [[T[i][j] for j in rest] for i in rest]
    W = load(wbits); W = conv(W) if flip else W
    f = iso(C, W)                      # child vertex -> witness-host vertex
    if f is None: return (tname, c, 'NOISO', None)
    inv = {f[i]: i for i in f}
    orders = [[inv[w] for w in (O[::-1] if flip else O)] for O in worders]   # orders on child vertices
    out = [T[c][u] for u in rest]
    line = f"5 {n - 1} " + ' '.join(' '.join(map(str, o)) for o in orders) + ' ' + ' '.join(map(str, out))
    r = subprocess.run([os.path.join(H, 'extend')], input=line + '\n', capture_output=True, text=True).stdout.split()
    if r[0] != 'EXT': return (tname, c, 'NOEXT', None)
    pos = list(map(int, r[1:]))
    full = []
    for o, p in zip(orders, pos):
        oo = [rest[x] for x in o]; full.append(oo[:p] + [c] + oo[p:])
    return (tname, c, 'EXT', full)


def main():
    W = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    l2 = rows(R + 'tournaments/drt23_del/HOSTS_level2.tsv'); l3 = rows(R + 'tournaments/drt23_del/HOSTS_level3.tsv')
    raw = subprocess.run(f"zstd -dc {R}evidence/n21_level_witnesses.tar.zst | tar -xOf - n21_level/SETTLED.tsv",
                         shell=True, capture_output=True, text=True).stdout
    settled = {l.split('\t')[0] for l in raw.split('\n') if l and not l.startswith('#')}
    have = {f[:-4] for f in os.listdir(os.path.join(H, 'found')) if f.endswith('.log')} if os.path.isdir(os.path.join(H, 'found')) else set()
    openT = sorted(t for t in l2 if t not in settled and t not in have)
    # banked 20-vertex witnesses, by host name
    wit = {}
    tf = tarfile.open(fileobj=io.BytesIO(subprocess.run(['zstd', '-dc', R + 'evidence/n20_descent_witnesses.tar.zst'],
                                                        capture_output=True, check=True).stdout))
    for m in tf:
        nm = os.path.basename(m.name)
        if m.isfile() and nm.endswith('.log') and nm[:-4] in l3:
            o = [list(map(int, x.split())) for x in re.findall(r'^\s*voter \d+:\s*([\d ]+)$', tf.extractfile(m).read().decode(), re.M)]
            if len(o) == 5: wit[nm[:-4]] = o
    # pool[canonical form] = list of (host bits, orders, flip): the banked witness, and (round 2 on)
    # every settled 21-vertex witness restricted to each of its 20-vertex children
    pool = {}
    hostbits = {w: l3[w] for w in wit}; worders = dict(wit)
    if '--from21' in sys.argv:
        raw21 = subprocess.run(['zstd', '-dc', R + 'evidence/n21_level_witnesses.tar.zst'], capture_output=True, check=True).stdout
        t21 = tarfile.open(fileobj=io.BytesIO(raw21)); src = {}
        for m in t21:
            nm = os.path.basename(m.name)
            if m.isfile() and nm.endswith('.log') and nm[:-4] in l2 and 'BADWITNESS' not in nm:
                src[nm[:-4]] = t21.extractfile(m).read().decode()
        for f in os.listdir(os.path.join(H, 'found')):
            if f.endswith('.log'): src[f[:-4]] = open(os.path.join(H, 'found', f)).read()
        for t, txt in src.items():
            o = [list(map(int, x.split())) for x in re.findall(r'^\s*voter \d+:\s*([\d ]+)$', txt, re.M)]
            if len(o) != 5: continue
            T = load(l2[t]); n = len(T)
            for c in range(n):
                rest = [u for u in range(n) if u != c]; idx = {u: i for i, u in enumerate(rest)}
                C = [[T[i][j] for j in rest] for i in rest]
                key = f'{t}-{c}'
                hostbits[key] = ''.join(str(C[i][j]) for i in range(n - 1) for j in range(i + 1, n - 1))
                worders[key] = [[idx[u] for u in O if u != c] for O in o]
    names = sorted(hostbits)
    cf = canon([digraph6(load(hostbits[w])) for w in names] + [digraph6(conv(load(hostbits[w]))) for w in names], LABELG)
    for i, w in enumerate(names):
        pool.setdefault(cf[i], []).append((w, False)); pool.setdefault(cf[len(names) + i], []).append((w, True))
    byclass = pool
    print(f'{len(openT)} open classes, {len(names)} banked 20-vertex witnesses, {len(byclass)} canonical forms covered', flush=True)
    jobs = []
    for t in openT:
        T = load(l2[t]); n = len(T)
        kids = [digraph6([[T[i][j] for j in range(n) if j != c] for i in range(n) if i != c]) for c in range(n)]
        for c, cfc in enumerate(canon(kids, LABELG)):
            for w, flip in byclass.get(cfc, []):
                jobs.append((t, l2[t], c, w, hostbits[w], worders[w], flip))
    print(f'{len(jobs)} (class, vertex, witness) attempts', flush=True)
    os.makedirs(os.path.join(H, 'found'), exist_ok=True)
    hits, done = {}, 0
    with mp.Pool(W) as pool, open(os.path.join(H, 'progress.log'), 'a') as pl:
        for t, c, st, full in pool.imap_unordered(job, jobs, chunksize=20):
            done += 1
            if st == 'EXT' and t not in hits:
                hits[t] = c
                with open(os.path.join(H, 'found', t + '.log'), 'w') as f:
                    f.write(f'n=21 K=5 margin=majority source=witness-extension (host {t} witness extended from {t} - vertex {c})\nWITNESS\n')
                    for i, o in enumerate(full): f.write(f'  voter {i}: ' + ' '.join(map(str, o)) + '\n')
            if done % 2000 == 0 or done == len(jobs):
                pl.write(f'{done}/{len(jobs)} pairs tried, {len(hits)} classes extended\n'); pl.flush()
    print(f'DONE: {len(hits)} of {len(openT)} open classes extended', flush=True)


if __name__ == '__main__':
    main()
