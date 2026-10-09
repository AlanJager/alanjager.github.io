#define _GNU_SOURCE
#include <errno.h>
#include <sched.h>
#include <sys/resource.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

static void put(const char *name, const char *value) {
    char path[256]; snprintf(path,sizeof(path),"/sys/kernel/tracing/%s",name);
    int fd=open(path,O_WRONLY|O_TRUNC); if(fd<0){perror(path);exit(1);}
    size_t left=strlen(value);
    while(left) {
        ssize_t n=write(fd,value,left);
        if(n<=0){perror(path);exit(1);}
        value+=n;left-=(size_t)n;
    }
    close(fd);
}
static uint64_t ns(void) {
    struct timespec t; if(clock_gettime(CLOCK_MONOTONIC_RAW,&t)){perror("clock");exit(1);}
    return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;
}
static int node(void *p) {
    int status=-999;
    long rc=syscall(SYS_move_pages,0,1,&p,NULL,&status,0);
    if(rc<0){perror("move_pages query");exit(1);} return status;
}
static uint64_t value(size_t w) {
    uint64_t v=0x9e3779b97f4a7c15ULL+(w%128);
    v=(v^(v>>30))*0xbf58476d1ce4e5b9ULL;
    v=(v^(v>>27))*0x94d049bb133111ebULL;
    return v^(v>>31);
}
static void snapshot(const char *phase,void *buf,size_t bytes,size_t ps) {
 size_t pages=bytes/ps;int pm=open("/proc/self/pagemap",O_RDONLY);
 size_t n0=0,n2=0,sw=0,other=0;size_t stride=64;
 for(size_t i=0;i<pages;i+=stride){void *p=(char*)buf+i*ps;uint64_t e;
   if(pread(pm,&e,8,((uintptr_t)p/ps)*8)!=8)exit(1);
   if(e&(1ULL<<62))sw++;else if(e&(1ULL<<63)){int n=node(p);if(n==0)n0++;else if(n==2)n2++;else other++;}else other++;
 }
 close(pm);printf("DISTRIBUTION %s bytes=%zu stride_pages=64 node0=%zu node2=%zu swapped=%zu other=%zu\n",phase,bytes,n0,n2,sw,other);fflush(stdout);
 const char *files[]={"/proc/meminfo","/proc/vmstat","/sys/block/zram0/mm_stat","/proc/pressure/memory"};
 for(unsigned i=0;i<4;i++){FILE *f=fopen(files[i],"r");if(!f)continue;char line[512];printf("SNAPSHOT_BEGIN %s %s\n",phase,files[i]);while(fgets(line,sizeof(line),f))fputs(line,stdout);fclose(f);printf("SNAPSHOT_END %s %s\n",phase,files[i]);}fflush(stdout);
}
int main(int argc,char **argv){
 if(argc!=3)return 1;
 int target=atoi(argv[2]);size_t ps=sysconf(_SC_PAGESIZE);
 put("tracing_on","0");put("current_tracer","nop");put("events/enable","0");
 if(!strcmp(argv[1],"probe")){
   uint64_t *buf=mmap(NULL,ps,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);if(buf==MAP_FAILED)return 1;
   for(size_t w=0;w<ps/8;w++)buf[w]=value(w);
   void *a=buf;int st=-999;long rc=syscall(SYS_move_pages,0,1,&a,&target,&st,0);int en=errno;
   printf("MIGRATION_PROBE rc=%ld errno=%d status=%d node=%d\n",rc,rc<0?en:0,st,node(buf));
   for(size_t w=0;w<ps/8;w++)if(buf[w]!=value(w))return 3;
   puts("PROBE_DATA_PASS");munmap(buf,ps);return 0;
 }
 const size_t len=480UL*1024*1024,chunk=16UL*1024*1024;
 uint64_t *buf=mmap(NULL,len,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);if(buf==MAP_FAILED)return 1;
 FILE *adj=fopen("/proc/self/oom_score_adj","w");if(adj){fputs("1000",adj);fclose(adj);}
 printf("WORKLOAD %s bytes=%zu chunk=%zu\n",argv[1],len,chunk);fflush(stdout);
 for(size_t end=chunk;end<=len;end+=chunk){
   for(size_t p=(end-chunk)/ps;p<end/ps;p++)for(size_t w=0;w<ps/8;w++)buf[p*ps/8+w]=value(w);
   printf("ALLOC_STEP %s bytes=%zu\n",argv[1],end);fflush(stdout);usleep(100000);
 }
 sleep(2);snapshot("cold",buf,len,ps);snapshot("cold_target",buf,64UL*1024*1024,ps);
 size_t warm=64UL*1024*1024;uint64_t begin=ns();
 for(size_t p=0;p<warm/ps;p++)buf[p*ps/8]=0xfeed123456789abcULL;
 printf("WARM_WRITE ns=%" PRIu64 " bytes=%zu\n",ns()-begin,warm);snapshot("warm",buf,len,ps);snapshot("warm_target",buf,warm,ps);
 for(size_t p=0;p<len/ps;p++)for(size_t w=0;w<ps/8;w++){
   uint64_t want=(p<warm/ps&&w==0)?0xfeed123456789abcULL:value(w);
   if(buf[p*ps/8+w]!=want){puts("WORKLOAD_DATA_FAIL");return 3;}
 }
 puts("WORKLOAD_DATA_PASS");munmap(buf,len);return 0;
}
