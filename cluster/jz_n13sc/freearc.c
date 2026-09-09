/* Count arcs lying in NO directed 3-cycle ("free arcs"), and split a listing by
 * whether it has any.
 *
 * WHY THESE ARCS: a linear order agrees with at most 2 arcs of a cyclic
 * triangle, so over k voters the three supports of a 3-cycle sum to <= 2k and
 * none can be unanimous.  Hence an arc inside any 3-cycle can never be
 * unanimous, and the arcs OUTSIDE every 3-cycle are the only ones where plain
 * majority permits a 5:0 split.  Margin-1 forbids that and demands exactly 3:2
 * there -- so these arcs are precisely where the unit-margin requirement asks
 * for something majority does not, which is where the k=3 analogue puts the
 * "inducible but not margin-1" tournaments and their forced arcs.
 *
 * arc u->v is in no 3-cycle  <=>  no w with v->w->u  <=>  N+(v) & N-(u) = 0.
 *
 * Note this selects TOWARD imbalance: every arc of a regular tournament lies in
 * a 3-cycle, so regular hosts have zero free arcs.  It is a different signal
 * from the symmetry ordering, not a refinement of it.
 *
 * usage: freearc <n> <infile> <withfree> <nofree>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAXN 32

int main(int argc, char **argv) {
    int n = atoi(argv[1]);
    FILE *f = fopen(argv[2], "r");
    FILE *fw = fopen(argv[3], "w");
    FILE *fn = fopen(argv[4], "w");
    if (!f || !fw || !fn) { perror("open"); return 1; }
    int need = n * (n - 1) / 2;
    char *line = malloc(need + 64);
    unsigned int out[MAXN], in[MAXN];
    long long nwith = 0, nno = 0, hist[128];
    memset(hist, 0, sizeof hist);
    while (fgets(line, need + 64, f)) {
        int len = 0;
        while (line[len] == '0' || line[len] == '1') len++;
        if (len != need) continue;
        for (int i = 0; i < n; i++) { out[i] = 0; in[i] = 0; }
        int k = 0;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++, k++) {
                if (line[k] == '1') { out[i] |= 1u << j; in[j] |= 1u << i; }
                else                { out[j] |= 1u << i; in[i] |= 1u << j; }
            }
        int free_arcs = 0;
        for (int u = 0; u < n; u++)
            for (int v = 0; v < n; v++)
                if (u != v && (out[u] >> v & 1))
                    if ((out[v] & in[u]) == 0) free_arcs++;
        line[need] = 0;
        if (free_arcs < 128) hist[free_arcs]++;
        if (free_arcs > 0) { fprintf(fw, "%s\n", line); nwith++; }
        else               { fprintf(fn, "%s\n", line); nno++; }
    }
    fprintf(stderr, "  %s: %lld with free arcs, %lld with none\n", argv[2], nwith, nno);
    fprintf(stderr, "  free-arc count histogram:");
    for (int i = 0; i < 20; i++) if (hist[i]) fprintf(stderr, " %d:%lld", i, hist[i]);
    fprintf(stderr, "\n");
    return 0;
}
