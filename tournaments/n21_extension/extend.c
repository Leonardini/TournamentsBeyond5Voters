/* Insert one vertex v into a fixed K-voter majority witness of T - v.
 * stdin, one job per line:  K m  ord[0][0..m-1] ... ord[K-1][0..m-1]  out[0..m-1]
 *   (orders best-first over vertices 0..m-1 of T - v; out[u] = 1 if v -> u in T)
 * For every voter, v goes into one of m+1 slots; slot p puts v above the voter's
 * last m - p vertices.  We need, for every u, more than K/2 voters on the side
 * the arc between v and u requires.  Depth-first over voters, pruning a branch as
 * soon as some u can no longer reach a majority with the voters left.
 * stdout, per job:  "EXT p_0 ... p_{K-1}"  or  "NOEXT".                          */
#include <stdio.h>
#define MAXK 7
#define MAXM 64
static int K, m, ord[MAXK][MAXM], out[MAXM], good[MAXK][MAXM + 1][MAXM], cnt[MAXM], pos[MAXK], need;
static int rec(int i) {
    if (i == K) { for (int u = 0; u < m; u++) if (cnt[u] < need) return 0; return 1; }
    for (int p = 0; p <= m; p++) {
        int ok = 1;
        for (int u = 0; u < m; u++) cnt[u] += good[i][p][u];
        for (int u = 0; u < m && ok; u++) if (cnt[u] + (K - 1 - i) < need) ok = 0;
        if (ok) { pos[i] = p; if (rec(i + 1)) return 1; }
        for (int u = 0; u < m; u++) cnt[u] -= good[i][p][u];
    }
    return 0;
}
int main(void) {
    while (scanf("%d %d", &K, &m) == 2) {
        for (int i = 0; i < K; i++) for (int r = 0; r < m; r++) scanf("%d", &ord[i][r]);
        for (int u = 0; u < m; u++) scanf("%d", &out[u]);
        need = K / 2 + 1;
        for (int i = 0; i < K; i++) for (int p = 0; p <= m; p++) {
            /* slot p: v sits after the first p vertices of voter i's order */
            int before[MAXM] = {0};
            for (int r = 0; r < p; r++) before[ord[i][r]] = 1;          /* u above v */
            for (int u = 0; u < m; u++) good[i][p][u] = out[u] ? !before[u] : before[u];
        }
        for (int u = 0; u < m; u++) cnt[u] = 0;
        if (rec(0)) { printf("EXT"); for (int i = 0; i < K; i++) printf(" %d", pos[i]); printf("\n"); }
        else printf("NOEXT\n");
        fflush(stdout);
    }
    return 0;
}
