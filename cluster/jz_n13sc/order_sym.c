/* Order a tournament listing from MOST to LEAST symmetric, cheaply.
 *
 * Proxy: score-sequence imbalance sum|d_i - (n-1)/2|.  Full |Aut| would be
 * better but costs a canonicalisation per host (~100us x 95M = 2.6 core-h);
 * imbalance is O(n^2) with no allocation and correlates with the symmetry we
 * care about -- the known margin-1 obstruction, Paley(19), is regular.
 *
 * Imbalance 0 (fully REGULAR) hosts are dropped: every regular tournament on
 * n<=13 is already known 5-inducible at both margins, so re-running them is
 * pure waste.  Their count is reported so the skip is auditable.
 *
 * With --only-regular the filter is inverted and ONLY those hosts are emitted,
 * so the skipped set can be swept directly instead of being taken on trust
 * from a cross-reference.  The degree computation stays in one place, which is
 * the point: a second tool that recomputed imbalance its own way could drift
 * from this one and partition the listing differently.
 *
 * usage: order_sym <n> <infile> [--only-regular]
 *          -> prints "imbalance<TAB>line" to stdout
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: order_sym <n> <infile> [--only-regular]\n"); return 2; }
    int n = atoi(argv[1]);
    int only_regular = (argc > 3 && strcmp(argv[3], "--only-regular") == 0);
    FILE *f = fopen(argv[2], "r");
    if (!f) { perror(argv[2]); return 1; }
    int need = n * (n - 1) / 2;
    char *line = malloc(need + 64);
    long long total = 0, regular = 0;
    int d[64];
    while (fgets(line, need + 64, f)) {
        int len = 0; while (line[len] == '0' || line[len] == '1') len++;
        if (len != need) continue;
        total++;
        for (int i = 0; i < n; i++) d[i] = 0;
        int k = 0;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++, k++)
                if (line[k] == '1') d[i]++; else d[j]++;
        /* imbalance x2 so it stays integral for even n as well */
        int imb = 0;
        for (int i = 0; i < n; i++) { int t = 2 * d[i] - (n - 1); imb += t < 0 ? -t : t; }
        if (imb == 0) regular++;
        if ((imb == 0) != only_regular) continue;   /* skip the half not asked for */
        line[need] = 0;
        printf("%d\t%s\n", imb, line);
    }
    fprintf(stderr, "  %s: %lld hosts, %lld regular, %lld irregular; emitted the %s\n",
            argv[2], total, regular, total - regular,
            only_regular ? "regular" : "irregular");
    return 0;
}
