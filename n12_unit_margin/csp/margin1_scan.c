/* margin1_scan.c — triple-local CSP decision of (a) margin-1 3-realizability
 * (3 labels) and (b) full 3-realizability (4 labels: 0 = unanimous arc), for
 * gentourng bit-string input (upper triangle, bit=1 <=> i->j for i<j).
 *
 * Labels = dissenting voter per arc (0 = none).  Constraints per vertex triple:
 *   cyclic triple:      labels are a permutation of {1,2,3}  (rainbow, no 0)
 *   transitive triple (shortcut s, path p1,p2), for each voter i in {1,2,3}:
 *       not( ls==i && l1!=i && l2!=i )     [class i = {s} alone]
 *       not( l1==i && l2==i && ls!=i )     [class i = {p1,p2} without s]
 * Class i = inversion set of voter i's order; reversal transitive <=> no
 * directed C3 after reversal <=> exactly these triple conditions.
 *
 * Usage: margin1_scan n < bitstrings
 * Output per tournament: one char: 'M' margin-1-realizable, 'R' 3-realizable
 * but not margin-1 (echoes the line to stdout, prefixed R), 'N' neither.
 * Final tallies to stderr.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int n, m;                       /* vertices, arcs = n(n-1)/2 */
#define MAXN 14
#define MAXM (MAXN*(MAXN-1)/2)
#define MAXT (MAXN*(MAXN-1)*(MAXN-2)/6)

static int A[MAXN][MAXN];
static int aidx[MAXN][MAXN];           /* arc index of ordered arc u->v */
static int ntri;
static int tri_kind[MAXT];             /* 1 cyclic, 0 transitive */
static int tri_arc[MAXT][3];           /* cyclic: any order; trans: s,p1,p2 */
static int occ[MAXM][MAXN*3];          /* triples containing arc */
static int nocc[MAXM];

static void build_triples(void) {
    ntri = 0;
    for (int x = 0; x < n; x++) for (int y = x+1; y < n; y++) for (int z = y+1; z < n; z++) {
        int ab = A[x][y], bc = A[y][z], ca = A[z][x];
        int t = ntri++;
        if ((ab && bc && ca) || (!ab && !bc && !ca)) {
            tri_kind[t] = 1;
            if (ab) { tri_arc[t][0]=aidx[x][y]; tri_arc[t][1]=aidx[y][z]; tri_arc[t][2]=aidx[z][x]; }
            else    { tri_arc[t][0]=aidx[y][x]; tri_arc[t][1]=aidx[z][y]; tri_arc[t][2]=aidx[x][z]; }
        } else {
            /* transitive: find source (beats both), sink (loses both), mid */
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
        for (int k = 0; k < 3; k++) {
            int a = tri_arc[t][k];
            occ[a][nocc[a]++] = t;
        }
    }
}

/* masks: bit l set <=> label l still possible (bits 0..3) */
static int prune(unsigned char *mask, int *queue, int qn) {
    static unsigned char inq[MAXT];
    memset(inq, 0, ntri);
    int head = 0;
    for (int i = 0; i < qn; i++) inq[queue[i]] = 1;
    while (head < qn) {
        int t = queue[head++]; inq[t] = 0;
        int a0 = tri_arc[t][0], a1 = tri_arc[t][1], a2 = tri_arc[t][2];
        int m0 = mask[a0], m1 = mask[a1], m2 = mask[a2];
        int n0 = 0, n1 = 0, n2 = 0;
        if (tri_kind[t]) {                       /* rainbow over {1,2,3} */
            for (int c0 = 1; c0 <= 3; c0++) { if (!((m0>>c0)&1)) continue;
                for (int c1 = 1; c1 <= 3; c1++) { if (c1==c0 || !((m1>>c1)&1)) continue;
                    int c2 = 6 - c0 - c1;
                    if ((m2>>c2)&1) { n0 |= 1<<c0; n1 |= 1<<c1; n2 |= 1<<c2; }
                } }
        } else {                                 /* s,p1,p2 */
            for (int cs = 0; cs <= 3; cs++) { if (!((m0>>cs)&1)) continue;
                for (int c1 = 0; c1 <= 3; c1++) { if (!((m1>>c1)&1)) continue;
                    for (int c2 = 0; c2 <= 3; c2++) { if (!((m2>>c2)&1)) continue;
                        if (cs != 0 && cs != c1 && cs != c2) continue;      /* {s} alone */
                        if (c1 != 0 && c1 == c2 && cs != c1) continue;      /* {p1,p2} */
                        n0 |= 1<<cs; n1 |= 1<<c1; n2 |= 1<<c2;
                    } } }
        }
        if (!n0 || !n1 || !n2) return 0;
        int as[3] = {a0, a1, a2}, ns[3] = {n0, n1, n2};
        for (int k = 0; k < 3; k++) {
            if (ns[k] != mask[as[k]]) {
                mask[as[k]] = (unsigned char)ns[k];
                for (int j = 0; j < nocc[as[k]]; j++) {
                    int tt = occ[as[k]][j];
                    if (!inq[tt]) { inq[tt] = 1; queue[qn++] = tt; }
                }
            }
        }
        if (qn > MAXT*8) { fprintf(stderr, "queue overflow\n"); exit(1); }
    }
    return 1;
}

static int popc(int x){ int c=0; while(x){c+=x&1;x>>=1;} return c; }

static int dfs(unsigned char *mask, int usedmax) {
    int best = 5, ba = -1;
    for (int a = 0; a < m; a++) {
        int pc = popc(mask[a]);
        if (pc > 1 && pc < best) { best = pc; ba = a; }
    }
    if (ba < 0) return 1;
    int capped = usedmax + 1; if (capped > 3) capped = 3;
    for (int c = 0; c <= capped; c++) {          /* label 0 first, then 1..usedmax+1 */
        if (!((mask[ba]>>c)&1)) continue;
        unsigned char m2[MAXM];
        memcpy(m2, mask, m);
        m2[ba] = (unsigned char)(1 << c);
        int queue[MAXT*8], qn = 0;
        for (int j = 0; j < nocc[ba]; j++) queue[qn++] = occ[ba][j];
        int um = usedmax > c ? usedmax : c;
        if (prune(m2, queue, qn) && dfs(m2, um)) return 1;
    }
    return 0;
}

static int solve(int allow0) {
    unsigned char mask[MAXM];
    unsigned char init = allow0 ? 0x0F : 0x0E;
    for (int a = 0; a < m; a++) mask[a] = init;
    /* value symmetry over voters 1..3: fix nothing beyond usedmax ordering;
       seed: first arc restricted to {0,1} (or {1} if !allow0) */
    mask[0] &= allow0 ? 0x03 : 0x02;
    int queue[MAXT*8], qn = 0;
    for (int j = 0; j < nocc[0]; j++) queue[qn++] = occ[0][j];
    if (!prune(mask, queue, qn)) return 0;
    return dfs(mask, 1);                          /* labels <= usedmax+1; start 1 */
}

int main(int argc, char **argv) {
    n = atoi(argv[1]); m = n*(n-1)/2;
    char line[256];
    long tot = 0, msat = 0, rns = 0, nreal = 0;
    while (fgets(line, sizeof line, stdin)) {
        int k = 0;
        for (int i = 0; i < n; i++) for (int j = i+1; j < n; j++) {
            if (line[k] == '1') { A[i][j] = 1; A[j][i] = 0; }
            else                { A[i][j] = 0; A[j][i] = 1; }
            k++;
        }
        if (!(line[k]=='\n' || line[k]=='\r' || line[k]==0)) { fprintf(stderr, "bad line len\n"); return 1; }
        int idx = 0;
        for (int i = 0; i < n; i++) for (int j = i+1; j < n; j++) {
            if (A[i][j]) aidx[i][j] = idx; else aidx[j][i] = idx;
            idx++;
        }
        memset(nocc, 0, sizeof nocc);
        build_triples();
        tot++;
        if (solve(0)) msat++;                     /* margin-1 realizable */
        else if (solve(1)) { rns++; line[m] = 0; printf("R %s\n", line); }
        else { nreal++;
               if (argc > 2 && !strcmp(argv[2], "emitn")) { line[m] = 0; printf("N %s\n", line); } }
        if (tot % 1000000 == 0) fprintf(stderr, "... %ld done (M %ld / R %ld / N %ld)\n", tot, msat, rns, nreal);
    }
    fprintf(stderr, "n=%d: total %ld, margin1-SAT %ld, REALIZABLE-NOT-MARGIN1 %ld, non-realizable %ld\n",
            n, tot, msat, rns, nreal);
    return 0;
}
