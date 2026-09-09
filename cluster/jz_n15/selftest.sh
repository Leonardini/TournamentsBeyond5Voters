#!/bin/bash
# MANDATORY known-answer gate.  Every number below is independently established;
# if any line says FAIL, do NOT submit the array -- the toolchain on this
# machine does not reproduce known results.
#
# Counts of regular tournaments (OEIS A096368): n=5:1, 7:3, 9:15, 11:1223,
# 13:1495297, 15:12007554066.
# Verdicts established locally 2026-09-02 (kinduce20, --order mrv --inc):
#   regular n=9  (15)   k=5 exact 15/0     k=5 majority 15/0    k=3 exact 7/8
#   regular n=11 (1223) k=5 exact 1223/0   k=5 majority 1223/0  k=3 exact 48/1175
set -u
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
# locate gentourng: explicit override, then a loaded module on PATH, then a
# local build.  Nauty already exists on JZ, so the PATH/override paths are the
# normal ones and nothing is fetched.
if [ -n "${GENTOURNG:-}" ]; then GT="$GENTOURNG"
elif [ -n "${NAUTY_DIR:-}" ] && [ -x "${NAUTY_DIR}/gentourng" ]; then GT="${NAUTY_DIR}/gentourng"
elif command -v gentourng >/dev/null 2>&1; then GT="$(command -v gentourng)"
else GT="$ROOT/nauty/gentourng"; fi
KI=../kinduce20
rc=0
chk() { # label expected actual
  if [ "$2" = "$3" ]; then printf "  PASS  %-42s %s\n" "$1" "$3"
  else printf "  FAIL  %-42s got %s, expected %s\n" "$1" "$3" "$2"; rc=1; fi
}

echo "== generator counts =="
for pair in 5:2:1 7:3:3 9:4:15 11:5:1223 13:6:1495297; do
  N=${pair%%:*}; rest=${pair#*:}; D=${rest%%:*}; EXP=${rest##*:}
  GOT=$($GT -u -d$D -D$D $N 2>&1 | sed -n 's/.*Z \([0-9]*\) graphs.*/\1/p')
  chk "regular n=$N count" "$EXP" "$GOT"
done

echo "== engine verdicts =="
$GT -d4 -D4 9  2>/dev/null > /tmp/st9.bits
$GT -d5 -D5 11 2>/dev/null > /tmp/st11.bits
sumline() { $KI --batch "$1" --n "$2" --k "$3" --margin "$4" --order mrv --inc 2>/dev/null \
            | sed -n 's/.*instances=\([0-9]*\) SAT=\([0-9]*\) UNSAT=\([0-9]*\).*/\2\/\3/p'; }
chk "n=9  k=5 exact    (SAT/UNSAT)" "15/0"      "$(sumline /tmp/st9.bits 9 5 exact)"
chk "n=9  k=5 majority (SAT/UNSAT)" "15/0"      "$(sumline /tmp/st9.bits 9 5 majority)"
chk "n=9  k=3 exact    (SAT/UNSAT)" "7/8"       "$(sumline /tmp/st9.bits 9 3 exact)"
chk "n=11 k=5 exact    (SAT/UNSAT)" "1223/0"    "$(sumline /tmp/st11.bits 11 5 exact)"
chk "n=11 k=5 majority (SAT/UNSAT)" "1223/0"    "$(sumline /tmp/st11.bits 11 5 majority)"
chk "n=11 k=3 exact    (SAT/UNSAT)" "48/1175"   "$(sumline /tmp/st11.bits 11 3 exact)"

echo "== executability (a non-executable script fails execve on EVERY task) =="
for f in screen_residue.sh aggregate.sh n15_margin1.slurm build.sh selftest.sh; do
  if [ -x "$f" ]; then printf "  PASS  %-42s executable\n" "$f"
  else printf "  FAIL  %-42s NOT executable -- run: chmod +x %s\n" "$f" "$f"; rc=1; fi
done

echo "== screen_residue.sh end to end (the actual job step) =="
RT=$(mktemp -d /tmp/n15self_XXXXXX)
if ./screen_residue.sh 0 1000000 "$RT" exact >/dev/null 2>&1 && [ -f "$RT/done/r0" ]; then
  printf "  PASS  %-42s %s\n" "screen_residue.sh writes its done marker" "$(cat "$RT/done/r0")"
  if ./screen_residue.sh 0 1000000 "$RT" exact 2>&1 | grep -q "already done"; then
    printf "  PASS  %-42s skips completed residue\n" "resume"
  else
    printf "  FAIL  %-42s did NOT skip -- resume is broken\n" "resume"; rc=1
  fi
else
  printf "  FAIL  %-42s no done marker produced\n" "screen_residue.sh end to end"; rc=1
fi
rm -rf "$RT"

echo "== n=15 plumbing (bit width) =="
$GT -d7 -D7 15 0/1000000 2>/dev/null > /tmp/st15.bits
L=$(head -1 /tmp/st15.bits | tr -d '\n' | wc -c | tr -d ' ')
chk "n=15 bits per line" "105" "$L"
S=$(sumline /tmp/st15.bits 15 5 exact)
printf "  INFO  %-42s %s\n" "n=15 residue 0/1000000 (SAT/UNSAT)" "$S"

rm -f /tmp/st9.bits /tmp/st11.bits /tmp/st15.bits
echo
[ $rc -eq 0 ] && echo "ALL CHECKS PASSED -- safe to submit." || echo "*** SELFTEST FAILED -- DO NOT SUBMIT ***"
exit $rc
