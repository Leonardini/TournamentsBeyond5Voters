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
/* --max-margin M : the MARGIN HIERARCHY.  With k voters an arc's support s
 * gives margin |s - (k-s)|, so for k=5 the rungs are M=1 (every arc 3:2),
 * M=3 (3:2 or 4:1, i.e. NO unanimous arc) and M=5 (unrestricted).  The
 * conjecture in the last paper is that the hierarchy is STRICT: some
 * tournaments are 5-inducible at M=3 but not M=1 (settled by Paley(19)), and
 * some are 5-inducible at M=5 but not M=3 (OPEN -- it needs a tournament that
 * REQUIRES a unanimous arc).
 * A pair is admissible iff its support lies in [supLO, supHI] with
 * supHI = (k+M)/2, supLO = (k-M)/2; combined with the orientation constraint
 * this reads  Aset (arc): [tHI, supHI],  Bset (non-arc): [k-supHI, tLO].
 * M = 1 reproduces --margin exact and M = k reproduces --margin majority
 * exactly, which is how the flag gates itself.                              */
static int max_margin = -1, supHI = 0;
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
static long long per_base_nodes = 0;        /* node cap PER base state      */
static long long base_nodes0 = 0;
static int base_abort = 0;
static int use_bound = 1;        /* cheap per-voter agreement bound as a filter */
static int select_cheap = 0;     /* pick v* by the top-tHI agreement score only  */
static int select_hybrid = 0;    /* exact counts (fail-first) + cheap ORDERING   */
static long long bound_fails = 0, bound_skips = 0;
static long long dsz_hist[MAXN][8];   /* [depth][log2 bucket] of FULL |D(v)| */
static long long dsz_sum[MAXN], dsz_cnt[MAXN], dsz_max[MAXN];
static int measure_dsz = 0;
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
static uint64_t Aset, Bset, Rv;
static long long dcount, dcutoff;
static int dmode;
static uint8_t dpos[MAXK];
static uint8_t *tstack;
static long tsp;

/* ---- incremental domain maintenance -----------------------------------
 * dompool is a stack-disciplined arena.  At depth d we hold, for every
 * unplaced v, the FULL domain D(v|S) as a packed list of MAXK-byte tuples.
 * Child domains are refined from the parent's rather than re-enumerated.   */
static int use_inc = 0;
static uint8_t *dompool;
static size_t poolcap, poolsp;
static long pool_mb = 256;
/* ---- global dissent-budget bound (minFAS oracle) -----------------------
 * Under margin-1 every arc has exactly tLO dissenters; under majority at most
 * tLO.  Either way  sum_j dissents(sigma_j) <= tLO*|E|.  Each voter's dissents
 * are at least minFAS of whatever it still has to order, so with S placed and
 * F = V\S:      D_S + K*minFAS(T[F])  >  tLO*|E|   =>  the node is dead.
 * fastab[U] = minFAS(T[U]) for every U, by the subset DP
 *   f(U) = min_{v in U}[ f(U\v) + |N+(v) & (U\v)| ]  -- O(2^n n), 2 bytes/state. */
static uint16_t *fastab = NULL;
static int use_fas = 0;                 /* tier 1: O(1) test at every node   */
static long long fas_fails = 0, fas_tests = 0;
static long long fas_fire_depth[MAXN];
static int budget = 0;                  /* tLO * |E| */
static int DS = 0;                      /* dissents among arcs inside S      */
static int DS_stack[MAXN];
/* ---- tier 2: EXACT per-voter minimum over extensions of pi_j|_S ---------
 * m_j(P) = min back arcs over full orders extending voter j's current order.
 * DP state (j, U): j = how much of the S-sequence is consumed, U subset of F
 * already placed; cost adds |N+(x) & placed| when x is appended.  Exactly
 * (|S|+1)*2^|F| states, so it gets CHEAPER with depth -- the opposite of the
 * one-step lookahead.  sum_j m_j(P) > budget  =>  node is dead.            */
static uint16_t *g2 = NULL;
static uint64_t *umask = NULL;
static int fas2_depth = -1;
static int tie_fas = 0;   /* 1 = prefer max minFAS delta, -1 = prefer min */
/* ---- Aut symmetry break: "vertex 0 is the top-ranked vertex of SOME voter"
 * Sound ONLY when Aut(T) is transitive on vertices (Paley is): some sigma sends
 * one of the K top vertices to 0, and the condition is invariant under voter
 * permutations, so it survives the base lex-sort -- unlike pinning a PARTICULAR
 * voter's top, which the re-sorting destroys.  Monotone: once vertex 0 is
 * placed, voter i can still top it only if it is first among i's placed
 * vertices, and that can only be lost, never regained.                      */
static int top0 = 0;
static long long top0_fails = 0;
/* second-position pin: require SOME voter to have 0 first and top0_r second.
 * sigma: x -> a(x-t), a in QR, sends (t,s) -> (0, a(s-t)), and a(s-t) sweeps the
 * whole coset QR*(s-t) -- so one fixed representative per coset suffices, and
 * the two cosets (s-t a residue or not, i.e. top beats second or not) are
 * mutually exclusive and exhaustive.  Still voter-invariant, so it survives the
 * base lex-sort.  Run BOTH values of r; their union is complete.            */
static int top0_r = -1, top0_r2 = -1;
/* --toporb r1 r2 ... : generalised Aut break for tournaments that are NOT
 * vertex-transitive.  Let r1..rm be orbit representatives of Aut(T) on V.
 * WLOG SOME voter ranks one of them first: take any voter, its top u lies in
 * the orbit of some ri, so pick sigma in Aut(T) with sigma(u) = ri and apply
 * sigma to the whole profile.  Voter-invariant, so it composes with the base
 * voter lex-sort, exactly as --top0rr does.  Monotone in the same way: a voter
 * can still top some ri only while either its first PLACED vertex already is
 * one of them, or some ri is still unplaced (a later insertion can precede it),
 * so the test fires only once EVERY representative is placed.
 *
 * SOUNDNESS IS ON THE CALLER.  The engine cannot compute Aut(T), so it cannot
 * check that r1..rm meet every orbit; a representative set that MISSES an orbit
 * silently discards every profile whose top vertices all lie in it.  Ported
 * from kinduce23.c, where it was validated 15/15 against no-break verdicts on
 * the regular n=9 tournaments across |Aut| = 1, 3, 9, 81.                    */
static int toporb[MAXN], toporb_m = 0;
static uint64_t toporb_mask = 0;
/* --toppair u1 v1 u2 v2 : general two-representative Aut break.  Aut(Paley) acts
 * REGULARLY on arcs, so the q(q-1) ordered pairs split into exactly two orbits
 * (agrees / disagrees with T's arc) and a complete break picks one rep from
 * each: WLOG some voter's global (top, second) equals (u1,v1) or (u2,v2).
 * Monotone relaxation per voter i and rep (u,v):
 *   both placed : ordv[i][0]==u && ordv[i][1]==v
 *   u placed only: ordv[i][0]==u   (v can still be inserted right after u)
 *   v placed only: ordv[i][0]==v   (u can still be inserted in front of v)
 *   neither      : still possible
 * Each condition can only be lost, never regained, so pruning is sound.      */
static int tp_u[2] = {-1,-1}, tp_v[2] = {-1,-1}, tp_n = 0;

/* ---- defect-1 search: arc-criticality decided in ONE run --------------
 * Look for a profile whose majority (or margin-1) tournament is T with
 * EXACTLY ONE arc reversed, that arc confined to a set R given by --defect.
 * This is route (b) of the symmetry-break analysis; see defect_set.py for the
 * derivation.  In outline: Aut(T) acts on defect-1 solutions by
 * g.(P,e) = (gP, g(e)) -- the defect travels with the relabelling -- so
 * --top0 stays WLOG, and its residual G_0 = Stab_Aut(0), cyclic of order
 * (q-1)/2, acts FREELY on arcs.  Hence "e lies in R", one arc per G_0-orbit,
 * is WLOG as well.  The total break is |Aut(T)|, the same strength as
 * --toppair, but spent so that R can be chosen to MISS the base's C(5,2) = 10
 * internal arcs, which is possible exactly when (q-1)/2 > 10, i.e. q >= 23.
 * THAT is what lets the base states still be enumerated against the exact
 * restriction of T, and main() REFUSES an R meeting the base -- combining
 * --toppair (or any full-strength break) with "the defect avoids the base" is
 * precisely the unsound combination this file exists to avoid.
 *
 * Bookkeeping.  RM[v] holds the u with {v,u} in R.  Every pair is constrained
 * exactly once -- in dom_rec while the base is seeded, otherwise in refine
 * when the later of its two endpoints is placed -- so a tuple can carry the
 * number of defects it spends (0 or 1) in byte DFB, insert_v adds that to
 * defect_used and remove_v restores it, and every test demands
 * defect_used + tag <= 1.  Pruning is relaxed ONLY on R-pairs and ONLY while
 * the budget is unspent, so beneath the arc that spends it the engine is back
 * to full strength.
 *
 * The lookahead is a RELAXATION, not exact: two distinct unplaced vertices can
 * each be kept alive by the same single unit of budget.  That over-estimates
 * domains, hence is sound, and is caught as soon as either is placed.      */
#define DFB (MAXK - 1)
static uint64_t RM[MAXN];
static const char *defect_file = NULL;
static int defect_n = 0, defect_used = 0;
/* --defect-support LO HI : the defect arc's support IN T's OWN DIRECTION must
 * lie in [LO,HI].  Default [0,tLO] is "reversed, any margin" = the old
 * behaviour exactly.  Leonid's split (majority, K=5, tHI=3, tLO=2):
 *      [2,2]  the flipped arc goes 3:2   -- a UNIVERSAL lower bound of 2, with
 *             at most one arc below 3.  Contiguous with [tHI,K], so the domain
 *             gains ONE support value instead of three and the monotone break
 *             survives.
 *      [0,1]  the flipped arc goes 4:1 or 5:0.
 * The union of the two is complete.  A window with HI < tLO makes the allowed
 * set [LO,HI] u [tHI,K] NON-CONVEX, so a lower-bound failure at an R-pair can
 * still recover at a larger p and `break` would be UNSOUND there -- such pairs
 * take `continue` instead (see dom_rec).                                    */
static int def_lo = -1, def_hi = -1;
static int defect_stack[MAXN];
static long long fas2_fails = 0, fas2_tests = 0, fas2_fire_depth[MAXN];
static int voter_min_fas(int i, uint64_t F, const int *fv, int f);
static inline int dissents_at(int i, int v, int p);
static size_t domoff[MAXN + 1][MAXN];
static int domcnt[MAXN + 1][MAXN];
static long long refine_tuples = 0;

static void dom_rec(int i, uint64_t b0, uint64_t b1, uint64_t b2) {
    dom_nodes++;
    if ((dom_nodes & 0xFFFFF) == 0) {
        if (node_limit && nodes >= node_limit) aborted = 1;
        if (time_limit > 0 && now() - t0 > time_limit) aborted = 1;
        if (aborted) return;
    }
    if (i == K) {
        uint64_t bad;
        if (exact_margin)
            bad = (Aset & ~eqm(b0, b1, b2, tHI)) | (Bset & ~eqm(b0, b1, b2, tLO));
        else {
            uint64_t g = geq(b0, b1, b2, tHI);
            bad = (Aset & ~g) | (Bset & g);
            if (supHI < K)      /* forbid margins above M on either side */
                bad |= (Aset & geq(b0, b1, b2, supHI + 1))
                     | (Bset & ~geq(b0, b1, b2, K - supHI));
        }
        int tag = 0;
        if (bad) {
            /* A violated pair is survivable only if it lies in R AND sits at
             * exactly the REVERSED requirement.  Under majority "not >= tHI"
             * already means "<= tLO", so the second test is vacuous there and
             * is needed only for margin-1.                                 */
            uint64_t allow = Rv;
            if (exact_margin)
                allow &= (Aset & eqm(b0, b1, b2, tLO)) | (Bset & eqm(b0, b1, b2, tHI));
            else
                allow &= (Aset & geq(b0,b1,b2,def_lo) & ~geq(b0,b1,b2,def_hi+1))
                       | (Bset & geq(b0,b1,b2,K-def_hi) & ~geq(b0,b1,b2,K-def_lo+1));
            if (bad & ~allow) return;
            tag = __builtin_popcountll(bad);
            if (tag + defect_used > 1) return;
        }
        dcount++;
        if (dmode == 1) {
            if (tsp >= TCAP) { fprintf(stderr,
                "FATAL tuple stack overflow at depth %d (domain too large; "
                "use --order mrv, or raise TCAP)\n", m); exit(2); }
            dpos[DFB] = (uint8_t)tag;
            memcpy(tstack + tsp * MAXK, dpos, MAXK); tsp++;
        }
        return;
    }
    if (exact_margin && i == K - 1 && !defect_n) {
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
            dpos[DFB] = 0;
            memcpy(tstack + tsp * MAXK, dpos, MAXK); tsp++;
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
        uint64_t upbad = (Bset & geq(c0, c1, c2, tLO + 1));
        if (exact_margin) upbad |= (Aset & geq(c0, c1, c2, tHI + 1));
        if (!exact_margin && supHI < K) {
            upbad |= (Aset & geq(c0, c1, c2, supHI + 1));      /* support only grows */
            if (K - supHI - r > 0)
                lowbad |= (Bset & ~geq(c0, c1, c2, K - supHI - r));
        }
        uint64_t softdead = 0;
        if (defect_n && !defect_used) {
            /* An R-pair failing the ORDINARY bound is not dead: it may be the
             * defect.  It IS dead once the defect window has become
             * unreachable too -- [c, c+r] must still meet [def_lo,def_hi] in
             * T's direction, which for a Bset pair reads [K-def_hi,K-def_lo]. */
            uint64_t soft = (lowbad | upbad) & Rv;
            lowbad &= ~Rv; upbad &= ~Rv;
            if (soft) {
                uint64_t liveA = geq(c0,c1,c2,def_lo - r) & ~geq(c0,c1,c2,def_hi + 1);
                uint64_t liveB = geq(c0,c1,c2,K - def_hi - r) & ~geq(c0,c1,c2,K - def_lo + 1);
                softdead = (soft & Aset & ~liveA) | (soft & Bset & ~liveB);
            }
        }
        if (lowbad) break;                       /* counts only shrink in p  */
        /* softdead takes `continue`, never `break`: with a non-convex allowed
         * set a larger p can recover, so breaking would lose solutions.    */
        if (upbad | softdead) continue;
        dpos[i] = (uint8_t)p;
        dom_rec(i + 1, c0, c1, c2);
        if (dmode == 0 && dcount >= dcutoff) return;
        if (aborted) return;
    }
}
static long long domain_of(int v, int mode, long long cutoff) {
    Aset = OUTM[v] & placed;
    Bset = placed & ~OUTM[v];
    Rv   = RM[v] & placed;
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
    if (use_fas) {
        DS_stack[m] = DS;
        for (int i = 0; i < K; i++) DS += dissents_at(i, v, p[i]);
    }
    if (defect_n) { defect_stack[m] = defect_used; defect_used += p[DFB]; }
    for (int i = 0; i < K; i++) {
        memmove(&ordv[i][p[i] + 1], &ordv[i][p[i]], (size_t)(m - p[i]) * sizeof(int));
        ordv[i][p[i]] = v;
    }
    m++; placed |= 1ULL << v;
}
static void remove_v(int v, const uint8_t *p) {
    m--;
    if (use_fas) DS = DS_stack[m];
    if (defect_n) defect_used = defect_stack[m];
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
    int bad = 0, mn = K + 1, mx = -1, clean_rev = 0, off_R = 0;
    for (int a = 0; a < n; a++) for (int b = 0; b < n; b++) {
        if (a == b || !((OUTM[a] >> b) & 1)) continue;
        int c = 0;
        for (int i = 0; i < K; i++) if (pos[i][a] < pos[i][b]) c++;
        if (c < mn) mn = c;
        if (c > mx) mx = c;
        if (exact_margin ? (c != tHI) : (c < tHI)) {
            bad++;
            /* a clean reversal is the arc sitting at exactly the reversed
             * requirement -- tLO for margin-1, <= tLO for majority          */
            int rev = exact_margin ? (c == tLO) : (c <= tLO);
            int inR = defect_n && (int)((RM[a] >> b) & 1);
            if (rev) clean_rev++;
            if (!inR) off_R++;
            printf("  DEFECT arc %d->%d support=%d%s%s\n", a, b, c,
                   rev ? " (clean reversal)" : " *** NOT a clean reversal ***",
                   inR ? " in R" : " *** NOT IN R ***");
        }
    }
    /* Without --defect the only acceptable witness has bad == 0, exactly as
     * before.  With --defect, exactly the one budgeted arc may be reversed,
     * it must be a clean reversal, and it must lie in R.                   */
    int okw = defect_n ? (bad == 1 && clean_rev == 1 && off_R == 0) : (bad == 0);
    printf("VERIFY bad_arcs=%d reversed=%d off_R=%d support_min=%d support_max=%d %s\n",
           bad, clean_rev, off_R, mn, mx, okw ? "OK" : "*** INVALID ***");
    fflush(stdout);
}


/* ---- cheap per-voter agreement bound -----------------------------------
 * A_i(p) = |Out(v) & U_i(p)| + |In(v) & (S \ U_i(p))| is voter i's agreement
 * with the arcs between v and S when v is inserted at slot p.  Counting the
 * per-arc agreement two ways gives  sum_i A_i(p_i) = tHI*|S|  exactly (>= for
 * majority), so  sum_i max_p A_i(p) < tHI*|S|  PROVES D(v) is empty, and for
 * exact margin also  sum_i min_p A_i(p) > tHI*|S|  does.  O(k|S|) per vertex.
 * Returns 1 if v is provably impossible; *score = sum of the top tHI maxima
 * (a heuristic ranking only, deliberately not a bound).                    */
static inline int cheap_bound(int v, int *score) {
    uint64_t A = OUTM[v] & placed;
    int Ms[MAXK];
    int total_max = 0, total_min = 0;
    for (int i = 0; i < K; i++) {
        int a = __builtin_popcountll(A);       /* slot 0: all of S is suffix */
        int best = a, worst = a;
        for (int p = 0; p < m; p++) {
            int x = ordv[i][p];
            if ((A >> x) & 1) a--; else a++;
            if (a > best)  best = a;
            if (a < worst) worst = a;
        }
        Ms[i] = best; total_max += best; total_min += worst;
    }
    int need = tHI * m;
    if (total_max < need) return 1;
    if (exact_margin && total_min > need) return 1;
    /* top tHI of Ms, descending (K is tiny; insertion sort) */
    for (int i = 1; i < K; i++) { int x = Ms[i], j = i - 1;
        while (j >= 0 && Ms[j] < x) { Ms[j+1] = Ms[j]; j--; } Ms[j+1] = x; }
    int s = 0; for (int i = 0; i < tHI && i < K; i++) s += Ms[i];
    *score = s;
    return 0;
}


/* Refine D(v|S) into D(v|S+u), given that u was inserted at slots q.
 *
 * Deleting u from the child's orders maps D(v|S+u) into D(v|S) (removing u
 * leaves every c_v(w), w in S, unchanged), so the child's domain is a
 * REFINEMENT of the parent's.  Going the other way, for each parent tuple p
 * and each voter i:
 *     p_i <  q_i  ->  p'_i = p_i      (v strictly before u, forced)
 *     p_i >  q_i  ->  p'_i = p_i + 1  (v strictly after  u, forced)
 *     p_i == q_i  ->  BOTH are legal  (v may sit immediately either side)
 * and then the one new arc (v,u) filters by c_v(u) = #{i : v before u}.
 * With F forced-before and E free voters, c_v(u) = F + |chosen subset|.     */
static int refine(int d, int v, int u, const uint8_t *q) {
    const uint8_t *srcbase = dompool + domoff[d][v];
    int nsrc = domcnt[d][v];
    int vu = (int)((OUTM[v] >> u) & 1);          /* 1 iff v->u in T */
    int inR = defect_n && (int)((RM[v] >> u) & 1);
    size_t dst = poolsp;
    int ndst = 0;
    for (int t = 0; t < nsrc; t++) {
        const uint8_t *p = srcbase + (size_t)t * MAXK;
        int F = 0, nf = 0, freei[MAXK];
        for (int i = 0; i < K; i++) {
            if (p[i] < q[i]) F++;
            else if (p[i] == q[i]) freei[nf++] = i;
        }
        for (int msk = 0; msk < (1 << nf); msk++) {
            int c = F + __builtin_popcount((unsigned)msk);
            int ok = exact_margin ? (c == (vu ? tHI : tLO))
                                  : (vu ? (c >= tHI && c <= supHI)
                                        : (c <= tLO && c >= K - supHI));
            int tag = p[DFB];
            if (!ok) {
                if (!inR) continue;
                int rev = exact_margin ? (c == (vu ? tLO : tHI))
                                       : (vu ? (c >= def_lo && c <= def_hi)
                                             : (c >= K - def_hi && c <= K - def_lo));
                if (!rev) continue;
                tag++;
            }
            if (tag + defect_used > 1) continue;
            if (dst + (size_t)(ndst + 1) * MAXK > poolcap) {
                fprintf(stderr, "FATAL domain pool exhausted at depth %d\n", d); exit(2);
            }
            uint8_t *o = dompool + dst + (size_t)ndst * MAXK;
            int fi = 0;
            for (int i = 0; i < K; i++) {
                if (p[i] < q[i])       o[i] = p[i];
                else if (p[i] > q[i])  o[i] = (uint8_t)(p[i] + 1);
                else {                                   /* free voter */
                    o[i] = ((msk >> fi) & 1) ? p[i] : (uint8_t)(p[i] + 1);
                    fi++;
                }
            }
            o[DFB] = (uint8_t)tag;
            ndst++;
        }
    }
    domoff[d + 1][v] = dst;
    domcnt[d + 1][v] = ndst;
    poolsp = dst + (size_t)ndst * MAXK;
    refine_tuples += nsrc;
    return ndst;
}

/* Fresh full enumeration for every unplaced vertex -- used once per base
 * state to seed the incremental chain. */
static int init_domains(int d) {
    poolsp = 0;
    build_suf();
    for (int v = 0; v < n; v++) {
        if ((placed >> v) & 1) continue;
        long base = tsp;
        domain_of(v, 1, LLONG_MAX);
        long cnt = tsp - base;
        if (poolsp + (size_t)cnt * MAXK > poolcap) {
            fprintf(stderr, "FATAL domain pool exhausted seeding depth %d\n", d); exit(2);
        }
        memcpy(dompool + poolsp, tstack + (size_t)base * MAXK, (size_t)cnt * MAXK);
        domoff[d][v] = poolsp; domcnt[d][v] = (int)cnt;
        poolsp += (size_t)cnt * MAXK;
        tsp = base;
        if (cnt == 0) return 0;
    }
    return 1;
}

static int dfs_inc(int d) {
    nodes++;
    if (per_base_nodes && (nodes & 0xFFF) == 0 && nodes - base_nodes0 >= per_base_nodes) {
        base_abort = 1; return 0;
    }
    if ((nodes & 0x3FFFF) == 0) {
        if (node_limit && nodes >= node_limit) { aborted = 1; return 0; }
        if (time_limit > 0 && now() - t0 > time_limit) { aborted = 1; return 0; }
        if (verbose) { fprintf(stderr, "  [%7.1fs] nodes=%-12lld depth=%2d sols=%lld\n",
                               now() - t0, nodes, d, sols); fflush(stderr); }
    }
    if (d == n) { sols++; if (find_one) { print_and_verify(); return 1; } return 0; }

    if (toporb_m && (placed & toporb_mask) == toporb_mask) {
        int viable = 0;
        for (int i = 0; i < K; i++)
            if ((toporb_mask >> ordv[i][0]) & 1) { viable = 1; break; }
        if (!viable) { top0_fails++; return 0; }
    }

    if (tp_n) {
        int viable = 0;
        for (int i = 0; i < K && !viable; i++)
            for (int r = 0; r < tp_n; r++) {
                int u = tp_u[r], v = tp_v[r];
                int pu = (placed >> u) & 1, pv = (placed >> v) & 1;
                int ok;
                if (pu && pv)      ok = (ordv[i][0] == u && ordv[i][1] == v);
                else if (pu)       ok = (ordv[i][0] == u);
                else if (pv)       ok = (ordv[i][0] == v);
                else               ok = 1;
                if (ok) { viable = 1; break; }
            }
        if (!viable) { top0_fails++; return 0; }
    }

    if (top0 && ((placed >> 0) & 1)) {
        int rplaced = (top0_r >= 0) && ((placed >> top0_r) & 1);
        int viable = 0;
        for (int i = 0; i < K; i++) {
            if (ordv[i][0] != 0) continue;
            if (top0_r >= 0) {
                int ok = 0;
                if (!rplaced || ordv[i][1] == top0_r) ok = 1;
                if (!ok && top0_r2 >= 0 &&
                    (!((placed >> top0_r2) & 1) || ordv[i][1] == top0_r2)) ok = 1;
                if (!ok) continue;
            }
            viable = 1; break;
        }
        if (!viable) { top0_fails++; return 0; }
    }

    if (use_fas) {
        uint64_t F = (n == 64 ? ~0ULL : ((1ULL << n) - 1)) & ~placed;
        fas_tests++;
        if (DS + K * (int)fastab[F] > budget) {
            fas_fails++; fas_fire_depth[d]++; return 0;
        }
    }

    if (fas2_depth >= 0 && d >= fas2_depth && d < n) {
        uint64_t F = (n == 64 ? ~0ULL : ((1ULL << n) - 1)) & ~placed;
        int fv[MAXN], f = 0;
        uint64_t r = F;
        while (r) { fv[f++] = __builtin_ctzll(r); r &= r - 1; }
        int tot = 0;
        for (int i = 0; i < K; i++) tot += voter_min_fas(i, F, fv, f);
        fas2_tests++;
        if (tot > budget) { fas2_fails++; fas2_fire_depth[d]++; return 0; }
    }

    /* exact full sizes are already known -- argmin is free, no cap needed */
    int vstar = -1, besttie = -1;
    long long best = LLONG_MAX;
    for (int v = 0; v < n; v++) {
        if ((placed >> v) & 1) continue;
        long long c = domcnt[d][v];
        if (c == 0) { mrv_fails++; return 0; }
        int tie = 0;
        if (tie_imbalance) {
            int o = __builtin_popcountll(OUTM[v] & placed);
            tie = 2 * o - d; if (tie < 0) tie = -tie;
        }
        if (c < best || (c == best && tie > besttie)) { best = c; besttie = tie; vstar = v; }
    }

    size_t mark = poolsp;
    int nq = domcnt[d][vstar];
    for (int t = 0; t < nq; t++) {
        uint8_t q[MAXK];
        memcpy(q, dompool + domoff[d][vstar] + (size_t)t * MAXK, MAXK);
        poolsp = mark;
        insert_v(vstar, q);
        int ok = 1;
        for (int v = 0; v < n && ok; v++) {
            if ((placed >> v) & 1) continue;
            if (refine(d, v, vstar, q) == 0) { mrv_fails++; ok = 0; }
        }
        int got = ok ? dfs_inc(d + 1) : 0;
        remove_v(vstar, q);
        if (got || aborted || base_abort) { poolsp = mark; return got; }
    }
    poolsp = mark;
    return 0;
}

/* ---------------- main DFS -------------------------------------------- */
static int dfs(void) {
    nodes++;
    if (per_base_nodes && (nodes & 0xFFF) == 0 && nodes - base_nodes0 >= per_base_nodes) {
        base_abort = 1; return 0;               /* skip THIS base state only */
    }
    if ((nodes & 0x3FFFF) == 0) {
        if (node_limit && nodes >= node_limit) { aborted = 1; return 0; }
        if (time_limit > 0 && now() - t0 > time_limit) { aborted = 1; return 0; }
        if (verbose) { fprintf(stderr, "  [%7.1fs] nodes=%-12lld depth=%2d sols=%lld\n",
                               now() - t0, nodes, m, sols); fflush(stderr); }
    }
    if (m == n) { sols++; if (find_one) { print_and_verify(); return 1; } return 0; }
    build_suf();

    int vstar = -1;
    if (order_mrv && select_cheap) {
        /* rank by the cheap agreement score; exact-enumerate only the winner */
        int bestscore = INT_MAX;
        for (int v = 0; v < n; v++) {
            if ((placed >> v) & 1) continue;
            int sc;
            if (cheap_bound(v, &sc)) { bound_fails++; return 0; }
            if (sc < bestscore) { bestscore = sc; vstar = v; }
        }
    } else if (order_mrv) {
        /* Scan every unplaced vertex but count its domain only up to mrv_cap.
         * A capped count still detects the EMPTY domain exactly, which is the
         * whole value of fail-first; beyond the cap the MRV signal is weak, so
         * ties are broken by the cheap static-ish imbalance heuristic below.
         * Any choice of v* is sound, so none of this can affect completeness. */
        long long best = mrv_cap + 1;
        int besttie = -1, bestcheap = INT_MAX;
        for (int v = 0; v < n; v++) {
            if ((placed >> v) & 1) continue;
            int sc = 0;
            if (use_bound || select_hybrid) {
                if (cheap_bound(v, &sc)) { bound_fails++; return 0; }
            }
            long long c = domain_of(v, 0, measure_dsz ? LLONG_MAX : mrv_cap);
            if (measure_dsz) {
                int b = 0; long long x = c; while (x > 1 && b < 7) { x >>= 1; b++; }
                dsz_hist[m][b]++; dsz_sum[m] += c; dsz_cnt[m]++;
                if (c > dsz_max[m]) dsz_max[m] = c;
            }
            if (c == 0) { mrv_fails++; return 0; }
            if (select_hybrid) {                 /* fail-first kept, cheap order */
                if (sc < bestcheap) { bestcheap = sc; vstar = v; }
                continue;
            }
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
        if (got || aborted || base_abort) { tsp = base; return got; }
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
    /* Paley(q) is only defined for q a PRIME POWER = 3 mod 4, and this Z/q
     * construction is only valid for q PRIME.  For a prime power like q=27=3^3
     * the squares mod 27 do not split the nonzero residues, so 81 pairs get NO
     * arc in either direction and the result is not a tournament.  Fail loudly:
     * silently searching a non-tournament produces confident nonsense.
     * For prime-power q, build the tournament over GF(q) and pass it via
     * --bits (see p27_paley.bits, made by make_paley27.py).                  */
    for (int a = 0; a < n; a++) for (int b = a + 1; b < n; b++) {
        int ab = (OUTM[a] >> b) & 1, ba = (OUTM[b] >> a) & 1;
        if (ab + ba != 1) {
            fprintf(stderr,
                "FATAL --paley %d: the Z/q construction gives %s for the pair "
                "(%d,%d), so this is NOT a tournament.  q must be PRIME and "
                "= 3 mod 4; for a prime power use --bits with a GF(q) build.\n",
                q, ab ? "both directions" : "no arc", a, b);
            exit(1);
        }
    }

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
static void build_fastab(void) {
    if (n > 26) { fprintf(stderr, "minFAS table needs n<=26 (n=%d)\n", n); exit(1); }
    size_t N = (size_t)1 << n;
    fastab = malloc(N * sizeof(uint16_t));
    if (!fastab) { fprintf(stderr, "FATAL cannot allocate minFAS table (%.0f MB)\n", N*2.0/1048576); exit(1); }
    fastab[0] = 0;
    for (size_t U = 1; U < N; U++) {
        int best = 1 << 20;
        uint64_t r = U;
        while (r) {
            int v = __builtin_ctzll(r); r &= r - 1;
            uint64_t Uv = U & ~(1ULL << v);
            int c = fastab[Uv] + __builtin_popcountll(OUTM[v] & Uv);
            if (c < best) best = c;
        }
        fastab[U] = (uint16_t)best;
    }
    budget = tLO * (n * (n - 1) / 2);
}

/* dissents voter i incurs on the arcs between v and S when v sits at slot p */
static inline int dissents_at(int i, int v, int p) {
    int agree = 0;
    for (int j = 0; j < m; j++) {
        int u = ordv[i][j];
        if (j >= p) agree += (int)((OUTM[v] >> u) & 1);   /* v before u: want v->u */
        else        agree += (int)((OUTM[u] >> v) & 1);   /* u before v: want u->v */
    }
    return m - agree;
}

static int voter_min_fas(int i, uint64_t F, const int *fv, int f) {
    size_t W = (size_t)1 << f;
    uint64_t pref[MAXN + 1];
    pref[0] = 0;
    for (int j = 0; j < m; j++) pref[j + 1] = pref[j] | (1ULL << ordv[i][j]);
    for (size_t U = 0; U < W; U++) {
        if (!U) { umask[0] = 0; continue; }
        int b = __builtin_ctzll(U);
        umask[U] = umask[U & (U - 1)] | (1ULL << fv[b]);
    }
    size_t tot = (size_t)(m + 1) * W;
    for (size_t x = 0; x < tot; x++) g2[x] = 0xFFFF;
    g2[0] = 0;
    for (int j = 0; j <= m; j++) {
        for (size_t U = 0; U < W; U++) {
            int cur = g2[(size_t)j * W + U];
            if (cur == 0xFFFF) continue;
            uint64_t P = pref[j] | umask[U];
            if (j < m) {
                int x = ordv[i][j];
                int c = cur + __builtin_popcountll(OUTM[x] & P);
                size_t k2 = (size_t)(j + 1) * W + U;
                if (c < g2[k2]) g2[k2] = (uint16_t)c;
            }
            for (int b = 0; b < f; b++) {
                if ((U >> b) & 1) continue;
                int x = fv[b];
                int c = cur + __builtin_popcountll(OUTM[x] & P);
                size_t k2 = (size_t)j * W + (U | ((size_t)1 << b));
                if (c < g2[k2]) g2[k2] = (uint16_t)c;
            }
        }
    }
    return g2[(size_t)m * W + (W - 1)];
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
    { /* The mask -> base-state-count map depends only on the ABSTRACT 5-vertex
       * tournament, not on the instance, so it is computed once per process
       * and reused across a whole batch (this was ~13.7s per instance). */
      static long long *cache = NULL;
      if (!cache) {
          cache = malloc(sizeof(long long) << bNE);
          for (int i = 0; i < (1 << bNE); i++) cache[i] = -1;
      }
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
      memcpy(base_v, best, sizeof(int) * base_sz);
    }
    make_static_order();
    int bm = mask_of_subset(base_v, base_sz);
    static int (*bst)[MAXK] = NULL;
    if (!bst) bst = malloc(sizeof(int) * MAXK * 4000000);
    long long nb = base_states(bm, 1, bst, 4000000);
    nodes = 0; sols = 0; dom_calls = 0; dom_nodes = 0; mrv_fails = 0; top0_fails = 0; bound_fails = 0; refine_tuples = 0; fas_fails = 0; fas_tests = 0; DS = 0; aborted = 0; tsp = 0;
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
        if (use_inc) got = init_domains(base_sz) ? dfs_inc(base_sz) : 0;
        else         got = dfs();
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
        printf("BATCH %d %s nodes=%lld time=%.3f\n", idx, v, nodes, now() - t0); fflush(stdout);
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
        else if (!strcmp(argv[i], "--per-base-nodes")) per_base_nodes = atoll(argv[++i]);
        else if (!strcmp(argv[i], "--no-bound")) use_bound = 0;
        else if (!strcmp(argv[i], "--measure-dsz")) measure_dsz = 1;
        else if (!strcmp(argv[i], "--inc")) use_inc = 1;
        else if (!strcmp(argv[i], "--pool-mb")) pool_mb = atol(argv[++i]);
        else if (!strcmp(argv[i], "--fas")) use_fas = 1;
        else if (!strcmp(argv[i], "--fas2")) fas2_depth = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--max-margin")) max_margin = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--defect")) defect_file = argv[++i];
        else if (!strcmp(argv[i], "--defect-support")) {
            def_lo = atoi(argv[++i]); def_hi = atoi(argv[++i]);
        }
        else if (!strcmp(argv[i], "--top0")) top0 = 1;
        else if (!strcmp(argv[i], "--top0r")) { top0 = 1; top0_r = atoi(argv[++i]); }
        else if (!strcmp(argv[i], "--top0rr")) { top0 = 1; top0_r = atoi(argv[++i]); top0_r2 = atoi(argv[++i]); }
        else if (!strcmp(argv[i], "--toporb")) {
            while (i + 1 < argc && argv[i+1][0] != '-') {
                toporb[toporb_m++] = atoi(argv[++i]);
                toporb_mask |= 1ULL << toporb[toporb_m-1];
            }
        }
        else if (!strcmp(argv[i], "--toppair")) {
            tp_u[0] = atoi(argv[++i]); tp_v[0] = atoi(argv[++i]);
            tp_u[1] = atoi(argv[++i]); tp_v[1] = atoi(argv[++i]); tp_n = 2;
        }
        else if (!strcmp(argv[i], "--tie-fas")) { tie_fas = !strcmp(argv[++i], "max") ? 1 : -1; use_fas = 1; }
        else if (!strcmp(argv[i], "--select")) {
            const char *s = argv[++i];
            select_cheap  = !strcmp(s, "cheap");
            select_hybrid = !strcmp(s, "hybrid");
        }
        else if (!strcmp(argv[i], "-v"))      verbose = 1;
        else { fprintf(stderr, "unknown arg %s\n", argv[i]); return 1; }
    }
    if (q) make_paley(q);
    else if (bits) { if (!nn) { fprintf(stderr, "--bits needs --n\n"); return 1; } make_bits(bits, nn); }
    else if (batch_file) { if (!nn) { fprintf(stderr, "--batch needs --n\n"); return 1; } n = nn; }
    else { fprintf(stderr, "need --paley q, --bits F --n N, or --batch F --n N\n"); return 1; }
    if (K > MAXK || K % 2 == 0) { fprintf(stderr, "K must be odd <= %d\n", MAXK); return 1; }
    /* --toppair is only a COMPLETE case split if the two representatives lie in
     * DIFFERENT arc orbits: one must be an arc of T, the other a non-arc.  Two
     * reps in the same orbit silently discards every profile whose (top,second)
     * falls in the other orbit.  (Arc-transitivity of Aut(T) itself cannot be
     * checked here -- it holds for Paley, which is the only intended use.)   */
    if (tp_n) {
        int a0 = (OUTM[tp_u[0]] >> tp_v[0]) & 1;
        int a1 = (OUTM[tp_u[1]] >> tp_v[1]) & 1;
        for (int r = 0; r < 2; r++)
            if (tp_u[r] == tp_v[r] || tp_u[r] >= n || tp_v[r] >= n) {
                fprintf(stderr, "FATAL --toppair: (%d,%d) is not a valid vertex pair\n",
                        tp_u[r], tp_v[r]); return 1;
            }
        if (a0 == a1) {
            fprintf(stderr, "FATAL --toppair: (%d,%d) and (%d,%d) are both %s of T "
                    "-- the two reps must lie in DIFFERENT arc orbits, else the "
                    "break is UNSOUND\n", tp_u[0], tp_v[0], tp_u[1], tp_v[1],
                    a0 ? "arcs" : "non-arcs"); return 1;
        }
        printf("  toppair reps: (%d,%d) is %s, (%d,%d) is %s -- one per orbit, OK\n",
               tp_u[0], tp_v[0], a0 ? "an arc" : "a non-arc",
               tp_u[1], tp_v[1], a1 ? "an arc" : "a non-arc");
    }

    if (toporb_m) {
        if (!use_inc) { fprintf(stderr, "FATAL --toporb needs --inc: the break is "
            "implemented in dfs_inc only\n"); return 1; }
        for (int j = 0; j < toporb_m; j++)
            if (toporb[j] < 0 || toporb[j] >= n) {
                fprintf(stderr, "FATAL --toporb: %d is not a vertex of this "
                        "%d-vertex host\n", toporb[j], n); return 1; }
        printf("  toporb reps:");
        for (int j = 0; j < toporb_m; j++) printf(" %d", toporb[j]);
        printf("  -- SOUND ONLY IF these meet EVERY Aut(T)-orbit on V; the "
               "engine cannot check that\n");
    }

    tHI = (K + 1) / 2; tLO = (K - 1) / 2;
    supHI = K;
    if (max_margin >= 0) {
        if (max_margin < 1 || max_margin > K || (max_margin % 2) != (K % 2)) {
            fprintf(stderr, "FATAL --max-margin %d: must be odd, 1..%d "
                    "(support s gives margin |2s-%d|)\n", max_margin, K, K); return 1; }
        if (defect_file) { fprintf(stderr, "FATAL --max-margin with --defect is "
                "not implemented: the defect window and the margin cap would "
                "have to be reconciled pair by pair\n"); return 1; }
        supHI = (K + max_margin) / 2;
        if (max_margin == 1) exact_margin = 1;            /* = --margin exact */
        else exact_margin = 0;
        printf("  max-margin %d: arc support in [%d,%d], non-arc in [%d,%d]%s\n",
               max_margin, tHI, supHI, K - supHI, tLO,
               max_margin == 1 ? "  (= --margin exact)" :
               max_margin == K ? "  (= --margin majority)" : "");
    }
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
    /* ---- the defect set R -------------------------------------------
     * Loaded here, after the base is final, because the soundness of the
     * whole route turns on R missing the base's internal arcs.            */
    if (defect_file) {
        if (def_lo < 0) { def_lo = 0; def_hi = tLO; }   /* = the old behaviour */
        if (def_lo > def_hi || def_lo < 0 || def_hi > tLO) {
            fprintf(stderr, "FATAL --defect-support %d %d: need 0 <= LO <= HI <= "
                    "tLO = %d (support is measured in T's OWN direction, and a "
                    "reversed arc has at most tLO of it)\n", def_lo, def_hi, tLO);
            return 1; }
        if (exact_margin && !(def_lo == tLO && def_hi == tLO) && def_hi != tLO) {
            fprintf(stderr, "FATAL --defect-support with --margin exact: at "
                    "margin 1 a reversed arc sits at exactly tLO = %d, so the "
                    "only meaningful window is %d %d\n", tLO, tLO, tLO);
            return 1; }
        if (!use_inc) { fprintf(stderr, "FATAL --defect needs --inc: the "
            "non-incremental dfs() has no defect bookkeeping\n"); return 1; }
        if (use_fas || fas2_depth >= 0) { fprintf(stderr, "FATAL --defect is "
            "incompatible with --fas/--fas2: the minFAS dissent budget is "
            "computed for T, and reversing an arc changes it\n"); return 1; }
        if (batch_file) { fprintf(stderr, "FATAL --defect does not support "
            "--batch\n"); return 1; }
        if (K >= MAXK) { fprintf(stderr, "FATAL --defect needs K < MAXK=%d: the "
            "per-tuple defect tag lives in byte %d of the tuple\n", MAXK, DFB);
            return 1; }
        FILE *df = fopen(defect_file, "r");
        if (!df) { perror(defect_file); return 1; }
        char line[256];
        uint64_t bmask = 0;
        for (int j = 0; j < base_sz; j++) bmask |= 1ULL << base_v[j];
        while (fgets(line, sizeof line, df)) {
            char *p = line; while (*p == ' ' || *p == '\t') p++;
            if (*p == '#' || *p == '\n' || *p == 0) continue;
            int u, v;
            if (sscanf(p, "%d %d", &u, &v) != 2) {
                fprintf(stderr, "FATAL --defect: cannot parse '%s'\n", p); return 1; }
            if (u == v || u < 0 || v < 0 || u >= n || v >= n) {
                fprintf(stderr, "FATAL --defect: (%d,%d) is not a vertex pair "
                        "of this %d-vertex host\n", u, v, n); return 1; }
            if (!((OUTM[u] >> v) & 1)) {
                fprintf(stderr, "FATAL --defect: (%d,%d) is not an ARC of T "
                        "(it runs the other way).  R lists arcs to be "
                        "REVERSED, in T's own direction.\n", u, v); return 1; }
            if (((bmask >> u) & 1) && ((bmask >> v) & 1)) {
                fprintf(stderr, "FATAL --defect: arc (%d,%d) lies INSIDE the "
                        "base, so the base states -- enumerated against the "
                        "exact restriction of T -- would miss every solution "
                        "spending its defect there.  This is the unsound "
                        "combination; choose R to miss the base (see "
                        "defect_set.py) or choose another base.\n", u, v);
                return 1; }
            if ((RM[u] >> v) & 1) continue;         /* duplicate line       */
            RM[u] |= 1ULL << v; RM[v] |= 1ULL << u; defect_n++;
        }
        fclose(df);
        if (!defect_n) { fprintf(stderr, "FATAL --defect: %s lists no arcs\n",
                                 defect_file); return 1; }
        printf("  defect budget 1, confined to %d arc(s) from %s; none inside "
               "the base -- OK\n", defect_n, defect_file);
        printf("  defect support window [%d,%d] in T's direction%s\n", def_lo, def_hi,
               (def_lo == 0 && def_hi == tLO) ? "  (default: any reversal)"
               : (def_hi == tLO) ? "  (convex with [tHI,K]: monotone break kept)"
               : "  (NON-convex: R-pairs take continue, not break)");
    }

    make_static_order();

    if (use_inc) {
        poolcap = (size_t)pool_mb * 1024 * 1024;
        dompool = malloc(poolcap);
        if (!dompool) { fprintf(stderr, "FATAL cannot allocate domain pool\n"); return 1; }
    }
    if (use_fas) build_fastab();
    if (fas2_depth >= 0) {
        budget = tLO * (n * (n - 1) / 2);
        int fmax = n - fas2_depth; if (fmax > 22) fmax = 22;
        g2 = malloc(sizeof(uint16_t) * (size_t)(n + 1) * ((size_t)1 << fmax));
        umask = malloc(sizeof(uint64_t) * ((size_t)1 << fmax));
        if (!g2 || !umask) { fprintf(stderr, "FATAL cannot allocate tier-2 DP\n"); return 1; }
    }
    tstack = malloc((size_t)TCAP * MAXK);
    int (*bstates)[MAXK] = malloc(sizeof(int) * MAXK * 4000000);
    if (!tstack || !bstates) { fprintf(stderr, "FATAL alloc\n"); return 1; }

    int bm = mask_of_subset(base_v, base_sz);
    long long nb = base_states(bm, 1, bstates, 4000000);

    printf("n=%d K=%d margin=%s order=%s%s mrv_cap=%lld tie_imb=%d mode=%s symbreak=%d defect_R=%d base_sz=%d base=",
           n, K, exact_margin ? "exact1" : "majority", order_mrv ? "mrv" : "static",
           use_inc ? "+inc" : "", mrv_cap, tie_imbalance, find_one ? "one" : "count", symbreak, defect_n, base_sz);
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
    long long n_cleared = 0, n_capped = 0;
    for (long long b = blo; b < bhi && !got && !aborted; b++) {
        base_nodes0 = nodes; base_abort = 0;
        m = base_sz; placed = 0; tsp = 0;
        for (int i = 0; i < K; i++) {
            int pi = bstates[b][i];
            for (int j = 0; j < base_sz; j++) ordv[i][j] = base_v[bperm[pi][j]];
        }
        for (int j = 0; j < base_sz; j++) placed |= 1ULL << base_v[j];
        if (base_sz == n) { sols++; if (find_one) { print_and_verify(); got = 1; } continue; }
        if (use_inc) got = init_domains(base_sz) ? dfs_inc(base_sz) : 0;
        else         got = dfs();
        if (base_abort) n_capped++;
        else if (!got && !aborted) n_cleared++;
        if (((b - blo) & 0x1F) == 0x1F || b + 1 == bhi) {
            printf("PROGRESS b=%lld/%lld cleared=%lld capped=%lld nodes=%lld time=%.1fs\n",
                   b + 1, bhi, n_cleared, n_capped, nodes, now() - t0); fflush(stdout);
        }
    }
    printf("SLICE cleared=%lld capped=%lld of [%lld,%lld)%s\n", n_cleared, n_capped, blo, bhi,
           (n_capped == 0 && !got && !aborted) ? "  => SLICE EXHAUSTED, no witness" : "");
    double el = now() - t0;
    if (measure_dsz) {
        printf("FULL DOMAIN SIZES |D(v|S)| by depth |S| (uncapped)\n");
        printf("  %4s %10s %8s %8s   distribution by size bucket\n", "|S|", "samples", "mean", "max");
        for (int d = 0; d < n; d++) if (dsz_cnt[d]) {
            printf("  %4d %10lld %8.1f %8lld   ", d, dsz_cnt[d],
                   (double)dsz_sum[d] / dsz_cnt[d], dsz_max[d]);
            const char *lbl[8] = {"0-1","2-3","4-7","8-15","16-31","32-63","64-127","128+"};
            for (int b = 0; b < 8; b++) if (dsz_hist[d][b])
                printf("%s:%.0f%% ", lbl[b], 100.0 * dsz_hist[d][b] / dsz_cnt[d]);
            printf("\n");
        }
    }
    if (use_fas) {
        printf("FAS budget=%d  fired %lld / %lld tests (%.2f%%)  by depth:", budget, fas_fails, fas_tests,
               fas_tests ? 100.0*fas_fails/fas_tests : 0.0);
        for (int d = 0; d < n; d++) if (fas_fire_depth[d]) printf(" %d:%lld", d, fas_fire_depth[d]);
        printf("\n");
    }
    if (fas2_depth >= 0) {
        printf("FAS2 depth>=%d budget=%d  fired %lld / %lld tests (%.2f%%)  by depth:",
               fas2_depth, budget, fas2_fails, fas2_tests, fas2_tests ? 100.0*fas2_fails/fas2_tests : 0.0);
        for (int d = 0; d < n; d++) if (fas2_fire_depth[d]) printf(" %d:%lld", d, fas2_fire_depth[d]);
        printf("\n");
    }
    printf("RESULT %s nodes=%lld sols=%lld base_states=%lld dom_calls=%lld dom_nodes=%lld mrv_fails=%lld top0_fails=%lld bound_fails=%lld fas_fails=%lld/%lld refine_tuples=%lld time=%.3fs\n",
           aborted ? "ABORTED" : (find_one ? (got ? "SAT" : "UNSAT") : "COUNTED"),
           nodes, sols, nb, dom_calls, dom_nodes, mrv_fails, top0_fails, bound_fails, fas_fails, fas_tests, refine_tuples, el);
    return 0;
}
