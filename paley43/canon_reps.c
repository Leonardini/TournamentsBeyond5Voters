/* canon_reps.c — canonicalize + dedup orbit reps of Paley(q), print distinct count.
 * Mirrors dp43 close()'s canonicalization (lexmin image over the NAUT=|Aut| maps) but
 * SKIPS the full-pool expansion. Used to (a) validate enum completeness against the census
 * orbit count and (b) emit clean deduped reps for the disjointness screen.
 * Usage: canon_reps <raw_file> <out_reps_file>   (q=43)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>
typedef uint8_t u8;
static double now_s(void){ struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts); return ts.tv_sec+ts.tv_nsec/1e9; }
static int q=43,NQR,NAUT,qrl[64],amaps[1024][2];
static u8 *raw; static long N;
static u8 *canon;             /* [N][q] canonical images */

static void build_group(void){
  int isqr[64]={0}; for(long x=1;x<q;x++) isqr[(x*x)%q]=1;
  NQR=0; for(int s=1;s<q;s++) if(isqr[s]) qrl[NQR++]=s; NAUT=NQR*q;
  int m=0; for(int ai=0;ai<NQR;ai++) for(int b=0;b<q;b++){ amaps[m][0]=qrl[ai]; amaps[m][1]=b; m++; }
}
typedef struct{ long lo,hi; } Arg;
static void* worker(void*vp){ Arg*A=vp; u8 best[64],img[64];
  for(long r=A->lo;r<A->hi;r++){ const u8*o=raw+r*q; memset(best,0xff,q);
    for(int mi=0;mi<NAUT;mi++){ int a=amaps[mi][0],b=amaps[mi][1];
      for(int t=0;t<q;t++) img[t]=(u8)((a*o[t]+b)%q);
      if(memcmp(img,best,q)<0) memcpy(best,img,q);
    }
    memcpy(canon+r*q,best,q);
  }
  return NULL;
}
static int cmprow(const void*a,const void*b){ return memcmp(a,b,43); }
int main(int argc,char**argv){
  if(argc<3){ fprintf(stderr,"usage: %s raw_file out_reps\n",argv[0]); return 1; }
  build_group();
  double t0=now_s();
  FILE*f=fopen(argv[1],"r"); if(!f){perror("open");return 1;}
  long cap=1<<16; raw=malloc((size_t)cap*q); N=0;
  for(;;){ int v,ok=1; for(int t=0;t<q;t++){ if(fscanf(f,"%d",&v)!=1){ok=0;break;} raw[N*q+t]=(u8)v; }
    if(!ok) break; if(++N==cap){cap*=2; raw=realloc(raw,(size_t)cap*q);} }
  fclose(f);
  fprintf(stderr,"loaded %ld raw orders  %.1fs\n",N,now_s()-t0);
  canon=malloc((size_t)N*q);
  int NTH=8; pthread_t th[8]; Arg ar[8];
  double t1=now_s();
  for(int i=0;i<NTH;i++){ ar[i].lo=N*(long)i/NTH; ar[i].hi=N*(long)(i+1)/NTH; pthread_create(&th[i],NULL,worker,&ar[i]); }
  for(int i=0;i<NTH;i++) pthread_join(th[i],NULL);
  fprintf(stderr,"canonicalized  %.1fs\n",now_s()-t1);
  qsort(canon,(size_t)N,q,cmprow);
  long R = N?1:0;
  for(long r=1;r<N;r++) if(memcmp(canon+r*q,canon+(R-1)*q,q)){ memcpy(canon+R*q,canon+r*q,q); R++; }
  FILE*o=fopen(argv[2],"w");
  for(long r=0;r<R;r++){ for(int t=0;t<q;t++) fprintf(o,"%d%c",canon[r*q+t],t==q-1?'\n':' '); }
  fclose(o);
  printf("raw=%ld distinct_orbits=%ld  (census delta<=1 = 1841303)  -> %s\n",N,R,argv[2]);
  return 0;
}
