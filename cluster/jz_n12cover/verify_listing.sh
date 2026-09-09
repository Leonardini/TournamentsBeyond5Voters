#!/bin/bash
# GATE a pre-existing order-11 listing before evaluating against it.
#
# A listing of the right SIZE but the wrong convention, or a partial run left
# over from an earlier campaign, would evaluate the wrong tournaments and come
# back clean for the wrong reason.  Three checks:
#
#   C1  line count == 903,753,248 (the exact number of order-11 classes)
#   C2  every sampled line is exactly 55 characters of 0/1
#   C3  the number of REGULAR tournaments (all out-degrees 5) is exactly 1,223
#       -- a published invariant, and sensitive to a misparse
#
# C3 is the real check.  Note it does NOT catch a global transpose (converse):
# the regular classes are closed under converse and relabelling, so a
# consistently transposed listing still enumerates every class exactly once and
# is HARMLESS for this campaign.  What C3 catches is a parse that is not a
# bijection onto tournaments at all.
#
#   usage: verify_listing.sh <file-or-directory-of-shards>
set -eu
SRC=${1:?usage: verify_listing.sh <file|dir>}
if [ -d "$SRC" ]; then CAT="cat $SRC/sh_*"; else CAT="cat $SRC"; fi
echo "C1 counting lines (this reads the whole listing, several minutes at ~51 GB)"
N=$(eval "$CAT" | wc -l | tr -d ' ')
echo "   lines = $N"
[ "$N" = 903753248 ] && echo "   C1 PASS" || echo "   C1 FAIL: expected 903,753,248"

echo "C2 sampling line shape"
BAD=$(eval "$CAT" | awk 'NR%1000000==1{if(length($0)!=55 || $0!~/^[01]+$/) b++} END{print b+0}')
echo "   malformed sampled lines = $BAD"
[ "$BAD" = 0 ] && echo "   C2 PASS" || echo "   C2 FAIL"

echo "C3 counting regular tournaments (expect exactly 1,223)"
REG=$(eval "$CAT" | awk '{
    n=11; delete d; for(i=0;i<n;i++) d[i]=0; k=1;
    for(i=0;i<n-1;i++) for(j=i+1;j<n;j++){
        if(substr($0,k,1)=="1") d[i]++; else d[j]++; k++ }
    ok=1; for(i=0;i<n;i++) if(d[i]!=5) { ok=0; break }
    if(ok) c++
  } END{print c+0}')
echo "   regular = $REG"
[ "$REG" = 1223 ] && echo "   C3 PASS" || echo "   C3 FAIL: expected 1223"
