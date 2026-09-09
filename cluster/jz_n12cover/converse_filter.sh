#!/bin/bash
# Keep one host from each converse pair.  See converse_filter.py for the
# correctness argument and its exhaustive selftest; this is the PRODUCTION
# implementation and it uses only awk and nauty's labelg.
#
# WHY NOT PYTHON.  converse_filter.py was the first thing in this kit's
# compute-node path to need an interpreter, and n12cover.slurm loads no module:
# on Jean Zay python3 is not in the default PATH on a compute node, so every
# residue died without a done marker and the aggregator read "residues done: 0".
# The selftest had passed, because the selftest runs on the LOGIN node.  awk is
# present on every node by definition.  The .py version is kept only for its
# selftest, which is run by hand.
#
# LC_ALL=C so that comparing canonical forms is byte order and not locale order.
# Otherwise which host of a pair survives could differ between machines, and two
# machines sweeping different residues could keep BOTH members of a pair or
# NEITHER -- the second of which would silently lose coverage.
export LC_ALL=C
set -u
N=${1:?usage: converse_filter.sh N [stats] < hosts > kept}
STATS=${2:-}
: "${LABELG:?LABELG not set; source gt_path.sh first}"
[ -x "$LABELG" ] || { echo "converse_filter: no executable labelg at '$LABELG'" >&2; exit 1; }

# upper triangle (row major, ascii) -> digraph6.  rev=1 emits the converse.
D6='
function emit(n, a,   i, j, k, v, out, bits, nb) {
  nb = 0
  for (i = 0; i < n; i++) for (j = 0; j < n; j++) bits[nb++] = a[i, j]
  while (nb % 6) bits[nb++] = 0
  out = "&" sprintf("%c", 63 + n)
  for (k = 0; k < nb; k += 6) {
    v = 0
    for (i = 0; i < 6; i++) v = v * 2 + bits[k + i]
    out = out sprintf("%c", 63 + v)
  }
  return out
}
{
  k = 0
  for (i = 0; i < n; i++) for (j = i + 1; j < n; j++) {
    b = substr($0, ++k, 1)
    if (rev) { a[i, j] = (b == "1") ? 0 : 1; a[j, i] = (b == "1") ? 1 : 0 }
    else     { a[i, j] = (b == "1") ? 1 : 0; a[j, i] = (b == "1") ? 0 : 1 }
  }
  if (k != n * (n - 1) / 2) {
    printf("converse_filter: line %d has %d bits, expected C(%d,2)=%d\n",
           NR, length($0), n, n * (n - 1) / 2) > "/dev/stderr"
    exit 1
  }
  for (i = 0; i < n; i++) a[i, i] = 0
  print emit(n, a)
}'

TMP=$(mktemp -d) || exit 1
trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/in"
awk -v n="$N" -v rev=0 "$D6" "$TMP/in" | "$LABELG" -zq > "$TMP/fwd" || exit 1
awk -v n="$N" -v rev=1 "$D6" "$TMP/in" | "$LABELG" -zq > "$TMP/rev" || exit 1
NI=$(wc -l < "$TMP/in" | tr -d ' ')
NF=$(wc -l < "$TMP/fwd" | tr -d ' ')
NRV=$(wc -l < "$TMP/rev" | tr -d ' ')
if [ "$NF" -ne "$NI" ] || [ "$NRV" -ne "$NI" ]; then
  echo "converse_filter: labelg returned $NF and $NRV forms for $NI hosts" >&2
  exit 1
fi
# Keep iff canon(T) <= canon(conv(T)).  Equality means a self-converse host,
# which MUST be kept: it pairs with nothing, so dropping it loses coverage.
# ("" $2) forces string comparison rather than awk's numeric guess.
paste "$TMP/in" "$TMP/fwd" "$TMP/rev" \
  | awk -F'\t' '{ if (("" $2) <= ("" $3)) { print $1; k++ } }
                 END { print k + 0 > "/dev/stderr" }' 2> "$TMP/kept"
K=$(cat "$TMP/kept")
[ -n "$STATS" ] && echo "converse filter: $NI in, $K out" >&2
exit 0
