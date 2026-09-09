#!/bin/bash
# Measure, on THIS machine, the two rates the n=15 campaign is sized from --
# generation and search, separated -- plus the engine's one-off setup.
#
#   usage:  KInduceDFS/jz_n15/probe_rate.sh [res] [mod] [nprobe]
#
# Written after a hand-rolled inline probe failed for the dullest reason: the
# environment variables it interpolated were unset in that shell, so it ran
# `cd /KInduceDFS` and `-u: command not found` and reported nothing.  A script
# resolves its own paths and fails loudly, so one round trip suffices.
set -u
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
RES=${1:-0}; MOD=${2:-6000}; NPROBE=${3:-400000}

# Generator: explicit override, then a loaded module, then the known cluster
# tree, then a local build.  Print what was chosen -- an unset variable is the
# whole reason this script exists.
CLUSTERNAUTY=/lustre/fswork/projects/rech/lia/uex76wa/nauty2_9_3
if   [ -n "${GENTOURNG:-}" ] && [ -x "${GENTOURNG}" ]; then GT="$GENTOURNG"
elif [ -n "${NAUTY_DIR:-}" ] && [ -x "${NAUTY_DIR}/gentourng" ]; then GT="${NAUTY_DIR}/gentourng"
elif command -v gentourng >/dev/null 2>&1; then GT="$(command -v gentourng)"
elif [ -x "$CLUSTERNAUTY/gentourng" ]; then GT="$CLUSTERNAUTY/gentourng"
elif [ -x "$ROOT/nauty/gentourng" ]; then GT="$ROOT/nauty/gentourng"
else
  echo "FATAL: no gentourng found.  Set GENTOURNG=/path/to/gentourng and re-run." >&2
  echo "  tried: \$GENTOURNG, \$NAUTY_DIR/gentourng, PATH, $CLUSTERNAUTY, $ROOT/nauty" >&2
  exit 1
fi
KI=../kinduce20
[ -x "$KI" ] || { echo "FATAL: $KI not built -- run ./build.sh" >&2; exit 1; }

W=${JOBSCRATCH:-${SLURM_TMPDIR:-/tmp}}
B="$W/probe_r$RES.bits"
trap 'rm -f "$B" "$W/probe_1.bits" "$W/probe_N.bits"' EXIT

echo "host      $(hostname)"
echo "gentourng $GT"
echo "engine    $(cd .. && pwd)/kinduce20"
echo "scratch   $W"
echo

# 1. generation, compute only (-u counts, writes nothing) -----------------
t0=$SECONDS
CNT=$("$GT" -u -d7 -D7 15 "$RES/$MOD" 2>&1 | sed -n 's/.*Z \([0-9]*\) graphs.*/\1/p')
T_COUNT=$((SECONDS - t0))
[ -n "$CNT" ] || { echo "FATAL: gentourng -u produced no count" >&2; exit 1; }

# 2. generation to a file (adds the I/O) ---------------------------------
t0=$SECONDS
"$GT" -d7 -D7 15 "$RES/$MOD" 2>/dev/null > "$B"
T_GEN=$((SECONDS - t0))
N=$(wc -l < "$B" | tr -d ' ')
[ "$N" = "$CNT" ] || echo "WARNING: -u counted $CNT but the file has $N lines"

# 3. engine setup, on ONE instance ---------------------------------------
head -1 "$B" > "$W/probe_1.bits"
t0=$SECONDS
$KI --batch "$W/probe_1.bits" --n 15 --k 5 --margin exact --order mrv --inc >/dev/null 2>&1
T_SETUP=$((SECONDS - t0))

# 4. engine marginal, on NPROBE instances --------------------------------
[ "$NPROBE" -gt "$N" ] && NPROBE=$N
head -"$NPROBE" "$B" > "$W/probe_N.bits"
t0=$SECONDS
$KI --batch "$W/probe_N.bits" --n 15 --k 5 --margin exact --order mrv --inc \
    2>&1 | grep BATCH_SUMMARY
T_RUN=$((SECONDS - t0))

python3 - "$CNT" "$T_COUNT" "$T_GEN" "$T_SETUP" "$NPROBE" "$T_RUN" <<'PY'
import sys
cnt, tc, tg, ts, npb, tr = (int(x) for x in sys.argv[1:7])
gen_io = tg - tc
marg = (tr - ts) / npb * 1e6 if npb else 0.0
tot = 18400989629
print()
print(f"instances in residue       {cnt}")
print(f"generation compute         {tc} s   ({tc*1e6/cnt:.1f} us/inst)")
print(f"generation I/O on top      {gen_io} s   ({gen_io*1e6/cnt:+.1f} us/inst)")
print(f"engine setup (1 instance)  {ts} s")
print(f"engine on {npb} inst    {tr} s   ({marg:.1f} us/inst marginal)")
print()
print(f"PROBE res_instances={cnt} gen_us={tc*1e6/cnt:.1f} genio_us={gen_io*1e6/cnt:.1f} "
      f"setup_s={ts} search_us={marg:.1f} "
      f"residue_s={tc + gen_io + ts + cnt*marg/1e6:.0f}")
print("LAPTOP reference (2026-09-03, residue 0 of 6000): res_instances=3205018 "
      "gen_us=29.3 genio_us=0.0 setup_s=18 search_us=100.8 residue_s=417")
campaign = tot*(tc*1e6/cnt + gen_io*1e6/cnt + marg)/1e6/3600 + 6000*ts/3600
print(f"projected campaign (this machine, MOD=6000): {campaign:.0f} core-h")
print("  = 18,400,989,629 x (gen_us + genio_us + search_us) / 3.6e9  +  6000 x setup_s / 3600")
print("  laptop reference: 694 core-h")
PY
