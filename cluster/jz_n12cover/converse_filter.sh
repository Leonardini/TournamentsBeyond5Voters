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
# A SHORT INPUT MUST NOT PASS AS A SMALL RESIDUE.  This `cat` is unchecked, and
# $TMP comes from mktemp -d -- $TMPDIR or /tmp, NOT the job scratch the caller
# sized.  A full or over-quota $TMPDIR truncates the input here, and every count
# below is then self-consistently too small, so nothing in this script can
# notice.  The caller knows how many hosts it sent, so report how many arrived
# (NI, below) and let the caller be the one to assert that they agree.
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
  | awk -F'\t' '{ if (("" $2) <= ("" $3)) { print $1; k++ }
                  if (("" $2) == ("" $3)) e++ }
                 END { print (k + 0), (e + 0) > "/dev/stderr" }' 2> "$TMP/kept"
# The write side matters too: this awk writes the kept hosts to OUR stdout, which
# is the caller's host file.  A short write there used to be invisible, because
# the script ended in an unconditional `exit 0`.
PS=${PIPESTATUS[*]}
case "$PS" in *[1-9]*) echo "converse_filter: paste|awk failed (status $PS)" >&2; exit 1 ;; esac
read -r K E < "$TMP/kept"
[ -n "${K:-}" ] && [ -n "${E:-}" ] || { echo "converse_filter: no tally from awk" >&2; exit 1; }
# Self-converse hosts are counted, not just kept, because they are the ONLY
# unknown in the global identity kept == (N + S)/2.  Summed over the residues
# they measure S, so the census gate can check an equality it derives rather than
# one it was told.  See aggregate.sh.
if [ -n "${CF_COUNTS:-}" ]; then
  printf 'in=%s kept=%s self=%s\n' "$NI" "$K" "$E" > "$CF_COUNTS" || exit 1
fi
[ -n "$STATS" ] && echo "converse filter: $NI in, $K out, $E self-converse" >&2
exit 0
