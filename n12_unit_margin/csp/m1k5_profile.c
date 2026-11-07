/* m1k5_profile.c — turn cert_m1k5 witnesses into explicit five-voter profiles.
 *
 * Input: the stdout of cert_m1k5 (lines "Y <bits> | <label per arc>"; an
 * "N <bits>" line means cert_m1k5 found no unit-margin profile, and this
 * program stops with an error on it, since every input is meant to have one).
 * Each label names the pair of voters (cert_m1k5's init_labels order) that
 * rank the arc backward.  Voter i's order is therefore the tournament with the
 * arcs of every pair containing i reversed; that digraph must be transitive,
 * and the order lists its vertices by decreasing out-degree.
 *
 * Output, one line per tournament: "<bits> <o1> <o2> <o3> <o4> <o5>", where
 * <bits> is the input bitstring (gentourng upper-triangle order, bit 1 <=> i->j
 * for i < j) and each <ok> lists the vertices 0..n-1 from top to bottom, one
 * character per vertex.  The output is checked by verify_unit_margin.py, which
 * shares no code with this program or with cert_m1k5.
 *
 * Usage: m1k5_profile n < cert_output > profiles   (n <= 10)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 10
static int n, m;
static int A[MAXN][MAXN];
static int pairA[10], pairB[10];

static void die(const char *msg, const char *line) {
    fprintf(stderr, "m1k5_profile FAIL (%s): %s\n", msg, line);
    exit(1);
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: m1k5_profile n\n"); return 2; }
    n = atoi(argv[1]); m = n * (n - 1) / 2;
    if (n < 3 || n > MAXN) { fprintf(stderr, "n must be in 3..%d\n", MAXN); return 2; }
    int l = 0;
    for (int i = 0; i < 5; i++) for (int j = i + 1; j < 5; j++) { pairA[l] = i; pairB[l] = j; l++; }
    char line[1024];
    long count = 0;
    while (fgets(line, sizeof line, stdin)) {
        if (line[0] == 'N') die("cert_m1k5 found no unit-margin profile", line);
        if (line[0] != 'Y' || line[1] != ' ') die("unexpected line", line);
        char *bits = line + 2;
        char *bar = strchr(line, '|');
        if (!bar || bar - bits != m + 1) die("bitstring has the wrong length", line);
        int k = 0, au[MAXN * MAXN], av[MAXN * MAXN];
        for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) {
            if (bits[k] == '1') { A[i][j] = 1; A[j][i] = 0; au[k] = i; av[k] = j; }
            else if (bits[k] == '0') { A[i][j] = 0; A[j][i] = 1; au[k] = j; av[k] = i; }
            else die("bad bit", line);
            k++;
        }
        int lab[MAXN * MAXN];
        char *p = bar + 1, *q;
        for (int a = 0; a < m; a++) {
            lab[a] = (int)strtol(p, &q, 10);
            if (q == p || lab[a] < 0 || lab[a] > 9) die("bad label", line);
            p = q;
        }
        char out[5][MAXN + 1];
        for (int v = 0; v < 5; v++) {
            int D[MAXN][MAXN];
            memcpy(D, A, sizeof D);
            for (int a = 0; a < m; a++)
                if (pairA[lab[a]] == v || pairB[lab[a]] == v) { D[au[a]][av[a]] = 0; D[av[a]][au[a]] = 1; }
            int slot[MAXN];
            for (int s = 0; s < n; s++) slot[s] = -1;
            for (int x = 0; x < n; x++) {
                int d = 0;
                for (int y = 0; y < n; y++) d += D[x][y];
                /* a transitive tournament has out-degrees n-1, ..., 0, each once */
                if (slot[n - 1 - d] != -1) die("a voter's digraph is not transitive", line);
                slot[n - 1 - d] = x;
            }
            for (int s = 0; s < n; s++) out[v][s] = (char)('0' + slot[s]);
            out[v][n] = 0;
        }
        fwrite(bits, 1, m, stdout);
        for (int v = 0; v < 5; v++) printf(" %s", out[v]);
        printf("\n");
        count++;
    }
    fprintf(stderr, "m1k5_profile: wrote %ld profiles\n", count);
    return 0;
}
