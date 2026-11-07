/* verify_d0.c — independent re-derivation of the Paley(43) level-0 facts of
 * PALEY43_NONREALIZABLE.md Appendix A.1/A.2, from the single committed input
 * paley43/d0_reps.txt (the delta = 0 orbit representatives).
 *
 * Written for the reproduction: it shares no code with dp43.c / canon_reps.c /
 * razor_screen.c. It rebuilds Paley(43) from quadratic residues and checks:
 *
 *   A. structure   — tournament, out-regular 21, doubly regular (11 triangles/arc),
 *                    C = 903 arcs, T = 3311 cyclic triangles
 *   B. group       — G = {x -> ax+b : a in QR, b in Z_43} has order 903 and every
 *                    element is an arc-preserving automorphism
 *   C. seed        — every rep is a permutation of Z_43 with fwd = 543 exactly
 *   D. orbits      — every rep has trivial G-stabiliser (orbit size exactly 903) and
 *                    all reps lie in pairwise distinct orbits, compared by the lexmin
 *                    image computed here. (The committed seed stores an arbitrary
 *                    representative per orbit, not the canonical one, so canonicity is
 *                    derived rather than assumed — razor_screen re-expands each rep over
 *                    the whole group anyway, so the file needs no canonical form.)
 *   E. arithmetic  — MAS >= 543, alpha* >= 543/903 = 181/301 > 3/5, slack
 *                    5*MAS - 3C = 6, forced top-two level floor(6/4) = 1
 *
 * Usage: verify_d0 <d0_reps.txt> [threads]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>

typedef uint8_t u8;
#define Q 43
#define C 903

static int isqr[Q], qrl[Q], NQR, NAUT;
static int amap[1024][2];
static u8 adj[Q][Q];                  /* adj[u][v] = 1 iff u -> v */
static u8 *reps;                      /* [N][Q] the seed as read */
static u8 *canon;                     /* [N][Q] lexmin image of each rep, computed here */
static long N;
static int fail = 0;

static void chk(int ok, const char *what) {
  printf("  %-58s %s\n", what, ok ? "OK" : "*** FAILED ***");
  if (!ok) fail = 1;
}

/* ---- per-rep worker: fwd count, stabiliser size, lexmin image ---- */
typedef struct { long lo, hi; long nbad_fwd, nbad_orb, n_is_lexmin; } Arg;

static int cmp43(const void *a, const void *b) { return memcmp(a, b, Q); }

static void *worker(void *vp) {
  Arg *A = vp;
  A->nbad_fwd = A->nbad_orb = A->n_is_lexmin = 0;
  u8 *imgs = malloc((size_t)NAUT * Q);
  int pos[Q];
  for (long r = A->lo; r < A->hi; r++) {
    const u8 *o = reps + (size_t)r * Q;
    for (int t = 0; t < Q; t++) pos[o[t]] = t;
    /* C: forward-arc count */
    int fwd = 0;
    for (int u = 0; u < Q; u++)
      for (int v = 0; v < Q; v++)
        if (adj[u][v] && pos[u] < pos[v]) fwd++;
    if (fwd != 543) A->nbad_fwd++;
    /* D: orbit under G — all NAUT images, then dedup */
    for (int m = 0; m < NAUT; m++) {
      int a = amap[m][0], b = amap[m][1];
      u8 *img = imgs + (size_t)m * Q;
      for (int t = 0; t < Q; t++) img[t] = (u8)((a * o[t] + b) % Q);
    }
    qsort(imgs, (size_t)NAUT, Q, cmp43);
    long distinct = 1;
    for (int m = 1; m < NAUT; m++)
      if (memcmp(imgs + (size_t)m * Q, imgs + (size_t)(m - 1) * Q, Q)) distinct++;
    if (distinct != NAUT) A->nbad_orb++;          /* stabiliser must be trivial */
    memcpy(canon + (size_t)r * Q, imgs, Q);       /* imgs[0] = lexmin image of this orbit */
    if (!memcmp(imgs, o, Q)) A->n_is_lexmin++;    /* informational: is the seed canonical? */
  }
  free(imgs);
  return NULL;
}

int main(int argc, char **argv) {
  if (argc < 2) { fprintf(stderr, "usage: %s d0_reps.txt [threads]\n", argv[0]); return 1; }
  int NTH = argc > 2 ? atoi(argv[2]) : 8;
  if (NTH < 1) NTH = 1; if (NTH > 10) NTH = 10;   /* laptop rule */

  printf("== A. Paley(43) structure (rebuilt from quadratic residues) ==\n");
  for (int x = 1; x < Q; x++) isqr[(x * x) % Q] = 1;
  NQR = 0;
  for (int s = 1; s < Q; s++) if (isqr[s]) qrl[NQR++] = s;
  for (int u = 0; u < Q; u++)
    for (int v = 0; v < Q; v++)
      if (u != v) adj[u][v] = (u8)isqr[((v - u) % Q + Q) % Q];

  int tourn = 1, arcs = 0, minout = Q, maxout = 0;
  for (int u = 0; u < Q; u++) {
    int outd = 0;
    for (int v = 0; v < Q; v++) {
      if (u == v) { if (adj[u][v]) tourn = 0; continue; }
      if (adj[u][v] + adj[v][u] != 1) tourn = 0;
      if (adj[u][v]) { outd++; arcs++; }
    }
    if (outd < minout) minout = outd;
    if (outd > maxout) maxout = outd;
  }
  chk(NQR == 21, "quadratic residues |QR| = 21");
  chk(tourn, "is a tournament (exactly one of u->v, v->u)");
  chk(arcs == C, "arc count C = 903");
  chk(minout == 21 && maxout == 21, "out-regular of degree 21");

  /* cyclic triangles, and triangles per arc (double regularity) */
  long tri = 0; int mintpa = 1 << 30, maxtpa = 0;
  for (int u = 0; u < Q; u++)
    for (int v = 0; v < Q; v++) {
      if (!adj[u][v]) continue;
      int tpa = 0;
      for (int w = 0; w < Q; w++) if (adj[v][w] && adj[w][u]) tpa++;
      tri += tpa;
      if (tpa < mintpa) mintpa = tpa;
      if (tpa > maxtpa) maxtpa = tpa;
    }
  tri /= 3;                                       /* each 3-cycle counted once per arc */
  chk(tri == 3311, "cyclic triangles T = 3311");
  chk(mintpa == 11 && maxtpa == 11, "doubly regular: 11 cyclic triangles per arc");

  printf("== B. automorphism group G = {x -> ax+b, a in QR} ==\n");
  NAUT = NQR * Q;
  { int m = 0;
    for (int i = 0; i < NQR; i++) for (int b = 0; b < Q; b++) { amap[m][0] = qrl[i]; amap[m][1] = b; m++; } }
  chk(NAUT == 903, "|G| = q(q-1)/2 = 903");
  int allauto = 1;
  for (int m = 0; m < NAUT && allauto; m++) {
    int a = amap[m][0], b = amap[m][1];
    for (int u = 0; u < Q && allauto; u++)
      for (int v = 0; v < Q; v++) {
        if (u == v) continue;
        int su = (a * u + b) % Q, sv = (a * v + b) % Q;
        if (adj[u][v] != adj[su][sv]) { allauto = 0; break; }
      }
  }
  chk(allauto, "every element of G preserves all 903 arcs");

  printf("== C/D. the committed delta=0 seed (%s) ==\n", argv[1]);
  FILE *f = fopen(argv[1], "r");
  if (!f) { perror("open"); return 1; }
  long cap = 1 << 15; reps = malloc((size_t)cap * Q); N = 0;
  for (;;) {
    int v, ok = 1, seen[Q] = {0}, isperm = 1;
    for (int t = 0; t < Q; t++) {
      if (fscanf(f, "%d", &v) != 1) { ok = 0; break; }
      if (v < 0 || v >= Q || seen[v]) isperm = 0; else seen[v] = 1;
      reps[(size_t)N * Q + t] = (u8)v;
    }
    if (!ok) break;
    if (!isperm) { printf("  line %ld is not a permutation of Z_43\n", N + 1); fail = 1; }
    if (++N == cap) { cap *= 2; reps = realloc(reps, (size_t)cap * Q); }
  }
  fclose(f);
  chk(N == 19651, "delta=0 orbit representatives read = 19,651");

  canon = malloc((size_t)N * Q);
  pthread_t th[10]; Arg ar[10];
  for (int i = 0; i < NTH; i++) {
    ar[i].lo = N * (long)i / NTH; ar[i].hi = N * (long)(i + 1) / NTH;
    pthread_create(&th[i], NULL, worker, &ar[i]);
  }
  long bf = 0, bo = 0, nlex = 0;
  for (int i = 0; i < NTH; i++) { pthread_join(th[i], NULL); bf += ar[i].nbad_fwd; bo += ar[i].nbad_orb; nlex += ar[i].n_is_lexmin; }
  printf("  reps with fwd != 543: %ld ; nontrivial stabiliser: %ld\n", bf, bo);
  chk(bf == 0, "all 19,651 reps have fwd = 543 exactly");
  chk(bo == 0, "all reps have trivial G-stabiliser (orbit = 903 orders)");
  printf("  (informational) reps that happen to be their orbit's lexmin: %ld/%ld\n", nlex, N);

  /* distinct orbits: the lexmin images computed above must be pairwise distinct */
  qsort(canon, (size_t)N, Q, cmp43);
  long distinct = N ? 1 : 0;
  for (long r = 1; r < N; r++) if (memcmp(canon + (size_t)r * Q, canon + (size_t)(r - 1) * Q, Q)) distinct++;
  printf("  distinct orbit canonical forms: %ld\n", distinct);
  chk(distinct == N, "all reps lie in pairwise distinct G-orbits (by lexmin image)");

  printf("== E. what the seed implies ==\n");
  long orders = N * (long)NAUT;
  printf("  level-0 orbits           %ld\n", N);
  printf("  level-0 orders           %ld  (= %ld x %d)\n", orders, N, NAUT);
  chk(orders == 17744853, "level-0 order count = 17,744,853 (Appendix A.2)");
  printf("  MAS(Paley43)            >= 543\n");
  printf("  alpha* = MAS/C          >= 543/903 = 181/301 = %.9f  (3/5 = %.9f)\n", 543.0 / 903.0, 0.6);
  chk(543 * 5 > 3 * C, "alpha* > 3/5, so the density test does NOT rule Paley(43) out");
  printf("  slack 5*MAS - 3C         = %d\n", 5 * 543 - 3 * C);
  chk(5 * 543 - 3 * C == 6, "realization slack = 6");
  printf("  forced top-two level     = floor(6/4) = %d\n", (5 * 543 - 3 * C) / 4);
  chk((5 * 543 - 3 * C) / 4 == 1, "the two highest-agreement voters are forced to level <= 1");

  printf("\n%s\n", fail ? "verify_d0: FAILED" : "verify_d0: ALL CHECKS PASSED");
  return fail;
}
