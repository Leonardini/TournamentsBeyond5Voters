#!/usr/bin/env bash
# Reproduction driver for arXiv 2609.13924, "Tournaments not inducible by five
# voters" (Chindelevitch & Harutyunyan).
#
# Every node of the experiment tree runs THIS FILE with no arguments. What a
# node reproduces is decided entirely by repro2609/claims.conf on its branch.
#
# Logs are the only evidence channel, so everything a reader needs is printed:
# the pinned upstream commit, the engine's own self-describing configuration
# header, per-base-state node counts and times, the index-cover audit, the
# memory trace, and one `CLAIM` line per claim giving paper vs observed.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
# shellcheck disable=SC1091
. repro2609/claims.conf

UPSTREAM_URL=https://github.com/Leonardini/TournamentsBeyond5Voters.git
UPSTREAM_SHA=48b4a49eabeb7ccb0706428da8fbb84815e41577
CACHE=$HOME/.cache/openresearch/beyond5-pinned
OUT=$ROOT/repro2609/out
# Sweep evidence lives OUTSIDE the per-run repo clone, so a sweep that is
# interrupted -- by the memory watchdog, by a cancel, by the machine -- can be
# resumed instead of restarted. Soundness rests on the fingerprint check below:
# a resume is only allowed when the engine source, the exact argument vector and
# the base-state count are all unchanged.
SWEEPS=$HOME/.cache/openresearch/beyond5-sweeps
BIN=$OUT/kinduce
# The paper's own runs used a 14-core/24 GB Apple M-series laptop with at most
# 11 cores concurrently (Appendix A.4). Same machine, same width, so core-hours
# are directly comparable rather than merely order-of-magnitude comparable.
NPROC=11

mkdir -p "$OUT"
say() { printf '\n========== %s ==========\n' "$*"; }
claim() { printf 'CLAIM %s\n' "$*"; }

say "ENVIRONMENT"
date -u '+utc %Y-%m-%dT%H:%M:%SZ'
echo "host_cores=$(sysctl -n hw.ncpu) ram_bytes=$(sysctl -n hw.memsize) workers=$NPROC"
uname -a
cc --version | head -1
python3 --version
echo "claims=$CLAIMS"

# ---------------------------------------------------------------- upstream ---
# The package under test is the authors' own, pinned by full SHA. We clone it
# rather than vendoring a copy so that what ran is unambiguously their code at a
# named commit, and we hard-fail if the checkout is not that commit.
say "UPSTREAM PACKAGE"
if [ ! -d "$CACHE/.git" ]; then
    mkdir -p "$(dirname "$CACHE")"
    git clone --quiet "$UPSTREAM_URL" "$CACHE" || exit 1
fi
git -C "$CACHE" fetch --quiet origin || true
git -C "$CACHE" checkout --quiet "$UPSTREAM_SHA" || exit 1
got=$(git -C "$CACHE" rev-parse HEAD)
echo "upstream_url=$UPSTREAM_URL"
echo "upstream_pinned=$UPSTREAM_SHA"
echo "upstream_head=$got"
[ "$got" = "$UPSTREAM_SHA" ] || { echo "FATAL: upstream HEAD is not the pin"; exit 1; }
git -C "$CACHE" status --porcelain | head -5
T=$CACHE/tournaments
V=$CACHE/verify

# ---------------------------------------------------------------- watchdog ---
# Global rule on this laptop: keep combined RSS inside physical RAM so swap
# stays near zero. This Mac idles at 17-18 GB of swap, so the trip wire is swap
# GROWTH from the run's own baseline, never the absolute figure.
watchdog() {
    base=$(sysctl -n vm.swapusage | sed -n 's/.*used = \([0-9.]*\)M.*/\1/p')
    echo "MEM baseline_swap_used=${base}M"
    while :; do
        sleep 30
        now=$(sysctl -n vm.swapusage | sed -n 's/.*used = \([0-9.]*\)M.*/\1/p')
        rss=$(ps -Ao rss,comm | awk '/kinduce/ {s+=$1; n++} END {printf "%.0f", s/1024}')
        nw=$(pgrep -f "$BIN" | wc -l | tr -d ' ')
        grow=$(awk -v a="$now" -v b="$base" 'BEGIN{printf "%.0f", a-b}')
        printf 'MEM t=%s workers=%s kinduce_rss_total=%sM swap_used=%sM swap_growth=%sM\n' \
               "$(date -u +%H:%M:%S)" "$nw" "$rss" "$now" "$grow"
        if [ "$grow" -gt 3072 ] 2>/dev/null; then
            echo "MEM ABORT: swap grew ${grow}M over baseline; killing workers"
            pkill -f "$BIN" ; exit 1
        fi
    done
}
watchdog & WD=$!
trap 'kill $WD 2>/dev/null' EXIT

# ------------------------------------------------------------------ helpers ---
# A sliced sweep: one kinduce invocation per base state, pulled off a queue by
# `xargs -P`, so the 11 workers stay balanced even though per-state cost spans
# two orders of magnitude. Per-state granularity also makes the index cover of
# done/ an exact completeness certificate (SOUNDNESS, kinduce(1)).
sweep() {
    tag=$1; shift
    n=$1; shift
    d=$SWEEPS/$tag
    src=$(shasum -a 256 "$CACHE/engine/kinduce.c" | cut -d' ' -f1)
    fp="engine=$src upstream=$UPSTREAM_SHA states=$n args=$*"
    mkdir -p "$d/done"
    if [ -f "$d/fingerprint" ] && [ "$(cat "$d/fingerprint")" = "$fp" ]; then
        echo "sweep tag=$tag RESUMING -- fingerprint matches"
        echo "  inherited $(ls "$d/done" | wc -l | tr -d ' ') cleared base states"
    else
        [ -f "$d/fingerprint" ] && echo "sweep tag=$tag fingerprint CHANGED -- discarding"
        rm -rf "$d"; mkdir -p "$d/done"; : > "$d/times.txt"
        printf '%s' "$fp" > "$d/fingerprint"
    fi
    echo "sweep tag=$tag base_states=$n workers=$NPROC"
    echo "sweep fingerprint: $fp"
    echo "cmd: kinduce $* --bs-from <i> --bs-to <i+1>   for i in [0,$n)"
    # the engine's self-describing header, printed once for the record
    "$BIN" "$@" --bs-from 0 --bs-to 0 2>&1 | head -30
    # only the base states not already cleared; the union is audited below
    todo=$(mktemp)
    seq 0 $((n - 1)) | while read -r i; do
        [ -f "$d/done/$i" ] || echo "$i"
    done > "$todo"
    echo "sweep todo=$(wc -l < "$todo" | tr -d ' ') of $n"
    t0=$(date +%s)
    xargs -P "$NPROC" -I{} "$ROOT/repro2609/one_state.sh" {} "$d" "$BIN" "$@" < "$todo"
    t1=$(date +%s)
    rm -f "$todo"
    echo "sweep_wall_seconds=$((t1 - t0))"
}

audit() {
    tag=$1; n=$2
    d=$SWEEPS/$tag
    ls "$d/done" 2>/dev/null | sort -n > "$d/got.txt"
    seq 0 $((n - 1)) > "$d/want.txt"
    missing=$(comm -13 "$d/got.txt" "$d/want.txt" | wc -l | tr -d ' ')
    extra=$(comm -23 "$d/got.txt" "$d/want.txt" | wc -l | tr -d ' ')
    nsat=$(ls "$d"/SAT.* 2>/dev/null | wc -l | tr -d ' ')
    ncap=$(ls "$d"/CAPPED.* 2>/dev/null | wc -l | tr -d ' ')
    nerr=$(ls "$d"/ERROR.* 2>/dev/null | wc -l | tr -d ' ')
    read -r nodes secs live < <(awk '$2!="NA"{tn+=$2; ts+=$3; if($2>0) lv++}
        END{printf "%d %.1f %d", tn, ts, lv}' "$d/times.txt")
    coreh=$(awk -v s="$secs" 'BEGIN{printf "%.2f", s/3600}')
    perlive=$(awk -v s="$secs" -v l="$live" 'BEGIN{if(l>0) printf "%.1f", s/l; else print "NA"}')
    echo "AUDIT tag=$tag expected=$n cleared=$(wc -l < "$d/got.txt" | tr -d ' ')" \
         "missing=$missing extra=$extra capped=$ncap sat=$nsat errors=$nerr"
    echo "AUDIT tag=$tag nodes=$nodes core_seconds=$secs core_hours=$coreh" \
         "states_with_search=$live seconds_per_searched_state=$perlive"
    AUDIT_MISSING=$missing; AUDIT_EXTRA=$extra; AUDIT_CAP=$ncap
    AUDIT_SAT=$nsat; AUDIT_ERR=$nerr; AUDIT_NODES=$nodes
    AUDIT_COREH=$coreh; AUDIT_LIVE=$live
}

verdict_of() {  # a complete refutation, or not
    if [ "$AUDIT_MISSING" = 0 ] && [ "$AUDIT_EXTRA" = 0 ] && [ "$AUDIT_CAP" = 0 ] \
       && [ "$AUDIT_SAT" = 0 ] && [ "$AUDIT_ERR" = 0 ]; then
        echo "not 5-inducible (complete refutation, exact index cover)"
    else
        echo "INCOMPLETE"
    fi
}

# One unsliced invocation, expecting a witness. Capped: a search for a WITNESS
# may be cut off at no cost to soundness -- it can only fail to find one, never
# wrongly report its absence. (The opposite of a cap in a refutation, which
# voids the verdict; that is why the sweeps below are never capped.)
single() {
    tag=$1; shift
    cap=$1; shift
    d=$OUT/$tag; mkdir -p "$d"
    echo "cmd: kinduce $*    [cap ${cap}s]"
    timeout "$cap" "$BIN" "$@" > "$d/log.txt" 2>&1
    rc=$?
    [ "$rc" = 124 ] && echo "CAP-HIT after ${cap}s -- no witness within the cap, which refutes nothing"
    grep -E '^(RESULT|VERIFY|SLICE)' "$d/log.txt" | tail -4
    echo "exit=$rc"
}

# =============================================================== the claims ===
for c in $CLAIMS; do
case $c in

build)
    say "BUILD + REGRESSION GATE"
    ( cd "$CACHE/engine" && cc -O3 -march=native -o "$BIN" kinduce.c ) || exit 1
    ls -l "$BIN"
    echo "kinduce.c sha256: $(shasum -a 256 "$CACHE/engine/kinduce.c" | cut -d' ' -f1)"
    # Node-for-node agreement between the consolidated engine and the historical
    # version that originally produced each published result. This is the
    # package's own acceptance gate.
    ( cd "$CACHE/engine" && sh regression.sh --fast ) 2>&1 | tail -25
    rg=$?
    claim "build regression_gate paper='11 cases, 0 failures (--fast subset)' observed_exit=$rg"
    ;;

pos)
    say "POSITIVE CONTROL 1 -- P3: Paley(19) IS 5-inducible (margin <= 3)"
    single p19_sat 900 --paley 19 --k 5 --max-margin 3 --order mrv --inc --base 0 1 2 3 5
    python3 "$V/verify_witness_bits.py" "$OUT/p19_sat/log.txt" \
            "$T/p19_paley.bits" 19 5 --majority; echo "witness_check_exit=$?"
    # P5: the support histogram the paper reports for this witness class
    grep -E '^(support|histogram)' "$OUT/p19_sat/log.txt" | head -3

    say "POSITIVE CONTROL 2 -- P6: Paley(23) minus a vertex IS 5-inducible"
    # CLAIMS.md records the witness at base state 6,560, so we go straight there
    # instead of scanning up to it. What is being reproduced is the WITNESS --
    # re-verified below against the bit string by a program that shares no code
    # with the search -- not the cost of locating it.
    single p23mv_sat 900 --bits "$T/p23_minus1v.bits" --n 22 --k 5 --margin majority \
           --order mrv --inc --pool-mb 512 --bs-from 6560 --bs-to 6561
    python3 "$V/verify_witness_bits.py" "$OUT/p23mv_sat/log.txt" \
            "$T/p23_minus1v.bits" 22 5 --majority; echo "witness_check_exit=$?"

    say "POSITIVE CONTROL 3 -- K5: Paley(23) is arc-critical"
    single p23arc 900 --bits "$T/p23_arcrev.bits" --n 23 --k 5 --margin majority \
           --order mrv --inc --pool-mb 512 --bs-from 1160 --bs-to 1164
    echo "-- witness against the REVERSED host (must verify):"
    python3 "$V/verify_witness_bits.py" "$OUT/p23arc/log.txt" \
            "$T/p23_arcrev.bits" 23 5 --majority; echo "exit=$?"
    echo "-- NEGATIVE CONTROL: same witness against UNREVERSED Paley(23),"
    echo "   which must fail on exactly the one reversed arc (0,1):"
    python3 "$V/verify_witness_bits.py" "$OUT/p23arc/log.txt" \
            "$T/p23_paley.bits" 23 5 --majority; echo "exit=$? (nonzero is the expected outcome)"
    ;;

calib)
    say "CALIBRATION -- 100 base states of the Paley(23) sweep"
    # Not a refutation: a throughput measurement to size the headline run.
    sweep p23calib 100 --paley 23 --k 5 --margin majority --order mrv --inc \
          --pool-mb 512 --base 0 1 2 5 11 --top0rr 2 5
    audit p23calib 100
    proj=$(awk -v ch="$AUDIT_COREH" 'BEGIN{printf "%.1f", ch*8031/100}')
    echo "PROJECTION full_p23_core_hours_if_uniform=$proj (paper: 34.03)"
    claim "calib paper_seconds_per_live_base_state=47.3 observed_core_hours_100_states=$AUDIT_COREH"
    ;;

p23)
    say "B1 -- Paley(23) is not 5-inducible, hence N(5) <= 23"
    sweep p23 8031 --paley 23 --k 5 --margin majority --order mrv --inc \
          --pool-mb 512 --base 0 1 2 5 11 --top0rr 2 5
    audit p23 8031
    claim "B1 paper='not 5-inducible, 8031 base states, 2591 live, 34.03 core-h'" \
          "observed='$(verdict_of)' live=$AUDIT_LIVE core_hours=$AUDIT_COREH nodes=$AUDIT_NODES"
    ;;

p31)
    say "P2 -- Paley(31) is not 5-inducible"
    sweep p31 21009 --paley 31 --k 5 --margin majority --order mrv --inc \
          --pool-mb 512 --base 0 1 2 3 6 --toppair 2 3 0 3
    audit p31 21009
    claim "P2 paper='not 5-inducible, 21009 base states, 4007 live, 3.43e9 nodes, 26.89 core-h'" \
          "observed='$(verdict_of)' live=$AUDIT_LIVE core_hours=$AUDIT_COREH nodes=$AUDIT_NODES"
    ;;

p19m1)
    say "P4 -- Paley(19) is NOT 5-inducible at unit margin"
    sweep p19m1 2200 --paley 19 --k 5 --max-margin 1 --order mrv --inc \
          --base 0 1 2 3 5
    audit p19m1 2200
    claim "P4 paper='not unit-margin inducible, 2200 base states, ~2.5 core-h (DFS route)'" \
          "observed='$(verdict_of)' core_hours=$AUDIT_COREH nodes=$AUDIT_NODES"
    ;;

dr19)
    say "K10 -- the second doubly regular tournament on 19 vertices"
    echo "-- majority-inducible (expect SAT, paper: 176 s):"
    single dr19_sat 900 --bits "$T/dr19_g2.bits" --n 19 --k 5 --max-margin 3 \
           --order mrv --inc --toporb 0 1 4 6 7 8 12
    python3 "$V/verify_witness_bits.py" "$OUT/dr19_sat/log.txt" \
            "$T/dr19_g2.bits" 19 5 --majority; echo "witness_check_exit=$?"
    echo "-- unit-margin obstruction (expect UNSAT over all 2200 base states):"
    sweep dr19m1 2200 --bits "$T/dr19_g2.bits" --n 19 --k 5 --max-margin 1 \
          --order mrv --inc
    audit dr19m1 2200
    claim "K10 paper='unit-margin obstruction, majority-inducible, 2.70 core-h at margin 1'" \
          "observed='$(verdict_of)' core_hours=$AUDIT_COREH"

    say "K9 -- that tournament is arc-critical at unit margin: 57 orbits, 57 witnesses"
    # |Aut| = 3, so the 171 arcs fall into 57 orbits of size 3. Reversing one
    # representative of each must restore unit-margin inducibility.
    d=$OUT/dr19flip; rm -rf "$d"; mkdir -p "$d"
    nhost=$(ls "$T"/dr19_arcflip/*.bits | wc -l | tr -d ' ')
    t0=$(date +%s)
    ls "$T"/dr19_arcflip/*.bits \
      | xargs -P "$NPROC" -I{} "$ROOT/repro2609/one_host.sh" {} "$d" "$BIN" 19 1800
    t1=$(date +%s)
    nsat=$(ls "$d"/sat.* 2>/dev/null | wc -l | tr -d ' ')
    secs=$(grep -ho 'time=[0-9.]*' "$d"/*.log | sed 's/time=//' \
           | awk '{s+=$1} END {printf "%.1f", s}')
    echo "AUDIT tag=dr19flip hosts=$nhost sat=$nsat other=$((nhost - nsat))" \
         "core_hours=$(awk -v s="$secs" 'BEGIN{printf "%.2f", s/3600}') wall_seconds=$((t1 - t0))"
    claim "K9 paper='57 orbit representatives, all SAT, 3.59 core-h' observed_sat=$nsat observed_other=$((nhost - nsat))"
    ;;

root19|root23)
    if [ "$c" = root19 ]; then
        q=19; base="0 1 2 3 4 11"; arc="0 1"; non="2 1"; margin=exact
        cubes=22876; cid=B2-P19
        root=0eeb9dd53956fec2c77b752d74b89b12c7d1dddd6dc4047405ecb7907896a78a
    else
        q=23; base="0 1 2 5 6 3"; arc="2 6"; non="1 6"; margin=majority
        cubes=343896; cid=B2-P23
        root=7e6c9c26ac386e675687d28420ac41401c11d6bdbc0d006b9722fff394de49cb
    fi
    say "$cid -- ROOT (CNF): regenerate every cube's CNF and hash it, no solving"
    # Section 5.2: ROOT (CNF) "is reproducible on any machine: a third party who
    # regenerates the cube set must obtain this exact value." This is therefore
    # the package's own designated independent check, and it is the half of the
    # certification that does not need CaDiCaL.
    echo "expected_root=$root expected_live_cubes=$cubes"
    ( cd "$CACHE/sat" && time python3 verify_root.py --q "$q" --k 5 --margin "$margin" \
        --base $base --arc $arc --non $non --cubes "$cubes" --root "$root" ) 2>&1 | tail -20
    rc=${PIPESTATUS[0]}
    claim "$cid paper_root_cnf=$root regeneration_exit=$rc (0 = byte-identical cube set)"
    ;;

*)
    echo "unknown claim id: $c"; exit 1 ;;
esac
done

say "DONE"
date -u '+utc %Y-%m-%dT%H:%M:%SZ'
