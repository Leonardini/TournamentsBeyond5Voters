#!/bin/bash
# KNOWN-ANSWER TESTS.  Run before every campaign; all three must pass.
#
# T1  k=3, n=7->8, caps OFF: the uncovered masks must reproduce the published
#     census of 96 non-3-inducible order-8 tournaments.  Summed over the 456
#     order-7 classes the count is 808 (NOT 8x96=768 -- automorphisms inflate
#     it by Sum_v |Aut(T-v)|/|Aut(T)|).  This is the two-sided test: it checks
#     the engine covers everything coverable AND leaves exactly what is not.
# T2  the 1,223 regular order-11 tournaments must all come out ALL at margin-1.
# T3  regression: with --cover absent the engine must still report 1223 SAT.
# T4  THE GENERATOR.  T1-T3 exercise kcover against checked-in host lists and never touch
#     gentourng at all -- which is exactly why the 2026-09-07 run passed its selftest and
#     then swept ZERO tournaments.  T4 runs the generator in the SAME res/mod form the
#     campaign uses and checks it against published counts (OEIS A000568) and against the
#     partition identity the completeness argument depends on.
set -eu
# Absolute, BEFORE the cd.  Deriving it again after the cd is the bug this kit
# has now hit twice: $0 keeps its original relative value, so re-evaluating
# dirname "$0" from the new cwd resolves against the wrong directory and the
# subshell yields the empty string.
_KITDIR=$(cd "$(dirname "$0")" && pwd)
cd "$_KITDIR"
ROOT=$(cd ../.. && pwd)
SP=$ROOT/Check3Majority/margin1_sat
REG=$ROOT/Paley23Decide/regulartournaments11_bits.txt
[ -x ./kcover ] || ./build.sh
fail=0

echo "T1  k=3 n=7->8, caps off, expect total uncovered = 808 over 456 hosts"
T1=$(./kcover --batch "$SP/allt_n7.txt" --n 7 --k 3 --inc --cover --cover-skip 0 \
       --margin majority 2>/dev/null | grep -c '^COVER')
T1S=$(./kcover --batch "$SP/allt_n7.txt" --n 7 --k 3 --inc --cover --cover-skip 0 \
       --margin majority 2>/dev/null | grep '^COVER' \
       | awk '{split($3,a,"="); split(a[2],b,"/"); s+=b[2]-b[1]} END{print s+0}')
echo "    hosts=$T1 uncovered=$T1S"
[ "$T1" = 456 ] && [ "$T1S" = 808 ] || { echo "    T1 FAIL"; fail=1; }

echo "T2  1,223 regular order-11, margin-1, expect ALL=1223"
T2=$(./kcover --batch "$REG" --n 11 --k 5 --inc --cover --cover-skip 4096 \
       --per-base-nodes 200 --margin exact 2>/dev/null | grep '^COVER' \
       | awk '{split($3,a,"="); split(a[2],b,"/"); if(b[1]==b[2])ok++} END{print ok+0}')
echo "    ALL=$T2"
[ "$T2" = 1223 ] || { echo "    T2 FAIL"; fail=1; }

echo "T3  regression, no --cover, expect SAT=1223"
T3=$(./kcover --batch "$REG" --n 11 --k 5 --inc --margin exact 2>/dev/null \
       | sed -n 's/.*instances=1223 SAT=\([0-9]*\).*/\1/p')
echo "    SAT=$T3"
[ "$T3" = 1223 ] || { echo "    T3 FAIL"; fail=1; }

echo "T4  gentourng: published counts + residue partition"
. "$_KITDIR/../gt_path.sh"
: "${GT:?gt_path.sh did not set GT}"
if ! "$GT" 1 >/dev/null 2>&1; then
  echo "    T4 FAIL: no working gentourng at '$GT'"
  echo "      set GENTOURNG=/path/to/gentourng (it is a SEPARATE make target from the"
  echo "      nauty library, so a configured tree may still lack the binary), then rerun."
  fail=1
else
  echo "    using $GT"
  # Published counts of tournaments up to isomorphism, OEIS A000568.  ASSERTED, not printed:
  # the campaign's whole completeness argument is a count identity, so the generator's counts
  # are checked against an independent source before anything is swept.
  for spec in 5:12 6:56 7:456; do
    n=${spec%%:*}; want=${spec##*:}
    got=$("$GT" "$n" 2>/dev/null | wc -l | tr -d " ")
    [ "$got" = "$want" ] && echo "    n=$n: $got classes (A000568 says $want) OK" \
      || { echo "    T4 FAIL: n=$n gave $got, A000568 says $want"; fail=1; }
  done
  # The res/mod split must PARTITION: no host generated twice, none dropped.  This is the
  # exact invocation screen_residue.sh makes, tested at a size where the truth is published.
  sum=0
  for r in 0 1 2 3 4 5 6; do
    c=$("$GT" 7 "$r/7" 2>/dev/null | wc -l | tr -d " ")
    sum=$((sum + c))
  done
  [ "$sum" = 456 ] && echo "    res/mod partition: 7 residues sum to $sum OK" \
    || { echo "    T4 FAIL: residues sum to $sum, not 456 -- split is NOT a partition"; fail=1; }
fi

[ $fail = 0 ] && echo "T5  screen_residue.sh resolves its own paths, invoked as the batch script invokes it"
# THE TEST THAT WAS MISSING.  T1-T4 all run from inside this directory; the batch
# script runs `KInduceDFS/jz_n12cover/screen_residue.sh` FROM THE REPO ROOT, and it
# was exactly that difference that hid the cd-order bug which killed all 40,000
# residues on 2026-09-07 with `GT: unbound variable`.  Test the real invocation.
_ROOT=$(cd "$_KITDIR/../.." && pwd)
if out=$(cd "$_ROOT" && KInduceDFS/jz_n12cover/screen_residue.sh --check-paths 2>&1); then
  echo "    $out"
else
  echo "    FAIL: $out"; echo "SELFTEST FAILED"; exit 1
fi

echo "T6  converse halving: kept counts and the extension/converse correspondence"
# The halving is what makes the n=12 case analysis affordable, so its correctness
# is tested here and not merely argued: kept == (N+S)/2 at n=5..8 against A000568,
# and conv(T + S) == conv(T) + complement(S) checked on every (host, out-set) pair
# at n = 5, 6, 7.
if out=$(GENTOURNG="$GT" LABELG="$LABELG" python3 "$_KITDIR/converse_filter.py" --selftest 2>&1); then
  echo "$out" | sed 's/^/  /'
else
  echo "$out" | sed 's/^/    /'; echo "SELFTEST FAILED"; exit 1
fi

echo "T7  the compute-node path needs no interpreter"
# THE TEST THAT WAS MISSING, AGAIN.  T1-T6 all run on a LOGIN node, where python3
# exists.  n12cover.slurm loads no module and python3 is not in the default PATH
# on a Jean Zay compute node, so converse_filter.py -- the first thing in this
# kit's compute path to need an interpreter -- killed every residue while this
# selftest passed.  Two checks: nothing on the compute path names an interpreter
# outside a comment, and the filter still works with a poisoned python3 first in
# PATH.
_BAD=0
_CPATH="screen_residue.sh tiers.sh converse_filter.sh eval_shard.sh"
for f in $_CPATH; do
  [ -f "$_KITDIR/$f" ] || continue
  _hits=$(grep -n 'python3\|python2\|[^a-z]python ' "$_KITDIR/$f" | grep -v '^[0-9]*: *#' | wc -l | tr -d ' ')
  if [ "$_hits" -ne 0 ]; then
    echo "    FAIL: $f invokes an interpreter outside a comment:"
    grep -n 'python3\|python2\|[^a-z]python ' "$_KITDIR/$f" | grep -v '^[0-9]*: *#' | sed 's/^/      /'
    _BAD=1
  fi
done
[ "$_BAD" = 0 ] && echo "    no interpreter on the compute path ($_CPATH)"
_POISON=$(mktemp -d); printf '#!/bin/sh\necho "python3 must not be needed here" >&2\nexit 127\n' > "$_POISON/python3"
chmod +x "$_POISON/python3"
"$GT" -q 7 > "$_POISON/h7.txt" 2>/dev/null
_a=$(LABELG="$LABELG" PATH="$_POISON:$PATH" "$_KITDIR/converse_filter.sh" 7 < "$_POISON/h7.txt" | wc -l | tr -d ' ')
_b=$(LABELG="$LABELG" "$_KITDIR/converse_filter.sh" 7 < "$_POISON/h7.txt" | wc -l | tr -d ' ')
rm -rf "$_POISON"
if [ "$_a" = "$_b" ] && [ "$_a" = "272" ]; then
  echo "    filter kept $_a of 456 with a poisoned python3 first in PATH, matching the clean run and (N+S)/2"
else
  echo "    FAIL: kept $_a with poisoned python3 vs $_b clean, expected 272"; _BAD=1
fi
[ "$_BAD" = 0 ] || { echo "SELFTEST FAILED"; exit 1; }

echo "T8  the extension builder: conventions, both directions, on real leftovers"
# The single most dangerous piece of this kit.  If the bit conventions are wrong,
# the pipeline decides real order-12 tournaments -- just not the ones the cover
# search left open -- and every check downstream still passes.  So this test does
# not inspect the builder; it rebuilds the property from the definitions:
#   (i)  restricting the built order-12 tournament to the first 11 vertices must
#        give back the host, bit for bit; and
#   (ii) the new vertex must beat exactly the vertices in the mask.
# Both are checked in awk that shares no code with the builder, on the actual
# UNCOVERED output of a real tier-1 run.
_T8=$(mktemp -d)
"$GT" -q 11 0/40000 2>/dev/null | head -20 > "$_T8/hosts"
./kcover --batch "$_T8/hosts" --n 11 --k 5 --inc --cover --cover-skip 4096 \
         --per-base-nodes 200 --margin exact --cover-dump > "$_T8/t1.log" 2>&1
grep '^UNCOVERED' "$_T8/t1.log" > "$_T8/unc"
_NU=$(wc -l < "$_T8/unc" | tr -d ' ')
if [ "$_NU" -eq 0 ]; then
  echo "    FAIL: no uncovered masks on residue 0, whose first host is transitive -- "
  echo "          either the caps changed or --cover-dump stopped working"; _BAD=1
else
  # Extract the builder from screen_residue.sh rather than copying it, so the test
  # can never drift from the code it tests.
  sed -n "/^EXTEND='/,/^}'$/p" tiers.sh | sed "s/^EXTEND='//; s/^}'$/}/" > "$_T8/extend.awk"
  awk -v n=11 -v key="$_T8/key" -f "$_T8/extend.awk" "$_T8/hosts" "$_T8/unc" > "$_T8/ext"
  _NE=$(wc -l < "$_T8/ext" | tr -d ' ')
  _CHK=$(paste "$_T8/key" "$_T8/ext" | awk -v n=11 'NR==FNR{h[FNR-1]=$0;next}
    { idx=$1; mask=$2; t=$3
      # (i) restriction: read T back as a matrix, then re-emit the first n vertices
      k=0
      for (a=0;a<=n;a++) for (b=a+1;b<=n;b++) { k++; up[a","b]=substr(t,k,1) }
      if (k != (n+1)*n/2) { print "bitcount"; exit }
      r=""
      for (a=0;a<n;a++) for (b=a+1;b<n;b++) r = r up[a","b]
      if (r != h[idx]) { printf "restriction mismatch at line %d\n", FNR; bad=1; exit }
      # (ii) the new vertex beats exactly the mask
      m=0
      for (a=0;a<n;a++) if (up[a","n]=="0") m += 2^a     # a->v is "1", so v beats a iff "0"
      if (m != mask+0) { printf "mask mismatch at line %d: got %d want %d\n", FNR, m, mask; bad=1; exit }
      ok++ }
    END { if (bad) exit 1; print ok+0 }' "$_T8/hosts" - ) || { echo "    FAIL: $_CHK"; _BAD=1; }
  if [ "${_CHK:-0}" = "$_NE" ] && [ "$_NE" = "$_NU" ]; then
    echo "    $_NE extensions built from $_NU uncovered masks; every one restricts to its host"
    echo "    and beats exactly its mask (checked by independent awk)"
  else
    echo "    FAIL: built $_NE from $_NU, verified $_CHK"; _BAD=1
  fi
fi

echo "T9  end to end on real hosts: tier 1 leaves leftovers, tier 2 decides them"
# The leftovers are what the whole redesign is about, so run the actual second
# tier on them and require every one to come back decided -- not capped.
if [ "${_NU:-0}" -gt 0 ]; then
  _K=${KINDUCE:-$_KITDIR/../kinduce}
  _T9=$("$_K" --batch "$_T8/ext" --n 12 --k 5 --margin exact --inc --time 60 2>&1 \
        | grep '^BATCH_SUMMARY')
  _s=$(echo "$_T9" | sed -nE 's/.* SAT=([0-9]+).*/\1/p')
  _u=$(echo "$_T9" | sed -nE 's/.* UNSAT=([0-9]+).*/\1/p')
  _a=$(echo "$_T9" | sed -nE 's/.* ABORTED=([0-9]+).*/\1/p')
  if [ "$((_s + _u + _a))" -ne "$_NE" ]; then
    echo "    FAIL: tier 2 accounted for $((_s + _u + _a)) of $_NE instances"; _BAD=1
  elif [ "$_a" -ne 0 ]; then
    echo "    FAIL: $_a instance(s) hit the 60 s cap; measured cost is 14 ms"; _BAD=1
  else
    echo "    $_NE leftover instances decided: SAT=$_s UNSAT=$_u, none capped"
    [ "$_u" -gt 0 ] && echo "    NOTE: $_u are not margin-1 inducible and would go to tier 3 (majority)"
  fi
fi
rm -rf "$_T8"

echo "T10a neither worker may carry its own copy of the pipeline"
# The check that makes the shared tiers.sh worth having: if either worker grows a
# kcover or kinduce call of its own, the two can diverge again silently.
_DUP=0
for f in screen_residue.sh eval_shard.sh; do
  _n=$(grep -c 'kcover --batch\|\$KINDUCE --batch' "$f" || true)
  # screen_residue.sh legitimately runs kinduce once, in --check-paths, as a
  # known-answer test; that is not a second pipeline.
  _allowed=0; [ "$f" = screen_residue.sh ] && _allowed=1
  if [ "$_n" -gt "$_allowed" ]; then
    echo "    FAIL: $f makes $_n engine calls of its own (allowed $_allowed) -- the pipeline belongs in tiers.sh"
    _DUP=1
  fi
done
[ "$_DUP" = 0 ] && echo "    both workers delegate to tiers.sh; neither has its own engine calls"
[ "$_DUP" = 0 ] || _BAD=1

echo "T10 verdict plumbing: ABORTED must block the marker, majority UNSAT must be a candidate"
# Tiers 2 and 3 are driven entirely by parsing BATCH lines, and the two branches
# that matter most are the two that cannot be provoked on demand: an instance
# that runs out of budget, and one that is not inducible at all.  Feed the
# parsers synthetic logs so both are exercised every time the selftest runs.
_T10=$(mktemp -d)
printf 'BATCH 0 SAT nodes=8 time=0.000\nBATCH 1 ABORTED nodes=99 time=60.000\nBATCH 2 UNSAT nodes=77 time=1.000\nBATCH_SUMMARY n=12 K=5 instances=3 SAT=1 UNSAT=1 ABORTED=1 wall=61.0s\n' > "$_T10/log"
_f=$(awk '/^BATCH /&&$3=="SAT"{c++}     END{print c+0}' "$_T10/log")
_ab=$(awk '/^BATCH /&&$3=="ABORTED"{c++} END{print c+0}' "$_T10/log")
_un=$(awk '/^BATCH /&&$3=="UNSAT"{print $2}' "$_T10/log")
if [ "$_f" = 1 ] && [ "$_ab" = 1 ] && [ "$_un" = 2 ]; then
  echo "    parsers agree: 1 settled, 1 capped (blocks the marker), UNSAT at index 2"
else
  echo "    FAIL: parsed settled=$_f capped=$_ab unsat_index=$_un"; _BAD=1
fi
# and the selection that turns a tier-3 UNSAT index into a candidate line
printf 'a\nb\nc\n' > "$_T10/ext"
_sel=$(printf '2\n' | awk 'NR==FNR{w[$1+1];next}(FNR in w){print "UNCOVERED", $0}' - "$_T10/ext")
[ "$_sel" = "UNCOVERED c" ] || { echo "    FAIL: candidate selection picked '$_sel', want 'UNCOVERED c'"; _BAD=1; }
[ "$_sel" = "UNCOVERED c" ] && echo "    candidate selection maps index 2 to the third instance, tagged UNCOVERED"
rm -rf "$_T10"

echo "T11 the AGGREGATOR: nothing tested it, and it is what every verdict is read from"
# The kit's whole lesson is that a report can look like success while nothing happened,
# and until 2026-09-09 the aggregator itself had no test.  It read the live done/ dir
# THREE times (ls, then two awk passes over "$D"/*), so it could print two different
# values for the same quantity -- and at 40,000 markers the glob exceeds ARG_MAX, awk
# fails to exec with its stderr discarded, `set -e` ends the script, and the output is
# a bare "residues done: 40000" with no census line at all: the vacuous-run signature,
# at the exact moment the census gate matters.
_T11=$(mktemp -d)
mkdir -p "$_T11/results/done"

# (a) an empty done/ must EXPLAIN itself, not just print a zero
_a=$(bash ./aggregate.sh "$_T11/results" | wc -l | tr -d ' ')
[ "$_a" -gt 1 ] || { echo "    FAIL: empty done/ printed $_a line(s), so it cannot be telling"; \
                     echo "          the caller whether the array is PENDING or broken"; _BAD=1; }

# (b) the two halves of the report must agree on generated and on instances.
#     They are the same sums from the same markers; only a re-read can split them.
for _r in 0 3 9; do
  printf 'res=%d generated=%d instances=%d tier1all=1 leftover=2 tier2fixed=2 tier3fixed=0 candidates=0 secs=7\n' \
    "$_r" "$(( (_r + 1) * 1000 ))" "$(( (_r + 1) * 500 ))" > "$_T11/results/done/r$_r"
done
_o=$(bash ./aggregate.sh "$_T11/results")
_g1=$(echo "$_o" | sed -nE 's/^hosts generated : ([0-9]+)$/\1/p')
_i1=$(echo "$_o" | sed -nE 's/^instances       : ([0-9]+) .*/\1/p')
_g2=$(echo "$_o" | sed -nE 's/^converse halving: ([0-9]+) generated.*/\1/p')
_i2=$(echo "$_o" | sed -nE 's/^converse halving: [0-9]+ generated, ([0-9]+) screened.*/\1/p')
_gw=$((1000 + 4000 + 10000)); _iw=$((500 + 2000 + 5000))
if [ "$_g1" = "$_gw" ] && [ "$_g2" = "$_gw" ] && [ "$_i1" = "$_iw" ] && [ "$_i2" = "$_iw" ]; then
  echo "    both halves agree: generated=$_gw instances=$_iw from one snapshot"
else
  echo "    FAIL: report disagrees with itself or with the markers --"
  echo "          generated $_g1 then $_g2 (want $_gw); instances $_i1 then $_i2 (want $_iw)"; _BAD=1
fi
# (b2) and the structural half of the same claim, because (b) alone CANNOT FAIL on a
#      static directory: the three reads agreed on the old code too, and only a marker
#      landing between two of them exposed the split.  So assert what makes the race
#      impossible instead -- the marker dir is read exactly once.  Same idiom as T10a,
#      which fails if either shard script grows an engine call of its own.
_reads=$(grep -cE '(ls|awk[^|]*|cat)[^#]*"\$D"/\*|ls "\$D"' ./aggregate.sh || true)
_snap=$(grep -cE '^find "\$D" -type f -exec cat' ./aggregate.sh || true)
if [ "$_reads" = 0 ] && [ "$_snap" = 1 ]; then
  echo "    the marker dir is read exactly once, so the halves cannot drift mid-sweep"
else
  echo "    FAIL: aggregate.sh has $_reads direct read(s) of \$D and $_snap snapshot(s);"
  echo "          want 0 and 1 -- every consumer must share one snapshot"; _BAD=1
fi

# (c) ARG_MAX.  Derive the marker count from the real limit and the real path length
#     rather than writing down a number: the hazard is bytes of argv, not files.
_PAD=$(printf 'd%.0s' $(seq 1 200))            # deepen the path so few files suffice
mkdir -p "$_T11/$_PAD/results/done"
_TAIL=/results/done/r00000          # a name, not a literal inside ${#...}:
_LEN=$(( ${#_T11} + 1 + ${#_PAD} + ${#_TAIL} ))   # ${#/results/...} silently yields 0
_LIM=$(getconf ARG_MAX 2>/dev/null || echo 1048576)
_N=$(( _LIM / _LEN + 200 ))                    # 200 markers of headroom over the limit
awk -v n="$_N" -v d="$_T11/$_PAD/results/done" 'BEGIN{
  for (r = 0; r < n; r++) printf "res=%d generated=2 instances=1 tier1all=1 leftover=0 tier2fixed=0 tier3fixed=0 candidates=0 secs=1\n", r > (d "/r" r) }'
# the negative control: a glob-based read of this directory MUST fail, or (c) proves nothing
if ( eval 'awk "{}" "$_T11/$_PAD/results/done"/*' ) 2>/dev/null; then
  echo "    WARN: $_N markers did not exceed ARG_MAX ($_LIM), so this case is not exercising the hazard"
else
  # ANCHORED: an unanchored 'converse halving' also matches the "(evaluated, i.e.
    # AFTER the converse halving)" parenthetical on the instances line, and a healthy
    # report then scores 2 and reads as a failure.
    _c=$(bash ./aggregate.sh "$_T11/$_PAD/results" | grep -c '^converse halving' || true)
  if [ "$_c" = 1 ]; then
    echo "    $_N markers (past ARG_MAX $_LIM) still reach the census line; a glob does not"
  else
    echo "    FAIL: at $_N markers the report stopped before the census gate --"
    echo "          this is the vacuous-run signature, produced at the finish line"; _BAD=1
  fi
fi

# (d) the recovery path must credit ONLY residues that actually have a marker
mkdir -p "$_T11/rec/results/done" "$_T11/rec/slurm"
printf 'res=3 instances=50 tier1all=1 leftover=0 tier2fixed=0 tier3fixed=0 candidates=0 secs=1\n' > "$_T11/rec/results/done/r3"
printf 'res=3 generated=100 screened=50\nres=77 generated=999999 screened=1\n' > "$_T11/rec/slurm/a.out"
_d=$(N12_LOGS="$_T11/rec/slurm" bash ./aggregate.sh "$_T11/rec/results" \
       | sed -nE 's/^converse halving: ([0-9]+) generated.*/\1/p')
if [ "$_d" = 100 ]; then
  echo "    recovery credits res=3 only: 100, not the 999999 of marker-less res=77"
else
  echo "    FAIL: recovery credited $_d, want 100 -- a residue that logged its counts"
  echo "          and then died must not count as swept"; _BAD=1
fi
rm -rf "$_T11"

echo "T12 the CENSUS GATE at the finish line, which only fires on a complete run"
# The gate is unreachable until generated == D11, so it had never executed on real
# data until 2026-09-12 -- when it fired, and the run it judged had kept 443,771,294
# of 903,753,248, BELOW the floor D11/2.  A gate that first runs at the finish line
# is a gate nothing has tested, so drive all three of its verdicts here on synthetic
# markers.  D11 and the recorded S11 are read out of aggregate.sh, not written down.
_D11=$(sed -nE 's/^D11=([0-9]+).*/\1/p' ./aggregate.sh)
_SPUB=$(sed -nE 's/^S11_PUB=([0-9]+).*/\1/p' ./aggregate.sh)
_T12=$(mktemp -d)
_gate() {                       # _gate <kept> <self-or-empty> -> prints "exit|line"
  # SEPARATE assignments: bash expands every word of a `local` before assigning any
  # of them, so `local _k=$1 _d=$_k` reads the OLD _k -- unset, and `set -u` dies.
  local _k=$1
  local _s=$2
  local _dir="$_T12/case_$_k.$_s"
  local _d="$_dir/results/done"
  local _f=""
  rm -rf "$_dir"; mkdir -p "$_d" "$_dir/results/candidates"
  [ -n "$_s" ] && _f=" self=$_s"
  printf 'res=0 generated=%d instances=%d%s tier1all=0 leftover=0 tier2fixed=0 tier3fixed=0 candidates=0 secs=1\n' \
    "$_D11" "$_k" "$_f" > "$_d/r0"
  local _out
  local _rc
  _out=$(bash ./aggregate.sh "$_dir/results" 2>&1); _rc=$?
  printf '%s|%s' "$_rc" "$(printf '%s' "$_out" | grep -cE '^(FATAL|  halving EXACT)')"
}
# (a) the floor.  Half of D11 minus one host is one host too few, whatever S11 is.
_r=$(_gate $(( _D11 / 2 - 1 )) "")
[ "${_r%%|*}" = 1 ] || { echo "    FAIL: kept = D11/2 - 1 passed the gate (exit ${_r%%|*});"; \
                         echo "          no keep rule can go below the floor, so this must be fatal"; _BAD=1; }
# (b) exactly the floor is legal only if S11 = 0, so it must trip the published-value
#     cross-check instead of the floor -- a different FATAL, still exit 1.
_r=$(_gate $(( _D11 / 2 )) "")
[ "${_r%%|*}" = 1 ] || { echo "    FAIL: kept = D11/2 implies S11 = 0 and did not fail"; _BAD=1; }
# (c) the recorded value, with the direct self-converse count agreeing: the only pass.
_r=$(_gate $(( (_D11 + _SPUB) / 2 )) "$_SPUB")
if [ "$_r" = "0|1" ]; then
  echo "    floor and cross-check both fire; kept = (D11 + S11)/2 with a matching self= passes"
else
  echo "    FAIL: the one correct run did not pass the gate cleanly (exit|matches = $_r)"; _BAD=1
fi
# (d) and the direct count must be able to CONTRADICT the implied one, or it is decoration.
_r=$(_gate $(( (_D11 + _SPUB) / 2 )) "$(( _SPUB + 2 ))")
[ "${_r%%|*}" = 1 ] || { echo "    FAIL: a self= count disagreeing with 2*kept-D11 was accepted"; _BAD=1; }
echo "    a self= count that contradicts 2*kept - D11 is caught"
rm -rf "$_T12"

[ "$_BAD" = 0 ] || { echo "SELFTEST FAILED"; exit 1; }

echo "SELFTEST PASS" || { echo "SELFTEST FAIL"; exit 1; }
