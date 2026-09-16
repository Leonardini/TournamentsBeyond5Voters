#!/usr/bin/env python3
"""Pull the reproduction's evidence out of the orx run logs into data/.

Everything the report and the notebook plot is derived here, once, from the run
logs and from the tournaments themselves -- nothing that a run measured is
retyped by hand into a figure. Published prior results (the N(5) bounds from the
literature) are the one exception, and they are citations rather than
measurements, so they carry their source instead of a recomputation.

  usage: collect.py <run-dir> [<run-dir> ...]      (orx local-run directories)
"""
import json, os, re, sys, glob, hashlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(OUT, exist_ok=True)
res = {'runs': {}, 'claims': {}, 'sweeps': {}, 'singles': {}, 'mem': []}

RESULT = re.compile(r'^RESULT (\w+) nodes=(\d+).*?time=([\d.]+)s', re.M)
AUDIT1 = re.compile(r'^AUDIT tag=(\S+) expected=(\d+) cleared=(\d+) missing=(\d+) '
                    r'extra=(\d+) capped=(\d+) sat=(\d+) errors=(\d+)')
AUDIT2 = re.compile(r'^AUDIT tag=(\S+) nodes=(\d+) core_seconds=([\d.]+) '
                    r'core_hours=([\d.]+) states_with_search=(\d+)')
FLIP = re.compile(r'^AUDIT tag=dr19flip hosts=(\d+) sat=(\d+) other=(\d+) '
                  r'core_hours=([\d.]+) wall_seconds=(\d+)')
MEM = re.compile(r'^MEM t=(\S+) workers=(\d+) kinduce_rss_total=(\d+)M '
                 r'swap_used=([\d.]+)M swap_growth=(-?\d+)M')

for rd in sys.argv[1:]:
    rid = os.path.basename(rd.rstrip('/'))
    log = os.path.join(rd, 'log')
    if not os.path.exists(log):
        cand = glob.glob(os.path.join(rd, '**', '*.log'), recursive=True)
        log = cand[0] if cand else None
    text = open(log, errors='replace').read() if log else ''
    res['runs'][rid] = {'log_bytes': len(text)}
    cur = None            # the sweep whose wall-clock line comes next
    for line in text.splitlines():
        if line.startswith('sweep tag='):
            cur = line.split('tag=')[1].split()[0]
        elif line.startswith('sweep_wall_seconds=') and cur:
            res['sweeps'].setdefault(cur, {})['wall_seconds'] = int(line.split('=')[1])
        if (m := AUDIT1.match(line)):
            res['sweeps'].setdefault(m[1], {}).update(
                expected=int(m[2]), cleared=int(m[3]), missing=int(m[4]),
                extra=int(m[5]), capped=int(m[6]), sat=int(m[7]), errors=int(m[8]))
        elif (m := AUDIT2.match(line)):
            res['sweeps'].setdefault(m[1], {}).update(
                nodes=int(m[2]), core_seconds=float(m[3]),
                core_hours=float(m[4]), searched=int(m[5]))
        elif (m := FLIP.match(line)):
            res['sweeps'].setdefault('dr19flip', {}).update(
                expected=int(m[1]), sat=int(m[2]), other=int(m[3]),
                core_hours=float(m[4]), wall_seconds=int(m[5]))
        elif (m := MEM.match(line)):
            res['mem'].append([m[1], int(m[2]), int(m[3]), float(m[4]), int(m[5])])
        elif line.startswith('CLAIM '):
            res['claims'].setdefault(line.split()[1], []).append(line[6:].strip())

    # per-base-state cost curves, and the single-shot searches. Sweeps run
    # after the resume change write to the durable sweeps directory instead of
    # into the run's own repo clone, so both places are scanned.
    SWEEPS = os.path.expanduser('~/.cache/openresearch/beyond5-sweeps')
    for t in (glob.glob(os.path.join(rd, '**', 'times.txt'), recursive=True)
              + glob.glob(os.path.join(SWEEPS, '*', 'times.txt'))):
        tag = os.path.basename(os.path.dirname(t))
        rows = [ln.split() for ln in open(t) if ln.strip()]
        secs = sorted((float(r[2]) for r in rows if r[2] != 'NA'), reverse=True)
        if secs:
            json.dump(secs, open(os.path.join(OUT, f'{tag}_times.json'), 'w'))
    for lg in glob.glob(os.path.join(rd, '**', 'out', '*', 'log.txt'), recursive=True):
        tag = os.path.basename(os.path.dirname(lg))
        body = open(lg, errors='replace').read()
        m = RESULT.search(body)
        entry = {'verdict': m[1] if m else None}
        if m:
            entry.update(nodes=int(m[2]), seconds=float(m[3]))
        if (v := re.search(r'^VERIFY (.*)$', body, re.M)):
            entry['verify'] = v[1].strip()
        # the witness itself, so the support histogram is recomputed not retyped
        ballots = [list(map(int, ln.split(':')[1].split()))
                   for ln in body.splitlines() if ln.strip().startswith('voter ')]
        if ballots:
            entry['ballots'] = ballots
        res['singles'][tag] = entry

json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=1)
print(f"sweeps:  {', '.join(sorted(res['sweeps']))}")
print(f"singles: {', '.join(sorted(res['singles']))}")
print(f"claims:  {len(res['claims'])} ids, mem samples: {len(res['mem'])}")
