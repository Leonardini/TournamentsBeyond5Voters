/* ===========================================================================
 * kinduce.c -- incremental placement DFS for k-inducing profiles with
 *              PER-NODE DYNAMIC vertex selection (minimum remaining values /
 *              fail-first), measured against a static vertex order.
 *
 * STATE at a node: a placed set S and the k voter orders restricted to it.
 * Extending by v notin S = choosing an insertion slot p_i in {0..|S|} in each
 * pi_i|_S.  With U_i(p_i) the suffix of pi_i|_S strictly after that slot,
 *      v <_i u  <==>  u in U_i(p_i),      c_v(u) = #{ i : u in U_i(p_i) }.
 * The arcs between v and S are the only constraints touched, so
 *   D(v|state) = { p : c_v(u) = (k+1)/2  for u in Out(v)&S,
 *                      c_v(u) = (k-1)/2  for u in In(v)&S }     [exact 1]
 * with =  relaxed to >= / <= in --margin majority.
 *
 * BRANCHING (--order mrv): at EVERY node, v* = argmin_{v notin S} |D(v)|,
 * computed from the current partial profile; the node fails the moment any
 * |D(v)| = 0.  This is sound however v* is chosen: for a fixed v*, every full
 * profile extending the node has exactly one insertion tuple for v*, so
 * branching over D(v*) partitions the subtree.  Nothing is precomputed.
 *
 * INITIALISATION: the base is a 5-vertex subset of T chosen (--auto-base) to
 * be the most restrictive one available -- fewest lex-ordered margin-1
 * realisations, looked up from an exhaustive one-time sweep of all sorted
 * k-tuples of the base_sz! orders, cached per labelled base tournament (at
 * most 2^10 of them).  Base states are enumerated directly as sorted
 * multisets, which is the full S_k voter-symmetry break.
 *
 * Counts are bit-sliced over 3 planes, one bit per vertex, so each prune is a
 * few 64-bit ops over all of S at once.  Within a voter, larger p gives a
 * smaller suffix, so counts are non-increasing in p: a lower-bound violation
 * can never recover -> break; an upper-bound violation can -> continue.
 * ===========================================================================
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>
#include <time.h>

#define MAXN 64
#define MAXK 7
#define TCAP 8000000L

static int n, K, tHI, tLO;
static int exact_margin = 1;
static uint64_t OUTM[MAXN];

static int ordv[MAXK][MAXN];
static int m;
static uint64_t placed;
static uint64_t suf[MAXK][MAXN + 1];

static long long nodes = 0, sols = 0, dom_calls = 0, dom_nodes = 0, mrv_fails = 0;
static long long node_limit = 0;
static double time_limit = 0.0;
static int aborted = 0, verbose = 0;

static int order_mrv = 1, find_one = 1, symbreak = 1;
static const char *batch_file = NULL;
static long long bs_from = 0, bs_to = -1;   /* base-state slice [from,to) */
static long long mrv_cap = 20000;
static int tie_imbalance = 1;   /* break MRV ties by |out(v)&S| - |in(v)&S| */
static int base_sz = 5, auto_base = 1;
static int base_v[MAXN], static_order[MAXN];
static double t0;

static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
                          return ts.tv_sec + 1e-9 * ts.tv_nsec; }

static inline uint64_t geq(uint64_t b0, uint64_t b1, uint64_t b2, int t) {
    switch (t) {
        case 0:  return ~0ULL;
        case 1:  return b0 | b1 | b2;
        case 2:  return b1 | b2;
        case 3:  return b2 | (b1 & b0);
        case 4:  return b2;
        case 5:  return b2 & (b0 | b1);
        case 6:  return b2 & b1;
        case 7:  return b2 & b1 & b0;
        default: return (t < 0) ? ~0ULL : 0ULL;
    }
}
static inline uint64_t eqm(uint64_t b0, uint64_t b1, uint64_t b2, int t) {
    uint64_t r = (t & 1) ? b0 : ~b0;
    r &= (t & 2) ? b1 : ~b1;
    r &= (t & 4) ? b2 : ~b2;
    return r;
}

/* ---------------- domain of a candidate vertex ------------------------- */
static uint64_t Aset, Bset;
static long long dcount, dcutoff;
static int dmode;
static uint8_t dpos[MAXK];
static uint8_t *tstack;
static long tsp;

static void dom_rec(int i, uint64_t b0, uint64_t b1, uint64_t b2) {
    dom_nodes++;
    if ((dom_nodes & 0xFFFFF) == 0) {
        if (node_limit && nodes >= node_limit) aborted = 1;
        if (time_limit > 0 && now() - t0 > time_limit) aborted = 1;
        if (aborted) return;
    }
    if (i == K) {
        int ok;
        if (exact_margin)
            ok = ((Aset & ~eqm(b0, b1, b2, tHI)) == 0) && ((Bset & ~eqm(b0, b1, b2, tLO)) == 0);
        else {
            uint64_t g = geq(b0, b1, b2, tHI);
            ok = ((Aset & ~g) == 0) && ((Bset & g) == 0);
        }
        if (ok) {
            dcount++;
            if (dmode == 1) {
                if (tsp >= TCAP) { fprintf(stderr,
                    "FATAL tuple stack overflow at depth %d (domain too large; "
                    "use --order mrv, or raise TCAP)\n", m); exit(2); }
                memcpy(tstack + tsp * MAXK, dpos, K); tsp++;
            }
        }
        return;
    }
    if (exact_margin && i == K - 1) {
        /* The last voter is FORCED.  With s_u the support accumulated over the
         * first k-1 voters, exactness needs the last voter to contribute
         * exactly tau(u) - s_u in {0,1}, so its suffix must be precisely
         *      R = { u in S : tau(u) - s_u = 1 },
         * leaving one candidate slot p = |S| - |R|, valid iff suf[k-1][p] == R.
         * Replaces the whole innermost loop with a few 64-bit ops. */
        uint64_t R = (Aset & eqm(b0, b1, b2, tHI - 1)) | (Bset & eqm(b0, b1, b2, tLO - 1));
        uint64_t Z = (Aset & eqm(b0, b1, b2, tHI))     | (Bset & eqm(b0, b1, b2, tLO));
        if ((R | Z) != placed) return;          /* some deficit outside {0,1}  */
        int p = m - __builtin_popcountll(R);
        if (p < 0 || suf[i][p] != R) return;
        dcount++;
        if (dmode == 1) {
            if (tsp >= TCAP) { fprintf(stderr, "FATAL tuple stack overflow at depth %d\n", m); exit(2); }
            dpos[i] = (uint8_t)p;
            memcpy(tstack + tsp * MAXK, dpos, K); tsp++;
        }
        return;
    }
    int r = K - 1 - i;
    for (int p = 0; p <= m; p++) {
        uint64_t mm = suf[i][p], c0 = b0, c1 = b1, c2 = b2, car, car2;
        car = c0 & mm;   c0 ^= mm;
        car2 = c1 & car; c1 ^= car;
        c2 ^= car2;
        uint64_t lowbad = 0;
        if (tHI - r > 0) lowbad |= (Aset & ~geq(c0, c1, c2, tHI - r));
        if (exact_margin && tLO - r > 0) lowbad |= (Bset & ~geq(c0, c1, c2, tLO - r));
        if (lowbad) break;                       /* counts only shrink in p  */
        uint64_t upbad = (Bset & geq(c0, c1, c2, tLO + 1));
        if (exact_margin) upbad |= (Aset & geq(c0, c1, c2, tHI + 1));
        if (upbad) continue;
        dpos[i] = (uint8_t)p;
        dom_rec(i + 1, c0, c1, c2);
        if (dmode == 0 && dcount >= dcutoff) return;
        if (aborted) return;
    }
}
static long long domain_of(int v, int mode, long long cutoff) {
    Aset = OUTM[v] & placed;
    Bset = placed & ~OUTM[v];
    dcount = 0; dcutoff = cutoff; dmode = mode; dom_calls++;
    dom_rec(0, 0, 0, 0);
    return dcount;
}

static void build_suf(void) {
    for (int i = 0; i < K; i++) {
        suf[i][m] = 0;
        for (int p = m - 1; p >= 0; p--) suf[i][p] = suf[i][p + 1] | (1ULL << ordv[i][p]);
    }
}
static void insert_v(int v, const uint8_t *p) {
    for (int i = 0; i < K; i++) {
        memmove(&ordv[i][p[i] + 1], &ordv[i][p[i]], (size_t)(m - p[i]) * sizeof(int));
        ordv[i][p[i]] = v;
    }
    m++; placed |= 1ULL << v;
}
static void remove_v(int v, const uint8_t *p) {
    m--;
    for (int i = 0; i < K; i++)
        memmove(&ordv[i][p[i]], &ordv[i][p[i] + 1], (size_t)(m - p[i]) * sizeof(int));
    placed &= ~(1ULL << v);
}

static void print_and_verify(void) {
    printf("WITNESS\n");
    for (int i = 0; i < K; i++) {
        printf("  voter %d:", i);
        for (int j = 0; j < n; j++) printf(" %d", ordv[i][j]);
        printf("\n");
    }
    int pos[MAXK][MAXN];
    for (int i = 0; i < K; i++) for (int j = 0; j < n; j++) pos[i][ordv[i][j]] = j;
    int bad = 0, mn = K + 1, mx = -1;
    for (int a = 0; a < n; a++) for (int b = 0; b < n; b++) {
        if (a == b || !((OUTM[a] >> b) & 1)) continue;
        int c = 0;
        for (int i = 0; i < K; i++) if (pos[i][a] < pos[i][b]) c++;
        if (c < mn) mn = c;
        if (c > mx) mx = c;
        if (exact_margin ? (c != tHI) : (c < tHI)) bad++;
    }
    printf("VERIFY bad_arcs=%d support_min=%d support_max=%d %s\n",
           bad, mn, mx, bad ? "*** INVALID ***" : "OK");
    fflush(stdout);
}

/* ---------------- main DFS -------------------------------------------- */
static int dfs(void) {
    nodes++;
    if ((nodes & 0x3FFFF) == 0) {
        if (node_limit && nodes >= node_limit) { aborted = 1; return 0; }
        if (time_limit > 0 && now() - t0 > time_limit) { aborted = 1; return 0; }
        if (verbose) { fprintf(stderr, "  [%7.1fs] nodes=%-12lld depth=%2d sols=%lld\n",
                               now() - t0, nodes, m, sols); fflush(stderr); }
    }
    if (m == n) { sols++; if (find_one) { print_and_verify(); return 1; } return 0; }
    build_suf();

    int vstar = -1;
    if (order_mrv) {
        /* Scan every unplaced vertex but count its domain only up to mrv_cap.
         * A capped count still detects the EMPTY domain exactly, which is the
         * whole value of fail-first; beyond the cap the MRV signal is weak, so
         * ties are broken by the cheap static-ish imbalance heuristic below.
         * Any choice of v* is sound, so none of this can affect completeness. */
        long long best = mrv_cap + 1;
        int besttie = -1;
        for (int v = 0; v < n; v++) {
            if ((placed >> v) & 1) continue;
            long long c = domain_of(v, 0, mrv_cap);
            if (c == 0) { mrv_fails++; return 0; }
            int tie = 0;
            if (tie_imbalance) {
                int o = __builtin_popcountll(OUTM[v] & placed);
                tie = 2 * o - m;                    /* out(v)&S minus in(v)&S  */
                if (tie < 0) tie = -tie;
            }
            if (c < best || (c == best && tie > besttie)) { best = c; besttie = tie; vstar = v; }
            if (aborted) return 0;
        }
    } else vstar = static_order[m];
    if (aborted) return 0;

    long base = tsp;
    domain_of(vstar, 1, LLONG_MAX);
    long cnt = tsp - base;
    for (long t = 0; t < cnt; t++) {
        uint8_t p[MAXK];
        memcpy(p, tstack + (base + t) * MAXK, K);
        insert_v(vstar, p);
        int got = dfs();
        remove_v(vstar, p);
        if (got || aborted) { tsp = base; return got; }
        build_suf();
    }
    tsp = base;
    return 0;
}

/* ---------------- base enumeration ------------------------------------ */
static int NBP, bpbits[720], bperm[720][8];
static int bpair_i[16], bpair_j[16], bNE;
static int btarget[16];
static int bchosen[MAXK], bcnt_e[16];
static long long bcount, bstore_cap;
static int (*bstore)[MAXK];
static int bmode;                          /* 0 = count, 1 = store          */

static void gen_base_perms(int b) {
    bNE = b * (b - 1) / 2;
    { int e = 0; for (int i = 0; i < b; i++) for (int j = i + 1; j < b; j++) { bpair_i[e]=i; bpair_j[e]=j; e++; } }
    int idx[8]; for (int i = 0; i < b; i++) idx[i] = i;
    NBP = 0;
    while (1) {
        int pos[8]; for (int i = 0; i < b; i++) pos[idx[i]] = i;
        int msk = 0;
        for (int e = 0; e < bNE; e++) if (pos[bpair_i[e]] < pos[bpair_j[e]]) msk |= 1 << e;
        memcpy(bperm[NBP], idx, sizeof(int) * b);
        bpbits[NBP++] = msk;
        int i = b - 2; while (i >= 0 && idx[i] > idx[i+1]) i--;
        if (i < 0) break;
        int j = b - 1; while (idx[j] < idx[i]) j--;
        int t = idx[i]; idx[i] = idx[j]; idx[j] = t;
        for (int a = i+1, c = b-1; a < c; a++, c--) { t = idx[a]; idx[a] = idx[c]; idx[c] = t; }
    }
}
static void brec(int t, int lo) {
    if (t == K) {
        for (int e = 0; e < bNE; e++) {
            if (exact_margin) { if (bcnt_e[e] != btarget[e]) return; }
            else { if (btarget[e] == tHI ? (bcnt_e[e] < tHI) : (bcnt_e[e] > tLO)) return; }
        }
        if (bmode == 1) {
            if (bcount < bstore_cap) memcpy(bstore[bcount], bchosen, sizeof(int) * K);
            else { fprintf(stderr, "FATAL base store overflow\n"); exit(2); }
        }
        bcount++;
        return;
    }
    int rem = K - t - 1;
    for (int p = (symbreak ? lo : 0); p < NBP; p++) {
        int msk = bpbits[p], ok = 1;
        for (int e = 0; e < bNE; e++) {
            int c = bcnt_e[e] + ((msk >> e) & 1);
            if (exact_margin) {
                if (c > btarget[e] || c + rem < btarget[e]) { ok = 0; break; }
            } else {
                if (btarget[e] == tHI) { if (c + rem < tHI) { ok = 0; break; } }
                else                   { if (c > tLO)       { ok = 0; break; } }
            }
        }
        if (!ok) continue;
        for (int e = 0; e < bNE; e++) bcnt_e[e] += (msk >> e) & 1;
        bchosen[t] = p;
        brec(t + 1, p);
        for (int e = 0; e < bNE; e++) bcnt_e[e] -= (msk >> e) & 1;
    }
}
/* count base states for the abstract base tournament given by pair-mask bm  */
static long long base_states(int bm, int mode, int (*store)[MAXK], long long cap) {
    for (int e = 0; e < bNE; e++) btarget[e] = ((bm >> e) & 1) ? tHI : tLO;
    memset(bcnt_e, 0, sizeof bcnt_e);
    bcount = 0; bmode = mode; bstore = store; bstore_cap = cap;
    brec(0, 0);
    return bcount;
}
static int mask_of_subset(const int *S, int b) {
    int msk = 0, e = 0;
    for (int i = 0; i < b; i++) for (int j = i + 1; j < b; j++, e++)
        if ((OUTM[S[i]] >> S[j]) & 1) msk |= 1 << e;
    return msk;
}

/* ---------------- instances ------------------------------------------- */
static void make_paley(int q) {
    n = q; int qr[MAXN]; memset(qr, 0, sizeof qr);
    for (int x = 1; x < q; x++) qr[(x * x) % q] = 1;
    for (int a = 0; a < q; a++) OUTM[a] = 0;
    for (int a = 0; a < q; a++) for (int b = 0; b < q; b++)
        if (a != b && qr[((b - a) % q + q) % q]) OUTM[a] |= 1ULL << b;
}
static void make_bits(const char *path, int nn) {
    FILE *f = fopen(path, "r"); if (!f) { perror(path); exit(1); }
    static char buf[1 << 16];
    size_t len = fread(buf, 1, sizeof buf - 1, f); buf[len] = 0; fclose(f);
    n = nn; for (int a = 0; a < n; a++) OUTM[a] = 0;
    size_t k = 0;
    for (int a = 0; a < n; a++) for (int b = a + 1; b < n; b++) {
        while (k < len && buf[k] != '0' && buf[k] != '1') k++;
        if (k >= len) { fprintf(stderr, "FATAL bits file too short\n"); exit(1); }
        if (buf[k++] == '1') OUTM[a] |= 1ULL << b; else OUTM[b] |= 1ULL << a;
    }
}
static void make_static_order(void) {
    int deg[MAXN], tri[MAXN];
    for (int v = 0; v < n; v++) { deg[v] = __builtin_popcountll(OUTM[v]); tri[v] = 0; }
    for (int a = 0; a < n; a++) for (int b = 0; b < n; b++) for (int c = 0; c < n; c++) {
        if (a == b || b == c || a == c) continue;
        if (((OUTM[a] >> b) & 1) && ((OUTM[b] >> c) & 1) && ((OUTM[c] >> a) & 1)) tri[a]++;
    }
    int used[MAXN]; memset(used, 0, sizeof used);
    int cnt = 0;
    for (int j = 0; j < base_sz; j++) { static_order[cnt++] = base_v[j]; used[base_v[j]] = 1; }
    while (cnt < n) {
        int bv = -1, bk1 = -1, bk2 = 0;
        for (int v = 0; v < n; v++) {
            if (used[v]) continue;
            int k1 = abs(2 * deg[v] - (n - 1));
            if (bv < 0 || k1 > bk1 || (k1 == bk1 && tri[v] < bk2)) { bv = v; bk1 = k1; bk2 = tri[v]; }
        }
        used[bv] = 1; static_order[cnt++] = bv;
    }
}


/* ---------------- one instance, then batch driver --------------------- */
static int quiet_witness = 0;
static int solve_one(int *out_nodes_lo) {
    (void)out_nodes_lo;
    gen_base_perms(base_sz);
    long long bestc = -1;
    { long long *cache = malloc(sizeof(long long) << bNE);
      for (int i = 0; i < (1 << bNE); i++) cache[i] = -1;
      int S[8], best[8];
      for (int i = 0; i < base_sz; i++) S[i] = i;
      while (1) {
          int bm = mask_of_subset(S, base_sz);
          if (cache[bm] < 0) cache[bm] = base_states(bm, 0, NULL, 0);
          if (bestc < 0 || cache[bm] < bestc) { bestc = cache[bm]; memcpy(best, S, sizeof(int) * base_sz); }
          int i = base_sz - 1;
          while (i >= 0 && S[i] == n - base_sz + i) i--;
          if (i < 0) break;
          S[i]++; for (int j = i + 1; j < base_sz; j++) S[j] = S[j-1] + 1;
      }
      free(cache);
      memcpy(base_v, best, sizeof(int) * base_sz);
    }
    make_static_order();
    int bm = mask_of_subset(base_v, base_sz);
    static int (*bst)[MAXK] = NULL;
    if (!bst) bst = malloc(sizeof(int) * MAXK * 4000000);
    long long nb = base_states(bm, 1, bst, 4000000);
    nodes = 0; sols = 0; dom_calls = 0; dom_nodes = 0; mrv_fails = 0; aborted = 0; tsp = 0;
    t0 = now();
    int got = 0;
    for (long long b = 0; b < nb && !got && !aborted; b++) {
        m = base_sz; placed = 0; tsp = 0;
        for (int i = 0; i < K; i++) {
            int pi = bst[b][i];
            for (int j = 0; j < base_sz; j++) ordv[i][j] = base_v[bperm[pi][j]];
        }
        for (int j = 0; j < base_sz; j++) placed |= 1ULL << base_v[j];
        if (base_sz == n) { sols++; if (find_one) { if (!quiet_witness) print_and_verify(); got = 1; } continue; }
        got = dfs();
    }
    return got;
}
static void run_batch(void) {
    FILE *f = fopen(batch_file, "r");
    if (!f) { perror(batch_file); exit(1); }
    char line[4096];
    int idx = 0, nsat = 0, nunsat = 0, nab = 0;
    quiet_witness = 1;
    double tstart = now();
    while (fgets(line, sizeof line, f)) {
        int len = 0; while (line[len] == '0' || line[len] == '1') len++;
        if (len == 0) continue;
        if (len != n * (n - 1) / 2) {
            fprintf(stderr, "line %d: %d bits, expected %d\n", idx, len, n * (n - 1) / 2); exit(1);
        }
        for (int a = 0; a < n; a++) OUTM[a] = 0;
        int k = 0;
        for (int a = 0; a < n; a++) for (int b = a + 1; b < n; b++, k++)
            if (line[k] == '1') OUTM[a] |= 1ULL << b; else OUTM[b] |= 1ULL << a;
        int got = solve_one(NULL);
        const char *v = aborted ? "ABORTED" : (got ? "SAT" : "UNSAT");
        if (aborted) nab++; else if (got) nsat++; else nunsat++;
        printf("BATCH %d %s nodes=%lld time=%.3f\n", idx, v, nodes, now() - t0);
        idx++;
    }
    fclose(f);
    printf("BATCH_SUMMARY n=%d K=%d margin=%s order=%s instances=%d SAT=%d UNSAT=%d ABORTED=%d wall=%.1fs\n",
           n, K, exact_margin ? "exact1" : "majority", order_mrv ? "mrv" : "static",
           idx, nsat, nunsat, nab, now() - tstart);
}

int main(int argc, char **argv) {
    int q = 0, nn = 0, have_base = 0; const char *bits = NULL;
    K = 5;
    for (int i = 1; i < argc; i++) {
        if      (!strcmp(argv[i], "--paley"))  q = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--bits"))   bits = argv[++i];
        else if (!strcmp(argv[i], "--n"))      nn = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--k"))      K = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--margin")) exact_margin = !strcmp(argv[++i], "exact");
        else if (!strcmp(argv[i], "--order"))  order_mrv = !strcmp(argv[++i], "mrv");
        else if (!strcmp(argv[i], "--count"))  find_one = 0;
        else if (!strcmp(argv[i], "--no-symbreak")) symbreak = 0;
        else if (!strcmp(argv[i], "--base-size")) base_sz = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--base")) {
            have_base = 1; auto_base = 0;
            for (int j = 0; j < base_sz; j++) base_v[j] = atoi(argv[++i]);
        }
        else if (!strcmp(argv[i], "--nodes")) node_limit = atoll(argv[++i]);
        else if (!strcmp(argv[i], "--time"))  time_limit = atof(argv[++i]);
        else if (!strcmp(argv[i], "--mrv-cap")) mrv_cap = atoll(argv[++i]);
        else if (!strcmp(argv[i], "--no-tie-imbalance")) tie_imbalance = 0;
        else if (!strcmp(argv[i], "--batch")) batch_file = argv[++i];
        else if (!strcmp(argv[i], "--bs-from")) bs_from = atoll(argv[++i]);
        else if (!strcmp(argv[i], "--bs-to")) bs_to = atoll(argv[++i]);
        else if (!strcmp(argv[i], "-v"))      verbose = 1;
        else { fprintf(stderr, "unknown arg %s\n", argv[i]); return 1; }
    }
    if (q) make_paley(q);
    else if (bits) { if (!nn) { fprintf(stderr, "--bits needs --n\n"); return 1; } make_bits(bits, nn); }
    else if (batch_file) { if (!nn) { fprintf(stderr, "--batch needs --n\n"); return 1; } n = nn; }
    else { fprintf(stderr, "need --paley q, --bits F --n N, or --batch F --n N\n"); return 1; }
    if (K > MAXK || K % 2 == 0) { fprintf(stderr, "K must be odd <= %d\n", MAXK); return 1; }
    tHI = (K + 1) / 2; tLO = (K - 1) / 2;
    if (base_sz > n) base_sz = n;
    if (base_sz < 1) base_sz = 1;
    gen_base_perms(base_sz);

    /* pick the base: most restrictive base_sz-subset, cached per labelled mask */
    long long bestc = -1;
    if (auto_base) {
        long long *cache = malloc(sizeof(long long) << bNE);
        for (int i = 0; i < (1 << bNE); i++) cache[i] = -1;
        int S[8], best[8];
        /* iterate all base_sz-subsets in lexicographic order */
        for (int i = 0; i < base_sz; i++) S[i] = i;
        while (1) {
            int bm = mask_of_subset(S, base_sz);
            if (cache[bm] < 0) cache[bm] = base_states(bm, 0, NULL, 0);
            if (bestc < 0 || cache[bm] < bestc) { bestc = cache[bm]; memcpy(best, S, sizeof(int) * base_sz); }
            int i = base_sz - 1;
            while (i >= 0 && S[i] == n - base_sz + i) i--;
            if (i < 0) break;
            S[i]++; for (int j = i + 1; j < base_sz; j++) S[j] = S[j-1] + 1;
        }
        free(cache);
        memcpy(base_v, best, sizeof(int) * base_sz);
    } else (void)have_base;
    make_static_order();

    tstack = malloc((size_t)TCAP * MAXK);
    int (*bstates)[MAXK] = malloc(sizeof(int) * MAXK * 4000000);
    if (!tstack || !bstates) { fprintf(stderr, "FATAL alloc\n"); return 1; }

    int bm = mask_of_subset(base_v, base_sz);
    long long nb = base_states(bm, 1, bstates, 4000000);

    printf("n=%d K=%d margin=%s order=%s mrv_cap=%lld tie_imb=%d mode=%s symbreak=%d base_sz=%d base=",
           n, K, exact_margin ? "exact1" : "majority", order_mrv ? "mrv" : "static",
           mrv_cap, tie_imbalance, find_one ? "one" : "count", symbreak, base_sz);
    for (int j = 0; j < base_sz; j++) printf("%s%d", j ? "," : "", base_v[j]);
    printf(" base_mask=%d base_states=%lld", bm, nb);
    if (auto_base) printf(" (most restrictive of C(%d,%d))", n, base_sz);
    printf("\n  static_tail=");
    for (int j = base_sz; j < n; j++) printf("%s%d", j > base_sz ? "," : "", static_order[j]);
    printf("\n"); fflush(stdout);

    if (batch_file) { run_batch(); return 0; }
    t0 = now();
    int got = 0;
    long long blo = bs_from, bhi = (bs_to < 0 || bs_to > nb) ? nb : bs_to;
    if (blo > nb) blo = nb;
    printf("  base_state_slice=[%lld,%lld)\n", blo, bhi); fflush(stdout);
    for (long long b = blo; b < bhi && !got && !aborted; b++) {
        m = base_sz; placed = 0; tsp = 0;
        for (int i = 0; i < K; i++) {
            int pi = bstates[b][i];
            for (int j = 0; j < base_sz; j++) ordv[i][j] = base_v[bperm[pi][j]];
        }
        for (int j = 0; j < base_sz; j++) placed |= 1ULL << base_v[j];
        if (base_sz == n) { sols++; if (find_one) { print_and_verify(); got = 1; } continue; }
        got = dfs();
        if (!got && !aborted)
            printf("PROGRESS base_cleared=%lld/%lld nodes=%lld mrv_fails=%lld dom_nodes=%lld time=%.1fs\n",
                   b + 1, nb, nodes, mrv_fails, dom_nodes, now() - t0), fflush(stdout);
    }
    double el = now() - t0;
    printf("RESULT %s nodes=%lld sols=%lld base_states=%lld dom_calls=%lld dom_nodes=%lld mrv_fails=%lld time=%.3fs\n",
           aborted ? "ABORTED" : (find_one ? (got ? "SAT" : "UNSAT") : "COUNTED"),
           nodes, sols, nb, dom_calls, dom_nodes, mrv_fails, el);
    return 0;
}
