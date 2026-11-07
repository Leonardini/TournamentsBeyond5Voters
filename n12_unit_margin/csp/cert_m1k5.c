/* cert_m1k5.c — decide margin-1 5-inducibility: five linear orders
 * such that every arc of T is forward in >= 4 of them (SAT => alpha*(T) >= 2/3,
 * and for non-transitive T then alpha* = 2/3 exactly; also => 5-inducible by
 * striking any voter: >= 3 of 5 per arc).
 *
 * CSP: label each arc by its dissent set D (voters ranking it backward),
 * |D| <= 2 (22 labels).  Per voter i, class {arcs : i in D} must be an
 * inversion set => triple-local conditions:
 *   cyclic triple: the three dissent sets are disjoint PAIRS partitioning the
 *     six voters (coverage >= 1 per voter, sizes <= 2, 3*2 = 6 forces this);
 *   transitive triple (s, p1, p2): D(s) subset of D(p1) u D(p2), and
 *     D(p1) n D(p2) subset of D(s).
 * Symmetry: voters S_6-interchangeable; broken by pinning the first cyclic
 * triple's partition to ({0,1},{2,3},{4,5}) (residual within-pair swaps only).
 *
 * Usage: cert6 n < bitstrings ; prints "Y <line>" / "N <line>", tallies stderr.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int n, m;
#define MAXN 24
#define MAXM (MAXN*(MAXN-1)/2)
#define MAXT (MAXN*(MAXN-1)*(MAXN-2)/6)
#define NL 10                     /* labels: the 10 dissent PAIRS of 5 voters */

static int A[MAXN][MAXN], aidx[MAXN][MAXN];
static int ntri, tri_kind[MAXT], tri_arc[MAXT][3];
static int occ[MAXM][MAXN*3], nocc[MAXM];
static int voterbm[NL], pair_lbl[64];

static void init_labels(void) {
    int l = 0;
    memset(pair_lbl, -1, sizeof pair_lbl);
    for (int i = 0; i < 5; i++) for (int j = i+1; j < 5; j++) {
        voterbm[l] = (1 << i) | (1 << j);
        pair_lbl[voterbm[l]] = l;
        l++;
    }
}

static void build(void) {
    int idx = 0;
    for (int i = 0; i < n; i++) for (int j = i+1; j < n; j++) {
        if (A[i][j]) aidx[i][j] = idx; else aidx[j][i] = idx;
        idx++;
    }
    memset(nocc, 0, sizeof nocc);
    ntri = 0;
    for (int x = 0; x < n; x++) for (int y = x+1; y < n; y++) for (int z = y+1; z < n; z++) {
        int ab = A[x][y], bc = A[y][z], ca = A[z][x];
        int t = ntri++;
        if ((ab && bc && ca) || (!ab && !bc && !ca)) {
            tri_kind[t] = 1;
            if (ab) { tri_arc[t][0]=aidx[x][y]; tri_arc[t][1]=aidx[y][z]; tri_arc[t][2]=aidx[z][x]; }
            else    { tri_arc[t][0]=aidx[y][x]; tri_arc[t][1]=aidx[z][y]; tri_arc[t][2]=aidx[x][z]; }
        } else {
            int v[3] = {x, y, z}, src=-1, snk=-1, mid=-1;
            for (int i = 0; i < 3; i++) {
                int wins = 0;
                for (int j = 0; j < 3; j++) if (i != j && A[v[i]][v[j]]) wins++;
                if (wins == 2) src = v[i];
                if (wins == 0) snk = v[i];
            }
            for (int i = 0; i < 3; i++) if (v[i] != src && v[i] != snk) mid = v[i];
            tri_kind[t] = 0;
            tri_arc[t][0] = aidx[src][snk];
            tri_arc[t][1] = aidx[src][mid];
            tri_arc[t][2] = aidx[mid][snk];
        }
        for (int k = 0; k < 3; k++) { int a = tri_arc[t][k]; occ[a][nocc[a]++] = t; }
    }
}

static int prune(unsigned int *mask, int *queue, int qn) {
    static unsigned char inq[MAXT];
    memset(inq, 0, ntri);
    int head = 0;
    for (int i = 0; i < qn; i++) inq[queue[i]] = 1;
    while (head < qn) {
        int t = queue[head++]; inq[t] = 0;
        int a0 = tri_arc[t][0], a1 = tri_arc[t][1], a2 = tri_arc[t][2];
        unsigned int m0 = mask[a0], m1 = mask[a1], m2 = mask[a2];
        unsigned int n0 = 0, n1 = 0, n2 = 0;
        if (tri_kind[t]) {   /* one voter doubled, four voters once: |union|=5? no:
                                 3 pairs, 6 slots over 5 voters, each >=1 => exactly one twice */
            for (int l0 = 0; l0 < NL; l0++) { if (!((m0 >> l0) & 1)) continue;
                int b0 = voterbm[l0];
                for (int l1 = 0; l1 < NL; l1++) { if (!((m1 >> l1) & 1)) continue;
                    int b1 = voterbm[l1];
                    for (int l2 = 0; l2 < NL; l2++) { if (!((m2 >> l2) & 1)) continue;
                        int b2 = voterbm[l2];
                        if ((b0 | b1 | b2) != 0x1F) continue;          /* cover all 5 */
                        n0 |= 1u << l0; n1 |= 1u << l1; n2 |= 1u << l2;
                    } } }
        } else {                                  /* s, p1, p2 */
            for (int ls = 0; ls < NL; ls++) { if (!((m0 >> ls) & 1)) continue;
                int bs = voterbm[ls];
                for (int l1 = 0; l1 < NL; l1++) { if (!((m1 >> l1) & 1)) continue;
                    int b1 = voterbm[l1];
                    for (int l2 = 0; l2 < NL; l2++) { if (!((m2 >> l2) & 1)) continue;
                        int b2 = voterbm[l2];
                        if (bs & ~(b1 | b2)) continue;        /* D(s) not covered */
                        if (b1 & b2 & ~bs) continue;          /* path pair escapes s */
                        n0 |= 1u << ls; n1 |= 1u << l1; n2 |= 1u << l2;
                    } } }
        }
        if (!n0 || !n1 || !n2) return 0;
        int as[3] = {a0, a1, a2}; unsigned int ns[3] = {n0, n1, n2};
        for (int k = 0; k < 3; k++) {
            if (ns[k] != mask[as[k]]) {
                mask[as[k]] = ns[k];
                for (int j = 0; j < nocc[as[k]]; j++) {
                    int tt = occ[as[k]][j];
                    if (!inq[tt]) { inq[tt] = 1; queue[qn++] = tt; }
                }
            }
        }
        if (qn > MAXT*24) { fprintf(stderr, "queue overflow\n"); exit(1); }
    }
    return 1;
}

static int popc(unsigned int x){ return __builtin_popcount(x); }
static unsigned int sol_mask[MAXM];
static int g_queue[MAXT*24];
static unsigned int g_m2[MAXM+2][MAXM];  /* per-depth branch masks */

static int dfs(unsigned int *mask, int depth) {
    int best = NL + 1, ba = -1;
    for (int a = 0; a < m; a++) {
        int pc = popc(mask[a]);
        if (pc > 1 && pc < best) { best = pc; ba = a; }
    }
    if (ba < 0) { memcpy(sol_mask, mask, m * sizeof(unsigned int)); return 1; }
    for (int l = 0; l < NL; l++) {
        if (!((mask[ba] >> l) & 1)) continue;
        unsigned int *m2 = g_m2[depth];
        memcpy(m2, mask, m * sizeof(unsigned int));
        m2[ba] = 1u << l;
        int qn = 0;
        for (int j = 0; j < nocc[ba]; j++) g_queue[qn++] = occ[ba][j];
        if (prune(m2, g_queue, qn) && dfs(m2, depth + 1)) return 1;
    }
    return 0;
}

static int pin_u = -1, pin_v = -1, pin_w = -1;
static int solve_cert6(void) {
    unsigned int mask[MAXM];
    unsigned int FULLM = (1u << NL) - 1;
    for (int a = 0; a < m; a++) mask[a] = FULLM;
    /* Symmetry (SOUND form): on the first cyclic triple the labels are, up to
       voter renaming, ({0,1},{0,2},{3,4}) in one of the 3 rotations — WHICH arc
       carries the doubled-voter-free pair {3,4} is structural and must be
       branched over, not pinned.  Union domains + the coverage constraint leave
       exactly the three rotation patterns (all cross-combinations fail coverage);
       residual symmetry: the 3<->4 swap only. */
    if (pin_u >= 0) {
        /* caller-designated triangle admitting a rotating graph automorphism
           (e.g. an affine order-3 orbit in a Paley tournament): the free-pair
           arc can be normalized, so the SINGLE pattern P1 is sound here. */
        int e1, e2, e3;
        if (A[pin_u][pin_v]) { e1 = aidx[pin_u][pin_v]; e2 = aidx[pin_v][pin_w]; e3 = aidx[pin_w][pin_u]; }
        else                 { e1 = aidx[pin_v][pin_u]; e2 = aidx[pin_u][pin_w]; e3 = aidx[pin_w][pin_v]; }
        mask[e1] = 1u << pair_lbl[0x03];
        mask[e2] = 1u << pair_lbl[0x05];
        mask[e3] = 1u << pair_lbl[0x18];
    } else
    for (int t = 0; t < ntri; t++) {
        if (tri_kind[t]) {
            mask[tri_arc[t][0]] = (1u << pair_lbl[0x03]) | (1u << pair_lbl[0x18]);
            mask[tri_arc[t][1]] = (1u << pair_lbl[0x05]) | (1u << pair_lbl[0x18])
                                | (1u << pair_lbl[0x03]);
            mask[tri_arc[t][2]] = (1u << pair_lbl[0x18]) | (1u << pair_lbl[0x05]);
            break;
        }
    }
    int qn = 0;
    for (int t = 0; t < ntri; t++) g_queue[qn++] = t;
    if (!prune(mask, g_queue, qn)) return 0;
    return dfs(mask, 0);
}

int main(int argc, char **argv) {
    n = atoi(argv[1]); m = n*(n-1)/2;
    init_labels();
    if (argc > 4) { pin_u = atoi(argv[2]); pin_v = atoi(argv[3]); pin_w = atoi(argv[4]); }
    char line[256];
    long tot = 0, yes = 0;
    while (fgets(line, sizeof line, stdin)) {
        if ((line[0] == 'C' || line[0] == 'N' || line[0] == 'R') && strchr(line, ' '))
            memmove(line, strchr(line, ' ') + 1, strlen(strchr(line, ' ')));
        int k = 0;
        for (int i = 0; i < n; i++) for (int j = i+1; j < n; j++) {
            if (line[k] == '1') { A[i][j] = 1; A[j][i] = 0; }
            else                { A[i][j] = 0; A[j][i] = 1; }
            k++;
        }
        line[m] = 0;
        build();
        tot++;
        if (solve_cert6()) {
            yes++;
            printf("Y %s |", line);
            for (int a = 0; a < m; a++) printf(" %d", __builtin_ctz(sol_mask[a]));
            printf("\n");
        }
        else printf("N %s\n", line);
        if (tot % 10000 == 0) fprintf(stderr, "... %ld (Y %ld)\n", tot, yes);
    }
    fprintf(stderr, "total %ld: margin1-k5-SAT %ld, UNSAT %ld\n", tot, yes, tot - yes);
    return 0;
}
