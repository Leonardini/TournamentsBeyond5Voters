#!/bin/bash
# One slice of the n=11 five-inducibility census:
#   gentourng 11 RES/MOD -> margin1_scan (3-inducibility triple-local CSP)
#     -> non-3-inducible lines -> cert_m1k5 (margin-1 5-voter CSP, witness out)
#     -> verify_m1k5 (independent witness check; passes UNSAT through)
# Streams end-to-end; nothing is buffered until the end.  Idempotent per slice.
#
# Usage: n11_worker.sh RES MOD OUTDIR BINDIR GENTOURNG
# Outputs: OUTDIR/w_RES.tally1  (margin1_scan tallies: total/M/R/N)
#          OUTDIR/w_RES.tally2  (cert_m1k5 tallies: SAT/UNSAT)
#          OUTDIR/w_RES.tally3  (verify_m1k5: witnesses verified)
#          OUTDIR/w_RES.residual (bit-strings needing the ILP stage)
#          OUTDIR/w_RES.done    (completion marker)
set -euo pipefail
RES=$1; MOD=$2; OUT=$3/w_${RES}; BIN=$4; GEN=$5

"$GEN" -q 11 ${RES}/${MOD} \
  | "$BIN/margin1_scan" 11 emitn 2> "${OUT}.tally1" \
  | { grep '^N ' || true; } | cut -d' ' -f2 \
  | "$BIN/cert_m1k5" 11 2> "${OUT}.tally2" \
  | "$BIN/verify_m1k5" 11 2> "${OUT}.tally3" \
  | { grep '^N ' || true; } | cut -d' ' -f2 > "${OUT}.residual"
touch "${OUT}.done"
