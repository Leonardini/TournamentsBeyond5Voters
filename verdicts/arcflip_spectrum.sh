#!/bin/bash
# The full arc-criticality spectrum at MARGIN 1 for the n=21 vertex-transitive
# margin-1 obstructions, one representative per arc orbit.
#
# Leonid's hypothesis (2026-09-08): per host it is all or nothing -- either every
# single-arc reversal restores margin-1 inducibility, or none does. h01 is already
# the "none" case, all ten orbits UNSAT. Paley(23) is the "all" case unrestricted.
#
# ORDER IS BREADTH-FIRST ACROSS HOSTS, deliberately: f00 for every host, then f01
# for every host, and so on. Depth-first would spend 5 core-h proving h02 before
# learning anything about h04 or h05, and the hypothesis is refuted the moment ONE
# host shows both a SAT and an UNSAT -- which breadth-first finds soonest.
set -u
cd "$(dirname "$0")"
LOG=arcflip_spectrum.log
say() { echo "[$(date '+%H:%M')] $*" | tee -a "$LOG"; }
busy() { pgrep -f 'kinduce[0-9]* --bits' | wc -l | tr -d ' '; }

HOSTS=${SPECTRUM_HOSTS:-"h02 h04 h05"}
[ "$(busy)" -eq 0 ] || { say "ABORT: $(busy) kinduce already running"; exit 1; }

# The flip names are DERIVED from the manifest, never typed: column 3 is the
# source host, column 1 the flip. A source host that contributes no flips is a
# hard error, not an empty sweep.
ORDER=""
for i in 0 1 2 3 4 5 6 7 8 9; do
  for h in $HOSTS; do
    f=$(awk -F'\t' -v s="$h" -v i="$i" 'NR>1 && $3==s && $1 ~ ("_f0" i "$") {print $1}' \
        vt21_arcflip/manifest.tsv)
    [ -n "$f" ] && ORDER="$ORDER $f"
  done
done
NF=$(echo $ORDER | wc -w | tr -d ' ')
NH=$(echo $HOSTS | wc -w | tr -d ' ')
EXPECT=$(( NH * 10 ))
[ "$NF" -eq "$EXPECT" ] || { say "ABORT: manifest gave $NF flips for $NH host(s), expected $EXPECT"; exit 1; }
say "hosts: $HOSTS"
say "$NF flips, breadth-first across hosts; ~30 min each on 10 cores if UNSAT, minutes if SAT"
say "worst case $(python3 -c "print(f'{$NF*5:.0f}')") core-h = $(python3 -c "print(f'{$NF*0.5:.1f}')") h wall"

export KINDUCE_HOSTDIR=vt21_arcflip KINDUCE_HOSTFMT='{host}'
START=$(date +%s); BUDGET=$((16*3600))
for f in $ORDER; do
  LEFT=$(( BUDGET - ($(date +%s) - START) ))
  [ "$LEFT" -le 600 ] && { say "STOP: 16 h budget spent; remaining flips not attempted"; break; }
  HRS=$(python3 -c "print(min(2.5, $LEFT/3600))")
  say "=== $f ==="
  # --resume: a flip already settled on its slice logs is skipped, and any other
  # restarts at its proved prefix. So this script is safe to re-run.
  python3 vt21_runner.py --hosts "$f" --margin exact --no-toporb --resume \
      --slices 72 --cores 10 --outdir vt21_arcflip_shard --hours "$HRS" --tag "$f" \
      >> "$LOG" 2>&1
  grep -E "^[[:space:]]+$f: (\*\*\*|SAT --|UNRESOLVED|AUDIT)" vt21_arcflip_shard/runner.log \
      | tail -2 | tee -a "$LOG"
done

# ---- the spectrum, read from the SLICE LOGS ------------------------------
say "=== SPECTRUM (audited from the slice logs) ==="
python3 - <<'PYA' | tee -a "$LOG"
import importlib.util, sys, os, subprocess
os.environ.setdefault("KINDUCE_HOSTDIR", "vt21_arcflip")
os.environ.setdefault("KINDUCE_HOSTFMT", "{host}")
spec = importlib.util.spec_from_file_location("r", "vt21_runner.py")
m = importlib.util.module_from_spec(spec); sys.modules["r"] = m; spec.loader.exec_module(m)
hosts = sorted({l.split("\t")[2] for l in open("vt21_arcflip/manifest.tsv").read().splitlines()[1:]})
verdict = {}
for h in hosts:
    row = []
    for i in range(10):
        f = f"{h}_f{i:02d}"
        if not os.path.exists(f"vt21_arcflip/{f}.bits"): row.append("-"); continue
        # Probing costs a kinduce startup (~12 s), so skip it for a flip with no
        # slice logs at all: with no evidence the verdict is INCOMPLETE whatever
        # the base-state count is.  Probing all 40 cost 8 minutes of pure report.
        import glob
        if not glob.glob(f"vt21_arcflip_shard/{f}_q*.log"): row.append("."); continue
        nb, _ = m.probe(f, "exact", False)
        v, _d = m.audit_host(f, nb, "vt21_arcflip_shard")
        row.append({"UNSAT": "U", "SAT": "S", "INCOMPLETE": "."}[v])
    verdict[h] = row
    print(f"  {h}: {''.join(row)}   U=obstruction  S=inducible  .=not yet decided")
done = {h: r for h, r in verdict.items() if "." not in r}
mixed = {h: r for h, r in done.items() if "U" in r and "S" in r}
print()
if mixed:
    print("  HYPOTHESIS REFUTED: " + ", ".join(f"{h} is mixed ({''.join(r)})" for h, r in mixed.items()))
elif done:
    print("  Consistent with the hypothesis so far: every fully decided host is "
          "uniform -- " + ", ".join(f"{h}={'all obstructions' if r[0]=='U' else 'all inducible'}"
                                    for h, r in done.items()))
if len(done) < len(verdict):
    print(f"  {len(verdict)-len(done)} host(s) still incomplete -- not a verdict for those")
PYA
say "DONE"
