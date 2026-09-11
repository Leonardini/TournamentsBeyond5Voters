#!/bin/sh
# Assemble this reproduction package from the working repository.
#
# Every file here came from KemenyMedian by way of this script, so the
# provenance of the package is one readable list rather than a recollection.
# Re-running it is idempotent: it copies over whatever is present.
#
#   usage: tools/assemble_from_source.sh [path-to-KemenyMedian]
#
# The default source path is the sibling checkout.

set -eu

SRC=${1:-$(cd "$(dirname "$0")/../.." && pwd)/KemenyMedian}
DST=$(cd "$(dirname "$0")/.." && pwd)
K="$SRC/KInduceDFS"

[ -d "$K" ] || { echo "FATAL no KInduceDFS under $SRC" >&2; exit 1; }
echo "source: $SRC"
echo "dest:   $DST"

# ---------------------------------------------------------------- engine
mkdir -p "$DST/engine/versions"
cp "$K/kinduce.c" "$K/kinduce.1" "$DST/engine/"
cp "$K/kcover.c" "$DST/engine/"          # order-12 witness extension (Appendix C)
cp "$K"/versions/kinduce[0-2][0-9].c "$DST/engine/versions/"
# kinduce25.c carries the --pin machinery that no published result used, and
# REPRODUCE.md excludes it from the package by name.  Drop it rather than ship
# a version the reproduction table never refers to.
rm -f "$DST/engine/versions/kinduce25.c"
# The regression that compares the consolidated engine against each of those
# versions on the published command lines.  Until it existed, REPRODUCE.md cited
# a versions/REGRESSION.md that was never written.
cp "$K/regression.sh" "$DST/engine/"
cp "$K/versions/REGRESSION.md" "$DST/engine/versions/" 2>/dev/null || true

# ---------------------------------------------------------- tournaments
# Vertex numbering is part of the input, not a detail: node counts only
# replicate against the numbering we used, and two of the 21-vertex hosts are
# not in the canonical labelling a fresh enumeration produces.  So the bit
# strings ship, and the generators ship beside them for checking.
mkdir -p "$DST/tournaments"
cp "$K"/*.bits "$DST/tournaments/"
for g in paley_bits.py make_paley_gf.py make_paley_minus.py vt21_family.py \
         vt_census.py vt_small_gen.py vt23_gen.py drt23_gen.py drt15_gen.py \
         gen_regular.py cayley_census.py deletion_classes.py; do
  [ -f "$K/$g" ] && cp "$K/$g" "$DST/tournaments/"
done
cp "$K/vt21_all_reps.npy" "$DST/tournaments/" 2>/dev/null || true
# McKay's locally transitive catalogue, orders 11-14.  Appendix E is the one
# result settled by construction rather than computation, so its artifact is a
# verifier plus the family to run it over; these four files are 104 KB.
mkdir -p "$DST/tournaments/locally_transitive"
for n in 11 12 13 14; do
  f="$SRC/Tournaments/SourceFiles/locallytransitivetournaments$n.txt"
  [ -f "$f" ] && cp "$f" "$DST/tournaments/locally_transitive/"
done

# families: the swept catalogues, with their verdict tables
for f in vt21_hosts vt21_arcflip dr19_arcflip vt15 vt17 vt19 vt23 drt23 \
         drt15 drt19 drt_small vt20_descent; do
  [ -d "$K/$f" ] || continue
  mkdir -p "$DST/tournaments/$f"
  find "$K/$f" -maxdepth 1 -type f \
       \( -name '*.bits' -o -name '*.tsv' -o -name '*.md' -o -name '*.sh' \
          -o -name '*.log' \) \
       -exec sh -c 'cp "$@" "$0"' "$DST/tournaments/$f/" {} +
done
# per-orbit outcome files behind the arc-flip spectrum table of Section 3.4
[ -d "$K/vt21_arcflip/out" ] && cp -R "$K/vt21_arcflip/out" "$DST/tournaments/vt21_arcflip/"

# ------------------------------------------------------------- SAT route
mkdir -p "$DST/sat"
for s in cubes.py cube_sat.py certify_d6.py certify_p19_m1.py cover_check.py \
         cover_deep.py certroot.py reroot.py run_cubes.py verify_root.py \
         verify_p19_root.py deepen.py cfg_hash.py leaf_bench.py \
         base_survivors.py registry.py; do
  [ -f "$K/$s" ] && cp "$K/$s" "$DST/sat/"
done

# ------------------------------------------------- independent verifiers
# These share no code with the search.  A witness is read back from its run
# log, the tournament from its bit string, and every arc's support recomputed.
mkdir -p "$DST/verify"
for v in verify_witness.py verify_witness_bits.py \
         verify_paley_minus_witness.py tri_per_arc.py tri_ceiling.py \
         appendix_e.py triangles_per_arc.py; do
  [ -f "$K/$v" ] && cp "$K/$v" "$DST/verify/"
done

# ---------------------------------------------------------- certificates
# The LRAT proof bytes were verified and discarded by design; what ships is
# the per-cube sha256 chain in log/, from which both published roots rebuild
# (tools/check_package.sh does exactly that).
mkdir -p "$DST/certificates"
for c in p19cert_d6 p23cert_d6; do
  [ -d "$K/$c" ] && cp -R "$K/$c" "$DST/certificates/"
done
cp "$K/p19_coverage_cert.txt" "$DST/certificates/" 2>/dev/null || true
cp "$K/p23cert_run.log" "$DST/certificates/" 2>/dev/null || true

# --------------------------------------------------------------- verdicts
mkdir -p "$DST/verdicts"
for v in verdict_ledger.tsv verdict_ledger.py p19_margin1_VERDICT.txt \
         p43_minus1v_VERDICT.txt p31_minus1v_VERDICT.txt \
         p23_arc_critical_VERDICT.txt \
         WITNESSES_paley_minus_vertex.md \
         WITNESSES_paley_arcrev.md WITNESSES_margin_hierarchy.md; do
  [ -f "$K/$v" ] && cp "$K/$v" "$DST/verdicts/"
done
for d in m1_family m1_arcrev vt21_majority vt21_margin1 n23_tmin4 \
         vt21_recover vt23_recover p27p31_probe drt19_wit p23arc_witness; do
  [ -d "$K/$d" ] || continue
  mkdir -p "$DST/verdicts/$d"
  find "$K/$d" -maxdepth 1 -type f \
       \( -name '*.md' -o -name '*.tsv' -o -name '*.txt' -o -name '*.sh' \
          -o -name '*.log' -o -name '*.witness' \) \
       -exec sh -c 'cp "$@" "$0"' "$DST/verdicts/$d/" {} +
done
# Section 3.4's arc-flip spectrum and the n=20 deletion descent: the run logs
# carry the witnesses, so they are the evidence for "every one of the 289 has
# an exhibited unit-margin witness" and not merely a record that it ran.
for f in arcflip_spectrum.log arcflip_spectrum.sh vt20_descent.log; do
  [ -f "$K/$f" ] && cp "$K/$f" "$DST/verdicts/"
done
# Section 3.4's two deleted-vertex sweeps, P31 - v and P43 - v.  Their 8,031
# per-base markers each are resumption state and gitignored at the source, so
# what ships is the condensed times file the kit writes -- one line per base
# state, from which the exact index cover and the 239.5 and 185.5 core-hours all
# re-derive with awk.  Before 2026-09-11 neither sweep had an evidence file in
# this package at all, and CLAIMS.md pointed the P43 - v row at the archive of
# the Paley(43) sweep, which is a different host.
for kit in p31mv_majority p43mv_majority; do
  [ -d "$K/$kit" ] || continue
  mkdir -p "$DST/verdicts/$kit"
  for f in README.md one.sh drive.sh setup.sh compete.sh FINISHED \
           BASE BREAK HOST N NBASE; do
    [ -f "$K/$kit/$f" ] && cp "$K/$kit/$f" "$DST/verdicts/$kit/"
  done
  find "$K/$kit" -maxdepth 1 -type f -name '*_times.txt' \
       -exec sh -c 'cp "$@" "$0"' "$DST/verdicts/$kit/" {} +
done
if [ -d "$K/vt20_descent_shard" ]; then
  mkdir -p "$DST/verdicts/vt20_descent_shard"
  find "$K/vt20_descent_shard" -maxdepth 1 -type f -name '*.log' \
       -exec sh -c 'cp "$@" "$0"' "$DST/verdicts/vt20_descent_shard/" {} +
fi

# --------------------------------------------------------------- evidence
# Chunk logs compress about 100x, which is what makes them trackable.
mkdir -p "$DST/evidence"
find "$K/run_evidence" -maxdepth 1 -type f -exec sh -c 'cp "$@" "$0"' "$DST/evidence/" {} +
[ -d "$K/run_evidence/measurements" ] && cp -R "$K/run_evidence/measurements" "$DST/evidence/"
[ -d "$K/run_evidence/arcrev" ] && cp -R "$K/run_evidence/arcrev" "$DST/evidence/"

# ---------------------------------------------------------------- cluster
# The three computations that used the cluster -- the 15-vertex regular census,
# the order-13 self-converse census (split between the two machines) and the
# order-12 analysis of Appendix C -- plus the independent-reproduction kit.
# Sources and records only.  These kits build helper binaries in place
# (freearc, rigid, order_sym, tri, kcover) and copying them would ship 35 MB of
# other-architecture executables that the .c files beside them regenerate.
mkdir -p "$DST/cluster"
for j in jz_n15 jz_n13sc jz_n12cover jz_reproduce jz_p23arc; do
  [ -d "$K/$j" ] || continue
  mkdir -p "$DST/cluster/$j"
  find "$K/$j" -maxdepth 1 -type f \
       \( -name '*.sh' -o -name '*.py' -o -name '*.c' -o -name '*.md' \
          -o -name '*.txt' -o -name '*.tsv' -o -name '*.slurm' \
          -o -name '*.log' -o -name '*.conf' -o -name '*.json' \) \
       -exec sh -c 'cp "$@" "$0"' "$DST/cluster/$j/" {} +
done
# jz_reproduce keeps two directories one level down: the instance confs, which
# are the only place a campaign's expected values live, and the SLURM logs that
# are the evidence for Section 5.2's independent-reproduction claim.
for sub in instances slurm; do
  [ -d "$K/jz_reproduce/$sub" ] || continue
  mkdir -p "$DST/cluster/jz_reproduce/$sub"
  find "$K/jz_reproduce/$sub" -maxdepth 1 -type f \
       -exec sh -c 'cp "$@" "$0"' "$DST/cluster/jz_reproduce/$sub/" {} +
done
# jz_n13sc keeps its accounting one level down: state/ holds the per-bucket
# partition that both machines must match line for line, which is the
# cross-check that makes the split sweep auditable at all.
if [ -d "$K/jz_n13sc/state" ]; then
  mkdir -p "$DST/cluster/jz_n13sc/state"
  find "$K/jz_n13sc/state" -maxdepth 1 -type f \
       -exec sh -c 'cp "$@" "$0"' "$DST/cluster/jz_n13sc/state/" {} +
fi
# The not-provably-rigid class: 77 chunk summaries, one line each.  These are
# the verdicts for 319,270 of the family, and until this sweep they existed
# only as a hard-coded figure in aggregate.sh -- which was wrong twice.
if [ -d "$K/jz_n13sc/results_excluded/done" ]; then
  mkdir -p "$DST/cluster/jz_n13sc/results_excluded/done"
  find "$K/jz_n13sc/results_excluded/done" -type f \
       -exec sh -c 'cp "$@" "$0"' "$DST/cluster/jz_n13sc/results_excluded/done/" {} +
fi
cp "$K/jz_n13sc/selfconverse_regular_n13.log" "$DST/cluster/jz_n13sc/" 2>/dev/null || true
cp "$K/n13_regular_result.txt" "$DST/verdicts/" 2>/dev/null || true
cp "$K/selfconverse_regular_count.py" "$DST/verify/" 2>/dev/null || true
# The laptop half's 81 shard markers.  One line each, and they ARE the evidence
# for the part of that sweep this package can vouch for; the kit's own
# aggregate reads them and reports how much of the family is still outstanding.
[ -d "$K/jz_n13sc/results_local" ] && cp -R "$K/jz_n13sc/results_local" "$DST/cluster/jz_n13sc/"

# ------------------------------------------------------------------ notes
cp "$K/RESEARCH_LOG.md" "$DST/notes_research_log.md"
cp "$K/REPRODUCE.md" "$DST/REPRODUCE.md"

# ------------------------------------------------------------- manuscript
mkdir -p "$DST/manuscript"
for m in Tournaments_not_inducible_by_five_voters.md \
         Tournaments_not_inducible_by_five_voters.tex \
         Tournaments_not_inducible_by_five_voters.pdf; do
  [ -f "$SRC/$m" ] && cp "$SRC/$m" "$DST/manuscript/"
done
# Figure 1 and the pipeline that draws it.  paley7_trace.py is a second,
# independent implementation of the placement search whose seven cross-checks
# must pass before it will emit a trace, and paley7_figure.py --check verifies
# the caption's numbers against that trace -- so the figure is an artifact, not
# an illustration.
mkdir -p "$DST/manuscript/figures"
for f in paley7_alg1.pdf paley7_alg1.tex paley7_figure.py paley7_trace.py \
         show_trace.py smallest_instance.py trace_maj.json n7_census.log README.md; do
  [ -f "$SRC/figures/$f" ] && cp "$SRC/figures/$f" "$DST/manuscript/figures/"
done
cp "$SRC/check_manuscript_tables.py" "$DST/tools/" 2>/dev/null || true

echo "assembled."
find "$DST" -type f | wc -l | sed 's/^/files: /'
du -sh "$DST" | sed 's/^/size:  /'
