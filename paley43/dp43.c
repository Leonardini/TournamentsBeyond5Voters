/* dp43.c — the Paley(q) near-MAS shell engine (DP43_PLAN.md, 2026-07-07).
 *
 * Certified enumeration of ALL orders of Paley(q) with fwd >= tau, via an
 * UNANCHORED subset DP over orbit representatives modulo
 * Aut = {x -> ax+b, a in QR(q)}, |Aut| = q(q-1)/2, with meet-in-the-middle
 * at the equator h = floor(q/2). Layered BFS: expand layer-j reps -> children
 * (gain computed in the parent's labeling BEFORE canonicalizing) -> per-record
 * budget prune -> canonicalize -> sort/dedup keeping max g -> layer j+1.
 *
 * Soundness of the pruned tables (the chain induction): for any full order o
 * with back(o) <= B = C - tau, every prefix set P_j of o stays alive and its
 * table value g~ satisfies g~ >= fwd(o restricted to P_j). Per-record pruning
 * with the candidate g is sound because the prune test is monotone in g and
 * the record from o's own parent passes it. A missing state therefore
 * certifies that no fwd>=tau order passes through it.
 *
 * MiM join at split (h | q-h): an order's suffix half is covered by the tables
 * through its REVERSED-NEGATED twin (x -> -x is the converse isomorphism,
 * q = 3 mod 4; negation is NOT in Aut and the inarcs prune term is not
 * negation-symmetric), so the join lookup for prefix rep S is
 * canon(neg(V\S)), NOT canon(V\S), against the streamed layer-(h+1) table.
 * Total through S = g(S) + cross(S) + g(V\S); max over alive splits = MAS
 * exactly (each term <= truth, and o's own split attains fwd(o)).
 * Enumeration: slack-backtrack both halves against the layer tables (suffix
 * lookups via canon(neg(.))), pair-filter fwdP+fwdT >= tau-cross, re-verify
 * every emitted order from scratch. Output is up-to-Aut; 'close' expands by
 * the |Aut| maps and dedups (build_orbits.R re-checks closure independently).
 *
 * Canonical form: min-as-integer bit mask over maps sending some s in S to 0
 * (always attainable by translation), s restricted to argmax of the invariant
 * score(s) = outdeg within S (a valid orbit-invariant refinement; canon_slow
 * in selftest replicates the same definition independently). Evaluation:
 * cyclic-rotate S by s, then per-a byte-scatter LUTs (6 lookups per map).
 *
 * Modes:
 *   dp43 burnside <q>                  exact per-layer orbit counts (sizing)
 *   dp43 selftest <q> <dir>            q<=11: canon/Burnside/brute-force/prune checks
 *   dp43 layers|join|enum|close|all <q> <tau> <dir>
 * env: THREADS(8,<=10) CHUNKMB(32) DEGFROM(10) ADAPTFROM(999) ROUNDS(12)
 *      NOPRUNE(0) RAMGB(12)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>

typedef uint64_t u64; typedef int64_t i64; typedef uint8_t u8;

#define MAXQ 47
#define MAXC 1081
#define NQRMAX 23
#define TCAP 4096
#define TOMB (~0ULL)

static int q, C, h, NQR, NAUT, tau, Bbud;
static u64 FULL;
static int adjm[MAXQ][MAXQ];
static u64 fullIn[MAXQ], fullOut[MAXQ];
static int qrl[NQRMAX];                    /* the (q-1)/2 quadratic residues */
static u64 SCAT[NQRMAX][6][256];           /* per-a byte scatter: src bit p -> image bit a*p */
static int aid[MAXQ][MAXQ], au_[MAXC + 1], av_[MAXC + 1];
static u64 tw[MAXC + 1];                   /* per-arc third-vertex masks (adaptive packing) */
static u64 burn[MAXQ + 2];                 /* exact orbit count of k-subsets (Burnside) */
static char DIR[900];
static int NTH = 8, DEGFROM = 10, ADAPTFROM = 999, ROUNDS = 12, NOPRUNE = 0;
static double RAMGB = 12.0;
static i64 CHUNK;                          /* records per worker chunk */

static double now_s(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + 1e-9 * t.tv_nsec; }
static void die(const char *m) { fprintf(stderr, "FATAL: %s\n", m); exit(1); }

/* ---------- Paley setup, group tables, Burnside ------------------------- */
static int modpow(long b, long e, long m) { long r = 1; b %= m; while (e) { if (e & 1) r = r * b % m; b = b * b % m; e >>= 1; } return (int)r; }

static void setup(int qq) {
  q = qq; C = q * (q - 1) / 2; h = q / 2; FULL = (q == 64) ? ~0ULL : ((1ULL << q) - 1);
  if (q < 3 || q > MAXQ || q % 4 != 3) die("q must be a prime = 3 mod 4, <= 43");
  for (int d = 2; d * d <= q; d++) if (q % d == 0) die("q not prime");
  int isqr[MAXQ] = {0};
  for (long x = 1; x < q; x++) isqr[(x * x) % q] = 1;
  NQR = 0;
  for (int s = 1; s < q; s++) if (isqr[s]) qrl[NQR++] = s;
  NAUT = NQR * q;
  for (int u = 0; u < q; u++) for (int v = 0; v < q; v++)
    adjm[u][v] = (u != v && isqr[((v - u) % q + q) % q]);
  for (int v = 0; v < q; v++) {
    fullIn[v] = fullOut[v] = 0;
    for (int u = 0; u < q; u++) {
      if (adjm[u][v]) fullIn[v] |= 1ULL << u;
      if (adjm[v][u]) fullOut[v] |= 1ULL << u;
    }
  }
  int ne = 0;
  for (int u = 0; u < q; u++) for (int v = 0; v < q; v++)
    if (adjm[u][v]) { aid[u][v] = ++ne; au_[ne] = u; av_[ne] = v; }
  for (int e = 1; e <= ne; e++) tw[e] = fullOut[av_[e]] & fullIn[au_[e]];
  /* scatter LUTs: image bit (a*p mod q) = source bit p */
  for (int ai = 0; ai < NQR; ai++) {
    long a = qrl[ai];
    for (int i = 0; i < 6; i++) for (int v = 0; v < 256; v++) {
      u64 w = 0;
      for (int j = 0; j < 8; j++) {
        int p = 8 * i + j;
        if (p < q && (v >> j & 1)) w |= 1ULL << (a * p % q);
      }
      SCAT[ai][i][v] = w;
    }
  }
  /* Burnside: #orbits of k-subsets = (1/NAUT) sum_sigma [x^k] prod_cycles (1+x^len) */
  u64 tot[MAXQ + 2] = {0};
  for (int ai = 0; ai < NQR; ai++) for (int b = 0; b < q; b++) {
    long a = qrl[ai];
    int seen[MAXQ] = {0};
    u64 c[MAXQ + 2] = {0}; c[0] = 1;
    int deg = 0;
    for (int v = 0; v < q; v++) if (!seen[v]) {
      int len = 0, x = v;
      do { seen[x] = 1; x = (int)((a * x + b) % q); len++; } while (x != v);
      for (int t = deg; t >= 0; t--) if (c[t]) c[t + len] += c[t];
      deg += len;
    }
    for (int k = 0; k <= q; k++) tot[k] += c[k];
  }
  for (int k = 0; k <= q; k++) {
    if (tot[k] % (u64)NAUT) die("Burnside not divisible — group bug");
    burn[k] = tot[k] / (u64)NAUT;
  }
}

/* ---------- canonicalization -------------------------------------------- */
static inline u64 rotq(u64 S, int s) { return s ? ((S >> s) | (S << (q - s))) & FULL : S; }

static inline u64 negset(u64 S) {
  u64 r = S & 1;                            /* 0 -> 0 */
  u64 x = S & ~1ULL;
  while (x) { int v = __builtin_ctzll(x); x &= x - 1; r |= 1ULL << (q - v); }
  return r;
}

static u64 canon(u64 S) {
  if (!S) return 0;
  int bs = -1, nc = 0; u8 cand[MAXQ];
  u64 x = S;
  while (x) {
    int v = __builtin_ctzll(x); x &= x - 1;
    int sc = __builtin_popcountll(fullOut[v] & S);
    if (sc > bs) { bs = sc; nc = 0; }
    if (sc == bs) cand[nc++] = (u8)v;
  }
  u64 best = ~0ULL;
  for (int ci = 0; ci < nc; ci++) {
    u64 Ss = rotq(S, cand[ci]);
    unsigned b0 = Ss & 255, b1 = (Ss >> 8) & 255, b2 = (Ss >> 16) & 255,
             b3 = (Ss >> 24) & 255, b4 = (Ss >> 32) & 255, b5 = (Ss >> 40) & 255;
    for (int ai = 0; ai < NQR; ai++) {
      const u64 *T = &SCAT[ai][0][0];
      u64 W = T[b0] | T[256 + b1] | T[512 + b2] | T[768 + b3] | T[1024 + b4] | T[1280 + b5];
      if (W < best) best = W;
    }
  }
  return best;
}

/* independent re-implementation of the same canonical definition (selftest) */
static u64 canon_slow(u64 S) {
  if (!S) return 0;
  int bs = -1;
  u64 x = S;
  while (x) { int v = __builtin_ctzll(x); x &= x - 1; int sc = __builtin_popcountll(fullOut[v] & S); if (sc > bs) bs = sc; }
  u64 best = ~0ULL;
  x = S;
  while (x) {
    int s = __builtin_ctzll(x); x &= x - 1;
    if (__builtin_popcountll(fullOut[s] & S) != bs) continue;
    for (int ai = 0; ai < NQR; ai++) {
      long a = qrl[ai], b = ((q - (long)s % q) * a) % q;   /* b = -a*s: sigma(s)=0 */
      u64 W = 0, y = S;
      while (y) { int v = __builtin_ctzll(y); y &= y - 1; W |= 1ULL << ((a * v + b) % q); }
      if (W < best) best = W;
    }
  }
  return best;
}

/* ---------- prune bounds ------------------------------------------------- */
static int I_of(u64 S) {                    /* #arcs from V\S INTO S (cross-back, exact) */
  int r = 0; u64 cp = FULL & ~S, x = S;
  while (x) { int v = __builtin_ctzll(x); x &= x - 1; r += __builtin_popcountll(fullIn[v] & cp); }
  return r;
}

static int deg_lb(u64 T) {                  /* sorted-outdeg LB on internal minback(T) */
  int d[MAXQ], t = 0;
  u64 x = T;
  while (x) { int v = __builtin_ctzll(x); x &= x - 1; d[t++] = __builtin_popcountll(fullOut[v] & T); }
  for (int a = 1; a < t; a++) { int key = d[a], b = a - 1; while (b >= 0 && d[b] > key) { d[b + 1] = d[b]; b--; } d[b + 1] = key; }
  int lb = 0;
  for (int i = 0; i < t; i++) if (d[i] > i) lb += d[i] - i;
  return lb;
}

typedef struct { int e1[TCAP], e2[TCAP], e3[TCAP]; double w[TCAP], load[MAXC + 1]; } AScr;

/* adaptive triangle packing on induced sub T: uniform weights, ROUNDS of
 * w /= own worst load, final exact-load rescale => sound LB on minback(T) */
static double adapt_lb(u64 T, AScr *sc) {
  int ntl = 0;
  u64 uu = T;
  while (uu) {
    int u = __builtin_ctzll(uu); uu &= uu - 1;
    u64 vv = fullOut[u] & T;
    while (vv) {
      int v = __builtin_ctzll(vv); vv &= vv - 1;
      u64 ww = tw[aid[u][v]] & T;
      while (ww) {
        int x = __builtin_ctzll(ww); ww &= ww - 1;
        if (u < v && u < x) {
          sc->e1[ntl] = aid[u][v]; sc->e2[ntl] = aid[v][x]; sc->e3[ntl] = aid[x][u];
          if (++ntl >= TCAP) return 0;
        }
      }
    }
  }
  if (!ntl) return 0;
  for (int t = 0; t < ntl; t++) sc->w[t] = 1;
  for (int r = 0; r <= ROUNDS; r++) {
    memset(sc->load, 0, sizeof(double) * (C + 1));
    for (int t = 0; t < ntl; t++) { sc->load[sc->e1[t]] += sc->w[t]; sc->load[sc->e2[t]] += sc->w[t]; sc->load[sc->e3[t]] += sc->w[t]; }
    if (r == ROUNDS) {
      double mx = 1, sw = 0;
      for (int t = 0; t < ntl; t++) {
        double tl = sc->load[sc->e1[t]];
        if (sc->load[sc->e2[t]] > tl) tl = sc->load[sc->e2[t]];
        if (sc->load[sc->e3[t]] > tl) tl = sc->load[sc->e3[t]];
        if (tl > mx) mx = tl;
        sw += sc->w[t];
      }
      return sw / mx;
    }
    for (int t = 0; t < ntl; t++) {
      double tl = sc->load[sc->e1[t]];
      if (sc->load[sc->e2[t]] > tl) tl = sc->load[sc->e2[t]];
      if (sc->load[sc->e3[t]] > tl) tl = sc->load[sc->e3[t]];
      if (tl > 1) sc->w[t] /= tl;
    }
  }
  return 0;
}

/* ---------- sort / dedup / merge ---------------------------------------- */
static void radix_u64(u64 *a, u64 *tmp, i64 n) {
  for (int pass = 0; pass < 8; pass++) {
    i64 cnt[256] = {0};
    int sh = pass * 8;
    for (i64 i = 0; i < n; i++) cnt[(a[i] >> sh) & 255]++;
    i64 s = 0;
    for (int b = 0; b < 256; b++) { i64 c = cnt[b]; cnt[b] = s; s += c; }
    for (i64 i = 0; i < n; i++) tmp[cnt[(a[i] >> sh) & 255]++] = a[i];
    u64 *t = a; a = tmp; tmp = t;
  }
}

static i64 dedup_max(u64 *a, i64 n) {      /* sorted asc; keep max-g per key */
  if (!n) return 0;
  i64 w = 0;
  for (i64 i = 1; i < n; i++) {
    if ((a[i] >> 16) != (a[w] >> 16)) a[++w] = a[i];
    else a[w] = a[i];
  }
  return w + 1;
}

/* backward in-place merge of sorted deduped B into A (A holds na at [0,na),
 * capacity >= na+nb); dedup keeps max g; returns new count, result at [0,.) */
static i64 merge_into(u64 *A, i64 na, const u64 *B, i64 nb) {
  if (!nb) return na;
  if (!na) { memcpy(A, B, (size_t)nb * 8); return nb; }
  i64 i = na, j = nb, w = na + nb;
  while (i > 0 && j > 0) {
    u64 av = A[i - 1], bv = B[j - 1], ak = av >> 16, bk = bv >> 16;
    if (ak == bk) { A[--w] = av > bv ? av : bv; i--; j--; }
    else if (ak > bk) { A[--w] = av; i--; }
    else { A[--w] = bv; j--; }
  }
  while (j > 0) A[--w] = B[--j];
  i64 tail = na + nb - w;
  if (i != w) memmove(A + i, A + w, (size_t)tail * 8);
  return i + tail;
}

/* ---------- manifest ----------------------------------------------------- */
static void man_path(char *p) { snprintf(p, 1000, "%s/manifest.txt", DIR); }

static int relax_tau = 0;                  /* read-only modes: built-tau <= run-tau is sound */

static i64 man_layer(int j) {              /* -1 if layer j not recorded done */
  char p[1000]; man_path(p);
  FILE *f = fopen(p, "r");
  if (!f) return -1;
  char line[256]; i64 res = -1;
  while (fgets(line, sizeof line, f)) {
    int jj, qq, tt; long long cc;
    if (sscanf(line, "L %d q %d tau %d n %lld", &jj, &qq, &tt, &cc) == 4 && jj == j) {
      if (qq != q) die("manifest q mismatch — wrong workdir");
      /* layers built at threshold tt keep every order with fwd >= tt; using
       * them at run-tau >= tt only tightens downstream filters => sound.
       * run-tau < tt would need records the prune already dropped => refuse. */
      if (relax_tau ? (tt > tau) : (tt != tau))
        die("manifest tau mismatch — tables built at a TIGHTER threshold than requested");
      res = cc;
    }
  }
  fclose(f);
  return res;
}

static int man_flag(const char *tag, long long *v1, long long *v2) {
  char p[1000]; man_path(p);
  FILE *f = fopen(p, "r");
  if (!f) return 0;
  char line[256], t[32]; int found = 0;
  while (fgets(line, sizeof line, f)) {
    long long a = 0, b = 0; int tt;
    if (sscanf(line, "%31s tau %d v1 %lld v2 %lld", t, &tt, &a, &b) >= 2 && !strcmp(t, tag) && tt == tau) {
      if (v1) *v1 = a; if (v2) *v2 = b; found = 1;
    }
  }
  fclose(f);
  return found;
}

static void man_add(const char *line) {
  char p[1000]; man_path(p);
  FILE *f = fopen(p, "a");
  if (!f) die("manifest append");
  fprintf(f, "%s\n", line);
  fclose(f);
}

static void lay_path(char *p, int j) { snprintf(p, 1000, "%s/L%02d.bin", DIR, j); }

/* ---------- worker/merger machinery for one layer transition ------------- */
#define QCAP 4
typedef struct { u64 *a; i64 n; } ChunkT;
static struct {
  const u64 *par; i64 npar; i64 nextblk;   /* input layer (mmap) */
  int jpar;                                /* |parent sets| */
  ChunkT ring[QCAP]; int qh, qt, qn, done_workers;
  u64 **freelist; int nfree;
  pthread_mutex_t mu; pthread_cond_t cv_prod, cv_cons;
  i64 st_children, st_killpre, st_pushed;  /* stats */
} TR;

#define BLK 4096

static void push_chunk(u64 *a, i64 n) {
  pthread_mutex_lock(&TR.mu);
  while (TR.qn == QCAP) pthread_cond_wait(&TR.cv_prod, &TR.mu);
  TR.ring[TR.qt].a = a; TR.ring[TR.qt].n = n;
  TR.qt = (TR.qt + 1) % QCAP; TR.qn++;
  pthread_cond_signal(&TR.cv_cons);
  pthread_mutex_unlock(&TR.mu);
}

static u64 *grab_buf(void) {
  pthread_mutex_lock(&TR.mu);
  while (!TR.nfree) pthread_cond_wait(&TR.cv_prod, &TR.mu);
  u64 *b = TR.freelist[--TR.nfree];
  pthread_mutex_unlock(&TR.mu);
  return b;
}

static void *expand_worker(void *arg) {
  u64 *tmp = malloc((size_t)CHUNK * 8);
  u64 *buf = grab_buf();
  i64 k = 0, st_ch = 0, st_kill = 0, st_push = 0;
  int jc = TR.jpar + 1;                     /* child layer */
  i64 backC = (i64)jc * (jc - 1) / 2;
  (void)arg;
  for (;;) {
    i64 b = __sync_fetch_and_add(&TR.nextblk, 1);
    i64 lo = b * BLK, hi = lo + BLK;
    if (lo >= TR.npar) break;
    if (hi > TR.npar) hi = TR.npar;
    for (i64 r = lo; r < hi; r++) {
      u64 rec = TR.par[r];
      u64 S = rec >> 16;
      int g = (int)(rec & 0xffff);
      int IS = I_of(S);
      u64 rest = FULL & ~S;
      while (rest) {
        int v = __builtin_ctzll(rest); rest &= rest - 1;
        int gain = __builtin_popcountll(fullIn[v] & S);
        int gT = g + gain;
        st_ch++;
        if (!NOPRUNE) {
          u64 T = S | (1ULL << v);
          u64 cpT = FULL & ~T;
          int IT = IS - __builtin_popcountll(fullOut[v] & S) + __builtin_popcountll(fullIn[v] & cpT);
          int cost = (int)backC - gT + IT;
          if (cost > Bbud) { st_kill++; continue; }
          if (jc >= DEGFROM && cost + deg_lb(cpT) > Bbud) { st_kill++; continue; }
        }
        u64 key = canon(S | (1ULL << v));
        buf[k++] = (key << 16) | (u64)gT;
        if (k == CHUNK) {
          radix_u64(buf, tmp, k);
          k = dedup_max(buf, k);
          st_push += k;
          push_chunk(buf, k);
          buf = grab_buf();
          k = 0;
        }
      }
    }
  }
  if (k) { radix_u64(buf, tmp, k); k = dedup_max(buf, k); st_push += k; push_chunk(buf, k); }
  else {
    pthread_mutex_lock(&TR.mu);
    TR.freelist[TR.nfree++] = buf;
    pthread_cond_broadcast(&TR.cv_prod);
    pthread_mutex_unlock(&TR.mu);
  }
  free(tmp);
  pthread_mutex_lock(&TR.mu);
  TR.done_workers++;
  __sync_fetch_and_add(&TR.st_children, st_ch);
  __sync_fetch_and_add(&TR.st_killpre, st_kill);
  __sync_fetch_and_add(&TR.st_pushed, st_push);
  pthread_cond_signal(&TR.cv_cons);
  pthread_mutex_unlock(&TR.mu);
  return NULL;
}

/* ---- K-way pending-chunk merge (merger scaling fix, 2026-07-07 12:40): the
 * incremental 2-way staging merge had ~trigger/(2*chunk) ~ 21x write
 * amplification and made the single-threaded merger the bottleneck from L14
 * up (throughput halving per layer). Instead: retain up to KMAX sorted chunks,
 * merge them in ONE K-way heap pass (parallel by key range) into runbuf, then
 * one backward in-place merge into master. Same dedup-max semantics. */
#define KMAX 128
typedef struct { u64 r; int c; } HEnt;
static struct { ChunkT pend[KMAX]; int npend; i64 pendrecs; u64 *runbuf; i64 mcap; } RM;
typedef struct { u64 lo, hi; i64 off, n; } RJob;
static struct { RJob job[16]; int njob; int next; } RJ;

static i64 lb_key(const u64 *a, i64 n, u64 key) {  /* first idx with (rec>>16) >= key */
  i64 lo = 0, hi = n;
  while (lo < hi) { i64 m = (lo + hi) >> 1; if ((a[m] >> 16) < key) lo = m + 1; else hi = m; }
  return lo;
}

static inline void hsift(HEnt *hp, int hn, HEnt e) {  /* root hole, sift e down */
  int i = 0;
  for (;;) {
    int l = 2 * i + 1;
    if (l >= hn) break;
    if (l + 1 < hn && hp[l + 1].r < hp[l].r) l++;
    if (hp[l].r >= e.r) break;
    hp[i] = hp[l]; i = l;
  }
  hp[i] = e;
}

static void *range_merge_worker(void *arg) {
  (void)arg;
  for (;;) {
    int t = __sync_fetch_and_add(&RJ.next, 1);
    if (t >= RJ.njob) break;
    RJob *J = &RJ.job[t];
    i64 cur[KMAX], end[KMAX];
    HEnt hp[KMAX]; int hn = 0;
    for (int c = 0; c < RM.npend; c++) {
      cur[c] = lb_key(RM.pend[c].a, RM.pend[c].n, J->lo);
      end[c] = lb_key(RM.pend[c].a, RM.pend[c].n, J->hi);
      if (cur[c] < end[c]) {
        u64 r = RM.pend[c].a[cur[c]++];
        int i = hn++;
        while (i && hp[(i - 1) / 2].r > r) { hp[i] = hp[(i - 1) / 2]; i = (i - 1) / 2; }
        hp[i].r = r; hp[i].c = c;
      }
    }
    u64 *out = RM.runbuf + J->off;
    i64 w = 0; u64 have = 0; int hv = 0;
    while (hn) {
      u64 r = hp[0].r; int c = hp[0].c;
      if (cur[c] < end[c]) { HEnt e = { RM.pend[c].a[cur[c]++], c }; hsift(hp, hn, e); }
      else if (--hn) { HEnt e = hp[hn]; hsift(hp, hn, e); }
      if (hv && (r >> 16) == (have >> 16)) { if (r > have) have = r; }   /* ascending => keep max g */
      else { if (hv) out[w++] = have; have = r; hv = 1; }
    }
    if (hv) out[w++] = have;
    J->n = w;
  }
  return NULL;
}

static i64 do_runmerge(u64 *master, i64 nm) {
  if (!RM.npend) return nm;
  /* merge_into writes transiently into master[0..nm+nr): the master buffer is
   * sized burn+KMAX*CHUNK so this can never overrun, but guard it anyway */
  if (nm + RM.pendrecs > RM.mcap) die("master transient overflow — capacity bug");
  if (RM.npend == 1) nm = merge_into(master, nm, RM.pend[0].a, RM.pend[0].n);
  else {
    int big = 0;
    for (int c = 1; c < RM.npend; c++) if (RM.pend[c].n > RM.pend[big].n) big = c;
    int njob = NTH < 16 ? NTH : 16;
    if (RM.pend[big].n < 4096) njob = 1;
    u64 bnd[17]; bnd[0] = 0; bnd[njob] = ~0ULL;
    for (int t = 1; t < njob; t++) bnd[t] = RM.pend[big].a[(i64)t * RM.pend[big].n / njob] >> 16;
    i64 off = 0;
    RJ.njob = njob; RJ.next = 0;
    for (int t = 0; t < njob; t++) {
      RJ.job[t].lo = bnd[t]; RJ.job[t].hi = bnd[t + 1];
      RJ.job[t].off = off; RJ.job[t].n = 0;
      for (int c = 0; c < RM.npend; c++)
        off += lb_key(RM.pend[c].a, RM.pend[c].n, bnd[t + 1]) - lb_key(RM.pend[c].a, RM.pend[c].n, bnd[t]);
    }
    pthread_t th[64];
    for (int i = 0; i < njob; i++) pthread_create(&th[i], NULL, range_merge_worker, NULL);
    for (int i = 0; i < njob; i++) pthread_join(th[i], NULL);
    i64 nr = 0;
    for (int t = 0; t < njob; t++) {
      if (RJ.job[t].n && nr != RJ.job[t].off)
        memmove(RM.runbuf + nr, RM.runbuf + RJ.job[t].off, (size_t)RJ.job[t].n * 8);
      nr += RJ.job[t].n;
    }
    nm = merge_into(master, nm, RM.runbuf, nr);
  }
  pthread_mutex_lock(&TR.mu);
  for (int c = 0; c < RM.npend; c++) TR.freelist[TR.nfree++] = RM.pend[c].a;
  pthread_cond_broadcast(&TR.cv_prod);
  pthread_mutex_unlock(&TR.mu);
  RM.npend = 0; RM.pendrecs = 0;
  return nm;
}

/* adapt post-pass over the deduped layer */
static struct { u64 *m; i64 n; i64 nextblk; int jc; i64 killed; } AP;

static void *adapt_worker(void *arg) {
  AScr *sc = malloc(sizeof(AScr));
  i64 kill = 0;
  i64 backC = (i64)AP.jc * (AP.jc - 1) / 2;
  (void)arg;
  for (;;) {
    i64 b = __sync_fetch_and_add(&AP.nextblk, 1);
    i64 lo = b * BLK, hi = lo + BLK;
    if (lo >= AP.n) break;
    if (hi > AP.n) hi = AP.n;
    for (i64 r = lo; r < hi; r++) {
      u64 S = AP.m[r] >> 16;
      int g = (int)(AP.m[r] & 0xffff);
      u64 cp = FULL & ~S;
      int cost = (int)backC - g + I_of(S);
      double la = adapt_lb(cp, sc);
      int lbA = la > 0 ? (int)(la - 1e-9) + 1 : 0;
      int dl = deg_lb(cp);
      if (lbA < dl) lbA = dl;
      if (cost + lbA > Bbud) { AP.m[r] = TOMB; kill++; }
    }
  }
  free(sc);
  __sync_fetch_and_add(&AP.killed, kill);
  return NULL;
}

/* mmap helper */
static const u64 *map_file(int j, i64 *n) {
  char p[1000]; lay_path(p, j);
  int fd = open(p, O_RDONLY);
  if (fd < 0) { fprintf(stderr, "missing %s\n", p); exit(1); }
  struct stat st; fstat(fd, &st);
  *n = st.st_size / 8;
  const u64 *m = mmap(NULL, st.st_size ? st.st_size : 8, PROT_READ, MAP_SHARED, fd, 0);
  if (m == MAP_FAILED) die("mmap");
  close(fd);
  return m;
}

static void write_layer(int j, const u64 *m, i64 n) {
  char p[1000], pt[1010];
  lay_path(p, j);
  snprintf(pt, sizeof pt, "%s.tmp", p);
  FILE *f = fopen(pt, "wb");
  if (!f) die("layer write");
  if (n && fwrite(m, 8, (size_t)n, f) != (size_t)n) die("layer write short");
  fclose(f);
  if (rename(pt, p)) die("layer rename");
  char line[200];
  snprintf(line, sizeof line, "L %d q %d tau %d n %lld", j, q, tau, (long long)n);
  man_add(line);
}

static void transition(int jpar) {
  double t0 = now_s();
  int jc = jpar + 1;
  i64 npar;
  const u64 *par = map_file(jpar, &npar);
  /* capacity: exact orbit-count ceiling PLUS one full pend batch — merge_into
   * needs transient room for nm + (not-yet-master-deduped) incoming records */
  i64 cap = (i64)burn[jc] + (i64)KMAX * CHUNK + 1024;
  u64 *master = malloc((size_t)cap * 8);
  if (!master) die("master alloc — layer exceeds RAM");
  i64 nm = 0;
  RM.mcap = cap;
  RM.npend = 0; RM.pendrecs = 0;
  RM.runbuf = malloc((size_t)KMAX * CHUNK * 8);
  if (!RM.runbuf) die("runbuf alloc");
  i64 trigger = (i64)(KMAX - 1) * CHUNK;
  TR.par = par; TR.npar = npar; TR.nextblk = 0; TR.jpar = jpar;
  TR.qh = TR.qt = TR.qn = 0; TR.done_workers = 0;
  TR.st_children = TR.st_killpre = TR.st_pushed = 0;
  int nbuf = KMAX + QCAP + NTH + 2;
  TR.freelist = malloc(sizeof(u64 *) * nbuf); TR.nfree = 0;
  for (int i = 0; i < nbuf; i++) TR.freelist[TR.nfree++] = malloc((size_t)CHUNK * 8);
  pthread_mutex_init(&TR.mu, NULL);
  pthread_cond_init(&TR.cv_prod, NULL); pthread_cond_init(&TR.cv_cons, NULL);
  pthread_t th[64];
  for (int i = 0; i < NTH; i++) pthread_create(&th[i], NULL, expand_worker, NULL);
  /* Progress heartbeat: a layer takes tens of minutes, and the per-layer summary below
   * only prints once it is finished. This says how far into the layer we are, on stderr
   * (stdout stays exactly as before). PROGRESS=0 turns it off. */
  const char *pe = getenv("PROGRESS"); int hb_on = !(pe && !strcmp(pe, "0"));
  double hb = now_s();
  for (;;) {
    pthread_mutex_lock(&TR.mu);
    while (TR.qn == 0 && TR.done_workers < NTH) pthread_cond_wait(&TR.cv_cons, &TR.mu);
    if (TR.qn == 0 && TR.done_workers == NTH) { pthread_mutex_unlock(&TR.mu); break; }
    ChunkT c = TR.ring[TR.qh];
    TR.qh = (TR.qh + 1) % QCAP; TR.qn--;
    pthread_cond_broadcast(&TR.cv_prod);   /* wake queue-blocked producers: buffers now park in pend, so the per-chunk return broadcast is gone */
    pthread_mutex_unlock(&TR.mu);
    if (hb_on && now_s() - hb >= 30.0) {
      hb = now_s();
      i64 done = __sync_fetch_and_add(&TR.nextblk, 0) * BLK; if (done > npar) done = npar;
      fprintf(stderr, "  L%02d: %lld/%lld parents dispatched (%.0f%%), %lld merged so far  %.0fs\n",
              jc, (long long)done, (long long)npar, npar ? 100.0 * (double)done / (double)npar : 0.0,
              (long long)nm, now_s() - t0);
      fflush(stderr);
    }
    RM.pend[RM.npend].a = c.a; RM.pend[RM.npend].n = c.n;
    RM.npend++; RM.pendrecs += c.n;
    if (RM.pendrecs >= trigger || RM.npend == KMAX) nm = do_runmerge(master, nm);
  }
  for (int i = 0; i < NTH; i++) pthread_join(th[i], NULL);
  nm = do_runmerge(master, nm);
  free(RM.runbuf);
  for (int i = 0; i < TR.nfree; i++) free(TR.freelist[i]);
  free(TR.freelist);
  if (nm > (i64)burn[jc]) die("layer count exceeds Burnside ceiling — canonicalization bug");
  i64 nadapt = 0;
  if (!NOPRUNE && jc >= ADAPTFROM) {
    AP.m = master; AP.n = nm; AP.nextblk = 0; AP.jc = jc; AP.killed = 0;
    pthread_t ath[64];
    for (int i = 0; i < NTH; i++) pthread_create(&ath[i], NULL, adapt_worker, NULL);
    for (int i = 0; i < NTH; i++) pthread_join(ath[i], NULL);
    i64 w = 0;
    for (i64 r = 0; r < nm; r++) if (master[r] != TOMB) master[w++] = master[r];
    nadapt = AP.killed; nm = w;
  }
  write_layer(jc, master, nm);
  munmap((void *)par, (size_t)(npar ? npar : 1) * 8);
  printf("L%02d: parents %lld children %lld killpre %lld pushed %lld killadapt %lld -> %lld reps (burn %llu)  %.1fs\n",
         jc, (long long)npar, (long long)TR.st_children, (long long)TR.st_killpre,
         (long long)TR.st_pushed, (long long)nadapt, (long long)nm, (unsigned long long)burn[jc], now_s() - t0);
  if (NOPRUNE && nm != (i64)burn[jc]) die("unpruned layer count != Burnside — canonicalization bug");
  fflush(stdout);
}

static void mode_layers(void) {
  printf("dp43 layers: q=%d C=%d |Aut|=%d h=%d tau=%d B=%d threads=%d chunk=%lldrec degfrom=%d adaptfrom=%d noprune=%d\n",
         q, C, NAUT, h, tau, Bbud, NTH, (long long)CHUNK, DEGFROM, ADAPTFROM, NOPRUNE);
  double bytes = 0;
  for (int k = 0; k <= h + 1; k++) bytes += (double)burn[k] * 8;
  printf("burnside ceilings: peak layer %llu reps (%.2f GB), all layers %.2f GB\n",
         (unsigned long long)burn[h], (double)burn[h] * 8 / 1e9, bytes / 1e9);
  fflush(stdout);
  if (man_layer(0) < 0) {
    u64 z = 0;
    write_layer(0, &z, 1);
  }
  for (int j = 0; j <= h; j++) {
    i64 have = man_layer(j + 1);
    if (have >= 0) {
      char p[1000]; lay_path(p, j + 1);
      struct stat st;
      if (!stat(p, &st) && st.st_size == have * 8) { printf("L%02d: resume, %lld reps\n", j + 1, (long long)have); continue; }
    }
    transition(j);
  }
  printf("layers complete: 0..%d\n", h + 1);
}

/* ---------- join ---------------------------------------------------------- */
typedef struct { u64 k22, sv; } Pair;      /* sv = (Skey<<16)|base */
#define NBUCK 8

static void radix_pair(Pair *a, Pair *tmp, i64 n) {
  for (int pass = 0; pass < 8; pass++) {
    i64 cnt[256] = {0};
    int sh = pass * 8;
    for (i64 i = 0; i < n; i++) cnt[(a[i].k22 >> sh) & 255]++;
    i64 s = 0;
    for (int b = 0; b < 256; b++) { i64 c = cnt[b]; cnt[b] = s; s += c; }
    for (i64 i = 0; i < n; i++) tmp[cnt[(a[i].k22 >> sh) & 255]++] = a[i];
    Pair *t = a; a = tmp; tmp = t;
  }
}

static struct {
  const u64 *lh; i64 nlh; i64 nextblk;
  FILE *bf[NBUCK]; pthread_mutex_t bmu[NBUCK];
} JN;

static void *join_worker(void *arg) {
  i64 bn[NBUCK] = {0};
  Pair *bb[NBUCK];
  const i64 BCAP = 1 << 16;
  for (int b = 0; b < NBUCK; b++) bb[b] = malloc(sizeof(Pair) * BCAP);
  (void)arg;
  for (;;) {
    i64 blk = __sync_fetch_and_add(&JN.nextblk, 1);
    i64 lo = blk * BLK, hi = lo + BLK;
    if (lo >= JN.nlh) break;
    if (hi > JN.nlh) hi = JN.nlh;
    for (i64 r = lo; r < hi; r++) {
      u64 rec = JN.lh[r], S = rec >> 16;
      int g = (int)(rec & 0xffff);
      int cross = h * (q - h) - I_of(S);
      u64 k22 = canon(negset(FULL & ~S));
      /* HASH bucketing: canonical (min-lex) keys are skewed toward small
       * values, so top-bit buckets would put ~everything in bucket 0.
       * Per-bucket pairs stay globally sorted by k22 after radix, so the
       * two-pointer join per bucket just rescans F (sequential mmap). */
      int b = (int)((k22 * 0x9E3779B97F4A7C15ULL) >> 61) & (NBUCK - 1);
      bb[b][bn[b]].k22 = k22;
      bb[b][bn[b]].sv = (S << 16) | (u64)(g + cross);
      if (++bn[b] == BCAP) {
        pthread_mutex_lock(&JN.bmu[b]);
        fwrite(bb[b], sizeof(Pair), (size_t)bn[b], JN.bf[b]);
        pthread_mutex_unlock(&JN.bmu[b]);
        bn[b] = 0;
      }
    }
  }
  for (int b = 0; b < NBUCK; b++) {
    if (bn[b]) {
      pthread_mutex_lock(&JN.bmu[b]);
      fwrite(bb[b], sizeof(Pair), (size_t)bn[b], JN.bf[b]);
      pthread_mutex_unlock(&JN.bmu[b]);
    }
    free(bb[b]);
  }
  return NULL;
}

typedef struct { u64 skey, k22; int base, gF; } Hit;

static void mode_join(void) {
  for (int j = 0; j <= h + 1; j++) if (man_layer(j) < 0) die("join: layers incomplete (manifest)");
  double t0 = now_s();
  i64 nf;
  const u64 *F = map_file(h + 1, &nf);
  JN.lh = map_file(h, &JN.nlh);
  JN.nextblk = 0;
  char bp[NBUCK][1000];
  for (int b = 0; b < NBUCK; b++) {
    snprintf(bp[b], 1000, "%s/jbucket%d.bin", DIR, b);
    JN.bf[b] = fopen(bp[b], "wb");
    if (!JN.bf[b]) die("bucket open");
    pthread_mutex_init(&JN.bmu[b], NULL);
  }
  pthread_t th[64];
  for (int i = 0; i < NTH; i++) pthread_create(&th[i], NULL, join_worker, NULL);
  for (int i = 0; i < NTH; i++) pthread_join(th[i], NULL);
  for (int b = 0; b < NBUCK; b++) fclose(JN.bf[b]);
  /* per-bucket: sort, merge-join vs F */
  char hp[1000];
  snprintf(hp, 1000, "%s/hits.bin", DIR);
  FILE *hf = fopen(hp, "wb");
  if (!hf) die("hits open");
  i64 maxtot = -1, nhits = 0, npairs = 0;
  for (int b = 0; b < NBUCK; b++) {
    struct stat st;
    if (stat(bp[b], &st)) die("bucket stat");
    i64 n = st.st_size / (i64)sizeof(Pair);
    npairs += n;
    if (!n) { unlink(bp[b]); continue; }
    Pair *A = malloc((size_t)n * sizeof(Pair)), *T = malloc((size_t)n * sizeof(Pair));
    FILE *f = fopen(bp[b], "rb");
    if (fread(A, sizeof(Pair), (size_t)n, f) != (size_t)n) die("bucket read");
    fclose(f);
    radix_pair(A, T, n);
    free(T);
    i64 fi = 0;
    for (i64 i = 0; i < n; i++) {
      u64 k = A[i].k22;
      while (fi < nf && (F[fi] >> 16) < k) fi++;
      if (fi >= nf) break;
      if ((F[fi] >> 16) != k) continue;
      int gF = (int)(F[fi] & 0xffff);
      int base = (int)(A[i].sv & 0xffff);
      i64 tot = base + gF;
      if (tot > maxtot) maxtot = tot;
      if (tot >= tau) {
        Hit ht = { A[i].sv >> 16, k, base, gF };
        fwrite(&ht, sizeof ht, 1, hf);
        nhits++;
      }
    }
    free(A);
    unlink(bp[b]);
  }
  fclose(hf);
  printf("join: %lld splits, maxtot=%lld (tau=%d) -> %lld hits  %.1fs\n",
         (long long)npairs, (long long)maxtot, tau, (long long)nhits, now_s() - t0);
  if (maxtot < tau) printf("join: EMPTY SHELL — no order reaches fwd >= %d; certified MAS <= %lld\n", tau, (long long)maxtot);
  else printf("join: certified MAS = %lld (max over alive splits; sound both ways on completion)\n", (long long)maxtot);
  char line[200];
  snprintf(line, sizeof line, "J tau %d v1 %lld v2 %lld", tau, (long long)maxtot, (long long)nhits);
  man_add(line);
  fflush(stdout);
}

/* ---------- enumeration --------------------------------------------------- */
static struct { const u64 *p; i64 n; } LAY[MAXQ];

static int lkup(int lay, u64 key) {
  const u64 *A = LAY[lay].p;
  i64 lo = 0, hi = LAY[lay].n;
  while (lo < hi) { i64 mid = (lo + hi) >> 1; if ((A[mid] >> 16) < key) lo = mid + 1; else hi = mid; }
  if (lo < LAY[lay].n && (A[lo] >> 16) == key) return (int)(A[lo] & 0xffff);
  return -1;
}

typedef struct { u8 *seq; int *fwd; i64 n, cap; int len; i64 *hist; int minf, maxf; } OrdL;

static void ol_init(OrdL *o, int len) { o->len = len; o->n = 0; o->cap = 1024; o->seq = malloc((size_t)o->cap * len); o->fwd = malloc(sizeof(int) * o->cap); o->hist = NULL; }
static void ol_free(OrdL *o) { free(o->seq); free(o->fwd); }

static u8 eo_seq[MAXQ];
static void eo_rec(u64 X, int req, int sz, int suffix, int facc, OrdL *out) {
  if (!X) {
    if (facc < 0) die("enum: negative fwd");
    if (out->hist) {                       /* counting mode: histogram only */
      out->hist[facc]++; out->n++;
      if (facc < out->minf) out->minf = facc;
      if (facc > out->maxf) out->maxf = facc;
      return;
    }
    if (out->n == out->cap) {
      out->cap *= 2;
      out->seq = realloc(out->seq, (size_t)out->cap * out->len);
      out->fwd = realloc(out->fwd, sizeof(int) * out->cap);
      if (!out->seq || !out->fwd) die("enum list realloc");
    }
    memcpy(out->seq + out->n * out->len, eo_seq, (size_t)out->len);
    out->fwd[out->n++] = facc;
    return;
  }
  u64 x = X;
  while (x) {
    int v = __builtin_ctzll(x); x &= x - 1;
    u64 Xp = X & ~(1ULL << v);
    int gain = __builtin_popcountll(fullIn[v] & Xp);
    int r2 = req - gain;
    int gt = lkup(sz - 1, suffix ? canon(negset(Xp)) : canon(Xp));
    if (gt < 0 || gt < r2) continue;       /* missing = certified dead; g~ < need = can't reach */
    eo_seq[sz - 1] = (u8)v;
    eo_rec(Xp, r2, sz - 1, suffix, facc + gain, out);
  }
}

static int fwd_of(const u8 *ord, int n) {
  int f = 0;
  for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) f += adjm[ord[i]][ord[j]];
  return f;
}

static void mode_enum(void) {
  long long maxtot, nhits;
  if (!man_flag("J", &maxtot, &nhits)) die("enum: join not recorded in manifest");
  double t0 = now_s();
  for (int j = 0; j <= h; j++) LAY[j].p = map_file(j, &LAY[j].n);
  char hp[1000], rp[1000];
  snprintf(hp, 1000, "%s/hits.bin", DIR);
  snprintf(rp, 1000, "%s/pool_raw.txt", DIR);
  FILE *hf = fopen(hp, "rb");
  if (!hf) die("hits.bin missing");
  int countonly = getenv("COUNTONLY") && atoi(getenv("COUNTONLY"));
  FILE *rf = NULL;
  if (!countonly) { rf = fopen(rp, "w"); if (!rf) die("pool_raw open"); }
  Hit ht;
  i64 nord = 0, nh = 0;
  i64 census[64] = {0};
  i64 *hP = NULL, *hQ = NULL;
  OrdL P, Q;
  ol_init(&P, h); ol_init(&Q, q - h);
  if (countonly) { hP = calloc(1024, 8); hQ = calloc(1024, 8); }
  while (fread(&ht, sizeof ht, 1, hf) == 1) {
    nh++;
    u64 S = ht.skey, T = FULL & ~S;
    int cross = h * (q - h) - I_of(S);
    int gS = lkup(h, S);
    if (gS < 0 || ht.base != gS + cross) die("enum: hit/base mismatch");
    P.n = Q.n = 0;
    if (countonly) {
      memset(hP, 0, 1024 * 8); memset(hQ, 0, 1024 * 8);
      P.hist = hP; Q.hist = hQ;
      P.minf = Q.minf = 1023; P.maxf = Q.maxf = 0;
    }
    eo_rec(S, tau - cross - ht.gF, h, 0, 0, &P);
    eo_rec(T, tau - cross - gS, q - h, 1, 0, &Q);
    if (countonly) {
      /* raw-order count by slack = convolution of the two fwd histograms */
      for (int a = P.minf; a <= P.maxf; a++) if (hP[a])
        for (int b = Q.minf; b <= Q.maxf; b++) if (hQ[b]) {
          int tot = a + b + cross;
          if (tot >= tau) { census[tot - tau < 63 ? tot - tau : 63] += hP[a] * hQ[b]; nord += hP[a] * hQ[b]; }
        }
      continue;
    }
    for (i64 a = 0; a < P.n; a++) for (i64 b = 0; b < Q.n; b++) {
      if (P.fwd[a] + Q.fwd[b] + cross < tau) continue;
      u8 o[MAXQ];
      memcpy(o, P.seq + a * P.len, (size_t)P.len);
      memcpy(o + P.len, Q.seq + b * Q.len, (size_t)Q.len);
      int f = fwd_of(o, q);
      if (f != P.fwd[a] + Q.fwd[b] + cross || f < tau) die("enum: fwd verification failed");
      for (int t = 0; t < q; t++) fprintf(rf, "%d%c", o[t], t == q - 1 ? '\n' : ' ');
      nord++;
      census[f - tau < 63 ? f - tau : 63]++;
    }
  }
  fclose(hf);
  if (rf) fclose(rf);
  ol_free(&P); ol_free(&Q);
  free(hP); free(hQ);
  printf("enum%s: %lld hits -> %lld raw orders (up-to-Aut)  %.1fs\n",
         countonly ? " [COUNT-ONLY]" : "", (long long)nh, (long long)nord, now_s() - t0);
  printf("raw census by fwd-tau slack:");
  for (int d = 0; d < 64; d++) if (census[d]) printf("  +%d:%lld", d, (long long)census[d]);
  printf("\n");
  if (!countonly) {
    char line[200];
    snprintf(line, sizeof line, "E tau %d v1 %lld v2 0", tau, (long long)nord);
    man_add(line);
  }
  for (int j = 0; j <= h; j++) munmap((void *)LAY[j].p, (size_t)(LAY[j].n ? LAY[j].n : 1) * 8);
  fflush(stdout);
}

/* ---------- closure ------------------------------------------------------- */
static int cmp_rows_q(const void *a, const void *b) { return memcmp(a, b, (size_t)q); }

static void mode_close(void) {
  long long nraw_m;
  if (!man_flag("E", &nraw_m, NULL)) die("close: enum not recorded in manifest");
  double t0 = now_s();
  char rp[1000], pp[1000];
  snprintf(rp, 1000, "%s/pool_raw.txt", DIR);
  snprintf(pp, 1000, "%s/pool.txt", DIR);
  FILE *rf = fopen(rp, "r");
  if (!rf) die("pool_raw missing");
  i64 cap = 1 << 16, N = 0;
  u8 *raw = malloc((size_t)cap * q);
  for (;;) {
    int v, t = 0, ok = 1;
    for (t = 0; t < q; t++) { if (fscanf(rf, "%d", &v) != 1) { ok = 0; break; } raw[N * q + t] = (u8)v; }
    if (!ok) break;
    if (++N == cap) { cap *= 2; raw = realloc(raw, (size_t)cap * q); if (!raw) die("raw realloc"); }
  }
  fclose(rf);
  if (N != nraw_m) die("close: raw count != manifest");
  /* per-order canonical orbit rep = lexmin image over the NAUT maps */
  u8 *reps = malloc((size_t)N * q);
  for (i64 r = 0; r < N; r++) {
    const u8 *o = raw + r * q;
    u8 best[MAXQ], img[MAXQ];
    memset(best, 0xff, (size_t)q);
    for (int ai = 0; ai < NQR; ai++) for (int b = 0; b < q; b++) {
      long a = qrl[ai];
      for (int t = 0; t < q; t++) img[t] = (u8)((a * o[t] + b) % q);
      if (memcmp(img, best, (size_t)q) < 0) memcpy(best, img, (size_t)q);
    }
    memcpy(reps + r * q, best, (size_t)q);
  }
  qsort(reps, (size_t)N, (size_t)q, cmp_rows_q);
  i64 R = N ? 1 : 0;
  for (i64 r = 1; r < N; r++)
    if (memcmp(reps + r * q, reps + (R - 1) * q, (size_t)q)) memcpy(reps + R++ * q, reps + r * q, (size_t)q);
  /* expand each orbit, dedup stabilizer copies, write + census */
  FILE *pf = fopen(pp, "w");
  if (!pf) die("pool open");
  u8 *orb = malloc((size_t)NAUT * q);
  i64 total = 0;
  i64 census[64] = {0};
  i64 sizehist_full = 0;
  int mind = 64;
  for (i64 r = 0; r < R; r++) {
    const u8 *o = reps + r * q;
    int m = 0;
    for (int ai = 0; ai < NQR; ai++) for (int b = 0; b < q; b++) {
      long a = qrl[ai];
      for (int t = 0; t < q; t++) orb[m * q + t] = (u8)((a * o[t] + b) % q);
      m++;
    }
    qsort(orb, (size_t)m, (size_t)q, cmp_rows_q);
    int u = 1;
    for (int i = 1; i < m; i++)
      if (memcmp(orb + i * q, orb + (u - 1) * q, (size_t)q)) memcpy(orb + u++ * q, orb + i * q, (size_t)q);
    if (NAUT % u) die("close: orbit size does not divide |Aut|");
    if (u == NAUT) sizehist_full++;
    int f = fwd_of(o, q);
    if (f < tau) die("close: sub-threshold order in pool");
    census[f - tau < 63 ? f - tau : 63] += u;
    if (f - tau < mind) mind = f - tau;
    for (int i = 0; i < u; i++) {
      for (int t = 0; t < q; t++) fprintf(pf, "%d%c", orb[i * q + t], t == q - 1 ? '\n' : ' ');
    }
    total += u;
  }
  fclose(pf);
  printf("close: %lld raw -> %lld orbits -> %lld orders (Aut-closed; %lld/%lld orbits full-size %d)\n",
         (long long)N, (long long)R, (long long)total, (long long)sizehist_full, (long long)R, NAUT);
  printf("census by fwd-tau slack:");
  for (int d = 0; d < 64; d++) if (census[d]) printf("  +%d:%lld", d, (long long)census[d]);
  printf("\n");
  char line[200];
  snprintf(line, sizeof line, "C tau %d v1 %lld v2 %lld", tau, (long long)total, (long long)R);
  man_add(line);
  printf("pool: %s  (closed=TRUE for build_orbits.R)  %.1fs\n", pp, now_s() - t0);
  free(raw); free(reps); free(orb);
  fflush(stdout);
}

/* ---------- selftest (q <= 11) -------------------------------------------- */
static u64 st_rng = 0x243F6A8885A308D3ULL;
static u64 st_rand(void) { st_rng ^= st_rng << 13; st_rng ^= st_rng >> 7; st_rng ^= st_rng << 17; return st_rng; }

static i64 bf_n;                            /* brute-force pool rows (sorted later) */
static u8 *bf_rows;
static int bf_tau;
static u8 bf_seq[MAXQ];
static int bf_MAS;

static void bf_rec(u64 used, int depth, int facc) {
  if (depth == q) {
    if (facc > bf_MAS) bf_MAS = facc;
    if (facc >= bf_tau) {
      memcpy(bf_rows + bf_n * q, bf_seq, (size_t)q);
      bf_n++;
    }
    return;
  }
  for (int v = 0; v < q; v++) if (!(used >> v & 1)) {
    bf_seq[depth] = (u8)v;
    bf_rec(used | (1ULL << v), depth + 1, facc + __builtin_popcountll(fullIn[v] & used));
  }
}

static i64 read_pool_sorted(const char *path, u8 **rows) {
  FILE *f = fopen(path, "r");
  if (!f) die("selftest: pool file missing");
  i64 cap = 1 << 16, n = 0;
  u8 *a = malloc((size_t)cap * q);
  for (;;) {
    int v, ok = 1;
    for (int t = 0; t < q; t++) { if (fscanf(f, "%d", &v) != 1) { ok = 0; break; } a[n * q + t] = (u8)v; }
    if (!ok) break;
    if (++n == cap) { cap *= 2; a = realloc(a, (size_t)cap * q); }
  }
  fclose(f);
  qsort(a, (size_t)n, (size_t)q, cmp_rows_q);
  *rows = a;
  return n;
}

static void run_pipeline(void);             /* fwd decl */

static void mode_selftest(const char *base) {
  if (q > 11) die("selftest needs q <= 11");
  /* 1. canon: fast == slow, Aut-invariant, idempotent */
  for (int it = 0; it < 20000; it++) {
    u64 S = st_rand() & FULL;
    u64 c = canon(S);
    if (c != canon_slow(S)) die("canon fast != slow");
    if (canon(c) != c) die("canon not idempotent");
    int ai = (int)(st_rand() % (u64)NQR), b = (int)(st_rand() % (u64)q);
    u64 img = 0, x = S;
    while (x) { int v = __builtin_ctzll(x); x &= x - 1; img |= 1ULL << ((qrl[ai] * v + b) % q); }
    if (canon(img) != c) die("canon not Aut-invariant");
  }
  printf("selftest: canon fast==slow, idempotent, Aut-invariant on 20000 random sets OK\n");
  /* 2/3. brute-force pools at several tau; engine (pruned + unpruned) must match */
  bf_rows = malloc((size_t)40000000 * q);   /* 11! = 39.9M rows worst case */
  for (int dd = 0; dd <= 3; dd += 3) {
    /* discover MAS with a cheap pass first */
    bf_tau = 1 << 30; bf_n = 0; bf_MAS = 0;
    bf_rec(0, 0, 0);
    int MAS = bf_MAS;
    bf_tau = MAS - dd; bf_n = 0; bf_MAS = 0;
    bf_rec(0, 0, 0);
    qsort(bf_rows, (size_t)bf_n, (size_t)q, cmp_rows_q);
    for (int noprune = 0; noprune <= 1; noprune++) {
      char d[900];
      snprintf(d, sizeof d, "%s/st_q%d_t%d_p%d", base, q, MAS - dd, noprune);
      char cmd[1000];
      snprintf(cmd, sizeof cmd, "mkdir -p %s", d);
      if (system(cmd)) die("mkdir");
      strcpy(DIR, d);
      tau = MAS - dd; Bbud = C - tau;
      NOPRUNE = noprune;
      run_pipeline();
      char pp[1000];
      snprintf(pp, 1000, "%s/pool.txt", DIR);
      u8 *rows;
      i64 n = read_pool_sorted(pp, &rows);
      if (n != bf_n) { fprintf(stderr, "pool %lld vs brute %lld\n", (long long)n, (long long)bf_n); die("selftest: pool size mismatch"); }
      if (memcmp(rows, bf_rows, (size_t)n * q)) die("selftest: pool content mismatch");
      free(rows);
      printf("selftest: q=%d tau=%d (delta=%d) noprune=%d pool == brute force (%lld orders) OK\n",
             q, MAS - dd, dd, noprune, (long long)bf_n);
    }
  }
  free(bf_rows);
  printf("selftest q=%d PASSED\n", q);
}

/* ---------- driver -------------------------------------------------------- */
static void run_pipeline(void) {
  mode_layers();
  mode_join();
  mode_enum();
  mode_close();
}

int main(int argc, char **argv) {
  if (argc < 3) {
    fprintf(stderr, "usage: dp43 burnside q | dp43 selftest q dir | dp43 layers|join|enum|close|all q tau dir\n");
    return 1;
  }
  setup(atoi(argv[2]));
  if (getenv("THREADS")) NTH = atoi(getenv("THREADS"));
  if (NTH < 1) NTH = 1;
  if (NTH > 40) NTH = 40;  /* laptop rule: never pass THREADS>10 locally; 40 = JZ node */
  if (getenv("DEGFROM")) DEGFROM = atoi(getenv("DEGFROM"));
  if (getenv("ADAPTFROM")) ADAPTFROM = atoi(getenv("ADAPTFROM"));
  if (getenv("ROUNDS")) ROUNDS = atoi(getenv("ROUNDS"));
  if (getenv("NOPRUNE")) NOPRUNE = atoi(getenv("NOPRUNE"));
  if (getenv("RAMGB")) RAMGB = atof(getenv("RAMGB"));
  i64 chunkmb = getenv("CHUNKMB") ? atol(getenv("CHUNKMB")) : 16;
  CHUNK = chunkmb * 131072;                 /* records per chunk */
  if (!strcmp(argv[1], "burnside")) {
    double bytes = 0;
    for (int k = 0; k <= h + 1; k++) {
      printf("layer %2d: %llu orbit reps  (%.3f GB)\n", k, (unsigned long long)burn[k], (double)burn[k] * 8 / 1e9);
      bytes += (double)burn[k] * 8;
    }
    printf("total layers 0..%d: %.2f GB on disk; peak RAM ~ %.2f GB master\n", h + 1, bytes / 1e9, (double)burn[h] * 8 / 1e9);
    return 0;
  }
  if (!strcmp(argv[1], "selftest")) {
    if (argc < 4) die("selftest needs dir");
    mode_selftest(argv[3]);
    return 0;
  }
  if (argc < 5) die("need: mode q tau dir");
  tau = atoi(argv[3]);
  Bbud = C - tau;
  strncpy(DIR, argv[4], sizeof DIR - 1);
  relax_tau = strcmp(argv[1], "layers") && strcmp(argv[1], "all");
  if (!strcmp(argv[1], "layers")) mode_layers();
  else if (!strcmp(argv[1], "join")) mode_join();
  else if (!strcmp(argv[1], "enum")) mode_enum();
  else if (!strcmp(argv[1], "close")) mode_close();
  else if (!strcmp(argv[1], "all")) run_pipeline();
  else die("unknown mode");
  return 0;
}
