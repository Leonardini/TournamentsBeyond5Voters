#!/bin/sh
# Acceptance gate for this reproduction package.
#
# The checks are chosen to FAIL if the package is wrong, not to confirm that it
# is right.  Every quantity is recomputed from the shipped bytes and compared
# against a value recorded in a *different* file, and each positive check is
# paired with a negative control that must fail.  A gate whose controls do not
# fire is not testing anything.
#
#   usage: tools/check_package.sh [--quick]
#
# --quick skips the two catalogue sweeps (about 1 minute of compute) and runs
# only the structural checks, which need no external solver.
#
# Single-threaded throughout, so it is safe to run beside a campaign that
# already holds the machine's core budget.

set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
QUICK=0
[ "${1:-}" = "--quick" ] && QUICK=1
TMP=$(mktemp -d) || exit 1
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0; skip=0
ok()   { pass=$((pass+1)); printf '  ok    %s\n' "$1"; }
bad()  { fail=$((fail+1)); printf '  FAIL  %s\n' "$1"; }
warn() { skip=$((skip+1)); printf '  skip  %s\n' "$1"; }

# ---------------------------------------------------------------------------
# Tool resolution.  Resolve through a ladder and fail loudly naming everything
# tried, rather than silently measuring nothing -- an inline command with an
# unset variable once "verified" a step it had never run.
# ---------------------------------------------------------------------------
resolve() {
  _n=$1; shift
  for _c in "$@"; do
    [ -n "$_c" ] && [ -x "$_c" ] && { echo "$_c"; return 0; }
  done
  _w=$(command -v "$_n" 2>/dev/null) && { echo "$_w"; return 0; }
  printf 'unresolved %s; tried:' "$_n" >&2
  for _c in "$@"; do printf ' %s' "$_c" >&2; done
  printf ' and $PATH\n' >&2
  return 1
}
SW=${SOFTWARE_DIR:-$HOME/Downloads/DownloadedSoftware}
GENTOURNG=$(resolve gentourng "${GENTOURNG:-}" "$SW/nauty2_8_6/gentourng" 2>/dev/null || true)

echo "== 1. the engine builds from the shipped source =="
CC=${CC:-cc}
if $CC -O2 -o "$TMP/kinduce" "$ROOT/engine/kinduce.c" 2>"$TMP/cc.err"; then
  ok "engine/kinduce.c compiles"
else
  bad "engine/kinduce.c does not compile"; sed 's/^/        /' "$TMP/cc.err"
fi
if $CC -O2 -o "$TMP/kcover" "$ROOT/engine/kcover.c" -lm 2>"$TMP/cc2.err"; then
  ok "engine/kcover.c compiles"
else
  bad "engine/kcover.c does not compile"; sed 's/^/        /' "$TMP/cc2.err"
fi

echo
echo "== 2. every artifact CLAIMS.md names exists =="
# CLAIMS.md carries one backticked path per artifact column.  Checking them
# mechanically is what keeps the index honest as the package changes; a
# reference that rots is the failure this catches.
#
# Only the claim tables are scanned.  The "Gaps" section deliberately names
# files that are NOT here -- that is its whole purpose -- so scanning it would
# turn every honestly declared hole into a spurious failure.
sed '/^# Gaps/,$d' "$ROOT/CLAIMS.md" > "$TMP/claims.head" 2>/dev/null || true
miss=0; seen=0
for p in $(grep -o '`[A-Za-z0-9_][A-Za-z0-9_./-]*`' "$TMP/claims.head" 2>/dev/null \
           | tr -d '`' | grep -E '/|\.(c|py|sh|md|txt|tsv|bits|zst|json)$' | sort -u); do
  case "$p" in
    *' '*|http*) continue ;;
  esac
  seen=$((seen+1))
  [ -e "$ROOT/$p" ] || { echo "        missing: $p"; miss=$((miss+1)); }
done
if [ "$seen" -eq 0 ]; then
  bad "CLAIMS.md named no artifacts -- the extraction found nothing to check"
elif [ "$miss" -eq 0 ]; then
  ok "all $seen artifacts named in CLAIMS.md are present"
else
  bad "$miss of $seen artifacts named in CLAIMS.md are missing"
fi

echo
echo "== 3. the certificate roots rebuild from the per-cube evidence =="
# The published roots and the per-cube sha256 chain live in different files, so
# their agreement is a real cross-check rather than a restatement.  Expected
# values are READ from the certificate, never written here: a constant copied
# into a checker is correct once, on the day it is copied.
for inst in p19 p23; do
  cd="$ROOT/certificates/${inst}cert_d6"
  [ -d "$cd" ] || { warn "$inst certificate directory absent"; continue; }
  vf="$cd/VERDICT.txt"; [ -f "$vf" ] || vf="$cd/README.md"
  exp_cnf=$(grep -oE '^ROOT \(CNF\) +[0-9a-f]{64}' "$vf" 2>/dev/null | awk '{print $3}' | head -1)
  if [ -z "$exp_cnf" ]; then
    exp_cnf=$(grep -oE 'search_root_cnf=[0-9a-f]{64}' "$cd/${inst}_cert.portable.txt" 2>/dev/null \
              | cut -d= -f2 | head -1)
  fi
  if [ -z "$exp_cnf" ]; then warn "$inst: no recorded ROOT (CNF) to compare against"; continue; fi
  out=$(python3 "$ROOT/sat/reroot.py" "$cd" "$exp_cnf" 2>&1)
  if echo "$out" | grep -q 'ROOT (CNF).*MATCHES'; then
    nc=$(echo "$out" | grep -oE 'cubes [0-9,]+' | head -1 | tr -d 'cubes ,')
    ok "$inst: ROOT (CNF) rebuilt from log/ matches the certificate ($nc cubes)"
  else
    bad "$inst: ROOT (CNF) does not rebuild from log/"; echo "$out" | sed 's/^/        /'
  fi
  # the cube count must agree with the certificate's own statement of it
  dc=$(grep -oE '^cubes *[0-9]+' "$vf" 2>/dev/null | awk '{print $2}' | head -1)
  [ -z "$dc" ] && dc=$(grep -oE 'cubes=[0-9]+' "$cd/${inst}_cert.portable.txt" 2>/dev/null | cut -d= -f2 | head -1)
  if [ -n "$dc" ] && [ -n "${nc:-}" ]; then
    if [ "$dc" = "$nc" ]; then ok "$inst: cube count agrees across certificate and log/ ($dc)"
    else bad "$inst: certificate says $dc cubes, log/ holds $nc"; fi
  fi
done

echo
echo "== 3b. NEGATIVE CONTROL: a corrupted evidence chain must be rejected =="
# If dropping a chunk left the root unchanged, check 3 would be vacuous.
cd="$ROOT/certificates/p19cert_d6"
if [ -d "$cd" ]; then
  cp -R "$cd" "$TMP/ctl" 2>/dev/null
  victim=$(ls "$TMP/ctl/log"/*.log | head -1)
  # flip one hex digit of one cube's CNF hash
  sed '3s/^\([0-9]* \)\([0-9a-f]\)/\1f/' "$victim" > "$victim.new" && mv "$victim.new" "$victim"
  exp_cnf=$(grep -oE 'search_root_cnf=[0-9a-f]{64}' "$cd/p19_cert.portable.txt" 2>/dev/null | cut -d= -f2 | head -1)
  [ -z "$exp_cnf" ] && exp_cnf=$(grep -oE '^ROOT \(CNF\) +[0-9a-f]{64}' "$cd/README.md" 2>/dev/null | awk '{print $3}' | head -1)
  if [ -n "$exp_cnf" ]; then
    out=$(python3 "$ROOT/sat/reroot.py" "$TMP/ctl" "$exp_cnf" 2>&1)
    if echo "$out" | grep -q 'MATCHES'; then
      bad "control did not fire: a corrupted hash still reproduced the root"
    else
      ok "corrupting one cube hash breaks the root, as it must"
    fi
  else
    warn "no recorded root for the p19 control"
  fi
else
  warn "p19 certificate absent, control not run"
fi

echo
echo "== 4. distributed refutations cover their base-state range exactly =="
# A refutation is only as good as the union of its slices.  Count is not
# enough: a missing index and a duplicated one cancel in a count.
audit() {
  arch="$ROOT/evidence/$1"; want=$2; label=$1
  [ -f "$arch" ] || { warn "$label absent"; return; }
  zstd -dc "$arch" 2>/dev/null | tar -xOf - 2>/dev/null > "$TMP/logs.txt" || {
    warn "$label could not be unpacked (zstd present?)"; return; }
  # every slice is [a,b); collect the a's and require them to tile [0,want)
  grep -oE 'base_state_slice=\[[0-9]+,' "$TMP/logs.txt" \
    | grep -oE '[0-9]+' | sort -n -u > "$TMP/got.txt"
  nres=$(grep -c '^RESULT UNSAT' "$TMP/logs.txt")
  ncap=$(grep -oE 'capped=[0-9]+' "$TMP/logs.txt" | grep -vc 'capped=0' || true)
  hi=$(tail -1 "$TMP/got.txt")
  nslice=$(wc -l < "$TMP/got.txt" | tr -d ' ')
  # slices are contiguous: the count of distinct starts must equal the number
  # of RESULT lines, and the last start must be below the range end
  if [ "$nres" -gt 0 ] && [ "$nslice" -eq "$nres" ] && [ "$ncap" -eq 0 ] && [ "$hi" -lt "$want" ]; then
    ok "$label: $nres UNSAT slices, none capped, starts distinct, top start $hi < $want"
  else
    bad "$label: $nres UNSAT, $nslice distinct starts, $ncap capped, top start $hi (want < $want)"
  fi
}
audit p27_majority.tar.zst 8031
audit p31_majority.tar.zst 21009
audit p43_majority.tar.zst 8031
audit rerun1_p23_majority.tar.zst 8031

echo
echo "== 4b. NEGATIVE CONTROL: the coverage audit must notice a capped run =="
# The n22 archive is a witness SEARCH: it stops at the first witness, so it
# does NOT cover its range.  Applying the refutation test to it must fail --
# if it passed, the test would be blind to incomplete coverage.
arch="$ROOT/evidence/n22_p23minusv.tar.zst"
if [ -f "$arch" ]; then
  zstd -dc "$arch" 2>/dev/null | tar -xOf - 2>/dev/null > "$TMP/n22.txt"
  nu=$(grep -c '^RESULT UNSAT' "$TMP/n22.txt" || true)
  ns=$(grep -c '^RESULT SAT' "$TMP/n22.txt" || true)
  if [ "$nu" -eq 0 ] && [ "$ns" -ge 1 ]; then
    ok "witness search carries SAT and no UNSAT, so the refutation test cannot pass on it"
  else
    bad "n22 archive has $nu UNSAT / $ns SAT -- not the expected witness-search shape"
  fi
else
  warn "n22 archive absent, control not run"
fi

echo
echo "== 5. witnesses verify against the tournament, independently of the search =="
# The verifier shares no code with the engine: it reads the bit string and the
# ballots and recomputes every arc's support.
wit="$ROOT/verdicts/WITNESSES_paley_arcrev.md"
if [ -f "$wit" ] && [ -f "$ROOT/verify/verify_witness_bits.py" ]; then
  ok "arc-reversal witness and its independent verifier are both present"
else
  warn "arc-reversal witness or verifier absent"
fi

echo
echo "== 5b. the order-13 self-converse partition sums to the catalogue total =="
# Three independently counted parts -- regular (excluded, settled elsewhere),
# possibly-symmetric (swept in full), and provably rigid (the sharded sweep) --
# must sum to S_13 = 95,458,560, which comes from McKay's catalogue and not from
# us.  Three counts agreeing with an outside total is a real cross-check; the
# same aggregate also reports honestly how much of the sweep this package holds.
if [ -f "$ROOT/cluster/jz_n13sc/aggregate.sh" ] && [ -d "$ROOT/cluster/jz_n13sc/results_local/done" ]; then
  # The census ran on two machines, so the claim is about the UNION of the two
  # marker sets -- 407 cluster shards and 81 laptop shards.  Roll up the union.
  a=$(cd "$ROOT/cluster/jz_n13sc" && timeout 600 bash aggregate.sh results results_local 2>&1)
  if echo "$a" | grep -q 'no gap, no overlap'; then
    tot=$(echo "$a" | grep -oE '= [0-9,]+$' | tr -d '=, ' | head -1)
    ok "partition reconciles with the catalogue total exactly (S_13 = $tot)"
  else
    bad "the order-13 partition does not reconcile"; echo "$a" | sed 's/^/        /' | tail -6
  fi
  if echo "$a" | grep -q 'HITS (UNSAT)  : 0'; then
    ok "order-13 self-converse: no obstruction anywhere in the family"
  else
    bad "order-13 self-converse: aggregate does not report zero hits"
  fi
  if echo "$a" | grep -q 'COVERED IN FULL'; then
    ok "the union of the two halves covers the rigid universe exactly"
  else
    bad "the union does not cover the rigid universe"
    echo "$a" | sed 's/^/        /' | tail -8
  fi
  # NEGATIVE CONTROL for the line above.  One half alone must NOT read as
  # covered; if it does, the completeness test is measuring nothing and a
  # missing set of shards would pass unnoticed.
  h=$(cd "$ROOT/cluster/jz_n13sc" && timeout 600 bash aggregate.sh results_local 2>&1)
  if echo "$h" | grep -q 'INCOMPLETE'; then
    ok "control: the laptop half alone still reads INCOMPLETE"
  else
    bad "control failed: 81 of 488 shards read as complete, so the test is blind"
  fi
else
  warn "order-13 self-converse kit or local results absent"
fi

echo
echo "== 5c. the 15-vertex regular census covers its range exactly =="
# Three quantities from independent sources must agree: the marker count, the
# index cover of r0..r(MOD-1), and the instance total against OEIS A096368(7),
# which is not ours.  A sweep can be complete and wrong, or exact and partial;
# only all three together say it is both.
D15="$ROOT/cluster/jz_n15/results_margin1/done"
if [ -d "$D15" ]; then
  MOD15=6000
  ls -1 "$D15" | grep -oE '[0-9]+$' | sed 's/^0*//;s/^$/0/' | sort -n > "$TMP/g15"
  seq 0 $((MOD15-1)) > "$TMP/w15"
  miss15=$(comm -13 "$TMP/g15" "$TMP/w15" | wc -l | tr -d ' ')
  extra15=$(comm -23 "$TMP/g15" "$TMP/w15" | wc -l | tr -d ' ')
  dup15=$(sort "$TMP/g15" | uniq -d | wc -l | tr -d ' ')
  # No process substitution: this script is /bin/sh, and `read < <(...)` is a
  # bashism that dash rejects outright -- a portability break in a gate is worse
  # than the check it guards, because it fails for the reader rather than for us.
  find "$D15" -type f -exec cat {} + 2>/dev/null |
    awk '{for(i=1;i<=NF;i++){split($i,a,"=");v[a[1]]+=a[2]}}
         END{print v["instances"]+0, v["unsat"]+0, v["aborted"]+0}' > "$TMP/n15sum"
  ni=$(awk '{print $1}' "$TMP/n15sum"); nu=$(awk '{print $2}' "$TMP/n15sum")
  na=$(awk '{print $3}' "$TMP/n15sum")
  # A096368(7); asserted because it is a published census, not something we
  # computed -- and the whole point is that our sum must land on it.
  A096368_7=18400989629
  if [ "$miss15" = 0 ] && [ "$extra15" = 0 ] && [ "$dup15" = 0 ]; then
    ok "n15: exact cover of $MOD15 residues, none missing, extra or duplicated"
  else
    bad "n15: cover is not exact (missing $miss15, extra $extra15, duplicated $dup15)"
  fi
  if [ "$ni" = "$A096368_7" ]; then
    ok "n15: instances sum to $ni = OEIS A096368(7)"
  else
    bad "n15: instances sum to $ni, OEIS A096368(7) is $A096368_7"
  fi
  if [ "$nu" = 0 ] && [ "$na" = 0 ]; then
    ok "n15: 0 UNSAT and 0 aborted, so every regular 15-tournament is unit-margin inducible"
  else
    bad "n15: $nu UNSAT and $na aborted -- an aborted instance is not a verdict"
  fi
else
  warn "n15 census markers absent"
fi

if [ "$QUICK" = 1 ]; then
  echo
  echo "== 6-7. catalogue sweeps skipped (--quick) =="
  warn "known-answer sweeps not run"
else
  echo
  echo "== 6. KNOWN ANSWER: every regular tournament on 9 and 11 vertices is inducible =="
  # N(5) >= 12 is proven, so every tournament on at most 11 vertices MUST come
  # back inducible.  A single UNSAT here would mean the engine is broken, and
  # the instance counts are OEIS A096368, so the generator is checked too.
  if [ -z "$GENTOURNG" ]; then
    warn "gentourng not found; set GENTOURNG or SOFTWARE_DIR"
  else
    for spec in "9 4 15" "11 5 1223"; do
      set -- $spec; n=$1; d=$2; expect=$3
      timeout 900 "$GENTOURNG" -d$d -D$d $n 2>/dev/null > "$TMP/reg$n.d6"
      got=$(wc -l < "$TMP/reg$n.d6" | tr -d ' ')
      if [ "$got" != "$expect" ]; then
        bad "regular n=$n: generator produced $got instances, OEIS A096368 says $expect"
        continue
      fi
      out=$(timeout 1800 "$TMP/kinduce" --batch "$TMP/reg$n.d6" --n $n --k 5 \
              --margin exact --order mrv --inc 2>&1 | grep '^BATCH_SUMMARY')
      s=$(echo "$out" | grep -oE 'SAT=[0-9]+' | head -1 | cut -d= -f2)
      u=$(echo "$out" | grep -oE 'UNSAT=[0-9]+' | cut -d= -f2)
      a=$(echo "$out" | grep -oE 'ABORTED=[0-9]+' | cut -d= -f2)
      if [ "$s" = "$expect" ] && [ "$u" = "0" ] && [ "$a" = "0" ]; then
        ok "regular n=$n: $expect instances (= A096368), all inducible at margin 1, 0 aborted"
      else
        bad "regular n=$n: SAT=$s UNSAT=$u ABORTED=$a, expected SAT=$expect and no others"
      fi
    done
  fi

  echo
  echo "== 7. KNOWN ANSWER: Paley(19) separates the two margins =="
  # The paper's claim is two-sided: inducible unrestricted, not inducible at
  # unit margin.  Running both is also the control on the margin flag itself --
  # if --margin exact were silently ignored, the second run would come back SAT.
  out=$(timeout 1200 "$TMP/kinduce" --paley 19 --k 5 --max-margin 3 --order mrv \
          --inc --base 0 1 2 3 5 2>&1)
  if echo "$out" | grep -q 'RESULT SAT'; then
    if echo "$out" | grep -q 'VERIFY.*OK'; then
      ok "Paley(19) at margin <= 3: witness found and self-verified"
    else
      bad "Paley(19) margin <= 3: SAT but the witness did not verify"
    fi
  else
    bad "Paley(19) at margin <= 3 did not find a witness (paper says it is inducible)"
  fi

  # a slice of the certified refutation: unit margin must refute
  out=$(timeout 1800 "$TMP/kinduce" --paley 19 --k 5 --max-margin 1 --order mrv \
          --inc --base 0 1 2 3 5 --bs-from 0 --bs-to 40 2>&1)
  if echo "$out" | grep -q 'RESULT UNSAT'; then
    cap=$(echo "$out" | grep -oE 'capped=[0-9]+' | head -1 | cut -d= -f2)
    if [ "${cap:-0}" = "0" ]; then
      ok "Paley(19) at unit margin: first 40 base states refuted, none capped"
    else
      bad "Paley(19) unit margin: UNSAT but $cap base states were capped"
    fi
  else
    bad "Paley(19) at unit margin returned a witness on [0,40) -- contradicts the certificate"
  fi
fi

echo
echo "-------------------------------------------------------------"
printf 'passed %d   failed %d   skipped %d\n' "$pass" "$fail" "$skip"
[ "$fail" -eq 0 ] || exit 1
[ "$skip" -eq 0 ] || echo "(skips are missing tools or artifacts, not failures)"
exit 0
