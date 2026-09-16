#!/usr/bin/env python3
"""Assert that the report, the README and the evidence still agree.

Two published figures drifted apart once already: the headline paragraph said
all 8,031 base states ran a search while the figure beside it said 2,571, and a
withdrawn node count survived in prose after the correction section retracted
it. Both slipped through because two components computed the same quantity with
their own local rule. Everything now reads `searched` from data/results.json,
where collect.py derives it once — and this script fails loudly if that stops
being true.

    usage: check_report.py     # exit 0 if consistent, 1 otherwise
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
D = json.load(open(os.path.join(HERE, 'data', 'results.json')))
report = open(os.path.join(HERE, 'report.md')).read()
readme = open(os.path.join(REPO, 'README.md')).read()

fails = []
def check(cond, msg):
    print(f"  {'ok  ' if cond else 'FAIL'}  {msg}")
    if not cond:
        fails.append(msg)

for tag, s in sorted(D['sweeps'].items()):
    if 'searched' in s and 'expected' in s:
        check(s['searched'] + s['unsearched'] == s['expected'],
              f"{tag}: searched + unsearched = expected "
              f"({s['searched']} + {s['unsearched']} = {s['expected']})")
    # a sweep is a refutation only on an exact index cover
    if 'cleared' in s:
        check(s['missing'] == 0 and s['extra'] == 0 and s['capped'] == 0
              and s['sat'] == 0 and s['errors'] == 0
              and s['cleared'] == s['expected'],
              f"{tag}: exact index cover, nothing capped, no witness")
    # the column the old scrape mislabelled must never be called a node count
    check('nodes' not in s, f"{tag}: no bare 'nodes' key (it held dom_nodes)")

p = D['sweeps']['p23']
check(f"{p['searched']:,}" in report and f"{p['unsearched']:,}" in report,
      "report quotes the shared searched / unsearched split")
check(f"only {p['expected']:,}** ran a search" not in report,
      "report does not claim every base state ran a search")
check(str(p['dom_nodes_total']) not in report.replace(',', ''),
      "report asserts no node count for the sweep")
check("One quantity diverged" not in readme,
      "README does not claim a node-count divergence")
sps = p['core_seconds'] / p['searched']
check(f"{sps:.1f} s" in report,
      f"report's seconds-per-searched-state matches the evidence ({sps:.1f} s)")

print(f"\n{len(fails)} failed" if fails else "\nreport and evidence agree")
sys.exit(1 if fails else 0)
