#!/usr/bin/env bash
# check_witnesses.sh N — check the shipped unit-margin profiles for order N (8 or 9) against
# McKay's catalogue: margin1_scan lists the non-3-inducible tournaments in catalogue order, and
# verify_unit_margin.py checks profile k against tournament k.  Needs ../get_data.sh run first.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
n=$1
case "$n" in 8) expect=96 ;; 9) expect=17674 ;; *) echo "usage: $0 8|9" >&2; exit 2 ;; esac
cat_file="$here/../data/mckay/tournaments$n.txt"
[ -s "$cat_file" ] || { echo "missing $cat_file: run ../get_data.sh first" >&2; exit 2; }
work=$(mktemp -d "${TMPDIR:-/tmp}/check_witnesses.XXXXXX"); trap 'rm -rf "$work"' EXIT
cc -O3 -o "$work/margin1_scan" "$here/../csp/margin1_scan.c"
"$work/margin1_scan" "$n" emitn < "$cat_file" 2>/dev/null | { grep '^N ' || true; } | cut -d' ' -f2 \
  | python3 "$here/verify_unit_margin.py" "$n" "$here/n${n}_unit_margin_profiles.txt.xz" - --expect "$expect"
