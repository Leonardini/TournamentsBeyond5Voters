#!/bin/bash
# Compare the halving audit against the census markers, and say which residues
# lost hosts.  See halving_audit.sh for why this exists.
set -eu
_ORIGPWD=$PWD
cd "$(dirname "$0")"
OUT=${1:-results}
case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac
D11=903753248
A="$OUT/audit"; D="$OUT/done"
[ -d "$A" ] || { echo "no audit directory at $A -- run halving_audit.sh first" >&2; exit 1; }
ASNAP=$(mktemp); DSNAP=$(mktemp); trap 'rm -f "$ASNAP" "$DSNAP"' EXIT
printf "reading the audit and the markers (this walks two large directories) ...\n"
find "$A" -type f -exec cat {} + > "$ASNAP" 2>/dev/null || true
find "$D" -type f -exec cat {} + > "$DSNAP" 2>/dev/null || true

# FNR==NR needs a NON-EMPTY first file to tell the two apart; with an empty audit
# it would read the markers as audit records and report nonsense.
[ -s "$ASNAP" ] || { echo "the audit directory is empty -- nothing to compare" >&2; exit 1; }
: > "$OUT/rescreen.txt"
awk -v d11="$D11" -v RESCREEN="$OUT/rescreen.txt" '
  # the audit: res= generated= kept= self=
  FNR == NR {
    split($1,a,"="); split($2,b,"="); split($3,c,"="); split($4,e,"=")
    r=a[2]; AG[r]=b[2]; AK[r]=c[2]; AS[r]=e[2]; na++; ag+=b[2]; ak+=c[2]; as+=e[2]; next }
  # the markers: res= generated= instances= ...
  /^res=/ {
    split($1,a,"="); r=a[2]
    for (i=1;i<=NF;i++) { split($i,f,"="); if (f[1]=="generated") MG[r]=f[2]; if (f[1]=="instances") MI[r]=f[2] }
    nm++; mg+=MG[r]; mi+=MI[r] }
  END {
    printf "\naudited residues %d, generated %d, kept %d, self-converse %d\n", na, ag, ak, as
    printf "marker  residues %d, generated %d, kept %d\n", nm, mg, mi
    # 1. is the AUDIT itself internally consistent?  It is only worth comparing
    #    against if it satisfies the identity the census failed.
    if (ag == d11) {
      printf "\nthe audit generated all %d order-11 classes\n", d11
      if (2*ak - ag != as) {
        printf "FATAL: the audit does not satisfy kept == (D11 + S11)/2 either:\n"
        printf "  kept %d, self-converse %d, implied %d.  The halving is wrong, not the plumbing.\n", ak, as, 2*ak-ag
        exit 1 }
      printf "  and it satisfies kept %d == (D11 + S11)/2 with S11 = %d MEASURED\n", ak, as
    } else
      printf "\nthe audit is INCOMPLETE: %d of %d classes (%.4f%%)\n", ag, d11, 100*ag/d11
    # 2. where did the census lose hosts?
    for (r in AK) {
      if (!(r in MI)) { nomark++; continue }
      if (AG[r] != MG[r]) { gbad++; if (gbad<=10) printf "  res=%s the GENERATOR disagrees: audit %s, marker %s\n", r, AG[r], MG[r] }
      if (AK[r] != MI[r]) {
        kbad++; short += AK[r] - MI[r]
        print r > RESCREEN
        if (kbad<=15) printf "  res=%-6s audit kept %-9s marker screened %-9s  lost %s\n", r, AK[r], MI[r], AK[r]-MI[r] } }
    printf "\nresidues audited but unmarked   : %d\n", nomark+0
    printf "residues where generated differs: %d\n", gbad+0
    printf "residues where kept differs     : %d\n", kbad+0
    printf "hosts the census never screened : %d\n", short+0
    if (kbad+0 == 0 && ag == d11)
      print "\nNothing was lost.  If the census still fails the gate, the two runs used\n" \
            "different nauty builds: a canonical labelling is not portable across\n" \
            "versions, and a converse pair split between two builds can lose BOTH.\n" \
            "Compare labelg in the campaign logs with the one the audit used."
    else if (kbad+0 > 0)
      printf "\n%d residue%s to re-screen, listed in the rescreen file\n", kbad, (kbad==1?"":"s")
  }' "$ASNAP" "$DSNAP"
[ -s "$OUT/rescreen.txt" ] && echo "wrote $OUT/rescreen.txt"
exit 0
