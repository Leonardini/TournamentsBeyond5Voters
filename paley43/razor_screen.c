/* razor_screen.c  — DB-disjointness screen for Paley(q) via a vertex-subset razor.
 *
 * Refutation logic (Leonid's co-backing route):
 *   - Co-backing theorem: in ANY 5-realization the 5 voters' double-back (DB) sets are
 *     PAIRWISE DISJOINT.
 *   - Every realization has >=2 voters at delta<=1 (f2 >= 542 for MAS(Paley43)=543).
 *   => if NO two delta<=1 orders have DB-disjoint sets, Paley(43) is NON-5-realizable (N(5)<=43).
 *
 *   DB(O) = { cyclic triangles t : O backs exactly 2 of t's 3 arcs (fwd==1) }.
 *   Two orders are DB-disjoint  iff  DB(O1) & DB(O2) == {}.
 *
 * The razor (Leonid's tweak): R = cyclic triangles induced inside a vertex subset W.
 *   rmask(O) = DB(O) & R  depends only on O|_W and is CHEAP (|R|~500 vs T=3311).
 *   If rmask(O1) & rmask(O2) != {}  then DB(O1) & DB(O2) != {}  (SOUND rejection).
 *   So a disjoint pair MUST have disjoint rmasks: screen on rmasks, double-check hits on full DB.
 *
 * Grouping collapse: rmask takes only ~O(1e5-1e7) DISTINCT values over the whole pool, so we
 *   work at the level of distinct rmasks (M) instead of orders (N ~ 1.66e9). We find all
 *   disjoint DISTINCT-rmask pairs (M^2/2 cheap ANDs), then double-check the orders in those
 *   (rare) "dangerous" groups with full 3311-bit DB.
 *
 * Input: orbit-rep orders (one per line, q ints, 0-indexed). With expand=1 we generate the
 *   full Aut-closed pool on the fly (rep x |Aut| images) so the 1.66e9-order pool is never stored.
 *
 * Usage: razor_screen <reps_file> <expand:0|1> <Wsize> [maxreps] [threads]
 *   W defaults to {0..Wsize-1}. expand=0 treats each input line as a full-pool order directly.
 *
 * Env modes:
 *   POOLVSPOOL=1  Aut-reduction-FREE confirmation. The default double-check uses the §6.2 one-side
 *     rep reduction (÷|Aut|): each dangerous group is tested only against the ORBIT REPS. With
 *     POOLVSPOOL=1 BOTH sides range over the full G-closed pool (GSRC vs GSRC) — no Aut trick
 *     anywhere. Each partner order's 3311-bit DB is materialised just-in-time from its rep+Aut map
 *     via db_from_src, so the 1.66e9-order pool is NEVER stored (no 198 GB file, no 690 GB repDB).
 *     Run as `POOLVSPOOL=1 razor_screen delta1_reps.txt 1 24 0 <thr>` (expand=1 => JIT full pool).
 *   MATERIALIZE=1 Dump the expanded pool (rep x amaps, or the input lines if expand=0) to stdout,
 *     one order per line, then exit. Only needed to cross-check the JIT screen against a brute
 *     expand=0 run on a materialised pool file; the screen itself never needs it.
 *   TRANSV=k (k=1,2)  ∃U-transversal screen for P-minus-k-vertices (PV_SETTLE_PLAN.md §2):
 *     a HIT is a pair whose full-DB overlap has a transversal of <=k vertices (overlap ⊆
 *     ∪_{u∈U} star(u), |U|=k). The property is Aut-invariant (σ star(u) = star(σu)), so the
 *     one-side ÷903 rep reduction REMAINS VALID — unlike DROPV, which fixes the deleted vertex
 *     and forfeits Aut. TRUE hits are top-two CANDIDATES for P-U, to be post-filtered by
 *     projected levels; 0 hits => no DB-disjoint P-U pair at these levels for ANY k-subset U.
 *     min_residual: k=1 exact min over candidate pairs of min_u |overlap \ star(u)| (monotone
 *     early-exit); k=2 detection is exact (3-branch), the reported margin is a LOWER bound
 *     ov-(top1+top2). Mutually exclusive with DROPV. TRANSV=0 == plain disjoint screen.
 *   XSIZE=X  3-tier nested razor (Leonid): reorder triangle indices as [inside W | inside X,
 *     meeting V\W | meeting V\X] so the word-by-word early-exit overlap loop scans the tiers
 *     coarse-to-fine (the cascade of COMPUTATION_TRICKS.md #13, implicit in bit order).
 *     X~30 balances |T1|~|T2|. Pure reordering: all counts/results are invariant.
 *   CANDCAP=N  abort cleanly if candidate pairs exceed N (default 2e8; transversal-feasible
 *     pairs are more common than disjoint ones).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>

typedef uint64_t u64;
typedef uint8_t  u8;
static double now_s(void){ struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts); return ts.tv_sec+ts.tv_nsec/1e9; }
static void die(const char*m){ fprintf(stderr,"FATAL: %s\n",m); exit(1); }

static int q, NQR, NAUT;
static int qrl[64];
static int adjm[64][64];
static int amaps[1024][2];            /* Aut maps (a,b): v -> (a*v+b)%q, a in QR */

/* cyclic triangles: tri[t] = {u0,v0,u1,v1,u2,v2}, three Paley arcs tail->head */
static int T;
static int (*tri)[6];
/* razor */
static int nR, RW, FW;
static int *Rlist;                    /* indices of triangles inside W */
static char *inR;                     /* inR[t]=1 iff triangle t is in the razor */
static int DBTEST=0;                  /* if set, "DB" uses only razor triangles (positive-detection test) */
static int POOLVSPOOL=0;              /* if set, double-check is full-pool vs full-pool (no Aut reduction) */
static int DROPV=-1;                  /* P-v screen: drop all cyclic triangles through vertex DROPV */
static long SEEDCAP=100000;           /* cap on stored seeds (count is always exact) */
static int TRANSV=-1;                 /* >=1: ∃U-transversal screen (see header); <=0: plain disjoint */
static int XSIZE=0;                   /* >0: 3-tier razor triangle reordering (pure permutation) */
static long CANDCAP=200000000;        /* candidate-pair store guard */
static int MEASONLY=0;                /* MEASURE mode: count candidates + set dang[], skip the pair store */
static u64 *vmaskF;                   /* vmaskF[t] = 43-bit vertex mask of triangle t */
static u64 *vmaskW;                   /* vmaskW[r] = vertex mask of razor triangle r */
static int (*triv)[3];                /* the 3 distinct vertices of triangle t */
#define VMASK43 ((1ULL<<43)-1)

static void build_group(void){
  int isqr[64]={0};
  for(long x=1;x<q;x++) isqr[(x*x)%q]=1;
  NQR=0; for(int s=1;s<q;s++) if(isqr[s]) qrl[NQR++]=s;
  NAUT=NQR*q;
  for(int u=0;u<q;u++) for(int v=0;v<q;v++) adjm[u][v]=(u!=v && isqr[((v-u)%q+q)%q]);
  int m=0;
  for(int ai=0;ai<NQR;ai++) for(int b=0;b<q;b++){ amaps[m][0]=qrl[ai]; amaps[m][1]=b; m++; }
  if(m!=NAUT) die("amap count");
}

static void build_tris(int Wsize){
  int cap=8192; tri=malloc((size_t)cap*sizeof *tri); T=0;
  int *inW=calloc(q,sizeof(int)); for(int i=0;i<Wsize && i<q;i++) inW[i]=1;
  int rcap=4096; Rlist=malloc(rcap*sizeof(int)); nR=0;
  for(int a=0;a<q;a++)for(int b=a+1;b<q;b++)for(int c=b+1;c<q;c++){
    if(DROPV>=0 && (a==DROPV||b==DROPV||c==DROPV)) continue;   /* P-v: drop triangles through v */
    int e[3][2]={{a,b},{a,c},{b,c}}, od[3]={0,0,0}; int vs[3]={a,b,c}; int arc[3][2];
    for(int k=0;k<3;k++){ int x=e[k][0],y=e[k][1];
      if(adjm[x][y]){arc[k][0]=x;arc[k][1]=y;} else {arc[k][0]=y;arc[k][1]=x;} }
    for(int k=0;k<3;k++){ int t=arc[k][0]; for(int j=0;j<3;j++) if(vs[j]==t) od[j]++; }
    if(!(od[0]==1&&od[1]==1&&od[2]==1)) continue;   /* keep cyclic triangles only */
    if(T==cap){cap*=2; tri=realloc(tri,(size_t)cap*sizeof *tri);}
    for(int k=0;k<3;k++){ tri[T][2*k]=arc[k][0]; tri[T][2*k+1]=arc[k][1]; }
    if(inW[a]&&inW[b]&&inW[c]){ if(nR==rcap){rcap*=2;Rlist=realloc(Rlist,rcap*sizeof(int));} Rlist[nR++]=T; }
    T++;
  }
  free(inW);
  if(XSIZE>0){                       /* 3-tier reorder: [inside W | inside X, meets V\W | meets V\X] */
    if(XSIZE<Wsize) die("XSIZE < Wsize");
    int oldnR=nR;
    int (*tn)[6]=malloc((size_t)T*sizeof *tn); int nt=0, ntier[3]={0,0,0};
    for(int pass=0;pass<3;pass++) for(int t=0;t<T;t++){
      int mx=0; for(int k=0;k<6;k++) if(tri[t][k]>mx) mx=tri[t][k];
      int tier = mx<Wsize?0 : mx<XSIZE?1 : 2;
      if(tier==pass){ memcpy(tn[nt++],tri[t],sizeof tri[t]); ntier[pass]++; }
    }
    if(nt!=T) die("tier reorder lost triangles");
    free(tri); tri=tn;
    nR=0; for(int t=0;t<ntier[0];t++) Rlist[nR++]=t;         /* tier-0 == razor, now contiguous */
    if(nR!=oldnR) die("tier0 count != razor count");
    fprintf(stderr,"3-tier razor: |T1|=%d (W=%d) |T2|=%d (X=%d) |T3|=%d\n",ntier[0],Wsize,ntier[1],XSIZE,ntier[2]);
  }
  RW=(nR+63)/64; FW=(T+63)/64;
  inR=calloc(T,1); for(int r=0;r<nR;r++) inR[Rlist[r]]=1;   /* razor membership (for DBTEST) */
  triv=malloc((size_t)T*sizeof *triv); vmaskF=malloc((size_t)T*8);
  for(int t=0;t<T;t++){ u64 m=0; int nv=0;
    for(int k=0;k<6;k++){ int v=tri[t][k]; if(!(m>>v&1)){ m|=1ULL<<v; if(nv<3) triv[t][nv]=v; nv++; } }
    if(nv!=3) die("triangle vertex count != 3");
    vmaskF[t]=m; }
  vmaskW=malloc((size_t)(nR?nR:1)*8); for(int r=0;r<nR;r++) vmaskW[r]=vmaskF[Rlist[r]];
}

/* window-overlap <=TRANSV-transversal feasibility (SOUND candidate filter: full overlap ⊆
 * ∪star(U) implies window overlap ⊆ ∪star(U) implies window transversal <=|U|). */
static inline int win_transv_feasible(const u64*mi,const u64*mj){
  if(TRANSV==1){
    u64 cand=VMASK43;
    for(int w=0;w<RW;w++){ u64 x=mi[w]&mj[w];
      while(x){ int r=w*64+__builtin_ctzll(x); x&=x-1;
        cand&=vmaskW[r]; if(!cand) return 0; } }
    return 1;
  }
  /* TRANSV==2: any 2-transversal must hit the FIRST overlap triangle; 3-branch on its vertices,
   * each branch keeps the AND-mask of valid partners over the triangles missing that vertex. */
  int bu[3]={-1,-1,-1}; u64 Y[3]={0,0,0}; int have=0;
  for(int w=0;w<RW;w++){ u64 x=mi[w]&mj[w];
    while(x){ int r=w*64+__builtin_ctzll(x); x&=x-1;
      u64 vm=vmaskW[r]; int t=Rlist[r];
      if(!have){ bu[0]=triv[t][0];bu[1]=triv[t][1];bu[2]=triv[t][2]; Y[0]=Y[1]=Y[2]=VMASK43; have=1; continue; }
      int alive=0;
      for(int k=0;k<3;k++){ if(bu[k]<0) continue;
        if(!(vm>>bu[k]&1)){ Y[k]&=vm; if(!Y[k]){ bu[k]=-1; continue; } }
        alive=1; }
      if(!alive) return 0;
    } }
  return 1;
}

/* full-DB residual for the TRANSV screen (PV_SETTLE_PLAN.md §2 margin semantics).
 * k=1: EXACT residual min_u |overlap \ star(u)| with a monotone early-exit against minres
 *      (ov - top1 never decreases); returns -1 for "bailed: residual >= minres".
 * k=2: EXACT 0-detection (a surviving branch's Y-mask is nonempty IFF some pair {u,w} covers
 *      the whole overlap); for non-hits returns -(lb+1) where lb = max(1, ov-top1-top2) is a
 *      residual LOWER bound. bestu: k=1 the transversal vertex (-1 if overlap empty);
 *      k=2 encoded u*64+w. */
static inline long pair_residual(const u64*dp,const u64*dy,long minres,long*bestu){
  int ov=0;
  if(TRANSV==1){
    uint16_t h[43]; memset(h,0,sizeof h); int m1=0, am1=-1;
    for(int w=0;w<FW;w++){ u64 x=dp[w]&dy[w];
      while(x){ int t=w*64+__builtin_ctzll(x); x&=x-1; ov++;
        for(int k=0;k<3;k++){ int u=triv[t][k]; int nh=++h[u]; if(nh>m1){m1=nh;am1=u;} }
        if(ov-m1>=minres) return -1;
      } }
    *bestu=am1; return ov-m1;
  }
  uint16_t h[43]; memset(h,0,sizeof h); int m1=0,m2=0,am1=-1;
  int bu[3]={-1,-1,-1}; u64 Y[3]={0,0,0}; int have=0;
  for(int w=0;w<FW;w++){ u64 x=dp[w]&dy[w];
    while(x){ int t=w*64+__builtin_ctzll(x); x&=x-1; ov++;
      u64 vm=vmaskF[t];
      if(!have){ bu[0]=triv[t][0];bu[1]=triv[t][1];bu[2]=triv[t][2]; Y[0]=Y[1]=Y[2]=VMASK43; have=1; }
      else for(int k=0;k<3;k++){ if(bu[k]>=0 && !(vm>>bu[k]&1)){ Y[k]&=vm; if(!Y[k]) bu[k]=-1; } }
      for(int k=0;k<3;k++){ int u=triv[t][k]; int nh=++h[u];
        if(u==am1) m1=nh;
        else if(nh>m1){ m2=m1; m1=nh; am1=u; }
        else if(nh>m2) m2=nh;
      }
    } }
  if(!have){ *bestu=-1; return 0; }              /* empty overlap: plain-disjoint pair, also a hit */
  for(int k=0;k<3;k++) if(bu[k]>=0){ *bestu=(long)bu[k]*64+__builtin_ctzll(Y[k]); return 0; }
  long lb=ov-m1-m2; if(lb<1) lb=1;
  return -(lb+1);
}

/* compute rmask (RW words) into out; pos[v]=rank */
static inline void rmask_of(const u8*pos, u64*out){
  memset(out,0,(size_t)RW*8);
  for(int r=0;r<nR;r++){ int*t=tri[Rlist[r]];
    int f=(pos[t[0]]<pos[t[1]])+(pos[t[2]]<pos[t[3]])+(pos[t[4]]<pos[t[5]]);
    if(f==1) out[r>>6]|=1ULL<<(r&63);
  }
}
/* full DB (FW words) */
static inline void fulldb_of(const u8*pos, u64*out){
  memset(out,0,(size_t)FW*8);
  for(int t=0;t<T;t++){ if(DBTEST && !inR[t]) continue;   /* DBTEST: DB == razor only */
    int*a=tri[t];
    int f=(pos[a[0]]<pos[a[1]])+(pos[a[2]]<pos[a[3]])+(pos[a[4]]<pos[a[5]]);
    if(f==1) out[t>>6]|=1ULL<<(t&63);
  }
}
static inline int popcnt(const u64*w,int n){ int s=0; for(int i=0;i<n;i++) s+=__builtin_popcountll(w[i]); return s; }

/* ---------- input ---------- */
static u8 *reps; static long Nr;
static void load_reps(const char*fn,long maxreps){
  FILE*f=fopen(fn,"r"); if(!f) die("open reps");
  long cap=1<<16; reps=malloc((size_t)cap*q); Nr=0;
  for(;;){ int v,ok=1;
    for(int t=0;t<q;t++){ if(fscanf(f,"%d",&v)!=1){ok=0;break;} reps[Nr*q+t]=(u8)v; }
    if(!ok) break;
    if(++Nr==cap){cap*=2; reps=realloc(reps,(size_t)cap*q);}
    if(maxreps>0 && Nr>=maxreps) break;
  }
  fclose(f);
}

/* ---------- distinct-rmask hash set (global, striped locks) ----------
 * Slots hold mask ids only (HID); key comparison reads masks[id] (no duplicate key store). */
static int *HID;       /* slot -> mask id, -1 empty */
static long HS;        /* number of slots (pow2) */
static u64 *masks;     /* [M][RW] distinct masks */
static long M, Mcap;
static pthread_mutex_t hstripe[4096];

static inline u64 hashmask(const u64*w){ u64 h=1469598103934665603ULL; for(int i=0;i<RW;i++){h^=w[i]; h*=1099511628211ULL;} return h; }
/* returns id of mask, inserting if new */
static long insert_mask(const u64*w){
  u64 h=hashmask(w); long slot=h&(HS-1);
  for(;;){
    int id=HID[slot];
    if(id>=0){ if(!memcmp(&masks[(size_t)id*RW],w,(size_t)RW*8)) return id; slot=(slot+1)&(HS-1); continue; }
    /* empty slot: lock stripe and re-probe (another thread may have filled) */
    pthread_mutex_t*mu=&hstripe[slot&4095]; pthread_mutex_lock(mu);
    long s2=slot;
    for(;;){ int id2=HID[s2];
      if(id2>=0){ if(!memcmp(&masks[(size_t)id2*RW],w,(size_t)RW*8)){ pthread_mutex_unlock(mu); return id2; } s2=(s2+1)&(HS-1); continue; }
      long idn=__sync_fetch_and_add(&M,1);
      if(idn>=Mcap){ pthread_mutex_unlock(mu); die("masks cap exceeded — raise Mcap"); }
      memcpy(&masks[(size_t)idn*RW],w,(size_t)RW*8);
      HID[s2]=(int)idn;
      pthread_mutex_unlock(mu); return idn;
    }
  }
}

/* pass-1 worker: iterate a rep-range x amaps, insert rmasks */
static int EXPAND, WSIZE, NTH;
typedef struct{ long lo,hi; long cnt; int minpop,maxpop; long popsum; } P1arg;
static void* p1_worker(void*vp){
  P1arg*A=vp; u8 pos[64],ord[64]; u64 rm[64]; A->cnt=0; A->minpop=1<<30; A->maxpop=0; A->popsum=0;
  int nmap = EXPAND? NAUT : 1;
  for(long r=A->lo;r<A->hi;r++){ const u8*rp=reps+r*q;
    for(int mi=0;mi<nmap;mi++){
      int a=amaps[mi][0],b=amaps[mi][1];
      if(EXPAND){ for(int i=0;i<q;i++){ int w=(a*rp[i]+b)%q; ord[i]=(u8)w; } }
      else       { for(int i=0;i<q;i++) ord[i]=rp[i]; }
      for(int i=0;i<q;i++) pos[ord[i]]=(u8)i;
      rmask_of(pos,rm); insert_mask(rm);
      int p=popcnt(rm,RW); A->popsum+=p; if(p<A->minpop)A->minpop=p; if(p>A->maxpop)A->maxpop=p;
      A->cnt++;
    }
  }
  return NULL;
}

/* ---------- candidate scan: disjoint DISTINCT-rmask pairs ----------
 * Most pairs share a bit already in word 0, so we keep a transposed contiguous copy of every
 * mask's word 0 (W0) for the dominant early-reject check (streams at cache speed); the rare
 * word-0-disjoint pairs fall back to the full RW-word test in masks[]. Tiled to reuse the
 * inner block across the i-loop. */
static char *dang;            /* dang[id]=1 if id belongs to some disjoint rmask pair */
static long ncand;            /* # disjoint distinct-rmask pairs */
static u64 *W0;               /* W0[id] = masks[id][0] (transposed, contiguous) */
static volatile long next_i;
typedef struct{ uint32_t a,b; } Pair;                 /* a<b: a disjoint distinct-rmask pair */
typedef struct{ Pair*v; long n,cap; } Candarg;        /* per-thread candidate-pair list */
static Candarg cargs[16];
/* Cache-TILED all-pairs scan: work-steal a j-block, iterate i-blocks [0..jb] against it so both
 * the i-block and j-block masks stay L1/L2-resident (avoids the O(M) W0 re-stream per i).
 * Records every disjoint (i,j) candidate pair (a=i<b=j) for the group-wise double-check. */
static void* cand_worker(void*vp){
  Candarg*A=vp; A->cap=1<<20; A->v=malloc(A->cap*sizeof(Pair)); A->n=0; long localc=0;
  const long B=2048;
  for(;;){ long jb=__sync_fetch_and_add(&next_i,B); if(jb>=M) break; long je=jb+B; if(je>M)je=M;
    for(long ib=0; ib<=jb; ib+=B){
      long ie=ib+B; if(ie>je) ie=je;                    /* diagonal block capped at je */
      for(long j=jb;j<je;j++){ u64 w0j=W0[j]; const u64*mj=&masks[(size_t)j*RW];
        long i1 = (ie> j)? j : ie;                       /* enforce i<j (matters on the diagonal block) */
        for(long i=ib;i<i1;i++){
          if(TRANSV>=1){
            if(!win_transv_feasible(&masks[(size_t)i*RW],mj)) continue;
          } else {
            if(w0j & W0[i]) continue;                    /* fast contiguous early reject */
            const u64*mi=&masks[(size_t)i*RW];
            int dj=1; for(int w=1;w<RW;w++){ if(mi[w]&mj[w]){dj=0;break;} }  /* word0 already 0 */
            if(!dj) continue;
          }
          dang[i]=1; dang[j]=1; localc++;
          if(MEASONLY) continue;                 /* MEASURE needs only dang[] + the count */
          if(A->n==A->cap){ A->cap*=2; A->v=realloc(A->v,A->cap*sizeof(Pair)); }
          A->v[A->n].a=(uint32_t)i; A->v[A->n].b=(uint32_t)j; A->n++;
          if(A->n>CANDCAP/NTH){ fprintf(stderr,"FATAL: candidate pairs exceed CANDCAP/NTH=%ld — raise CANDCAP or add the tiered candidate stage\n",CANDCAP/NTH); exit(3); }
        }
      }
    }
  }
  __sync_fetch_and_add(&ncand,localc); return NULL;
}

/* ---------- measure: count dangerous orders K (no storage) ---------- */
typedef struct{ long lo,hi,cnt; } KCarg;
static void* kc_worker(void*vp){
  KCarg*A=vp; u8 pos[64],ord[64]; u64 rm[64]; A->cnt=0; int nmap=EXPAND?NAUT:1;
  for(long r=A->lo;r<A->hi;r++){ const u8*rp=reps+r*q;
    for(int mi=0;mi<nmap;mi++){ int a=amaps[mi][0],b=amaps[mi][1];
      if(EXPAND){ for(int i=0;i<q;i++) ord[i]=(u8)((a*rp[i]+b)%q); } else for(int i=0;i<q;i++) ord[i]=rp[i];
      for(int i=0;i<q;i++) pos[ord[i]]=(u8)i;
      rmask_of(pos,rm); long id=insert_mask(rm); if(dang[id]) A->cnt++;
    }
  }
  return NULL;
}

/* ---------- pass 2: collect (id, src) of pool orders whose rmask is dangerous ----------
 * src = r*NAUT + amap-index (fits u32: max 1841302*903+902 < 2^31). */
typedef struct{ long lo,hi; uint32_t *id; uint32_t *src; long n,cap; } P2arg;
static void* p2_worker(void*vp){
  P2arg*A=vp; u8 pos[64],ord[64]; u64 rm[64];
  A->cap=1024; A->id=malloc(A->cap*4); A->src=malloc(A->cap*4); A->n=0;
  int nmap = EXPAND? NAUT : 1;
  for(long r=A->lo;r<A->hi;r++){ const u8*rp=reps+r*q;
    for(int mi=0;mi<nmap;mi++){
      int a=amaps[mi][0],b=amaps[mi][1];
      if(EXPAND){ for(int i=0;i<q;i++){ int w=(a*rp[i]+b)%q; ord[i]=(u8)w; } }
      else       { for(int i=0;i<q;i++) ord[i]=rp[i]; }
      for(int i=0;i<q;i++) pos[ord[i]]=(u8)i;
      rmask_of(pos,rm); long id=insert_mask(rm);
      if(!dang[id]) continue;
      if(A->n==A->cap){ A->cap*=2; A->id=realloc(A->id,A->cap*4); A->src=realloc(A->src,A->cap*4); }
      A->id[A->n]=(uint32_t)id; A->src[A->n]=(uint32_t)((u64)r*NAUT+mi); A->n++;
    }
  }
  return NULL;
}
/* reconstruct order O from src -> pos[]; then full DB */
static inline void db_from_src(uint32_t src, u64*out){
  long r=src/NAUT; int mi=src%NAUT; int a=amaps[mi][0],b=amaps[mi][1];
  u8 pos[64]; const u8*rp=reps+r*q;
  for(int i=0;i<q;i++){ int w=(a*rp[i]+b)%q; pos[w]=(u8)i; }
  fulldb_of(pos,out);
}
static inline void order_from_src(uint32_t src, u8*ord){
  long r=src/NAUT; int mi=src%NAUT; int a=amaps[mi][0],b=amaps[mi][1];
  const u8*rp=reps+r*q; for(int i=0;i<q;i++) ord[i]=(u8)((a*rp[i]+b)%q);
}
static inline int fwd_of_order(const u8*ord){
  u8 pos[64]; for(int i=0;i<q;i++) pos[ord[i]]=(u8)i; int f=0;
  for(int u=0;u<q;u++) for(int v=0;v<q;v++) if(adjm[u][v]&&pos[u]<pos[v]) f++; return f;
}

/* ---------- Aut-reduced double-check ----------
 * A disjoint pool pair exists IFF some CANONICAL ORBIT REP is DB-disjoint from a pool order
 * (Aut preserves DB-disjointness and the pool is Aut-closed). So we compute each dangerous
 * group g(r)'s DBs ONCE, and test them only against the ORBIT REPS whose rmask is a razor-
 * disjoint partner of r (reps are 1/|Aut| of the pool). Early-break disjoint detection. */
static long *gstart; static uint32_t *GSRC;            /* dangerous pool orders grouped by rmask id */
static Pair *cpairs; static long npairs;
static uint32_t *adj; static long *adj_start;          /* CSR adjacency of the disjointness graph */
static u64 *repDB; static long *rep_gstart; static uint32_t *rep_ord;  /* reps grouped by rmask id */
static long *Dids; static long nDids;                  /* dangerous rmask ids (|g|>0) */
static int MAXG;
static volatile long next_did;
typedef struct{ long checked, seedcount; uint32_t *seedsrc; uint32_t *seedu; long ns,scap; long minov; } DCarg;
/* shared inner test for both double-check workers: default = exact-overlap popcount with
 * bound-based early exit; TRANSV>=1 = pair_residual (hit iff residual 0). Updates stats,
 * stores the seed (s1,s2[,bestu]) on a hit. */
static inline void dc_test_pair(DCarg*A,const u64*dp,const u64*dy,uint32_t s1,uint32_t s2){
  A->checked++;
  if(TRANSV>=1){
    long bu=-1; long res=pair_residual(dp,dy,A->minov,&bu);
    if(res>=0){ if(res<A->minov) A->minov=res;
      if(res==0){ A->seedcount++;
        if(A->ns<SEEDCAP){
          if(A->ns==A->scap){ A->scap*=2; A->seedsrc=realloc(A->seedsrc,A->scap*8); A->seedu=realloc(A->seedu,A->scap*4); }
          A->seedsrc[A->ns*2]=s1; A->seedsrc[A->ns*2+1]=s2; A->seedu[A->ns]=(uint32_t)(bu<0?0xffffffffu:(u64)bu); A->ns++;
        }
      }
    } else if(TRANSV==2 && res<-1){ long lb=-res-1; if(lb<A->minov) A->minov=lb; }
    return;
  }
  long ov=0; int exceeded=0;                        /* bound-based: bail once overlap can't beat running min */
  for(int w=0;w<FW;w++){ u64 x=dp[w]&dy[w];
    if(x){ ov+=__builtin_popcountll(x); if(ov>=A->minov){ exceeded=1; break; } } }
  if(!exceeded){ A->minov=ov;                        /* ov is exact and strictly below the old min */
    if(ov==0){ A->seedcount++;
      if(A->ns<SEEDCAP){                             /* count is exact; storage is capped */
        if(A->ns==A->scap){ A->scap*=2; A->seedsrc=realloc(A->seedsrc,A->scap*8); A->seedu=realloc(A->seedu,A->scap*4); }
        A->seedsrc[A->ns*2]=s1; A->seedsrc[A->ns*2+1]=s2; A->seedu[A->ns]=0xffffffffu; A->ns++;
      }
    }
  }
}
static void* dc_worker(void*vp){
  DCarg*A=vp;
  A->checked=0; A->seedcount=0; A->ns=0; A->scap=64; A->seedsrc=malloc(A->scap*8); A->seedu=malloc(A->scap*4); A->minov=1L<<60;
  u64 *gdb=malloc((size_t)MAXG*FW*8);
  for(;;){ long di=__sync_fetch_and_add(&next_did,1); if(di>=nDids) break;
    long r=Dids[di]; long gs=gstart[r], ge=gstart[r+1]; int ng=(int)(ge-gs);
    /* skip if no partner group contains a rep (then no rep is disjoint from g(r)) */
    int hasrep=0; for(long e=adj_start[r];e<adj_start[r+1]&&!hasrep;e++){ long p=adj[e]; if(rep_gstart[p+1]>rep_gstart[p]) hasrep=1; }
    if(!hasrep) continue;
    for(long p=gs,y=0;p<ge;p++,y++) db_from_src(GSRC[p],&gdb[(size_t)y*FW]);   /* g(r) DBs, once */
    for(long e=adj_start[r];e<adj_start[r+1];e++){ long pm=adj[e];
      for(long rr=rep_gstart[pm];rr<rep_gstart[pm+1];rr++){ long ri=rep_ord[rr]; const u64*dp=&repDB[(size_t)ri*FW];
        for(int y=0;y<ng;y++)
          dc_test_pair(A,dp,&gdb[(size_t)y*FW],(uint32_t)((u64)ri*NAUT),GSRC[gs+y]);  /* rep = identity image */
      }
    }
  }
  free(gdb); return NULL;
}

/* ---------- pool-vs-pool double-check (POOLVSPOOL=1; NO Aut reduction) ----------
 * Independent confirmation of TRUE_DISJOINT that does NOT invoke the §6.2 one-side rep reduction:
 * BOTH sides range over the full G-closed pool of dangerous orders (GSRC), grouped by rmask id.
 * For each disjoint rmask-pair (r<p) we test every order of g(r) against every order of g(p) with
 * the full 3311-bit DB. Each pool order's DB is materialised JUST-IN-TIME from its orbit rep + Aut
 * map via db_from_src (identical helper the reduced check already uses on its pool side, line ~282),
 * so the pool is never stored: no 198 GB pool file, no 690 GB repDB — only the 1.84M reps + one
 * MAXG*FW DB buffer per thread. g(r)'s DBs are built once per r; each g(p) order's DB is built once
 * (reused across all |g(r)| comparisons). Enforcing p>r visits each unordered rmask-pair exactly
 * once, so `checked` counts full-pool order-pairs with no double-counting. */
static void* dc_worker_pvp(void*vp){
  DCarg*A=vp;
  A->checked=0; A->seedcount=0; A->ns=0; A->scap=64; A->seedsrc=malloc(A->scap*8); A->seedu=malloc(A->scap*4); A->minov=1L<<60;
  u64 *gdbA=malloc((size_t)MAXG*FW*8);   /* g(r) DBs, materialised once per r */
  u64 *dbp =malloc((size_t)FW*8);        /* one partner order's DB, materialised JIT then reused */
  for(;;){ long di=__sync_fetch_and_add(&next_did,1); if(di>=nDids) break;
    long r=Dids[di];
    int haspartner=0; for(long e=adj_start[r];e<adj_start[r+1];e++){ if(adj[e]>r || (adj[e]==r&&TRANSV>=1)){haspartner=1;break;} }
    if(!haspartner) continue;                              /* all its pairs handled from the smaller side */
    long gs=gstart[r], ge=gstart[r+1]; long ngr=ge-gs;
    for(long y=0;y<ngr;y++) db_from_src(GSRC[gs+y],&gdbA[(size_t)y*FW]);   /* g(r) DBs, once */
    for(long e=adj_start[r];e<adj_start[r+1];e++){ long p=adj[e];
      if(p<r || (p==r&&TRANSV<1)) continue;                /* each unordered rmask-pair exactly once */
      if(p==r){                                            /* TRANSV self-feasible group: intra-group pairs y<o */
        for(long o=1;o<ngr;o++) for(long y=0;y<o;y++)
          dc_test_pair(A,&gdbA[(size_t)o*FW],&gdbA[(size_t)y*FW],GSRC[gs+y],GSRC[gs+o]);
        continue;
      }
      for(long o=gstart[p]; o<gstart[p+1]; o++){
        db_from_src(GSRC[o],dbp);                          /* JIT-materialise this partner order's DB once */
        for(long y=0;y<ngr;y++)
          dc_test_pair(A,dbp,&gdbA[(size_t)y*FW],GSRC[gs+y],GSRC[o]);
      }
    }
  }
  free(gdbA); free(dbp); return NULL;
}
/* rep-DB precompute worker */
static long *repid;
typedef struct{ long lo,hi; } RepArg;
static void* rep_worker(void*vp){ RepArg*A=vp; u8 pos[64]; u64 rm[64];
  for(long r=A->lo;r<A->hi;r++){ const u8*rp=reps+r*q;
    for(int i=0;i<q;i++) pos[rp[i]]=(u8)i;
    rmask_of(pos,rm); repid[r]=insert_mask(rm);
    fulldb_of(pos,&repDB[(size_t)r*FW]);
  }
  return NULL;
}

int main(int argc,char**argv){
  if(argc<4){ fprintf(stderr,"usage: %s reps_file expand(0|1) Wsize [maxreps] [threads]\n",argv[0]); return 1; }
  const char*fn=argv[1]; EXPAND=atoi(argv[2]); WSIZE=atoi(argv[3]);
  long maxreps=argc>4?atol(argv[4]):0; NTH=argc>5?atoi(argv[5]):8; if(NTH>10)NTH=10;
  if(getenv("DBTEST")) DBTEST=atoi(getenv("DBTEST"));
  if(getenv("POOLVSPOOL")) POOLVSPOOL=atoi(getenv("POOLVSPOOL"));
  if(getenv("DROPV")) DROPV=atoi(getenv("DROPV"));
  if(getenv("SEEDCAP")) SEEDCAP=atol(getenv("SEEDCAP"));
  if(getenv("TRANSV")) TRANSV=atoi(getenv("TRANSV"));
  if(getenv("XSIZE")) XSIZE=atoi(getenv("XSIZE"));
  if(getenv("CANDCAP")) CANDCAP=atol(getenv("CANDCAP"));
  if(getenv("MEASURE")) MEASONLY=1;
  if(TRANSV>2) die("TRANSV must be 0, 1 or 2");
  if(TRANSV>=1 && DROPV>=0) die("TRANSV excludes DROPV (the transversal screen already quantifies over the deleted set)");
  q=43; build_group(); build_tris(WSIZE);
  fprintf(stderr,"q=%d NAUT=%d T=%d  W={0..%d} |R|=%d (RW=%d, FW=%d)%s",q,NAUT,T,WSIZE-1,nR,RW,FW,DROPV<0?"":"");
  if(DROPV>=0) fprintf(stderr,"  [P-v: dropped vertex %d -> %d non-v triangles; use POOLVSPOOL=1 (Aut÷903 invalid for P-v)]\n",DROPV,T);
  else fprintf(stderr,"\n");
  double t0=now_s();
  load_reps(fn,maxreps);
  long Ntot = EXPAND? Nr*(long)NAUT : Nr;
  fprintf(stderr,"loaded %ld reps -> %ld pool orders (expand=%d)  %.1fs\n",Nr,Ntot,EXPAND,now_s()-t0);
  if(POOLVSPOOL) fprintf(stderr,"MODE: pool-vs-pool double-check (no Aut reduction; partner DBs materialised JIT)\n");
  if(TRANSV>=1) fprintf(stderr,"MODE: TRANSV=%d — hit = DB-overlap with a <=%d-vertex transversal (∃U a-posteriori; Aut ÷%d one-side reduction VALID)\n",TRANSV,TRANSV,NAUT);

  if(getenv("MATERIALIZE")){
    /* JIT pool materialiser: expand reps x amaps (or echo lines if expand=0) to stdout, one order
     * per line. Purely a cross-check aid — lets a brute `POOLVSPOOL=1 razor_screen <poolfile> 0 ...`
     * reproduce the JIT run's counts. The screen itself never needs the pool file. */
    char*obuf=malloc(1<<20); setvbuf(stdout,obuf,_IOFBF,1<<20);
    int nmap=EXPAND?NAUT:1;
    for(long r=0;r<Nr;r++){ const u8*rp=reps+r*q;
      for(int mi=0;mi<nmap;mi++){ int a=amaps[mi][0],b=amaps[mi][1];
        for(int i=0;i<q;i++){ int w=EXPAND?(int)((a*rp[i]+b)%q):rp[i]; printf(i?" %d":"%d",w); }
        putchar('\n');
      }
    }
    fflush(stdout); return 0;
  }

  /* hash set sizing: Mcap = expected distinct rmask ceiling (env MCAP overrides). */
  long guess = getenv("MCAP")? atol(getenv("MCAP")) : (Ntot<50000000L?Ntot:50000000L);
  Mcap = guess; HS=1; while(HS < (long)(guess*2.5)) HS<<=1; if(HS<1024)HS=1024;
  masks=malloc((size_t)Mcap*RW*8); if(!masks) die("masks malloc");
  HID=malloc((size_t)HS*sizeof(int)); if(!HID) die("HID malloc");
  for(long i=0;i<HS;i++) HID[i]=-1;
  for(int i=0;i<4096;i++) pthread_mutex_init(&hstripe[i],NULL);
  fprintf(stderr,"hash slots=%ld, Mcap=%ld (masks %.2f GB + HID %.2f GB)\n",
          HS,Mcap,(double)Mcap*RW*8/1e9,(double)HS*4/1e9);

  /* ---- PASS 1: distinct rmasks ---- */
  double p1=now_s();
  pthread_t th[16]; P1arg pa[16];
  for(int i=0;i<NTH;i++){ pa[i].lo=Nr*(long)i/NTH; pa[i].hi=Nr*(long)(i+1)/NTH; pthread_create(&th[i],NULL,p1_worker,&pa[i]); }
  long cnt=0,popsum=0; int minpop=1<<30,maxpop=0;
  for(int i=0;i<NTH;i++){ pthread_join(th[i],NULL); cnt+=pa[i].cnt; popsum+=pa[i].popsum; if(pa[i].minpop<minpop)minpop=pa[i].minpop; if(pa[i].maxpop>maxpop)maxpop=pa[i].maxpop; }
  fprintf(stderr,"PASS1: %ld orders, DISTINCT rmasks M=%ld  meanpop=%.1f range[%d,%d]  %.1fs\n",
          cnt,M,(double)popsum/cnt,minpop,maxpop,now_s()-p1);
  if(minpop==0){ fprintf(stderr,"ABORT: zero-popcount rmask exists -> razor useless (order double-backs no triangle in R); widen W\n"); return 2; }
  if(getenv("P1ONLY")){ printf("M=%ld pool=%ld meanpop=%.1f minpop=%d maxpop=%d\n",M,cnt,(double)popsum/cnt,minpop,maxpop); return 0; }

  /* ---- CANDIDATE SCAN: disjoint distinct-rmask pairs ---- */
  double cs=now_s();
  dang=calloc(M,1); next_i=0; ncand=0;
  W0=malloc((size_t)M*8); for(long i=0;i<M;i++) W0[i]=masks[(size_t)i*RW];
  for(int i=0;i<NTH;i++) pthread_create(&th[i],NULL,cand_worker,&cargs[i]);
  for(int i=0;i<NTH;i++) pthread_join(th[i],NULL);
  long nD=0; for(long i=0;i<M;i++) nD+=dang[i];
  long nself=0; char*selff=NULL;
  if(TRANSV>=1){                       /* same-rmask pairs can be transversal hits (never disjoint ones) */
    selff=calloc(M,1);
    for(long i=0;i<M;i++) if(win_transv_feasible(&masks[(size_t)i*RW],&masks[(size_t)i*RW])){ selff[i]=1; dang[i]=1; nself++; }
    nD=0; for(long i=0;i<M;i++) nD+=dang[i];
    fprintf(stderr,"SELF: %ld self-feasible rmasks kept as (i,i) candidates\n",nself);
  }
  fprintf(stderr,"CAND: %ld %s rmask-pairs (+%ld self), %ld/%ld dangerous rmasks  %.1fs\n",
          ncand,TRANSV>=1?"transversal-feasible":"disjoint",nself,nD,M,now_s()-cs);
  if(ncand==0 && nself==0){
    printf("RESULT screen=%s M=%ld pool=%ld candidates=0  => NO %s pair at the razor level => NONE on full DB => proven\n",
           fn,M,cnt,TRANSV>=1?"transversal-feasible":"razor-disjoint"); return 0; }

  if(getenv("MEASURE")){
    double kc=now_s(); KCarg ka[16]; long K=0;
    for(int i=0;i<NTH;i++){ ka[i].lo=Nr*(long)i/NTH; ka[i].hi=Nr*(long)(i+1)/NTH; pthread_create(&th[i],NULL,kc_worker,&ka[i]); }
    for(int i=0;i<NTH;i++){ pthread_join(th[i],NULL); K+=ka[i].cnt; }
    fprintf(stderr,"MEASURE: K=%ld dangerous orders (fullDB store = %.2f GB; src store = %.2f GB)  %.1fs\n",
            K,(double)K*FW*8/1e9,(double)K*8/1e9,now_s()-kc);
    printf("MEASURE screen=%s M=%ld pool=%ld rmask_cand_pairs=%ld dangerous_ids=%ld K=%ld\n",fn,M,cnt,ncand,nD,K);
    return 0;
  }

  /* ---- merge candidate pairs; build CSR adjacency of the candidacy graph ---- */
  npairs=ncand+nself; cpairs=malloc((size_t)(npairs?npairs:1)*sizeof(Pair)); long pp=0;
  for(int i=0;i<NTH;i++){ memcpy(&cpairs[pp],cargs[i].v,(size_t)cargs[i].n*sizeof(Pair)); pp+=cargs[i].n; free(cargs[i].v); }
  if(selff){ for(long i=0;i<M;i++) if(selff[i]){ cpairs[pp].a=(uint32_t)i; cpairs[pp].b=(uint32_t)i; pp++; } free(selff); }
  if(pp!=npairs) die("pair merge count mismatch");
  adj_start=calloc(M+1,8);
  for(long i=0;i<npairs;i++){ adj_start[cpairs[i].a+1]++; if(cpairs[i].b!=cpairs[i].a) adj_start[cpairs[i].b+1]++; }
  for(long i=0;i<M;i++) adj_start[i+1]+=adj_start[i];
  adj=malloc((size_t)2*npairs*4);
  { long *cur=malloc(M*8); for(long i=0;i<M;i++) cur[i]=adj_start[i];
    for(long i=0;i<npairs;i++){ uint32_t a=cpairs[i].a,b=cpairs[i].b; adj[cur[a]++]=b; if(b!=a) adj[cur[b]++]=a; } free(cur); }

  /* ---- PASS 2: collect (id,src) for dangerous pool orders, grouped by rmask id ---- */
  double p2=now_s();
  P2arg pb[16];
  for(int i=0;i<NTH;i++){ pb[i].lo=Nr*(long)i/NTH; pb[i].hi=Nr*(long)(i+1)/NTH; pthread_create(&th[i],NULL,p2_worker,&pb[i]); }
  for(int i=0;i<NTH;i++) pthread_join(th[i],NULL);
  long K=0; for(int i=0;i<NTH;i++) K+=pb[i].n;
  gstart=calloc(M+1,8);
  for(int i=0;i<NTH;i++) for(long k=0;k<pb[i].n;k++) gstart[pb[i].id[k]+1]++;
  for(long i=0;i<M;i++) gstart[i+1]+=gstart[i];
  GSRC=malloc((size_t)K*4);                /* u32 src grouped by rmask id */
  { long *cur=malloc(M*8); for(long i=0;i<M;i++) cur[i]=gstart[i];
    for(int i=0;i<NTH;i++){ for(long k=0;k<pb[i].n;k++){ uint32_t id=pb[i].id[k]; GSRC[cur[id]++]=pb[i].src[k]; } free(pb[i].id); free(pb[i].src); }
    free(cur); }
  MAXG=0; Dids=malloc(nD*8); nDids=0;
  for(long id=0;id<M;id++){ int g=(int)(gstart[id+1]-gstart[id]); if(g>0){ Dids[nDids++]=id; if(g>MAXG)MAXG=g; } }
  fprintf(stderr,"PASS2: K=%ld dangerous orders, %ld dangerous ids, maxgroup=%d  %.1fs\n",K,nDids,MAXG,now_s()-p2);

  /* ---- precompute all orbit-rep DBs + group reps by rmask id (Aut-reduced path only) ---- */
  if(!POOLVSPOOL){
    double rp=now_s();
    repDB=malloc((size_t)Nr*FW*8); repid=malloc(Nr*8);
    { RepArg ra[16]; for(int i=0;i<NTH;i++){ ra[i].lo=Nr*(long)i/NTH; ra[i].hi=Nr*(long)(i+1)/NTH; pthread_create(&th[i],NULL,rep_worker,&ra[i]); }
      for(int i=0;i<NTH;i++) pthread_join(th[i],NULL); }
    rep_gstart=calloc(M+1,8);
    for(long r=0;r<Nr;r++) rep_gstart[repid[r]+1]++;
    for(long i=0;i<M;i++) rep_gstart[i+1]+=rep_gstart[i];
    rep_ord=malloc((size_t)Nr*4);
    { long *cur=malloc(M*8); for(long i=0;i<M;i++) cur[i]=rep_gstart[i];
      for(long r=0;r<Nr;r++){ long id=repid[r]; rep_ord[cur[id]++]=(uint32_t)r; } free(cur); }
    fprintf(stderr,"REPDB: %ld rep DBs (%.2f GB) grouped by rmask  %.1fs\n",Nr,(double)Nr*FW*8/1e9,now_s()-rp);
  }

  /* ---- double-check: Aut-reduced (default) or full pool-vs-pool (POOLVSPOOL=1) ---- */
  double dc=now_s();
  next_did=0; DCarg da[16];
  for(int i=0;i<NTH;i++) pthread_create(&th[i],NULL, POOLVSPOOL? dc_worker_pvp : dc_worker, &da[i]);
  long checked=0, truezero=0, minov=1L<<60;
  FILE*hitf=fopen("razor_disjoint_hits.txt","w");
  for(int i=0;i<NTH;i++){ pthread_join(th[i],NULL);
    checked+=da[i].checked; truezero+=da[i].seedcount; if(da[i].minov<minov) minov=da[i].minov;
    for(long s=0;s<da[i].ns;s++){ u8 o1[64],o2[64];
      order_from_src(da[i].seedsrc[s*2],o1); order_from_src(da[i].seedsrc[s*2+1],o2);
      int f1=fwd_of_order(o1),f2=fwd_of_order(o2);
      if(TRANSV>=1){ uint32_t uc=da[i].seedu[s];
        if(uc==0xffffffffu) fprintf(hitf,"SEED k=%d U=empty (plain DB-disjoint!) fwd1=%d(delta%d) fwd2=%d(delta%d)\n",TRANSV,f1,543-f1,f2,543-f2);
        else if(TRANSV==1)  fprintf(hitf,"SEED k=1 U={%u} fwd1=%d(delta%d) fwd2=%d(delta%d)\n",uc,f1,543-f1,f2,543-f2);
        else                fprintf(hitf,"SEED k=2 U={%u,%u} fwd1=%d(delta%d) fwd2=%d(delta%d)\n",uc/64,uc%64,f1,543-f1,f2,543-f2);
      } else fprintf(hitf,"SEED overlap=0 fwd1=%d(delta%d) fwd2=%d(delta%d)\n",f1,543-f1,f2,543-f2);
      fprintf(hitf,"  O1:"); for(int t=0;t<q;t++) fprintf(hitf," %d",o1[t]); fprintf(hitf,"\n");
      fprintf(hitf,"  O2:"); for(int t=0;t<q;t++) fprintf(hitf," %d",o2[t]); fprintf(hitf,"\n"); }
    free(da[i].seedsrc); free(da[i].seedu);
  }
  fclose(hitf);
  const char*mlabel = POOLVSPOOL? (TRANSV==1?"poolvspool-transv1":TRANSV==2?"poolvspool-transv2":"poolvspool")
                                : (TRANSV==1?"transv1":TRANSV==2?"transv2":"autreduced");
  fprintf(stderr,"DOUBLECHECK[%s]: %ld order-pairs checked, %s=%ld, %s=%ld  %.1fs\n",
          mlabel,checked,TRANSV>=1?"TRUE-HITS":"TRUE-DISJOINT",truezero,
          TRANSV==1?"min_residual":TRANSV==2?"min_residual_lb":"min_overlap",minov,now_s()-dc);
  printf("RESULT mode=%s screen=%s M=%ld pool=%ld rmask_cand_pairs=%ld self_pairs=%ld dangerous=%ld K=%ld pairs_checked=%ld %s=%ld %s=%ld\n",
         mlabel,fn,M,cnt,ncand,nself,nD,K,checked,
         TRANSV>=1?"TRUE_HITS":"TRUE_DISJOINT",truezero,
         TRANSV==1?"min_residual":TRANSV==2?"min_residual_lb":"min_overlap",minov);
  if(TRANSV>=1){
    if(truezero==0) printf("  => NO pair in this shell has a DB-overlap with a <=%d-vertex transversal => NO DB-disjoint P-minus-%d-vertices pair at these levels, for ANY deleted %d-set => co-backing pair obstruction holds AT THIS SHELL\n",TRANSV,TRANSV,TRANSV);
    else            printf("  => %ld transversal HIT candidate pair(s) — post-filter by projected P-S levels (c(u) bookkeeping), then completion search; see razor_disjoint_hits.txt\n",truezero);
  } else if(DROPV>=0){
    if(truezero==0) printf("  => NO two orders of this shell have disjoint P-v double-back sets (v=%d)  => necessary condition for P-v non-5-realizability holds AT THIS SHELL (top-two live at level<=6; not a full proof unless the shell reaches level 6)\n",DROPV);
    else            printf("  => %ld disjoint P-v pairs found — the pair-obstruction does NOT hold for P-v at this shell; see razor_disjoint_hits.txt\n",truezero);
  } else {
    if(truezero==0) printf("  => NO two delta<=1 orders are DB-disjoint over this pool  => Paley(%d) has NO 5-realization\n",q);
    else            printf("  => %ld DB-DISJOINT SEED pairs found — Paley(%d) may be 5-realizable; see razor_disjoint_hits.txt\n",truezero,q);
  }
  return 0;
}
