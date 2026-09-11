#!/usr/bin/env python3
"""Turn CLAIMS.md into claims.tsv and claims.json, for a reader that is a program.

CLAIMS.md is written for a person and is the single source of truth; this
derives the machine-readable form from it rather than asking anyone to maintain
two copies that would drift. `tools/check_package.sh` regenerates and diffs, so
a hand-edited claims.tsv is a gate failure rather than a silent divergence.

    usage: tools/claims_index.py [--check]

Without arguments it writes `claims.tsv` and `claims.json` at the package root.
With --check it regenerates into memory and exits non-zero if either file on
disk differs, printing the first difference.

What it extracts, per claim: the stable id, the manuscript sections, the claim
text, every backticked path that exists in the package, every backticked token
that is not a path (a command, a flag, a hash), and the declared status --
`established` for a claim whose row names an artifact that is present,
`declared_gap` for one whose row points at the gap list.

It also extracts the gaps themselves, numbered as CLAIMS.md numbers them, so a
tool can ask "what does this package NOT establish" without parsing prose.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CLAIMS = os.path.join(ROOT, 'CLAIMS.md')


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def backticked(text):
    return re.findall(r'`([^`]+)`', text)


def is_path(tok):
    """Does this backticked token name something in the package?"""
    if ' ' in tok or tok.startswith('-') or tok.startswith('http'):
        return False
    return '/' in tok or re.search(r'\.(c|py|sh|md|txt|tsv|bits|zst|json|npy|1)$', tok)


def resolve(tok):
    """Does the package hold what `tok` names?  Three shapes occur in CLAIMS.md.

    A brace list `a/{x,y}.out` and a glob `d/*.log` are patterns: at least one
    match is required, since the point is that the evidence is there, not that
    a particular file is.  A bare filename with no directory is resolved by
    basename anywhere in the package, because the surrounding prose supplies the
    directory and duplicating it in the token would only rot.  Anything with a
    slash must exist exactly.
    """
    if '{' in tok and '}' in tok:
        pre, rest = tok.split('{', 1)
        body, post = rest.split('}', 1)
        return all(resolve(pre + alt + post) for alt in body.split(','))
    if '*' in tok or '?' in tok:
        return len(glob.glob(os.path.join(ROOT, tok))) > 0
    if '/' in tok:
        return os.path.exists(os.path.join(ROOT, tok))
    return os.path.basename(tok) in _basenames()


_BASENAMES = None


def _basenames():
    """Every file and directory name in the package, walked once.

    Walking per token was quadratic in a 13,800-file tree and made the gate step
    take longer than the certificate check it sits beside.
    """
    global _BASENAMES
    if _BASENAMES is None:
        _BASENAMES = set()
        for dirpath, dirnames, files in os.walk(ROOT):
            dirnames[:] = [d for d in dirnames if d != '.git']
            _BASENAMES.update(files)
            _BASENAMES.update(dirnames)
    return _BASENAMES


def parse():
    claims, gaps = [], []
    section = None
    cur_header = None
    in_gaps = False
    gap = None
    for raw in open(CLAIMS):
        line = raw.rstrip('\n')
        if line.startswith('#'):
            section = line.lstrip('#').strip()
            in_gaps = section.lower().startswith('gaps')
            cur_header = None
            continue
        if in_gaps:
            m = re.match(r'\*\*Gap (\d+) — (.+?)\.?\*\*', line)
            if m:
                if gap:
                    gaps.append(gap)
                title = m.group(2).strip()
                # A gap that has been closed keeps its NUMBER -- renumbering
                # would silently move every other reference -- and gains a
                # status instead, so a machine reader can count what is still
                # open without parsing prose.
                gap = dict(number=int(m.group(1)), title=title,
                           status=('closed' if 'CLOSED' in title.upper() else 'open'),
                           detail=line.split('**', 2)[-1].strip())
            elif gap is not None and line.strip():
                gap['detail'] = (gap['detail'] + ' ' + line.strip()).strip()
            elif gap is not None and not line.strip():
                gaps.append(gap)
                gap = None
            continue
        if not line.startswith('|'):
            cur_header = None
            continue
        cells = split_row(line)
        if re.match(r'^[\s:|-]+$', line.strip('|')):
            continue
        if cur_header is None:
            cur_header = [c.lower() for c in cells]
            continue
        row = dict(zip(cur_header, cells))
        cid = row.get('id')
        if not cid or not re.match(r'^[A-Z]\d+$', cid):
            continue
        blob = ' | '.join(cells)
        toks = backticked(blob)
        paths = [t for t in toks if is_path(t)]
        claims.append(dict(
            id=cid,
            group=section,
            sections=[s.strip() for s in row.get('§', '').split(',') if s.strip()],
            claim=re.sub(r'\s+', ' ', row.get('claim') or row.get('table row') or
                         row.get('count') or '').strip(),
            artifacts=[p for p in paths if resolve(p)],
            missing=[p for p in paths if not resolve(p)],
            other_tokens=[t for t in toks if not is_path(t)],
            status=('declared_gap' if re.search(r'gap \d', blob, re.I) else 'established'),
        ))
    if gap:
        gaps.append(gap)
    return claims, gaps


def render(claims, gaps):
    tsv = ["\t".join(["id", "group", "sections", "status", "artifacts", "missing", "claim"])]
    for c in claims:
        tsv.append("\t".join([
            c['id'], c['group'] or '', ';'.join(c['sections']), c['status'],
            ';'.join(c['artifacts']), ';'.join(c['missing']),
            c['claim'].replace('\t', ' ')]))
    doc = dict(
        source='CLAIMS.md',
        manuscript='manuscript/Tournaments_not_inducible_by_five_voters.md',
        claims=claims,
        gaps=gaps,
        counts=dict(claims=len(claims),
                    established=sum(1 for c in claims if c['status'] == 'established'),
                    declared_gap=sum(1 for c in claims if c['status'] == 'declared_gap'),
                    missing_artifacts=sum(len(c['missing']) for c in claims),
                    gaps=len(gaps),
                    gaps_open=sum(1 for g in gaps if g.get('status') == 'open'),
                    gaps_closed=sum(1 for g in gaps if g.get('status') == 'closed')))
    return "\n".join(tsv) + "\n", json.dumps(doc, indent=1) + "\n"


def main(check):
    claims, gaps = parse()
    if not claims:
        print("FAIL: CLAIMS.md yielded no claim rows -- the parser found nothing "
              "to index, which is a failure and not an empty package")
        return 1
    tsv, js = render(claims, gaps)
    tsv_p = os.path.join(ROOT, 'claims.tsv')
    js_p = os.path.join(ROOT, 'claims.json')
    if check:
        bad = 0
        for path, want in ((tsv_p, tsv), (js_p, js)):
            if not os.path.exists(path):
                print("FAIL: %s is missing; run tools/claims_index.py"
                      % os.path.basename(path))
                bad = 1
                continue
            got = open(path).read()
            if got != want:
                for i, (a, b) in enumerate(zip(got.split('\n'), want.split('\n')), 1):
                    if a != b:
                        print("FAIL: %s differs from CLAIMS.md at line %d"
                              % (os.path.basename(path), i))
                        print("  on disk:    %s" % a[:120])
                        print("  regenerated:%s" % b[:120])
                        break
                else:
                    print("FAIL: %s differs from CLAIMS.md in length"
                          % os.path.basename(path))
                bad = 1
        miss = [(c['id'], p) for c in claims for p in c['missing']]
        if miss:
            print("FAIL: %d artifact path(s) named in CLAIMS.md do not exist:" % len(miss))
            for cid, p in miss[:10]:
                print("  %s -> %s" % (cid, p))
            bad = 1
        if not bad:
            nopen = sum(1 for g in gaps if g.get('status') == 'open')
            print("claims.tsv and claims.json agree with CLAIMS.md "
                  "(%d claims, %d gaps of which %d still open, 0 missing artifacts)"
                  % (len(claims), len(gaps), nopen))
        return bad
    open(tsv_p, 'w').write(tsv)
    open(js_p, 'w').write(js)
    print("wrote claims.tsv and claims.json: %d claims, %d gaps (%d open), "
          "%d missing artifacts"
          % (len(claims), len(gaps),
             sum(1 for g in gaps if g.get('status') == 'open'),
             sum(len(c['missing']) for c in claims)))
    for c in claims:
        for p in c['missing']:
            print("  MISSING  %s -> %s" % (c['id'], p))
    return 0


if __name__ == '__main__':
    sys.exit(main('--check' in sys.argv[1:]))
