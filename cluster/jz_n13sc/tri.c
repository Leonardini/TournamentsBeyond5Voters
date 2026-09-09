/* Triangles through each arc: min / mean / max over the arcs of a tournament.
 *
 * The count of 3-cycles is C(n,3) - sum_i C(d_i,2), maximised exactly when the
 * out-degrees are equal, so a REGULAR tournament has the most triangles per arc
 * of any tournament on n vertices -- an average of (n+1)/4.  Any bound of the
 * form "margin-1 failure needs at least t triangles through every arc" therefore
 * yields an immediate lower bound on the order of the smallest obstruction.
 *
 * triangles through u->v  =  |N+(v) & N-(u)|  (the w with v->w->u).
 *
 * usage: tri <n> <file>
 */
#include <stdio.h>
#include <stdlib.h>
#define MAXN 64

int main(int argc, char **argv) {
    int n = atoi(argv[1]);
    FILE *f = fopen(argv[2], "r");
    if (!f) { perror(argv[2]); return 1; }
    int need = n * (n - 1) / 2;
    char *line = malloc(need + 64);
    unsigned long long out[MAXN], in[MAXN];
    int idx = 0;
    while (fgets(line, need + 64, f)) {
        int len = 0;
        while (line[len] == '0' || line[len] == '1') len++;
        if (len != need) continue;
        for (int i = 0; i < n; i++) { out[i] = 0; in[i] = 0; }
        int k = 0;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++, k++) {
                if (line[k] == '1') { out[i] |= 1ULL << j; in[j] |= 1ULL << i; }
                else                { out[j] |= 1ULL << i; in[i] |= 1ULL << j; }
            }
        int mn = 1 << 30, mx = 0; long long tot = 0, narcs = 0, cyc = 0;
        for (int u = 0; u < n; u++)
            for (int v = 0; v < n; v++)
                if (u != v && (out[u] >> v & 1)) {
                    int t = __builtin_popcountll(out[v] & in[u]);
                    if (t < mn) mn = t;
                    if (t > mx) mx = t;
                    tot += t; narcs++;
                }
        cyc = tot / 3;
        int mind = n, maxd = 0;
        for (int i = 0; i < n; i++) {
            int d = __builtin_popcountll(out[i]);
            if (d < mind) mind = d;
            if (d > maxd) maxd = d;
        }
        printf("  %-26s arcs=%lld  3-cycles=%lld  tri/arc min=%d mean=%.2f max=%d   out-deg %d..%d\n",
               idx == 0 ? argv[2] : "", narcs, cyc, mn, (double)tot / narcs, mx, mind, maxd);
        idx++;
    }
    return 0;
}
