#!/bin/bash
# Zero-compute post-mortem on the converse halving, read from the slurm logs.
#
# WHY.  aggregate.sh can only check the halving GLOBALLY: kept must equal
# (D11 + S11)/2, and a floor of D11/2 holds whatever S11 is, because the rule
# "keep iff canon(T) <= canon(conv(T))" keeps at least one host of every converse
# pair.  On 2026-09-12 the completed census reported 903,753,248 generated and
# 443,771,294 kept -- 8,105,330 BELOW that floor, which no correct run can be.
#
# A deficit below the floor cannot come from the keep rule itself: for a pair
# (T, conv T) the two decisions read the same two canonical forms in opposite
# order, so exactly one host survives, deterministically.  It means HOSTS WENT
# MISSING.  There are exactly two places they can go, and screen_residue.sh
# checked neither:
#
#   before the filter   converse_filter.sh does `cat > "$TMP/in"` UNCHECKED, so a
#                       full or over-quota $TMPDIR truncates the input silently;
#                       every later count is then self-consistently too small.
#   after the filter    the final `paste | awk` writes to stdout and the script
#                       then `exit 0`s unconditionally, so a short write leaves a
#                       truncated host file that the caller accepts.
#
# Both are visible in the logs, because screen_residue.sh prints the filter's own
# tally beside the residue's: `converse filter: NI in, K out`, then
# `res=R generated=G screened=S`.  NI must equal G and K must equal S.
#
# It also writes the list of residues to re-screen, so the repair can start
# without waiting for halving_audit.slurm to confirm what the logs already say.
#
#   usage: filter_log_check.sh [logdir] [outdir]
#          defaults: this kit's slurm/ and results/
set -u
_ORIGPWD=$PWD
cd "$(dirname "$0")"
LOGS=${1:-slurm}
OUT=${2:-results}
case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac
ls "$LOGS"/*.out >/dev/null 2>&1 || { echo "no logs in $LOGS" >&2; exit 1; }
mkdir -p "$OUT"
LIST=$OUT/rescreen_from_logs.txt

echo "=== write errors the filter or the generator reported ==="
# ENOSPC and quota messages land in the log via the filter's stderr, indented.
grep -h -i 'no space left\|write error\|disk quota\|quota exceeded\|cannot create\|Killed\|Bus error' "$LOGS"/*.out \
  | sort | uniq -c | sort -rn | head -20
echo "  (nothing above means the loss was silent, which is the harder case)"

echo
echo "=== per-residue reconciliation ==="
# Keep the LAST attempt of each residue: a retried residue appears more than once
# and only its final attempt wrote the marker.
awk -v LIST="$LIST" '
  /converse filter: [0-9]+ in, [0-9]+ out/ { ni = $3; k = $5; next }
  /^res=[0-9]+ generated=[0-9]+ screened=[0-9]+$/ {
    split($1, a, "="); split($2, b, "="); split($3, c, "=")
    r = a[2]; G[r] = b[2]; S[r] = c[2]; IN[r] = ni; OUT[r] = k; ni = ""; k = ""
  }
  END {
    for (r in G) {
      n++; g += G[r]; s += S[r]; i += IN[r]; o += OUT[r]
      # A residue with NO filter line lost its hosts BEFORE the filter could even
      # report -- the stderr file it writes through is on the same full filesystem.
      # Those show as generated > 0 with screened = 0, and they must be re-screened
      # exactly like the truncated ones, so they are counted, not skipped.
      if (IN[r] == "") {
        nostats++
        if (G[r] > 0) { bad++; lost_in += G[r]; print r > LIST
                        if (bad <= 15) printf "  res=%-6s generated=%-9s NO filter line at all, screened=%s\n", r, G[r], S[r] }
        continue }
      if (IN[r] != G[r] || OUT[r] != S[r]) {
        bad++; lost_in += G[r] - IN[r]; lost_out += OUT[r] - S[r]; print r > LIST
        if (bad <= 15) printf "  res=%-6s generated=%-9s filter_in=%-9s filter_out=%-9s screened=%s\n", r, G[r], IN[r], OUT[r], S[r]
      }
    }
    printf "\nresidues with a log line      : %d\n", n
    printf "sum generated (logs)          : %d\n", g
    printf "sum the filter SAW            : %d   <== must equal generated\n", i
    printf "sum the filter KEPT           : %d\n", o
    printf "sum screened (logs)           : %d   <== must equal what it kept\n", s
    printf "residues with no filter tally : %d\n", nostats+0
    printf "residues that do not reconcile: %d\n", bad+0
    printf "hosts lost BEFORE the filter  : %d\n", lost_in+0
    printf "hosts lost AFTER  the filter  : %d\n", lost_out+0
    if (bad+0 == 0)
      print "\nEvery residue reconciles.  The hosts were NOT lost inside the filter,\n" \
            "so the next suspect is the canonical form itself: two nauty builds give\n" \
            "different canonical labellings, and a pair split across two residues that\n" \
            "used different ones can lose BOTH members.  Run halving_audit.sh."
  }' "$LOGS"/*.out
if [ -s "$LIST" ]; then
  sort -n -u "$LIST" -o "$LIST"
  echo
  echo "wrote $(wc -l < "$LIST" | tr -d ' ') residues to $LIST"
  echo "  these are the residues to re-screen; rescreen.slurm reads this file"
fi
