#!/bin/sh
# Assemble this reproduction package from the working repository.
#
# Every file here came from KemenyMedian by way of this script, so the
# provenance of the package is one readable list rather than a recollection.
#
#   usage: tools/assemble_from_source.sh [path-to-KemenyMedian]
#
# The default source path is the sibling checkout.
#
# THE SOURCE GUARD.  The package is edited in its own right: the manuscript is
# refreshed from the author's branch before the source checkout catches up, and
# files such as REPRODUCE.md, the certificate READMEs and the verify/, sat/ and
# figure scripts carry package-side edits (section labels, relabelled
# cross-references).  Overwriting any of them from the source would silently
# undo that work.  So EVERY file this script copies goes through one function,
# put(), and the script runs in two passes over the same list:
#
#   1. check: for each copy, compare the source with the package copy.
#        identical         -> nothing to do
#        package lacks it  -> a new file, copied in pass 2
#        they differ       -> REFUSED, unless accepted (below)
#      Nothing is written in this pass.  If any difference is refused, the
#      script stops after the pass, lists every refused file, and the package
#      is untouched.  Two copies aimed at the same package path also stop it.
#   2. copy: only if pass 1 refused nothing.  Identical files are left alone,
#      so a run against an identical source changes nothing at all.
#
# To take the source's version of a differing file deliberately, name the
# package path AND the exact source bytes:
#
#   ACCEPT_SOURCE="<package path>=<sha256 of the source file> ..." tools/assemble_from_source.sh
#
# with tokens separated by spaces or newlines.  Pass 1 prints the exact token of
# every refused file, so accepting is a deliberate choice of the ones wanted.
# Because a token names the bytes, an acceptance left set from an earlier run
# cannot accept a later, different source file.
#
# Not copies, and so not guarded: the CERT-v2 blocks, which pass 2 regenerates
# from package files alone (see the end).  Everything else, including the slice
# archive this script packs from the source, goes through put().
#
# The earlier manuscript-only guard (ACCEPT_MANUSCRIPT, bare sha256 values) is
# retired; setting it is a hard error rather than a silently ignored variable.

set -eu

SRC=${1:-$(cd "$(dirname "$0")/../.." && pwd)/KemenyMedian}
DST=$(cd "$(dirname "$0")/.." && pwd)
K="$SRC/KInduceDFS"

[ -d "$K" ] || { echo "FATAL no KInduceDFS under $SRC" >&2; exit 1; }
if [ -n "${ACCEPT_MANUSCRIPT:-}" ]; then
  echo "FATAL ACCEPT_MANUSCRIPT is retired; use ACCEPT_SOURCE=\"<package path>=<sha256>\" (see the header)" >&2
  exit 1
fi
echo "source: $SRC"
echo "dest:   $DST"

T=$(mktemp -d "${TMPDIR:-/tmp}/assemble.XXXXXX")
trap 'rm -rf "$T"' EXIT
: > "$T/refused"; : > "$T/accepted"; : > "$T/new"; : > "$T/tokens"; : > "$T/dests"
for tok in ${ACCEPT_SOURCE:-}; do
  case "$tok" in
    ?*=????????????????????????????????????????????????????????????????) echo "$tok" >> "$T/tokens" ;;
    *) echo "FATAL ACCEPT_SOURCE token '$tok' is not <package path>=<64-hex sha256>" >&2; exit 1 ;;
  esac
done

sha256_of() { (shasum -a 256 "$1" 2>/dev/null || sha256sum "$1") | cut -c1-64; }

# put SOURCE-FILE PACKAGE-FILE (absolute).  The one way this script writes a copy.
put() {
  [ -f "$1" ] || { echo "FATAL put: source $1 is not a regular file" >&2; exit 1; }
  [ ! -L "$1" ] || { echo "FATAL put: source $1 is a symbolic link" >&2; exit 1; }
  rel=${2#"$DST"/}
  [ "$rel" != "$2" ] || { echo "FATAL put: $2 is outside the package" >&2; exit 1; }
  if [ "$MODE" = check ]; then echo "$rel" >> "$T/dests"; fi
  if [ -e "$2" ]; then
    if cmp -s "$1" "$2"; then return 0; fi
    tok="$rel=$(sha256_of "$1")"
    if grep -qxF "$tok" "$T/tokens"; then
      if [ "$MODE" = check ]; then echo "$tok" >> "$T/accepted"; fi
    elif [ "$MODE" = check ]; then
      echo "$tok" >> "$T/refused"
      return 0
    else
      # Pass 2 runs only after pass 1 refused nothing, over the same list, so a
      # difference that is not accepted here means the source changed during the run.
      echo "FATAL $rel differs and was not accepted in pass 2; the source changed during the run" >&2
      exit 1
    fi
  elif [ "$MODE" = check ]; then
    echo "$rel" >> "$T/new"
  fi
  if [ "$MODE" = copy ]; then
    mkdir -p "$(dirname "$2")"
    cp "$1" "$2"
  fi
  return 0
}

# put_list PACKAGE-DIR < list-of-source-files: each into PACKAGE-DIR under its basename.
put_list() {
  while IFS= read -r f; do put "$f" "$1/$(basename "$f")"; done
  return 0
}

# put_tree SOURCE-DIR PACKAGE-DIR: the whole tree, relative paths kept (what cp -R did).
put_tree() {
  if [ -n "$(find "$1" -type l | head -1)" ]; then
    echo "FATAL put_tree: $1 holds symbolic links, which put() does not copy" >&2; exit 1
  fi
  find "$1" -type f | LC_ALL=C sort > "$T/tree"
  while IFS= read -r f; do put "$f" "$2/${f#"$1"/}"; done < "$T/tree"
  return 0
}

# put_found PACKAGE-DIR SOURCE-DIR [FIND-TESTS...]: what
# `find SOURCE-DIR -maxdepth 1 -type f FIND-TESTS -exec cp {} PACKAGE-DIR` did.
put_found() {
  pd=$1; sd=$2; shift 2
  find "$sd" -maxdepth 1 -type f "$@" | LC_ALL=C sort > "$T/found"
  put_list "$pd" < "$T/found"
}

assemble() {
# ---------------------------------------------------------------- engine
put "$K/kinduce.c" "$DST/engine/kinduce.c"
put "$K/kinduce.1" "$DST/engine/kinduce.1"
put "$K/kcover.c" "$DST/engine/kcover.c"          # order-12 witness extension (Appendix @app:order12)
# kinduce25.c carries the --pin machinery that no published result used, and
# REPRODUCE.md excludes it from the package by name, so it is never copied.
for v in "$K"/versions/kinduce[0-2][0-9].c; do
  [ "$(basename "$v")" = kinduce25.c ] && continue
  put "$v" "$DST/engine/versions/$(basename "$v")"
done
# The regression that compares the consolidated engine against each of those
# versions on the published command lines.  Until it existed, REPRODUCE.md cited
# a versions/REGRESSION.md that was never written.
put "$K/regression.sh" "$DST/engine/regression.sh"
if [ -f "$K/versions/REGRESSION.md" ]; then put "$K/versions/REGRESSION.md" "$DST/engine/versions/REGRESSION.md"; fi

# ---------------------------------------------------------- tournaments
# Vertex numbering is part of the input, not a detail: node counts only
# replicate against the numbering we used, and two of the 21-vertex hosts are
# not in the canonical labelling a fresh enumeration produces.  So the bit
# strings ship, and the generators ship beside them for checking.
put_found "$DST/tournaments" "$K" -name '*.bits'
for g in paley_bits.py make_paley_gf.py make_paley_minus.py vt21_family.py \
         vt_census.py vt_small_gen.py vt23_gen.py drt23_gen.py drt15_gen.py \
         gen_regular.py cayley_census.py deletion_classes.py vt21_all_reps.npy; do
  if [ -f "$K/$g" ]; then put "$K/$g" "$DST/tournaments/$g"; fi
done
# families: the swept catalogues, with their verdict tables
for f in vt21_hosts vt21_arcflip dr19_arcflip vt15 vt17 vt19 vt23 drt23 \
         drt15 drt19 drt_small vt20_descent; do
  [ -d "$K/$f" ] || continue
  put_found "$DST/tournaments/$f" "$K/$f" \
       \( -name '*.bits' -o -name '*.tsv' -o -name '*.md' -o -name '*.sh' -o -name '*.log' \)
done
# per-orbit outcome files behind the arc-flip spectrum at 21 vertices (Appendix @app:criticality21)
if [ -d "$K/vt21_arcflip/out" ]; then put_tree "$K/vt21_arcflip/out" "$DST/tournaments/vt21_arcflip/out"; fi

# ------------------------------------------------------------- SAT route
for s in cubes.py cube_sat.py certify_d6.py certify_p19_m1.py cover_check.py \
         cover_deep.py certroot.py reroot.py run_cubes.py verify_root.py \
         verify_p19_root.py deepen.py cfg_hash.py leaf_bench.py \
         base_survivors.py registry.py; do
  if [ -f "$K/$s" ]; then put "$K/$s" "$DST/sat/$s"; fi
done

# ------------------------------------------------- independent verifiers
# These share no code with the search.  A witness is read back from its run
# log, the tournament from its bit string, and every arc's support recomputed.
for v in verify_witness.py verify_witness_bits.py \
         verify_paley_minus_witness.py tri_per_arc.py tri_ceiling.py \
         triangles_per_arc.py \
         verify_descent_witnesses.py level_coverage.py drt23_level_counts.py \
         critical_deletions.py host_facts.py sweep_cover_audit.py; do
  if [ -f "$K/$v" ]; then put "$K/$v" "$DST/verify/$v"; fi
done

# ---------------------------------------------------------- certificates
# The LRAT proof bytes were verified and discarded by design; what ships is
# the per-cube sha256 chain in log/, from which both published roots rebuild
# (tools/check_package.sh does exactly that).
for c in p19cert_d6 p23cert_d6; do
  if [ -d "$K/$c" ]; then put_tree "$K/$c" "$DST/certificates/$c"; fi
done
# h02_f00 ships FILTERED, not wholesale: its source directory also holds the
# 130 MB coverage proof (regenerable in ~7 min, and over GitHub's per-file
# limit) and an empty work/.  What is the certificate's substance is done/,
# log/ and the verdict.
if [ -d "$K/h02f00_cert" ]; then
  put_tree "$K/h02f00_cert/done" "$DST/certificates/h02f00cert_d6/done"
  put_tree "$K/h02f00_cert/log" "$DST/certificates/h02f00cert_d6/log"
  put "$K/h02f00_cert/VERDICT.txt" "$DST/certificates/h02f00cert_d6/VERDICT.txt"
  if [ -f "$K/h02f00_cert/README.md" ]; then put "$K/h02f00_cert/README.md" "$DST/certificates/h02f00cert_d6/README.md"; fi
fi
# d005_mv04 (the N(5) <= 22 host) ships FILTERED for the same reason: beside
# done/, log/ and the verdict its source directory holds the 442 MB coverage
# proof, the 183 MB coverage CNF under work/, and the run's own watchdog files.
if [ -d "$K/d005mv04_cert" ]; then
  put_tree "$K/d005mv04_cert/done" "$DST/certificates/d005mv04cert_d6/done"
  put_tree "$K/d005mv04_cert/log" "$DST/certificates/d005mv04cert_d6/log"
  put "$K/d005mv04_cert/VERDICT.txt" "$DST/certificates/d005mv04cert_d6/VERDICT.txt"
  put "$K/d005mv04_cert/README.md" "$DST/certificates/d005mv04cert_d6/README.md"
fi
# Its host is a vertex deletion of a doubly regular tournament on 23 vertices;
# the working repository keeps it with the cluster sweep that found it.
if [ -f "$K/jz_sweep1/hosts/d005_mv04.bits" ]; then
  put "$K/jz_sweep1/hosts/d005_mv04.bits" "$DST/tournaments/drt23_del/d005_mv04.bits"
fi
# The second 22-vertex obstruction, and the levels below the doubly regular
# tournaments that Appendix @app:below22 reports: the 18 parents (one per converse pair)
# and the 21- and 20-vertex level files, one host per class, from which
# verify/drt23_level_counts.py re-derives the class counts.
if [ -f "$K/jz_sweep1/hosts/d027_mv04.bits" ]; then
  put "$K/jz_sweep1/hosts/d027_mv04.bits" "$DST/tournaments/drt23_del/d027_mv04.bits"
fi
for f in PARENTS18.txt HOSTS_level2.tsv HOSTS_level3.tsv; do
  if [ -f "$K/drt23_del/$f" ]; then put "$K/drt23_del/$f" "$DST/tournaments/drt23_del/$f"; fi
done
# The two 25-vertex parents of Appendix @app:below22's other lineages: Paley(27) less two
# vertices, and the circulant on 25 vertices with six triangles on every arc.
for h in p27_mv00_01 t25_tmin6; do
  if [ -f "$K/jz_sweep1/hosts/$h.bits" ]; then
    put "$K/jz_sweep1/hosts/$h.bits" "$DST/tournaments/descent_parents/$h.bits"
  fi
done
for f in p19_coverage_cert.txt h02f00_coverage_cert.txt d005mv04_coverage_cert.txt p23cert_run.log; do
  if [ -f "$K/$f" ]; then put "$K/$f" "$DST/certificates/$f"; fi
done

# --------------------------------------------------------------- verdicts
for v in verdict_ledger.tsv verdict_ledger.py p19_margin1_VERDICT.txt \
         p43_minus1v_VERDICT.txt p31_minus1v_VERDICT.txt \
         p23_arc_critical_VERDICT.txt \
         WITNESSES_paley_minus_vertex.md \
         WITNESSES_paley_arcrev.md WITNESSES_margin_hierarchy.md; do
  if [ -f "$K/$v" ]; then put "$K/$v" "$DST/verdicts/$v"; fi
done
for d in m1_family m1_arcrev vt21_majority vt21_margin1 n23_tmin4 \
         vt21_recover vt23_recover p27p31_probe drt19_wit p23arc_witness; do
  [ -d "$K/$d" ] || continue
  put_found "$DST/verdicts/$d" "$K/$d" \
       \( -name '*.md' -o -name '*.tsv' -o -name '*.txt' -o -name '*.sh' \
          -o -name '*.log' -o -name '*.witness' \)
done
# The doubly regular tournaments on 23 vertices (Section @sec:families): the unit-margin
# roll-up of all 18 converse classes, and the unrestricted roll-up of the two run
# on the laptop; the other 16 are cluster/jz_drt23maj/jz_drt23maj.tsv.
if [ -f "$K/drt23_m1/drt23_m1.tsv" ]; then put "$K/drt23_m1/drt23_m1.tsv" "$DST/verdicts/drt23/drt23_m1.tsv"; fi
if [ -f "$K/drt23_maj/drt23_maj.tsv" ]; then put "$K/drt23_maj/drt23_maj.tsv" "$DST/verdicts/drt23/drt23_maj.tsv"; fi
# The twelve hardest vertex-transitive tournaments on 23 vertices, at unit margin and
# unrestricted (Section @sec:families): the roll-ups the ledger reads, and the majority witnesses of
# the eleven that are unit-margin obstructions (plus v023's unit-margin witness).
for f in vt23_m1/vt23_m1.tsv vt23_maj/vt23_maj.tsv; do
  if [ -f "$K/$f" ]; then put "$K/$f" "$DST/verdicts/vt23/$(basename "$f")"; fi
done
if [ -d "$K/vt23_maj/out" ]; then put_found "$DST/verdicts/vt23/out" "$K/vt23_maj/out" -name '*.majority.txt'; fi
if [ -f "$K/vt23_m1/out/v023.exact.txt" ]; then put "$K/vt23_m1/out/v023.exact.txt" "$DST/verdicts/vt23/out/v023.exact.txt"; fi
# The two 22-vertex obstructions' roll-up.  Its check.sh compares the host
# copies against the cluster kit's directory, which is not shipped, so only the
# README and the verdict table come across; the hosts are in
# tournaments/drt23_del/.
if [ -d "$K/n22_obstructions" ]; then
  put "$K/n22_obstructions/README.md" "$DST/verdicts/n22_obstructions/README.md"
  put "$K/n22_obstructions/verdicts.tsv" "$DST/verdicts/n22_obstructions/verdicts.tsv"
fi
# The arc-flip spectrum at 21 vertices (Appendix @app:criticality21) and the n=20 deletion descent: the run logs
# carry the witnesses, so they are the evidence for "every one of the 289 has
# an exhibited unit-margin witness" and not merely a record that it ran.
for f in arcflip_spectrum.log arcflip_spectrum.sh vt20_descent.log; do
  if [ -f "$K/$f" ]; then put "$K/$f" "$DST/verdicts/$f"; fi
done
# The slice logs behind that spectrum: for each of the 15 reversals that stay unit-margin
# obstructions they tile all 2,200 base states, and verify/separation_supplement.py checks it.
# The spectrum log alone records h01_f05 to h01_f09 only in its summary line.  The archive
# is packed into a scratch file once and then put() like any other copy.
if [ -d "$K/vt21_arcflip_shard" ]; then
  if [ ! -f "$T/vt21_arcflip_slices.tar.zst" ]; then
    (cd "$K" && tar --format ustar -cf - vt21_arcflip_shard) | zstd -19 -q -f -o "$T/vt21_arcflip_slices.tar.zst"
  fi
  put "$T/vt21_arcflip_slices.tar.zst" "$DST/evidence/vt21_arcflip_slices.tar.zst"
fi
# The two deleted-vertex sweeps of Section @sec:paley23-critical, P31 - v and P43 - v.  Their 8,031
# per-base markers each are resumption state and gitignored at the source, so
# what ships is the condensed times file the kit writes -- one line per base
# state, from which the exact index cover and the 239.5 and 185.5 core-hours all
# re-derive with awk.  Before 2026-09-11 neither sweep had an evidence file in
# this package at all, and CLAIMS.md pointed the P43 - v row at the archive of
# the Paley(43) sweep, which is a different host.
for kit in p31mv_majority p43mv_majority; do
  [ -d "$K/$kit" ] || continue
  for f in README.md one.sh drive.sh setup.sh compete.sh FINISHED \
           BASE BREAK HOST N NBASE; do
    if [ -f "$K/$kit/$f" ]; then put "$K/$kit/$f" "$DST/verdicts/$kit/$f"; fi
  done
  put_found "$DST/verdicts/$kit" "$K/$kit" -name '*_times.txt'
done
if [ -d "$K/vt20_descent_shard" ]; then
  put_found "$DST/verdicts/vt20_descent_shard" "$K/vt20_descent_shard" -name '*.log'
fi

# --------------------------------------------------------------- evidence
# Chunk logs compress about 100x, which is what makes them trackable.
# d005mv04_cert_log.tar.zst is the archive of certificates/d005mv04cert_d6/log/,
# which ships unpacked because check 3 rebuilds the roots from it; one copy.
put_found "$DST/evidence" "$K/run_evidence" ! -name 'd005mv04_cert_log.tar.zst'
if [ -d "$K/run_evidence/measurements" ]; then put_tree "$K/run_evidence/measurements" "$DST/evidence/measurements"; fi
if [ -d "$K/run_evidence/arcrev" ]; then put_tree "$K/run_evidence/arcrev" "$DST/evidence/arcrev"; fi

# ---------------------------------------------------------------- cluster
# The computations that used the cluster -- the 15-vertex regular census, the
# order-13 self-converse census (split between the two machines), the order-12
# analysis of Appendix @app:order12, and the 16 doubly regular tournaments on 23 vertices
# at unrestricted margin (Section @sec:families) -- plus the independent-reproduction kit.
# Sources and records only.  These kits build helper binaries in place
# (freearc, rigid, order_sym, tri, kcover) and copying them would ship 35 MB of
# other-architecture executables that the .c files beside them regenerate.
for j in jz_n15 jz_n13sc jz_reproduce jz_p23arc jz_drt23maj; do
  [ -d "$K/$j" ] || continue
  put_found "$DST/cluster/$j" "$K/$j" \
       \( -name '*.sh' -o -name '*.py' -o -name '*.c' -o -name '*.md' \
          -o -name '*.txt' -o -name '*.tsv' -o -name '*.slurm' \
          -o -name '*.log' -o -name '*.conf' -o -name '*.json' \)
done
# The order-12 analysis lives with the rest of the n <= 12 unit-margin evidence.
if [ -d "$K/jz_n12cover" ]; then
  put_found "$DST/n12_unit_margin/n12_cover" "$K/jz_n12cover" \
       \( -name '*.sh' -o -name '*.py' -o -name '*.c' -o -name '*.md' \
          -o -name '*.txt' -o -name '*.slurm' \)
fi
# Not from KemenyMedian: the rest of n12_unit_margin/ (the n <= 11 witnesses, census and
# integer program), counting_bounds/, paley43/ and reports/paley43-five-voters/ moved here
# from the companion paper's repository (github.com/Leonardini/Tournaments) on 2026-11-07,
# when those results moved to this paper.  This script does not touch them.
# Also not from KemenyMedian: verdicts/ledger_supplement.tsv, the record of the 17
# unit-margin-only tournaments that the ledger's registry cannot hold (arc reversals and
# Paley(23) - v), and verify/separation_supplement.py, which re-derives it; both written in
# this package on 2026-11-07.
# The 378-deletion screen at 22 vertices (Appendix @app:below22): its per-host roll-up,
# from which 378 hosts, 18,900 base states tried and 13,863 exhausted re-add.
# The per-state markers stay on the cluster.
if [ -f "$K/jz_drt23mv/evidence/HARDNESS_378.tsv" ]; then
  put "$K/jz_drt23mv/evidence/HARDNESS_378.tsv" "$DST/cluster/jz_drt23mv/HARDNESS_378.tsv"
fi
# jz_reproduce keeps two directories one level down: the instance confs, which
# are the only place a campaign's expected values live, and the SLURM logs that
# are the evidence for Section @sec:reproducibility's independent-reproduction claim.
for sub in instances slurm; do
  [ -d "$K/jz_reproduce/$sub" ] || continue
  put_found "$DST/cluster/jz_reproduce/$sub" "$K/jz_reproduce/$sub"
done
# jz_n13sc keeps its accounting one level down: state/ holds the per-bucket
# partition that both machines must match line for line, which is the
# cross-check that makes the split sweep auditable at all.
if [ -d "$K/jz_n13sc/state" ]; then put_found "$DST/cluster/jz_n13sc/state" "$K/jz_n13sc/state"; fi
# The not-provably-rigid class: 77 chunk summaries, one line each.  These are
# the verdicts for 319,270 of the family, and until this sweep they existed
# only as a hard-coded figure in aggregate.sh -- which was wrong twice.
if [ -d "$K/jz_n13sc/results_excluded/done" ]; then
  find "$K/jz_n13sc/results_excluded/done" -type f | LC_ALL=C sort > "$T/excl"
  put_list "$DST/cluster/jz_n13sc/results_excluded/done" < "$T/excl"
fi
# (jz_n13sc/selfconverse_regular_n13.log comes with the kit's *.log files above.)
if [ -f "$K/n13_regular_result.txt" ]; then put "$K/n13_regular_result.txt" "$DST/verdicts/n13_regular_result.txt"; fi
if [ -f "$K/selfconverse_regular_count.py" ]; then put "$K/selfconverse_regular_count.py" "$DST/verify/selfconverse_regular_count.py"; fi
# The laptop half's 81 shard markers.  One line each, and they ARE the evidence
# for the part of that sweep this package can vouch for; the kit's own
# aggregate reads them and reports how much of the family is still outstanding.
if [ -d "$K/jz_n13sc/results_local" ]; then put_tree "$K/jz_n13sc/results_local" "$DST/cluster/jz_n13sc/results_local"; fi

# ------------------------------------------------------------------ notes
put "$K/RESEARCH_LOG.md" "$DST/notes_research_log.md"
put "$K/REPRODUCE.md" "$DST/REPRODUCE.md"

# ------------------------------------------------------------- manuscript
# The version submitted to Mathematical Social Sciences, with its highlights.
# The source checkout can hold an OLDER copy than this package (the author edits
# the manuscript on a branch, and the main checkout is stale until he merges it),
# which is how the guard above began.
for m in Tournaments_not_inducible_by_five_voters_MSS.md \
         Tournaments_not_inducible_by_five_voters_MSS.tex \
         Tournaments_not_inducible_by_five_voters_MSS.pdf \
         MSS_highlights_paper2.txt; do
  if [ -f "$SRC/$m" ]; then put "$SRC/$m" "$DST/manuscript/$m"; fi
done
# Figure @fig:paley7 and the pipeline that draws it.  paley7_trace.py is a second,
# independent implementation of the placement search whose seven cross-checks
# must pass before it will emit a trace, and paley7_figure.py --check verifies
# the caption's numbers against that trace -- so the figure is an artifact, not
# an illustration.
# EVERY figure artifact, by extension rather than by a hand-kept list.  A hand-kept
# list once went stale the moment a figure was added: README.md documented that
# figure and its checks while its script and outputs were not shipped, so the
# instructions referred to files the package did not contain.  A list of names is
# correct exactly once.
# The one exclusion: roundE*, the figure of the locally transitive appendix, which
# moved to the companion paper (without its figure); only superseded manuscript
# versions in the source still include it, so the package does not ship it.
put_found "$DST/manuscript/figures" "$SRC/figures" \
     \( -name '*.py' -o -name '*.tex' -o -name '*.pdf' -o -name '*.json' \
        -o -name '*.log' -o -name '*.md' \) ! -name 'roundE*'
if [ -f "$SRC/check_manuscript_tables.py" ]; then put "$SRC/check_manuscript_tables.py" "$DST/tools/check_manuscript_tables.py"; fi
return 0
}

# ------------------------------------------------------------ pass 1: check
MODE=check
assemble
dup=$(LC_ALL=C sort "$T/dests" | uniq -d)
if [ -n "$dup" ]; then
  echo "FATAL two copies aim at the same package path; nothing was copied:" >&2
  echo "$dup" | sed 's/^/  /' >&2
  exit 1
fi
if [ -s "$T/accepted" ]; then
  echo "accepted (the source version will replace the package's):"
  sed 's/^/  /' "$T/accepted"
fi
if [ -s "$T/refused" ]; then
  n=$(wc -l < "$T/refused" | tr -d ' ')
  echo "FATAL $n package file(s) differ from their source and were not accepted; nothing was copied:" >&2
  sed 's/^/  /' "$T/refused" >&2
  echo "      Each line is <package path>=<sha256 of the source file>.  If the source is the" >&2
  echo "      version to keep, put that exact line in ACCEPT_SOURCE (space-separated) and rerun." >&2
  echo "      If the package copy is the newer one, carry its edit back to the source first." >&2
  exit 1
fi

# ------------------------------------------------------------- pass 2: copy
MODE=copy
assemble
if [ -s "$T/new" ]; then echo "new files:"; sed 's/^/  /' "$T/new"; fi

# ------------------------------------------------- CERT-v2 blocks (DERIVED)
# Regenerated here rather than copied, because `host_bits` is a path RELATIVE
# TO THE BLOCK, so the value depends on THIS package's layout and a block built
# against the working repository's layout would hash differently.  Nothing is
# solved and nothing is retyped: --from-v1 lifts every parameter and all four
# component hashes out of the published v1 pair after verifying that both v1
# blocks hash to the values they state.  See certificates/CERT-v2.md.  These are
# a function of package files alone, so they are rebuilt, not guarded.
# v2_install PACKAGE-BASE: certroot.py wrote the new block beside PACKAGE-BASE under
# the prefix .assemble-new.v2 (the same directory, because host_bits is relative to
# it); move it into place file by file, replacing only what changed, so a rerun on
# identical inputs writes nothing.
v2_install() {
  d=$(dirname "$1")
  for f in "$d"/.assemble-new.v2*; do
    out="$1${f#"$d"/.assemble-new.v2}"
    if cmp -s "$f" "$out" 2>/dev/null; then rm -f "$f"
    else mv "$f" "$out"; echo "rebuilt: ${out#"$DST"/}"; fi
  done
  return 0
}
for inst in p19 p23; do
  [ -f "$DST/certificates/${inst}cert_d6/${inst}_cert.portable.txt" ] || continue
  python3 "$DST/sat/certroot.py" --v2 \
    --from-v1 "$DST/certificates/${inst}cert_d6/${inst}_cert" \
    --host-bits "$DST/tournaments/${inst}_paley.bits" \
    --host-name "${inst}_paley" \
    --origin "paley(${inst#p}), quadratic-residue convention of sat/cube_sat.py paley()" \
    --out "$(dirname "$DST/certificates/${inst}cert_d6/${inst}_cert.v2")/.assemble-new.v2" >/dev/null
  v2_install "$DST/certificates/${inst}cert_d6/${inst}_cert.v2"
done
# h02_f00 has no v1 block to lift from -- 21 is not a prime power, so no `q`
# describes it at all.  Its parameters and all four component hashes are READ
# from the two files that record them, never written here: a constant copied
# into a builder is correct once, on the day it is copied.
if [ -f "$DST/certificates/h02f00cert_d6/VERDICT.txt" ]; then
  V="$DST/certificates/h02f00cert_d6/VERDICT.txt"
  C="$DST/certificates/h02f00_coverage_cert.txt"
  python3 "$DST/sat/certroot.py" --v2 \
    --host-bits "$DST/tournaments/vt21_arcflip/h02_f00.bits" \
    --host-name h02_f00 \
    --origin "h02 with the arc 0->1 reversed (arc orbit 00 of the n=21 unit-margin obstruction h02; row h02_f00 of tournaments/vt21_arcflip/manifest.tsv)" \
    --k 5 --margin "$(awk '/^margin /{print $2; exit}' "$V")" \
    --base $(awk -F'[][]' '/^base /{gsub(/,/," ",$2); print $2; exit}' "$V") \
    --cubes "$(awk '/^cubes /{gsub(/,/,"",$2); print $2; exit}' "$V")" \
    --root-cnf "$(awk '/^ROOT \(CNF\)/{print $3; exit}' "$V")" \
    --root-proofs "$(awk '/^ROOT \(proofs\)/{print $3; exit}' "$V")" \
    --cover-cnf-sha "$(awk '/#   coverage CNF /{print $4; exit}' "$C")" \
    --cover-proof-sha "$(awk '/#   coverage proof /{print $4; exit}' "$C")" \
    --out "$(dirname "$DST/certificates/h02f00cert_d6/h02f00_cert.v2")/.assemble-new.v2" >/dev/null
  v2_install "$DST/certificates/h02f00cert_d6/h02f00_cert.v2"
fi
# d005_mv04: no q either (22 is not a prime power), and built the same way, from
# the verdict and the coverage record.
if [ -f "$DST/certificates/d005mv04cert_d6/VERDICT.txt" ]; then
  V="$DST/certificates/d005mv04cert_d6/VERDICT.txt"
  C="$DST/certificates/d005mv04_coverage_cert.txt"
  python3 "$DST/sat/certroot.py" --v2 \
    --host-bits "$DST/tournaments/drt23_del/d005_mv04.bits" \
    --host-name d005_mv04 \
    --origin "the doubly regular tournament d005 (line 6 of McKay's drtourn23.txt, tournaments/drt23/d005.bits) with vertex 4 (0-based) deleted, order of the remaining vertices kept" \
    --k 5 --margin "$(awk '/^margin /{print $2; exit}' "$V")" \
    --base $(awk -F'[][]' '/^base /{gsub(/,/," ",$2); print $2; exit}' "$V") \
    --cubes "$(awk '/^cubes /{gsub(/,/,"",$2); print $2; exit}' "$V")" \
    --root-cnf "$(awk '/^ROOT \(CNF\)/{print $3; exit}' "$V")" \
    --root-proofs "$(awk '/^ROOT \(proofs\)/{print $3; exit}' "$V")" \
    --cover-cnf-sha "$(awk '/#   coverage CNF /{print $4; exit}' "$C")" \
    --cover-proof-sha "$(awk '/#   coverage proof /{print $4; exit}' "$C")" \
    --out "$(dirname "$DST/certificates/d005mv04cert_d6/d005mv04_cert.v2")/.assemble-new.v2" >/dev/null
  v2_install "$DST/certificates/d005mv04cert_d6/d005mv04_cert.v2"
fi

echo "assembled."
find "$DST" -type f -not -path '*/.git/*' | wc -l | sed 's/^/files: /'
du -sh "$DST" | sed 's/^/size:  /'
