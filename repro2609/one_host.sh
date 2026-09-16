#!/usr/bin/env bash
# One arc-reversed host of the K9 sweep. Invoked by xargs -P from run.sh.
#   one_host.sh <bitsfile> <outdir> <binary> <n> <cap-seconds>
# Expects a unit-margin WITNESS, so a cap is sound: it can only fail to find
# one, never wrongly report its absence.
set -uo pipefail
f=$1; d=$2; bin=$3; n=$4; cap=$5
b=$(basename "$f" .bits)
timeout "$cap" "$bin" --bits "$f" --n "$n" --k 5 --max-margin 1 \
        --order mrv --inc > "$d/$b.log" 2>&1
rc=$?
res=$(grep '^RESULT ' "$d/$b.log" | tail -1)
if grep -q '^RESULT SAT' "$d/$b.log"; then
    : > "$d/sat.$b"
    printf '%-10s SAT   %s\n' "$b" "$(printf '%s' "$res" | sed -n 's/.*\(nodes=[0-9]*\).*\(time=[0-9.]*s\).*/\1 \2/p')"
elif [ "$rc" = 124 ]; then
    printf '%-10s CAP   hit %ss cap\n' "$b" "$cap"
else
    printf '%-10s OTHER %s\n' "$b" "${res:-no RESULT line, rc=$rc}"
fi
