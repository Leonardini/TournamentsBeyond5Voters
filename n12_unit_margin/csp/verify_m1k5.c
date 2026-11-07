/* verify_m1k5.c — independent verifier for cert_m1k5 witnesses.
 *
 * Input: the stdout of cert_m1k5 (lines "Y <bits> | <label per arc>" and
 * "N <bits>").  For each Y line: rebuild the tournament, decode each arc's
 * dissent pair from its label (the C(5,2) pairs in cert_m1k5's init_labels
 * order), form each voter's backward set B_i = {arcs whose pair contains i},
 * check that reversing B_i leaves an acyclic digraph (so B_i is the backward
 * set of a genuine linear order), realize the five orders by topological
 * sort, and re-count every arc's forward support from the orders themselves:
 * it must be exactly 3 of 5 (margin-1).  Any failure aborts with the line.
 * N lines are passed through to stdout (the residual pool for the ILP stage);
 * tallies go to stderr.
 *
 * Usage: verify_m1k5 n < cert_output
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 16
static int n, m;
static int A[MAXN][MAXN];          /* A[i][j]=1 iff i->j in T */
static int au[MAXN*MAXN], av[MAXN*MAXN];   /* arc index -> (u,v) with u->v */
static int pairA[10], pairB[10];

static void die(const char *msg, const char *line) {
    fprintf(stderr, "VERIFY FAIL (%s): %s\n", msg, line);
    exit(1);
}

/* topological order of the digraph D (n vertices); 1 if acyclic */
static int topo(int D[MAXN][MAXN], int *order) {
    int indeg[MAXN], used[MAXN] = {0};
    for (int v = 0; v < n; v++) {
        indeg[v] = 0;
        for (int u = 0; u < n; u++) if (D[u][v]) indeg[v]++;
    }
    for (int k = 0; k < n; k++) {
        int pick = -1;
        for (int v = 0; v < n; v++) if (!used[v] && indeg[v] == 0) { pick = v; break; }
        if (pick < 0) return 0;
        order[k] = pick; used[pick] = 1;
        for (int v = 0; v < n; v++) if (D[pick][v]) indeg[v]--;
    }
    return 1;
}

int main(int argc, char **argv) {
    n = atoi(argv[1]); m = n*(n-1)/2;
    int l = 0;
    for (int i = 0; i < 5; i++) for (int j = i+1; j < 5; j++) {
        pairA[l] = i; pairB[l] = j; l++;
    }
    char line[1024];
    long yes = 0, no = 0;
    while (fgets(line, sizeof line, stdin)) {
        if (line[0] == 'N') { no++; fputs(line, stdout); continue; }
        if (line[0] != 'Y') continue;
        char *bits = line + 2;
        char *bar = strchr(line, '|');
        if (!bar) die("no witness", line);
        /* tournament */
        int k = 0;
        for (int i = 0; i < n; i++) for (int j = i+1; j < n; j++) {
            if (bits[k] == '1') { A[i][j] = 1; A[j][i] = 0; }
            else if (bits[k] == '0') { A[i][j] = 0; A[j][i] = 1; }
            else die("bad bits", line);
            au[k] = A[i][j] ? i : j; av[k] = A[i][j] ? j : i;
            k++;
        }
        /* labels */
        int lab[MAXN*MAXN];
        char *p = bar + 1;
        for (int a = 0; a < m; a++) {
            lab[a] = (int)strtol(p, &p, 10);
            if (lab[a] < 0 || lab[a] > 9) die("bad label", line);
        }
        /* five voters: reverse B_i, topo-sort, then re-check majorities */
        int pos[5][MAXN];
        for (int i = 0; i < 5; i++) {
            int D[MAXN][MAXN];
            memcpy(D, A, sizeof D);
            for (int a = 0; a < m; a++)
                if (pairA[lab[a]] == i || pairB[lab[a]] == i) {
                    D[au[a]][av[a]] = 0; D[av[a]][au[a]] = 1;   /* voter i reverses arc a */
                }
            int ord[MAXN];
            if (!topo(D, ord)) die("backward set not acyclic", line);
            for (int k2 = 0; k2 < n; k2++) pos[i][ord[k2]] = k2;
        }
        for (int a = 0; a < m; a++) {
            int fwd = 0;
            for (int i = 0; i < 5; i++) if (pos[i][au[a]] < pos[i][av[a]]) fwd++;
            if (fwd != 3) die("margin not 3:2", line);
        }
        yes++;
    }
    fprintf(stderr, "verified %ld margin-1-k5 witnesses (all exact 3:2); %ld UNSAT passed through\n",
            yes, no);
    return 0;
}
