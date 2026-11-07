/* verify_ginv.c — independent check of the ONE property the screen's factor-903
 * automorphism reduction rests on (PALEY43_NONREALIZABLE.md §6.2), plus the triangle
 * orbit structure quoted in Appendix A.4.
 *
 * Theorem (§6.2). For every sigma in G and all orders O1, O2,
 *     |DB(sigma O1) ∩ DB(sigma O2)| = |DB(O1) ∩ DB(O2)|.
 * It is proved in the paper; Appendix A.4 says it was additionally cross-checked
 * exhaustively over all 903 sigma. This program does that check from scratch:
 *
 *   1. rebuild Paley(43) and enumerate its 3311 cyclic triangles
 *   2. build G = {x -> ax+b : a in QR}, |G| = 903, and its action on triangles
 *   3. orbits of that action    — paper: 5 orbits, sizes 903, 903, 903, 301, 301,
 *                                 and 602 triangles with a nontrivial stabiliser
 *   4. for every sigma in G and every pair from a sample of real level-0 orders,
 *      recompute both overlaps and compare  — paper: no violation
 *
 * Usage: verify_ginv <d0_reps.txt> [n_orders_to_sample]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef uint8_t u8;
#define Q 43
#define NT 3311

static int isqr[Q], qrl[Q], NQR, NAUT;
static int amap[1024][2];
static u8 adj[Q][Q];
static int tri[NT][3];                 /* the three vertices of each cyclic triangle */
static int tidx[Q][Q][Q];              /* sorted vertex triple -> triangle index, -1 if none */
static int ntri;
static int fail = 0;

static void chk(int ok, const char *what) {
  printf("  %-58s %s\n", what, ok ? "OK" : "*** FAILED ***");
  if (!ok) fail = 1;
}

/* DB(O) as a bitset over triangles: triangle double-backed iff 2 of its 3 arcs backward */
static void db_of(const u8 *o, uint64_t *out) {
  int pos[Q];
  for (int t = 0; t < Q; t++) pos[o[t]] = t;
  memset(out, 0, ((NT + 63) / 64) * 8);
  for (int i = 0; i < ntri; i++) {
    int a = tri[i][0], b = tri[i][1], c = tri[i][2];
    /* orient: exactly one of the two cyclic orientations holds */
    int x, y, z;
    if (adj[a][b] && adj[b][c] && adj[c][a]) { x = a; y = b; z = c; }
    else                                     { x = a; y = c; z = b; }
    int back = (pos[y] < pos[x]) + (pos[z] < pos[y]) + (pos[x] < pos[z]);
    if (back == 2) out[i >> 6] |= 1ULL << (i & 63);
  }
}

static long overlap(const uint64_t *p, const uint64_t *q) {
  long s = 0;
  for (int w = 0; w < (NT + 63) / 64; w++) s += __builtin_popcountll(p[w] & q[w]);
  return s;
}

int main(int argc, char **argv) {
  if (argc < 2) { fprintf(stderr, "usage: %s d0_reps.txt [n_sample]\n", argv[0]); return 1; }
  int nsample = argc > 2 ? atoi(argv[2]) : 60;

  printf("== 1. Paley(43) and its cyclic triangles ==\n");
  for (int x = 1; x < Q; x++) isqr[(x * x) % Q] = 1;
  NQR = 0;
  for (int s = 1; s < Q; s++) if (isqr[s]) qrl[NQR++] = s;
  for (int u = 0; u < Q; u++)
    for (int v = 0; v < Q; v++)
      if (u != v) adj[u][v] = (u8)isqr[((v - u) % Q + Q) % Q];

  memset(tidx, 0xff, sizeof tidx);
  ntri = 0;
  for (int a = 0; a < Q; a++)
    for (int b = a + 1; b < Q; b++)
      for (int c = b + 1; c < Q; c++) {
        int cyc = (adj[a][b] && adj[b][c] && adj[c][a]) || (adj[a][c] && adj[c][b] && adj[b][a]);
        if (!cyc) continue;
        tri[ntri][0] = a; tri[ntri][1] = b; tri[ntri][2] = c;
        tidx[a][b][c] = ntri++;
      }
  printf("  cyclic triangles enumerated: %d\n", ntri);
  chk(ntri == NT, "T = 3311 cyclic triangles");

  printf("== 2. G and its action on the triangles ==\n");
  NAUT = NQR * Q;
  { int m = 0;
    for (int i = 0; i < NQR; i++) for (int b = 0; b < Q; b++) { amap[m][0] = qrl[i]; amap[m][1] = b; m++; } }
  chk(NAUT == 903, "|G| = 903");

  static int act[903][NT];
  int perm_ok = 1;
  for (int m = 0; m < NAUT; m++) {
    int a = amap[m][0], b = amap[m][1];
    char *hit = calloc(ntri, 1);
    for (int i = 0; i < ntri; i++) {
      int v[3];
      for (int k = 0; k < 3; k++) v[k] = (a * tri[i][k] + b) % Q;
      for (int p = 0; p < 2; p++) for (int r = 0; r < 2; r++)      /* sort 3 */
        if (v[r] > v[r + 1]) { int t = v[r]; v[r] = v[r + 1]; v[r + 1] = t; }
      int j = tidx[v[0]][v[1]][v[2]];
      if (j < 0) { perm_ok = 0; break; }
      act[m][i] = j; hit[j] = 1;
    }
    if (perm_ok) for (int i = 0; i < ntri; i++) if (!hit[i]) { perm_ok = 0; break; }
    free(hit);
    if (!perm_ok) break;
  }
  chk(perm_ok, "every sigma permutes the 3311 cyclic triangles");

  printf("== 3. orbit structure of G on the triangles ==\n");
  int *orb = malloc(ntri * sizeof(int));
  for (int i = 0; i < ntri; i++) orb[i] = -1;
  int norb = 0; long sizes[64]; long nstab = 0;
  for (int i = 0; i < ntri; i++) {
    if (orb[i] >= 0) continue;
    long sz = 0, stab = 0;
    char *seen = calloc(ntri, 1);
    for (int m = 0; m < NAUT; m++) {
      int j = act[m][i];
      if (j == i) stab++;
      if (!seen[j]) { seen[j] = 1; orb[j] = norb; sz++; }
    }
    free(seen);
    if (norb < 64) sizes[norb] = sz;
    norb++;
    /* |orbit| * |stabiliser| = |G| */
    if (sz * stab != NAUT) { printf("  orbit-stabiliser identity broken on triangle %d\n", i); fail = 1; }
    if (stab > 1) nstab += sz;
  }
  printf("  orbits: %d, sizes:", norb);
  for (int i = 0; i < norb && i < 64; i++) printf(" %ld", sizes[i]);
  printf("\n  triangles with a nontrivial stabiliser: %ld\n", nstab);
  chk(norb == 5, "G has 5 orbits on the cyclic triangles");
  { long a = 0, b = 0;
    for (int i = 0; i < norb && i < 64; i++) { if (sizes[i] == 903) a++; else if (sizes[i] == 301) b++; }
    chk(a == 3 && b == 2, "orbit sizes are 903, 903, 903, 301, 301"); }
  chk(nstab == 602, "602 triangles carry a nontrivial stabiliser");

  printf("== 4. G-invariance of DB-overlap, exhaustive over all 903 sigma ==\n");
  FILE *f = fopen(argv[1], "r");
  if (!f) { perror("open"); return 1; }
  u8 *ord = malloc((size_t)nsample * Q);
  int nord = 0;
  while (nord < nsample) {
    int v, ok = 1;
    for (int t = 0; t < Q; t++) { if (fscanf(f, "%d", &v) != 1) { ok = 0; break; } ord[(size_t)nord * Q + t] = (u8)v; }
    if (!ok) break;
    nord++;
  }
  fclose(f);
  printf("  sampled %d level-0 orders => %d unordered pairs, each tested against all %d sigma\n",
         nord, nord * (nord - 1) / 2, NAUT);

  int W = (NT + 63) / 64;
  uint64_t *dbs = malloc((size_t)nord * NAUT * W * 8);   /* DB(sigma O) for every order, every sigma */
  u8 img[Q];
  for (int r = 0; r < nord; r++)
    for (int m = 0; m < NAUT; m++) {
      int a = amap[m][0], b = amap[m][1];
      for (int t = 0; t < Q; t++) img[t] = (u8)((a * ord[(size_t)r * Q + t] + b) % Q);
      db_of(img, dbs + ((size_t)r * NAUT + m) * W);
    }

  long viol = 0, tested = 0;
  for (int r1 = 0; r1 < nord; r1++)
    for (int r2 = r1 + 1; r2 < nord; r2++) {
      long base = overlap(dbs + ((size_t)r1 * NAUT + 0) * W, dbs + ((size_t)r2 * NAUT + 0) * W);
      for (int m = 0; m < NAUT; m++) {
        long ov = overlap(dbs + ((size_t)r1 * NAUT + m) * W, dbs + ((size_t)r2 * NAUT + m) * W);
        tested++;
        if (ov != base) viol++;
      }
    }
  printf("  (sigma, pair) combinations tested: %ld ; violations: %ld\n", tested, viol);
  chk(viol == 0, "|DB(sigma O1) ∩ DB(sigma O2)| is invariant for every sigma");

  /* the same sample also shows overlaps are far from 0 on the MAS layer */
  long mn = 1 << 30, mx = 0;
  for (int r1 = 0; r1 < nord; r1++)
    for (int r2 = r1 + 1; r2 < nord; r2++) {
      long ov = overlap(dbs + ((size_t)r1 * NAUT) * W, dbs + ((size_t)r2 * NAUT) * W);
      if (ov < mn) mn = ov;
      if (ov > mx) mx = ov;
    }
  printf("  DB-overlap over the sampled rep pairs: min %ld, max %ld (0 would be a realization seed)\n", mn, mx);

  printf("\n%s\n", fail ? "verify_ginv: FAILED" : "verify_ginv: ALL CHECKS PASSED");
  return fail;
}
