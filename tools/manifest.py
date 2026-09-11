#!/usr/bin/env python3
"""Write or verify MANIFEST.sha256: every shipped file, hashed.

An external examiner needs one question answered before any other: are these the
bytes the authors published?  The manifest answers it for the whole package in
one pass, and `--check` reports the three ways it can go wrong separately --
CHANGED, MISSING and UNTRACKED -- because they mean different things.  A changed
file is a corruption or an edit; a missing one is an incomplete copy; an
untracked one is usually a build product and occasionally a file someone added
without saying so.

    usage: tools/manifest.py [--check] [--quiet]

Excluded: `.git/`, `__pycache__/`, the manifest itself, and anything matched by
`.gitignore`-style junk (`.DS_Store`, `*.pyc`, `*.o`, editor backups).  The
exclusions are listed in SKIP below rather than being scattered through the
code, so what is NOT covered is readable in one place.

The manifest is sorted by path and uses forward slashes, so it is stable across
filesystems and diffs cleanly between versions of the package.
"""
import hashlib
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
MANIFEST = os.path.join(ROOT, 'MANIFEST.sha256')

SKIP_DIRS = {'.git', '__pycache__', '.ipynb_checkpoints'}
SKIP_NAMES = {'MANIFEST.sha256', '.DS_Store'}
SKIP_SUFFIX = ('.pyc', '.pyo', '.o', '.aux', '.out.log', '~', '.swp')


def walk():
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(files):
            if fn in SKIP_NAMES or fn.endswith(SKIP_SUFFIX):
                continue
            full = os.path.join(dirpath, fn)
            if os.path.islink(full):
                continue
            yield os.path.relpath(full, ROOT).replace(os.sep, '/'), full


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def main(check, quiet):
    live = dict(walk())
    if not check:
        total = 0
        with open(MANIFEST, 'w') as out:
            out.write("# sha256 of every file in this package, sorted by path.\n"
                      "# Verify with: python3 tools/manifest.py --check\n")
            for rel in sorted(live):
                out.write("%s  %s\n" % (sha256(live[rel]), rel))
                total += os.path.getsize(live[rel])
        print("MANIFEST.sha256: %d files, %.1f MB" % (len(live), total / 1e6))
        return 0

    if not os.path.exists(MANIFEST):
        print("FAIL: MANIFEST.sha256 is absent; run tools/manifest.py")
        return 1
    want = {}
    for line in open(MANIFEST):
        if line.startswith('#') or not line.strip():
            continue
        h, rel = line.rstrip('\n').split('  ', 1)
        want[rel] = h
    changed, missing = [], []
    for rel, h in sorted(want.items()):
        if rel not in live:
            missing.append(rel)
        elif sha256(live[rel]) != h:
            changed.append(rel)
    untracked = sorted(set(live) - set(want))
    if changed or missing or untracked:
        for label, rows in (('CHANGED', changed), ('MISSING', missing),
                            ('UNTRACKED', untracked)):
            for rel in rows[:12]:
                print("  %-9s %s" % (label, rel))
            if len(rows) > 12:
                print("  %-9s ... and %d more" % (label, len(rows) - 12))
        print("FAIL: %d changed, %d missing, %d untracked of %d files"
              % (len(changed), len(missing), len(untracked), len(want)))
        return 1
    if not quiet:
        print("MANIFEST.sha256 verified: %d files, 0 changed, 0 missing, 0 untracked"
              % len(want))
    return 0


if __name__ == '__main__':
    sys.exit(main('--check' in sys.argv[1:], '--quiet' in sys.argv[1:]))
