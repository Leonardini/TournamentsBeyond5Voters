#!/bin/bash
# ONE driver for every campaign.  The instance is DATA (instances/<name>.conf);
# nothing here knows about Paley(19) or Paley(23) specifically, so adding
# Paley(27) or Paley(31) is a new conf file and nothing else.
#
#   run.sh <instance> <stage>
#     root       regenerate every cube CNF and assert ROOT (CNF).  NO SOLVER.
#     coverage   build and solve the split-half CNF, assert clauses/UNSAT/verified
#     cert       bind split+search into the two combined roots
#     recertify  full re-solve of every cube (expensive; see SOLVE_CORE_H)
#     all        root, coverage, cert
#
# Every expected value is ASSERTED, not printed for a human to eyeball; an empty
# expectation in the conf means "record what you observe", never "assume it passed".
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/.." && pwd)"
I=${1:?usage: run.sh <instance> <stage>}; STAGE=${2:-all}
CONF="$HERE/instances/$I.conf"
[ -f "$CONF" ] || { echo "no such instance: $I (have: $(ls $HERE/instances | tr '\n' ' '))"; exit 1; }
. "$CONF"
W=${JOBSCRATCH:-${SLURM_TMPDIR:-/tmp}}      # EPHEMERAL: purged when the job ends
# DURABLE outputs must not live in $W.  On Jean Zay $JOBSCRATCH is destroyed at job end, so a
# wall-killed recertification loses every completed chunk AND certify_d6.py's resume (it skips
# any chunk with a done/k*.json) can never fire across allocations.  2026-09-07: job 1829003
# lost 58,600 already-solved cubes exactly this way, and p19's done/ and log/ went with it --
# only the ROOT line in the SLURM log survived.  Big temporary bytes (the coverage CNF and its
# 2 GB LRAT, meant to be verified and discarded) stay in $W; results go here.
DUR=${JZ_DURABLE:-${SCRATCH:-${WORK:-$W}}}
if [ "$DUR" = "$W" ]; then
  echo "WARNING: no persistent \$SCRATCH or \$WORK found -- durable outputs are going to" >&2
  echo "         $DUR, which a scheduler may purge at job end. Set JZ_DURABLE." >&2
fi
cd "$ROOT"
fail=0
root_derived=0      # set by stage_root on success; stage_cert says so if it is still 0
hdr() { printf "\n=== %s [%s: q=%s margin=%s base=%s] ===\n" "$1" "$I" "$Q" "$MARGIN" "$BASE"; }

stage_root() {
  hdr "ROOT (CNF) -- regenerating $CUBES cube CNFs, no solving"
  if python3 verify_root.py --q "$Q" --k "$K" --margin "$MARGIN" --base $BASE \
      --arc $ARC --non $NON --cubes "$CUBES" --root "$ROOT_CNF" \
      ${ARCHIVE:+--archive "$ARCHIVE"}; then root_derived=1; else fail=1; fi
}

stage_coverage() {
  hdr "SPLIT half -- coverage CNF solved fresh"
  local out="$W/${I}cover"
  python3 cover_check.py --q "$Q" --k "$K" --margin "$MARGIN" --base $BASE \
      --stream --dimacs "$out.cnf" --drat "$out.lrat" 2>&1 | tee "$out.out"
  grep -q "RESULT UNSAT" "$out.out" && grep -q "CHECK=VERIFIED" "$out.out" \
      || { echo "  FAIL: coverage not UNSAT+VERIFIED"; fail=1; return; }
  local got; got=$(sed -n 's/.*clauses=\([0-9]*\) .*/\1/p' "$out.out" | head -1)
  if [ -n "${COVER_CLAUSES:-}" ]; then
    [ "$got" = "$COVER_CLAUSES" ] && echo "  clause count $got matches expected" \
      || { echo "  FAIL: clauses $got != expected $COVER_CLAUSES"; fail=1; }
  else
    echo "  clause count OBSERVED: $got  (no expectation in $CONF -- record it there)"
  fi
  # ASSERT the coverage CNF's hash, do not print it for a human to compare.  This
  # is the value CERT (portable) commits to as split_cover_cnf, and until
  # 2026-09-11 it was only echoed -- so the one comparison that closed the
  # coverage half on the cluster was made by eye, against the kit's own stated
  # principle.  The proof hash stays informational: it is build-dependent.
  local csha; csha=$(shasum -a 256 "$out.cnf" | cut -d' ' -f1)
  if [ -n "${COVER_CNF_SHA:-}" ]; then
    if [ "$csha" = "$COVER_CNF_SHA" ]; then
      echo "  cover_cnf_sha256 matches split_cover_cnf inside CERT (portable)"
    else
      echo "  FAIL: cover_cnf_sha256=$csha != $COVER_CNF_SHA"; fail=1
    fi
  else
    echo "  cover_cnf_sha256 OBSERVED: $csha  (no expectation in $CONF -- record it there)"
  fi
  echo "  cover_proof_sha256=$(shasum -a 256 "$out.lrat" | cut -d' ' -f1)  (build-dependent, not compared)"
}

stage_cert() {
  hdr "CERT -- binding split and search"
  local out="$W/${I}cover"
  [ -f "$out.cnf" ] && [ -f "$out.lrat" ] || { echo "  run the coverage stage first"; fail=1; return; }
  python3 certroot.py --dir "${ARCHIVE:-.}" --cover-cnf "$out.cnf" --cover-proof "$out.lrat" \
      --q "$Q" --k "$K" --margin "$MARGIN" --base $BASE --arc $ARC --non $NON \
      --cubes "$CUBES" --root-cnf "$ROOT_CNF" --root-proofs "${ROOT_PROOFS:-none}" \
      --out "$DUR/${I}_cert" || fail=1
  # SAY WHICH HALF WAS DERIVED.  certroot.py hashes the coverage CNF from disk, so
  # split_cover_cnf is always computed here, but --root-cnf comes from the CONF FILE.
  # If the root stage did not pass in this same run, CERT (portable) is binding a
  # RECORDED search root to a freshly derived coverage hash, and "matches the recorded
  # value" then means only that the recorded number was re-hashed. On 2026-09-12 a p23
  # run printed that line with its root stage SIGKILLed at cube 200 of 343,896.
  if [ "$root_derived" = 0 ]; then
    echo "  NOTE: search_root_cnf was READ FROM $CONF, not derived in this run."
    echo "        Only the coverage half below is reproduced here; run the 'all' stage"
    echo "        to completion for a value that binds both halves independently."
  fi
  if [ -n "${CERT_PORTABLE:-}" ]; then
    local got; got=$(sed -n 's/^CERT_PORTABLE=//p' "$DUR/${I}_cert.portable.txt")
    if [ "$got" != "$CERT_PORTABLE" ]; then
      echo "  FAIL: CERT (portable) $got != $CERT_PORTABLE"; fail=1
    elif [ "$root_derived" = 0 ]; then
      echo "  CERT (portable) matches the recorded value -- COVERAGE HALF ONLY (see NOTE)"
    else
      echo "  CERT (portable) matches the recorded value"
    fi
  else
    echo "  CERT (portable) OBSERVED -- no expectation recorded yet"
  fi
}

stage_recertify() {
  hdr "FULL RE-CERTIFICATION -- ~${SOLVE_CORE_H} core-h"
  local out=${RECERT_OUT:-$DUR/recert_$I} w=${SLURM_CPUS_PER_TASK:-10}
  # USE THE WHOLE ALLOCATION.  This used to cap w at 10, which is the LAPTOP's core limit
  # leaking into cluster code -- there is no reason to idle cores you have been granted.
  # Measured 2026-09-07: p23 recert ran at 6.12 core-s/cube = 585 core-h for 343,896 cubes,
  # 2.6x the conf's SOLVE_CORE_H=228, so at 10 workers it needs 58 h and CANNOT fit a 20 h
  # wall; at 40 it needs ~15 h and does.  Capping at 10 guaranteed a wall-kill.
  # Override with RECERT_WORKERS if a node's memory ever makes that too many.
  w=${RECERT_WORKERS:-$w}
  # SAY WHETHER THIS ALLOCATION CAN FINISH, before spending it.  Job 1843769 was
  # given a 5 h wall for a 16 h job and was killed at 27%, having done 181 core-h
  # of useful work that only survived because the durable-output fix had landed.
  # A short wall is no longer destructive -- the next run resumes from done/ -- but
  # it should be a stated choice rather than a discovery from the log.
  if [ -n "${CLUSTER_CORE_S_PER_CUBE:-}" ] && [ -n "${CUBES:-}" ]; then
    local done_cubes=0
    [ -d "$out/done" ] && done_cubes=$(( $(ls "$out/done" 2>/dev/null | wc -l) * 200 ))
    local need_h
    need_h=$(awk -v c="$CUBES" -v d="$done_cubes" -v r="$CLUSTER_CORE_S_PER_CUBE" -v w="$w"                  'BEGIN{ left = c - d; if (left < 0) left = 0; printf "%.1f", left*r/w/3600 }')
    echo "  $done_cubes of $CUBES cubes already done; ${need_h} h of wall needed on $w workers"
    if [ -n "${SLURM_JOB_END_TIME:-}" ]; then
      local have_h
      have_h=$(awk -v e="$SLURM_JOB_END_TIME" -v n="$(date +%s)" 'BEGIN{printf "%.1f", (e-n)/3600}')
      echo "  this allocation has ${have_h} h"
      awk -v a="$have_h" -v b="$need_h" 'BEGIN{exit !(a < b)}' &&         echo "  *** WILL NOT FINISH: it will stop at the wall and the next run resumes from done/"
    fi
  fi
  python3 certify_d6.py --q "$Q" --margin "$MARGIN" --base $BASE --arc $ARC --non $NON \
      --workers "$w" --out "$out"
  local got; got=$(sed -n 's/^ROOT (CNF) *//p' "$out/VERDICT.txt" 2>/dev/null | tr -d ' ')
  echo "  ROOT (CNF) here     $got"
  echo "  ROOT (CNF) expected $ROOT_CNF"
  # An ABSENT root is a run that died -- job 1827897 had no cadical at all -- and
  # saying it "DIFFERS" invites someone reading the archive to conclude the
  # certificate failed to reproduce, which is the opposite of what happened.
  if [ -z "$got" ]; then
    echo "  *** NO ROOT PRODUCED -- this run did not finish; nothing was compared"
    fail=1
  elif [ "$got" = "$ROOT_CNF" ]; then
    echo "  PORTABLE ROOT MATCHES -- same problems solved, independently"
  else
    echo "  *** PORTABLE ROOT DIFFERS -- investigate"
    fail=1
  fi
  echo "  (ROOT (proofs) is expected to differ on a different build; not compared)"
}

case "$STAGE" in
  root)      stage_root ;;
  coverage)  stage_coverage ;;
  cert)      stage_cert ;;
  recertify) stage_recertify ;;
  # SHORT-CIRCUIT.  These ran unconditionally until 2026-09-12, so a p23 run whose
  # root was SIGKILLed at cube 200 of 343,896 went on to build a certificate anyway,
  # out of a recorded root and a coverage stage that had itself just failed.  A stage
  # that did not finish must stop the chain, not be papered over by the next one.
  all)       stage_root
             if [ $fail != 0 ]; then
               echo; echo "  *** ROOT STAGE FAILED -- stopping; coverage and cert not run."
               echo "      (cert would bind the RECORDED root from $CONF, which is not"
               echo "       a reproduction of the search half.)"
             else
               stage_coverage
               if [ $fail != 0 ]; then
                 echo; echo "  *** COVERAGE STAGE FAILED -- stopping; cert not run."
               else
                 stage_cert
               fi
             fi ;;
  *) echo "unknown stage: $STAGE"; exit 1 ;;
esac
printf "\n%s: %s\n" "$I/$STAGE" "$([ $fail = 0 ] && echo PASS || echo FAIL)"
exit $fail
