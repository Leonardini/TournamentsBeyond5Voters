#!/usr/bin/env bash
# One base state of a sliced refutation sweep. Invoked by xargs -P from run.sh.
#
#   one_state.sh <idx> <outdir> <binary> <kinduce args...>
#
# Writes a marker into <outdir>/done/<idx> ONLY on `RESULT UNSAT` with
# `capped=0`. That makes the exact index cover of done/ the completeness
# certificate: a capped, crashed or aborted state leaves no marker, so a bare
# count could not be faked by a gap and a duplicate cancelling out.
set -uo pipefail
idx=$1; shift
outdir=$1; shift
bin=$1; shift

out=$("$bin" "$@" --bs-from "$idx" --bs-to $((idx + 1)) 2>&1)
rc=$?

res=$(printf '%s\n' "$out" | grep '^RESULT ' | tail -1)
slice=$(printf '%s\n' "$out" | grep '^SLICE ' | tail -1)
nodes=$(printf '%s\n' "$res" | sed -n 's/.*nodes=\([0-9]*\).*/\1/p')
secs=$(printf '%s\n' "$res" | sed -n 's/.*time=\([0-9.]*\)s.*/\1/p')
capped=$(printf '%s\n' "$slice" | sed -n 's/.*capped=\([0-9]*\).*/\1/p')

printf '%s %s %s %s\n' "$idx" "${nodes:-NA}" "${secs:-NA}" "${capped:-NA}" \
    >> "$outdir/times.txt"

if [ "$rc" -ne 0 ]; then
    printf '%s\n' "$out" > "$outdir/ERROR.$idx"
    echo "WORKER-ERROR idx=$idx rc=$rc"
    exit 0
fi

case "$res" in
    *"RESULT SAT"*)
        printf '%s\n' "$out" > "$outdir/SAT.$idx"
        echo "WITNESS-FOUND idx=$idx $res"
        ;;
    *"RESULT UNSAT"*)
        if [ "${capped:-1}" = "0" ]; then
            : > "$outdir/done/$idx"
        else
            printf '%s\n' "$out" > "$outdir/CAPPED.$idx"
            echo "CAPPED idx=$idx $slice"
        fi
        ;;
    *)
        printf '%s\n' "$out" > "$outdir/ERROR.$idx"
        echo "NO-RESULT-LINE idx=$idx"
        ;;
esac
