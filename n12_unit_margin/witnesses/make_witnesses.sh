#!/usr/bin/env bash
# make_witnesses.sh — unit-margin five-voter profiles for every non-3-inducible
# tournament in one of McKay's catalogues (n <= 10).
#
#   catalogue -> margin1_scan (decides 3-inducibility; keeps the non-3-inducible)
#             -> cert_m1k5    (finds five voters with every arc carried exactly 3:2)
#             -> m1k5_profile (writes the five linear orders out explicitly)
#
# The catalogue is split into JOBS consecutive pieces processed in parallel and
# joined back in catalogue order, so the output does not depend on JOBS.
# A tournament with no unit-margin profile stops the run (m1k5_profile exits on
# cert_m1k5's "N" line); no profile is ever loosened to a larger margin.
#
# Usage:  ./make_witnesses.sh N CATALOGUE [JOBS]
#   e.g.  ./make_witnesses.sh 10 ../data/mckay/tournaments10.txt 4
# Output: nN_unit_margin_profiles.txt.xz in this directory: line k holds the five
# orders (vertices top to bottom) for the k-th non-3-inducible tournament of the
# catalogue, in catalogue order.
# Progress: timestamped lines on stderr every 30 s (PROGRESS_SECS to change).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
n=$1; cat_file=$2; jobs=${3:-1}
csp="$here/../csp"
work=$(mktemp -d "${TMPDIR:-/tmp}/unit_margin_n${n}.XXXXXX")
trap 'rm -rf "$work"' EXIT

for t in margin1_scan cert_m1k5 m1k5_profile; do
  cc -O3 -o "$work/$t" "$csp/$t.c"
done

total_lines=$(wc -l < "$cat_file" | tr -d ' ')
split -l $(( (total_lines + jobs - 1) / jobs )) -a 3 "$cat_file" "$work/piece_"
pids=()
for piece in "$work"/piece_[a-z][a-z][a-z]; do
  ( "$work/margin1_scan" "$n" emitn < "$piece" 2> "$piece.scan" \
      | { grep '^N ' || true; } | cut -d' ' -f2 \
      | "$work/cert_m1k5" "$n" 2> "$piece.cert" \
      | "$work/m1k5_profile" "$n" > "$piece.prof" 2> "$piece.conv" ) &
  pids+=($!)
done

while :; do
  running=0
  for p in "${pids[@]}"; do kill -0 "$p" 2>/dev/null && running=$((running+1)); done
  done_prof=$( (cat "$work"/piece_*.prof 2>/dev/null || true) | wc -l | tr -d ' ')
  echo "[$(date '+%F %T')] n=$n: $done_prof profiles written; $running of ${#pids[@]} pieces running (catalogue: $total_lines tournaments)" >&2
  [ "$running" = 0 ] && break
  sleep "${PROGRESS_SECS:-30}"
done
for p in "${pids[@]}"; do wait "$p"; done     # set -e: any failed piece stops here

# per-piece consistency: every non-3-inducible tournament got exactly one profile
for piece in "$work"/piece_[a-z][a-z][a-z]; do
  nonind=$(sed -n 's/.*non-realizable \([0-9]*\).*/\1/p' "$piece.scan")
  sat=$(sed -n 's/^total [0-9]*: margin1-k5-SAT \([0-9]*\), UNSAT \([0-9]*\)$/\1 \2/p' "$piece.cert")
  prof=$(wc -l < "$piece.prof" | tr -d ' ')
  [ "$sat" = "$nonind 0" ] && [ "$prof" = "$nonind" ] || {
    echo "FAIL: $(basename "$piece"): non-3-inducible $nonind, cert '$sat', profiles $prof" >&2; exit 1; }
done

cat "$work"/piece_[a-z][a-z][a-z].scan | grep '^n=' | awk -v n="$n" '
  { for (i = 1; i <= NF; i++) if ($i ~ /^[0-9]+,?$/) { v[++k] = $i + 0 } t += v[1]; m += v[2]; r += v[3]; x += v[4]; k = 0 }
  END { printf "n=%d: %d tournaments; 3-inducible with unit margin %d, 3-inducible only with a unanimous arc %d, not 3-inducible %d\n", n, t, m, r, x }' >&2
# the stored witness is the five orders; the bitstring is dropped, since the
# verifier rebuilds it from the orders and compares it with the catalogue
out="$here/n${n}_unit_margin_profiles.txt.xz"
cat "$work"/piece_[a-z][a-z][a-z].prof | cut -d' ' -f2- | xz -9 -T1 > "$out"
echo "wrote $out ($(xz -dc "$out" | wc -l | tr -d ' ') profiles)" >&2
