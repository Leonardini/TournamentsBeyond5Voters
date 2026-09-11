#!/bin/bash
# MANDATORY known-answer gate for the blind T^e scan.
#
# The point of a gate is to fail when the toolchain is wrong, so every check
# here has an answer established elsewhere.  Two of them are genuinely
# discriminating -- a SAT that must be found and an UNSAT that must not be
# broken -- rather than merely "it ran".
set -u
cd "$(dirname "$0")/.."
KI=${KI:-./kinduce}
pass=0; fail=0
ok()  { printf "  PASS  %-46s %s\n" "$1" "$2"; pass=$((pass+1)); }
bad() { printf "  FAIL  %-46s %s\n" "$1" "$2"; fail=$((fail+1)); }

echo "== engine present =="
[ -x "$KI" ] && ok "engine binary" "$KI" || bad "engine binary" "$KI missing -- run ./build.sh"

echo "== host is the right tournament =="
BITS=$(tr -cd '01' < p23_arcrev.bits | wc -c | tr -d ' ')
[ "$BITS" = 253 ] && ok "p23_arcrev.bits width" "253 = C(23,2)" \
                  || bad "p23_arcrev.bits width" "$BITS, expected 253"
python3 - <<'PY' && ok "differs from Paley(23) in exactly one arc" "(0,1) reversed" \
                 || bad "differs from Paley(23) in exactly one arc" "see above"
import sys
def load(p,n):
    s=''.join(c for c in open(p).read() if c in '01'); A=[[0]*n for _ in range(n)]; k=0
    for a in range(n):
        for b in range(a+1,n):
            if s[k]=='1': A[a][b]=1
            else: A[b][a]=1
            k+=1
    return A
q=23; QR={(x*x)%q for x in range(1,q)}
P=[[1 if a!=b and (b-a)%q in QR else 0 for b in range(q)] for a in range(q)]
E=load('p23_arcrev.bits',23)
d=[(a,b) for a in range(q) for b in range(q) if P[a][b]!=E[a][b]]
outs=sorted({sum(E[a]) for a in range(q)})
sys.exit(0 if d==[(0,1),(1,0)] and outs==[10,11,12] else 1)
PY

echo "== decomposition =="
BS=$($KI --bits p23_arcrev.bits --n 23 --k 5 --margin majority --order mrv --inc \
        --base 0 1 2 6 15 --bs-from 0 --bs-to 0 2>&1 | grep -oE 'base_states=[0-9]+' | head -1)
[ "$BS" = "base_states=8031" ] && ok "base {0,1,2,6,15} base states" "8031" \
                              || bad "base {0,1,2,6,15} base states" "$BS, expected 8031"

echo "== engine verdicts on arc-reversed hosts (the discriminating checks) =="
# Paley(19) with one arc reversed IS margin-1 5-inducible -- a witness exists and
# must be found.  A broken engine that refutes everything fails HERE.
# Base and slice are NAMED, not auto-selected: without --base the engine scans
# all C(19,5) = 11,628 subsets before searching, which turns a gate into a
# multi-minute job.  This slice is the one recorded in WITNESSES_paley_arcrev.md
# as holding the witness, so the check is seconds.
R=$($KI --bits p19_arcrev.bits --n 19 --k 5 --margin exact --order mrv --inc \
       --pool-mb 512 --base 0 1 2 9 16 --bs-from 1460 --bs-to 1464 2>&1 \
       | grep -oE '^RESULT (SAT|UNSAT)' | head -1)
[ "$R" = "RESULT SAT" ] && ok "p19_arcrev margin 1 must be SAT" "$R" \
                        || bad "p19_arcrev margin 1 must be SAT" "$R"
# Paley(27) arc-reversed is margin-1 UNSAT over all 2200 base states, so every
# slice of it is UNSAT too.  A broken engine that accepts anything fails HERE.
# Same reason, and worse at n=27: C(27,5) = 80,730 subsets.  Base 0 1 2 4 6 is
# the one m1_family/run_all.sh used for the p27e cell that came back UNSAT over
# all 2200 base states, so every slice of it must be UNSAT too.
R=$($KI --bits p27_arcrev.bits --n 27 --k 5 --margin exact --order mrv --inc \
       --pool-mb 512 --base 0 1 2 4 6 --bs-from 0 --bs-to 40 2>&1 \
       | grep -oE '^RESULT (SAT|UNSAT)' | head -1)
[ "$R" = "RESULT UNSAT" ] && ok "p27_arcrev margin 1 slice must be UNSAT" "$R" \
                          || bad "p27_arcrev margin 1 slice must be UNSAT" "$R"

echo "== driver end to end =="
D=$(mktemp -d)
if jz_p23arc/screen_chunk.sh 0 "$D" >/dev/null 2>&1 && [ -f "$D/done/0" ]; then
  ok "screen_chunk.sh writes its done marker" "$(cat "$D/done/0")"
else
  bad "screen_chunk.sh writes its done marker" "no marker at $D/done/0"
fi
OUT2=$(jz_p23arc/screen_chunk.sh 0 "$D" 2>&1)
[ -z "$OUT2" ] && ok "resume" "skips a completed base state" \
               || bad "resume" "reran a completed base state"
rm -rf "$D"

echo "== executability (a non-executable script fails execve on EVERY task) =="
for f in screen_chunk.sh aggregate.sh selftest.sh build.sh p23arc.slurm; do
  [ -x "jz_p23arc/$f" ] && ok "$f" "executable" || bad "$f" "NOT executable"
done

echo
if [ "$fail" -eq 0 ]; then
  echo "ALL CHECKS PASSED -- safe to submit."
else
  echo "$fail CHECK(S) FAILED -- DO NOT SUBMIT."
  exit 1
fi
