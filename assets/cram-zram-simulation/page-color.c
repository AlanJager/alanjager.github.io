#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#define LEN (480UL*1024*1024)
#define WARM (64UL*1024*1024)
#define STRIDE 64
#define SAMPLES (LEN/4096/STRIDE)
#define CAP 2000
static unsigned char *buf,*versions;
static uint64_t *pm;
static void **addresses;
static int *nodes;
static char *maps;
static uint64_t starts[CAP],ends[CAP],epoch;
static unsigned count;static atomic_int done;static int active;
static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;}
static void pin(int cpu){cpu_set_t set;CPU_ZERO(&set);CPU_SET(cpu,&set);if(pthread_setaffinity_np(pthread_self(),sizeof(set),&set)){perror("affinity");exit(2);}}
static uint64_t value(size_t w){uint64_t v=0x9e3779b97f4a7c15ULL+(w%128);v=(v^(v>>30))*0xbf58476d1ce4e5b9ULL;v=(v^(v>>27))*0x94d049bb133111ebULL;return v^(v>>31);}
static void snap(int fd){if(count==CAP)return;unsigned k=count;starts[k]=ns()-epoch;size_t pages=LEN/4096;
 if(pread(fd,pm,pages*8,((uintptr_t)buf/4096)*8)!=(ssize_t)(pages*8)){perror("pagemap");exit(3);}
 for(size_t i=0;i<SAMPLES;i++)nodes[i]=-999;
 long rc=syscall(SYS_move_pages,0,SAMPLES,addresses,NULL,nodes,0);if(rc<0){perror("query");exit(3);}
 for(size_t i=0;i<SAMPLES;i++){uint64_t e=pm[i*STRIDE];char c='U';if(e&(1ULL<<62))c='S';else if(e&(1ULL<<63)){if(nodes[i]==0)c='D';else if(nodes[i]==2)c='C';}maps[k*SAMPLES+i]=c;}
 ends[k]=ns()-epoch;count++;
}
static void *observe(void *x){(void)x;pin(1);int fd=open("/proc/self/pagemap",O_RDONLY);if(fd<0)exit(3);while(!atomic_load(&done)){snap(fd);usleep(20000);}close(fd);return NULL;}
int main(int argc,char **argv){if(argc!=2)return 2;active=atoi(argv[1]);if(sysconf(_SC_PAGESIZE)!=4096)return 2;pin(0);
 size_t pages=LEN/4096;buf=mmap(NULL,LEN,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);if(buf==MAP_FAILED)return 2;
 versions=calloc(pages,1);pm=calloc(pages,8);addresses=calloc(SAMPLES,sizeof(void*));nodes=calloc(SAMPLES,sizeof(int));maps=calloc(CAP*SAMPLES,1);
 if(!versions||!pm||!addresses||!nodes||!maps)return 2;
 /* Same observer storage in both runs; pre-touch it before the workload. */
 memset(pm,1,pages*8);memset(maps,'U',CAP*SAMPLES);
 for(size_t i=0;i<SAMPLES;i++)addresses[i]=buf+i*STRIDE*4096;
 for(size_t start=0;start<LEN;start+=16UL*1024*1024){for(size_t p=start/4096;p<(start+16UL*1024*1024)/4096;p++)for(size_t w=0;w<512;w++)((uint64_t*)buf)[p*512+w]=value(w);usleep(100000);}
 sleep(2);epoch=ns();pthread_t thread;pthread_attr_t attr;pthread_attr_init(&attr);pthread_attr_setstacksize(&attr,128*1024);
 int fd=open("/proc/self/pagemap",O_RDONLY);snap(fd);close(fd);
 if(active&&pthread_create(&thread,&attr,observe,NULL))return 2;
 usleep(100000);uint64_t t=ns();
 for(size_t p=0;p<WARM/4096;p++){((volatile uint64_t*)buf)[p*512]=0xfeed123456789a00ULL+1;versions[p]=1;}
 printf("WRITE original round=0 start_page=0 pages=%zu ns=%"PRIu64" begin=%"PRIu64" end=%"PRIu64"\n",WARM/4096,ns()-t,t-epoch,ns()-epoch);fflush(stdout);usleep(500000);
 for(unsigned round=0;round<24;round++){size_t start=(round%8)*WARM;size_t end=start+WARM;if(end>LEN)end=LEN;t=ns();
 for(size_t p=start/4096;p<end/4096;p++){((volatile uint64_t*)buf)[p*512]=0xfeed123456789a00ULL+(round+2);versions[p]=(unsigned char)(round+2);}
 printf("WRITE rotating round=%u start_page=%zu pages=%zu ns=%"PRIu64" begin=%"PRIu64" end=%"PRIu64"\n",round,start/4096,(end-start)/4096,ns()-t,t-epoch,ns()-epoch);fflush(stdout);usleep(100000);}
 usleep(500000);atomic_store(&done,1);if(active)pthread_join(thread,NULL);fd=open("/proc/self/pagemap",O_RDONLY);snap(fd);close(fd);
 for(unsigned k=0;k<count;k++){
 printf("RLE %"PRIu64" %"PRIu64" ",starts[k],ends[k]);
 size_t begin=0;while(begin<SAMPLES){size_t end=begin+1;char c=maps[k*SAMPLES+begin];while(end<SAMPLES&&maps[k*SAMPLES+end]==c)end++;printf("%c%zu,",c,end-begin);begin=end;}puts("");
 }
 printf("OBSERVER active=%d snapshots=%u cap=%d stride=%d\n",active,count,CAP,STRIDE);fflush(stdout);
 for(size_t p=0;p<pages;p++)for(size_t w=0;w<512;w++){uint64_t want=(w==0&&versions[p])?0xfeed123456789a00ULL+versions[p]:value(w);if(((volatile uint64_t*)buf)[p*512+w]!=want){printf("DATA_FAIL page=%zu word=%zu\n",p,w);return 4;}}
 puts("DATA_PASS");return 0;
}
