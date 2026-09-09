#!/bin/bash
# Sweep the shards Jean Zay did not reach, ON THIS LAPTOP.
#
# The cluster is ~3.3x slower per core than this machine (measured three ways), so the last
# 16% is CHEAPER here than in the queue: ~15.2M hosts at ~10-20 ms/host = 42-85 core-h.
#
# GATE: this may only run if the local partition is IDENTICAL to the cluster's, because a
# shard tag is just a (bucket, start line) pair -- if the buckets differ by even one line the
# tags name different tournaments and the sweep would silently cover the wrong hosts while
# reporting success.  So the bucket counts are compared and a mismatch is FATAL.
set -u
cd "$(dirname "$0")"; HERE=$PWD
W=${N13_WORK:-$HOME/Downloads/n13sc_local}
OUT=${N13_OUT:-$HERE/results_local}
CORES=${N13_CORES:-10}
PER=${N13_PER:-200000}
TAGS=${N13_TAGS:-$HERE/state/missing_shards_jz.txt}
JZC=$HERE/state/jz_counts.tsv
LOG=$HERE/local_sweep.log
mkdir -p "$OUT/done" "$OUT/hits" "$W/shards"
say() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

[ "$CORES" -le 10 ] || { say "FATAL: $CORES cores requested, the cap is 10"; exit 1; }

say "=== GATE: comparing this machine's partition with the cluster's ==="
bad=0
while read -r b c; do
  f="$W/rigid/imb$b.txt"
  [ -f "$f" ] || { say "  imb$b: MISSING locally"; bad=1; continue; }
  g=$(wc -l < "$f" | tr -d ' ')
  if [ "$g" != "$c" ]; then say "  imb$b: local $g != cluster $c"; bad=1; fi
done < "$JZC"
NB_J=$(wc -l < "$JZC" | tr -d ' '); NB_L=$(ls "$W"/rigid/imb*.txt 2>/dev/null | wc -l | tr -d ' ')
[ "$NB_J" = "$NB_L" ] || { say "  bucket COUNT differs: cluster $NB_J, local $NB_L"; bad=1; }
[ "$bad" = 0 ] || { say "FATAL: partitions differ -- the shard tags do NOT name the same hosts here"; exit 1; }
say "  all $NB_J buckets match line for line -- tags are transferable"

# Independent check: the tags must account for exactly (rigid total - swept) hosts.
python3 - "$JZC" "$TAGS" "$PER" <<'PY' | tee -a "$LOG"
import sys
jz, tags, per = sys.argv[1], sys.argv[2], int(sys.argv[3])
cnt = {int(l.split()[0]): int(l.split()[1]) for l in open(jz)}
h = 0
for t in open(tags):
    t = t.strip()
    if not t: continue
    b, lo = t.split("_"); b = int(b[3:]); lo = int(lo)
    assert (lo-1) % per == 0, f"{t}: start off the shard grid"
    assert lo <= cnt[b], f"{t}: start beyond bucket end"
    h += min(per, cnt[b]-lo+1)
print(f"  tags cover {h:,} hosts of {sum(cnt.values()):,} rigid "
      f"({100*h/sum(cnt.values()):.2f}%)")
PY
[ ${PIPESTATUS[0]} -eq 0 ] || { say "FATAL: tag list inconsistent with the bucket counts"; exit 1; }

say "=== sweeping: $(wc -l < "$TAGS" | tr -d ' ') shards, $CORES cores, margin 1, k=5, n=13 ==="
one_shard() {
  tag=$1; W=$2; OUT=$3; PER=$4; HERE=$5
  [ -f "$OUT/done/$tag" ] && return 0
  b=${tag%%_*}; lo=${tag##*_}
  bits="$W/shards/$tag.bits"
  sed -n "${lo},$((lo+PER-1))p" "$W/rigid/$b.txt" > "$bits"
  got=$(wc -l < "$bits" | tr -d ' ')
  "$HERE/../kinduce" --batch "$bits" --n 13 --k 5 --margin exact --inc --time 300 \
      > "$bits.log" 2>&1
  ran=$(grep -c '^BATCH ' "$bits.log")
  if [ "$ran" -ne "$got" ]; then
    echo "$tag: ran $ran of $got -- NOT a verdict, left unmarked" >&2
    rm -f "$bits" "$bits.log"; return 0
  fi
  U=$(grep -c ' UNSAT ' "$bits.log"); A=$(grep -c ' ABORTED ' "$bits.log")
  if [ "$U" -gt 0 ]; then
    echo "*** UNSAT at n=13 margin 1 in $tag -- a NEW smallest known margin-1 obstruction ***"
    grep ' UNSAT ' "$bits.log" | awk '{print $2}' | while read -r i; do
      sed -n "$((i+1))p" "$bits"; done > "$OUT/hits/$tag.bits"
    cat "$OUT/hits/$tag.bits"
  fi
  echo "hosts=$got unsat=$U aborted=$A" > "$OUT/done/$tag"
  rm -f "$bits" "$bits.log"
}
export -f one_shard
t0=$SECONDS
xargs -P "$CORES" -I{} bash -c 'one_shard "$@"' _ {} "$W" "$OUT" "$PER" "$HERE" \
    < "$TAGS" 2>&1 | tee -a "$LOG"
say "=== swept $(ls "$OUT/done" | wc -l | tr -d ' ') of $(wc -l < "$TAGS" | tr -d ' ') shards in $(( (SECONDS-t0)/60 )) min ==="
say "hosts: $(cat "$OUT"/done/* 2>/dev/null | sed 's/hosts=//;s/ .*//' | paste -sd+ - | bc)"
say "UNSAT: $(cat "$OUT"/done/* 2>/dev/null | grep -o 'unsat=[0-9]*' | cut -d= -f2 | paste -sd+ - | bc)"
say "ABORTED: $(cat "$OUT"/done/* 2>/dev/null | grep -o 'aborted=[0-9]*' | cut -d= -f2 | paste -sd+ - | bc)"
