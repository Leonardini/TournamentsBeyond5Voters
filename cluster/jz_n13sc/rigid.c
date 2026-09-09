/* Split a tournament listing into POSSIBLY-SYMMETRIC and PROVABLY-RIGID.
 *
 * Colour refinement (1-WL): start from out-degree, repeatedly recolour by
 * (own colour, sorted multiset of out-neighbour colours, sorted multiset of
 * in-neighbour colours) until stable.  If the partition becomes DISCRETE, any
 * automorphism must preserve colours and therefore fix every vertex, so the
 * tournament is RIGID.  That direction is a theorem, so nothing symmetric is
 * ever misfiled as rigid.  Non-discrete is only a CANDIDATE for symmetry
 * (1-WL is incomplete), which is the safe direction for ordering a hunt.
 *
 * NOTE for self-converse listings: "rigid" here means Aut(T) is trivial.  Every
 * self-converse tournament also carries an ANTI-automorphism sigma (u->v iff
 * sigma(v)->sigma(u)), which refinement cannot see because refinement respects
 * arc direction.  That symmetry is universal in the family, so it does not
 * discriminate between members and |Aut| remains the right ordering key.
 *
 * usage: rigid <n> <infile> <symfile> <rigidfile>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAXN 32
static int n, A[MAXN][MAXN];
static int col[MAXN], nc;

static int cmpint(const void *a, const void *b) { return *(int *)a - *(int *)b; }

static int refine(void) {
    static int sig[MAXN][2 * MAXN + 4];
    int width = 2 * n + 3;
    for (int it = 0; it < n; it++) {
        for (int v = 0; v < n; v++) {
            int k = 0;
            sig[v][k++] = col[v];
            int ou[MAXN], iv[MAXN], no = 0, ni = 0;
            for (int w = 0; w < n; w++)
                if (w != v) { if (A[v][w]) ou[no++] = col[w]; else iv[ni++] = col[w]; }
            qsort(ou, no, sizeof(int), cmpint);
            qsort(iv, ni, sizeof(int), cmpint);
            for (int i = 0; i < no; i++) sig[v][k++] = ou[i];
            sig[v][k++] = -1;
            for (int i = 0; i < ni; i++) sig[v][k++] = iv[i];
            while (k < width) sig[v][k++] = -2;
        }
        int newc[MAXN], changed = 0;
        for (int i = 0; i < n; i++) {
            int r = 0;
            for (int j = 0; j < n; j++)
                if (memcmp(sig[j], sig[i], sizeof(int) * width) < 0) r++;
            newc[i] = r;
        }
        for (int i = 0; i < n; i++) if (newc[i] != col[i]) changed = 1;
        memcpy(col, newc, sizeof(int) * n);
        if (!changed) break;
    }
    int seen[MAXN];
    memset(seen, 0, sizeof seen);
    nc = 0;
    for (int i = 0; i < n; i++) if (!seen[col[i]]) { seen[col[i]] = 1; nc++; }
    return nc == n;                   /* discrete => provably rigid */
}

int main(int argc, char **argv) {
    n = atoi(argv[1]);
    FILE *f = fopen(argv[2], "r");
    FILE *fs = fopen(argv[3], "w");
    FILE *fg = fopen(argv[4], "w");
    if (!f || !fs || !fg) { perror("open"); return 1; }
    int need = n * (n - 1) / 2;
    char *line = malloc(need + 64);
    long long sym = 0, rig = 0;
    while (fgets(line, need + 64, f)) {
        int len = 0;
        while (line[len] == '0' || line[len] == '1') len++;
        if (len != need) continue;
        int k = 0;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++, k++) { A[i][j] = line[k] == '1'; A[j][i] = !A[i][j]; }
        for (int i = 0; i < n; i++) {
            A[i][i] = 0;
            int d = 0;
            for (int j = 0; j < n; j++) d += A[i][j];
            col[i] = d;
        }
        line[need] = 0;
        if (refine()) { fprintf(fg, "%s\n", line); rig++; }
        else          { fprintf(fs, "%s\n", line); sym++; }
    }
    fprintf(stderr, "  %s: %lld possibly-symmetric, %lld provably rigid\n", argv[2], sym, rig);
    return 0;
}
