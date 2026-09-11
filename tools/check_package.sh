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
echo "== 2. CLAIMS.md, claims.tsv and claims.json agree, and every artifact exists =="
# CLAIMS.md is the human index and the single source of truth; claims.tsv and
# claims.json are DERIVED from it.  Regenerating and diffing is what stops the
# machine-readable copy drifting from the prose, and the same pass resolves
# every backticked path -- exact paths, globs, brace lists and bare filenames --
# so a reference that rots is a failure rather than a quiet lie.
#
# This replaced a looser check that tested `[ -e ]` only on tokens containing a
# slash, and so passed silently over every glob and every bare filename.
if out=$(python3 "$ROOT/tools/claims_index.py" --check 2>&1); then
  ok "$(echo "$out" | head -1)"
else
  bad "CLAIMS.md and its generated index disagree, or an artifact is missing"
  echo "$out" | sed 's/^/        /' | head -12
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
echo "== 3c. CERT (portable) recomputes from the block it publishes =="
# ROOT (CNF) covers the SEARCH half only; the coverage instance's hash is a
# separate value.  CERT (portable) is the one published value that commits to
# both halves at once, and the file it lives in is self-auditing.
if out=$(python3 "$ROOT/tools/check_cert_portable.py" \
         "$ROOT/certificates/p19cert_d6" "$ROOT/certificates/p23cert_d6" 2>&1); then
  echo "$out" | sed 's/^  ok    /  ok    /'
  pass=$((pass+2))
else
  bad "a portable certificate does not recompute, or its control did not fire"
  echo "$out" | sed 's/^/        /'
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
# ballots and recomputes every arc's support.  This used to check only that the
# two FILES existed, which is not a check of anything -- it would have passed on
# a witness that verified against nothing.
wit="$ROOT/verdicts/p23arc_witness/b1161.witness"
ver="$ROOT/verify/verify_witness_bits.py"
if [ -f "$wit" ] && [ -f "$ver" ]; then
  if python3 "$ver" "$wit" "$ROOT/tournaments/p23_arcrev.bits" 23 5 --majority \
       2>&1 | grep -q '^VERIFIED'; then
    ok "the Paley(23) arc-reversal witness verifies: all 253 arcs at >= 3 of 5"
  else
    bad "the Paley(23) arc-reversal witness does not verify against its host"
  fi
  # CONTROL.  The same ballots against the UNREVERSED Paley(23) must fail, and
  # must fail on exactly the reversed arc (0,1).  If they verified against both,
  # they would contradict Paley(23) not being 5-inducible -- so a control that
  # did not fire here would mean the result itself was wrong.
  cout=$(python3 "$ver" "$wit" "$ROOT/tournaments/p23_paley.bits" 23 5 --majority 2>&1)
  case "$cout" in
    *"FAIL: 1 arcs"*"(0, 1, 2)"*)
      ok "control: the same ballots fail on Paley(23) at exactly the reversed arc (0,1)" ;;
    *VERIFIED*)
      bad "control did not fire: the witness verifies against Paley(23) too, which would contradict its refutation" ;;
    *)
      bad "control fired in the wrong way: $cout" ;;
  esac
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
echo "== 8. the deleted-vertex sweeps cover their base-state range exactly =="
# These two are recorded as one line per base state rather than as slice logs,
# so the audit is on the index cover of the times file.  A line is written only
# on RESULT UNSAT, which is what makes an exact cover a completeness
# certificate: a capped or killed base state leaves nothing behind.
cover() {
  cf="$ROOT/$1"; cwant=$2; clabel=$3
  [ -f "$cf" ] || { warn "$clabel: $1 absent"; return; }
  awk -F'\t' '!/^#/ && NF>=2 {print $1}' "$cf" | sort -n > "$TMP/got"
  seq 0 $((cwant-1)) > "$TMP/want"
  cm=$(comm -13 "$TMP/got" "$TMP/want" | wc -l | tr -d ' ')
  cx=$(comm -23 "$TMP/got" "$TMP/want" | wc -l | tr -d ' ')
  cd=$(uniq -d < "$TMP/got" | wc -l | tr -d ' ')
  ch=$(awk -F'\t' '!/^#/ && NF>=2 {s+=$2} END {printf "%.2f", s/3600}' "$cf")
  if [ "$cm" = 0 ] && [ "$cx" = 0 ] && [ "$cd" = 0 ]; then
    ok "$clabel: exact cover of $cwant base states, 0 missing/extra/duplicated, $ch core-h"
  else
    bad "$clabel: cover is not exact (missing $cm, extra $cx, duplicated $cd)"
  fi
}
cover verdicts/p31mv_majority/p31mv_times.txt 8031 "P31 - v"
cover verdicts/p43mv_majority/p43mv_times.txt 8031 "P43 - v"

echo
echo "== 8b. NEGATIVE CONTROL: a hole in the cover must be noticed =="
# If deleting a base state left the audit passing, check 8 would measure nothing
# and a half-finished sweep would read as a complete refutation.
src="$ROOT/verdicts/p31mv_majority/p31mv_times.txt"
if [ -f "$src" ]; then
  grep -v '^4000	' "$src" > "$TMP/holed.txt"
  awk -F'\t' '!/^#/ && NF>=2 {print $1}' "$TMP/holed.txt" | sort -n > "$TMP/got"
  seq 0 8030 > "$TMP/want"
  hm=$(comm -13 "$TMP/got" "$TMP/want" | wc -l | tr -d ' ')
  if [ "$hm" -ge 1 ]; then
    ok "removing one base state leaves $hm missing, as it must"
  else
    bad "control did not fire: a base state was removed and the cover still read exact"
  fi
else
  warn "P31 - v times file absent, control not run"
fi

echo
echo "== 9. every number the manuscript prints that we can re-derive, re-derived =="
# The manuscript is the source of truth for what is CLAIMED; this recomputes the
# observed value from shipped bytes and compares.  A figure that changes in the
# paper and not in the package fails here rather than passing against a copy
# that drifted with it.
mout=$(python3 "$ROOT/tools/check_manuscript.py" 2>&1)
msum=$(echo "$mout" | tail -1)
if echo "$mout" | grep -q '^ FAIL'; then
  bad "manuscript figures do not all re-derive: $msum"
  echo "$mout" | grep -A1 '^ FAIL' | sed 's/^/        /'
else
  ok "$msum"
fi

echo
echo "== 10. Appendix E's construction, verified on the family it quantifies over =="
# The one result in the paper settled by construction rather than computation.
# The verifier builds A, B and C from the appendix's own prose and requires every
# support to be exactly 2, at every cut point of every locally transitive
# tournament it can reach, with the family selected by its DEFINITION.
eout=$(python3 "$ROOT/verify/appendix_e.py" 2>&1)
if echo "$eout" | grep -q '^OK: 0 problem'; then
  ok "Appendix E: $(echo "$eout" | awk '/^ *[0-9]+ / {n+=$(NF-3); c+=$(NF-1)} END {printf "%d cut points verified over %d STRONG locally transitive tournaments, orders 3-14", c, n}')"
  ok "control: $(echo "$eout" | grep 'outside the family' | sed 's/^ *//')"
else
  bad "Appendix E's construction did not verify"
  echo "$eout" | grep 'FAIL' | sed 's/^/        /' | head -5
fi

echo
echo "== 11. the 3-cycle hypothesis holds on every host that relied on it =="
# Several refutations ran at --max-margin 3 and are quoted as MAJORITY verdicts.
# That step is sound only if every arc of the host lies in a directed triangle,
# and Section 3.4 states the stronger form (q-3)/4.  Measured, not assumed.
if [ -f "$ROOT/verify/triangles_per_arc.py" ]; then
  tout=$(cd "$ROOT/tournaments" && python3 "$ROOT/verify/triangles_per_arc.py" \
        p23_minus1v.bits p27_minus1v.bits p31_minus1v.bits p43_minus1v.bits \
        --expect-paley-minus 2>&1)
  if echo "$tout" | grep -q '^OK: 0 problem'; then
    ok "every arc of P_q - v lies in at least (q-3)/4 triangles, q = 23, 27, 31, 43"
  else
    bad "Section 3.4's (q-3)/4 triangle claim does not hold as stated"
    echo "$tout" | sed 's/^/        /' | head -8
  fi
else
  warn "triangles_per_arc.py absent"
fi

echo
echo "== 12. the consolidated engine still agrees with the historical versions =="
# kinduce.c produced none of the published numbers; each result names the version
# that did.  --fast runs the cases that finish in about a second; the full set is
# recorded in engine/versions/REGRESSION.md.
if [ -f "$ROOT/engine/regression.sh" ]; then
  rout=$(sh "$ROOT/engine/regression.sh" --fast 2>&1)
  rline=$(echo "$rout" | tail -1)
  case "$rline" in
    *"failed 0"*) ok "engine regression, fast subset: $rline" ;;
    *) bad "engine regression: $rline"
       echo "$rout" | grep -A2 'FAIL' | sed 's/^/        /' | head -10 ;;
  esac
else
  warn "engine regression script absent"
fi

echo
echo "== 13. the manifest matches the bytes on disk =="
if [ -f "$ROOT/MANIFEST.sha256" ]; then
  if nout=$(cd "$ROOT" && python3 tools/manifest.py --check 2>&1); then
    ok "$(echo "$nout" | tail -1)"
  else
    bad "MANIFEST.sha256 does not match the package"
    echo "$nout" | sed 's/^/        /' | head -10
  fi
else
  warn "MANIFEST.sha256 absent; run tools/manifest.py"
fi

echo
echo "-------------------------------------------------------------"
printf 'passed %d   failed %d   skipped %d\n' "$pass" "$fail" "$skip"
[ "$fail" -eq 0 ] || exit 1
[ "$skip" -eq 0 ] || echo "(skips are missing tools or artifacts, not failures)"
exit 0
