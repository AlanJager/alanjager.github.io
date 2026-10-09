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

static volatile uint64_t sink;
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
static uint64_t pte(void *p,size_t ps) {
    int fd=open("/proc/self/pagemap",O_RDONLY); uint64_t v=0;
    if(fd<0 || pread(fd,&v,8,((uintptr_t)p/ps)*8)!=8){perror("pagemap");exit(1);}
    close(fd);return v;
}
static uint64_t value(size_t w) {
    uint64_t v=0x9e3779b97f4a7c15ULL+(w%128);
    v=(v^(v>>30))*0xbf58476d1ce4e5b9ULL;
    v=(v^(v>>27))*0x94d049bb133111ebULL;
    return v^(v>>31);
}
static uint64_t timed_read(volatile uint64_t *v) {
    uint64_t t=ns();sink=*v;return ns()-t;
}
static uint64_t timed_write(volatile uint64_t *v,uint64_t value) {
    uint64_t t=ns();*v=value;return ns()-t;
}
int main(int argc,char **argv) {
    if(argc!=4)return 1;
    const char *backend=argv[1],*mode=argv[2];int target=atoi(argv[3]);
    int cram=!strcmp(backend,"cram"),zram=!strcmp(backend,"zram");
    int direct=!strcmp(mode,"direct"),rw=!strcmp(mode,"readwrite");
    cpu_set_t cpus;CPU_ZERO(&cpus);CPU_SET(0,&cpus);
    if(sched_setaffinity(0,sizeof(cpus),&cpus)){perror("affinity");return 1;}
    put("tracing_on","0");put("current_tracer","nop");put("events/enable","0");
    size_t ps=sysconf(_SC_PAGESIZE);int pm=open("/proc/self/pagemap",O_RDONLY);
    if(pm<0)return 1;
    (void)ns();sink=0;
    unsigned success=0,failed=0;
    printf("CONFIG %s %s cpu=%d pages=1 bytes=%zu wanted=1000 max_attempts=1200 tracer=nop events=0\n",backend,mode,sched_getcpu(),ps);
    for(unsigned attempt=0;attempt<1200&&success<1000;attempt++) {
      uint64_t *buf=mmap(NULL,ps,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
      if(buf==MAP_FAILED)return 1;
      for(size_t w=0;w<ps/8;w++)buf[w]=value(w);
      unsigned tries=0;int enter_ok=1;uint64_t begin=ns();
      if(cram){void *p=buf;int st=-999;enter_ok=syscall(SYS_move_pages,0,1,&p,&target,&st,0)==0&&st==target;}
      else if(zram){do{if(madvise(buf,ps,MADV_PAGEOUT)){enter_ok=0;break;}tries++;
        if(pte(buf,ps)&(1ULL<<62))break;
        usleep(1000);
      }while(tries<100);}
      uint64_t enter=ns()-begin,e=pte(buf,ps);int en=node(buf);
      enter_ok=enter_ok&&(cram?((e&(1ULL<<63))&&en==target):zram?((e&(1ULL<<62))&&!(e&(1ULL<<63))):((e&(1ULL<<63))&&en==0));
      if(!enter_ok){printf("FAIL,%s,%s,%u,entry,%u\n",backend,mode,attempt,tries);failed++;munmap(buf,ps);continue;}
      uint64_t rd=0,rr=0,wr=0,rwr=0;int rn=-999,wn=-999,valid=1;
      volatile uint64_t *v=buf;
      if(!direct){rd=timed_read(v);if(!rw)rr=timed_read(v);
        rn=node(buf);e=pte(buf,ps);valid=(e&(1ULL<<63))&&!(e&(1ULL<<62))&&(cram?rn==target:rn==0);}
      if(direct||rw){wr=timed_write(v,0xfeed123456789abcULL);rwr=timed_write(v,0xabcd123456789abcULL);
        wn=node(buf);e=pte(buf,ps);valid=valid&&(e&(1ULL<<63))&&!(e&(1ULL<<62))&&wn==0;}
      for(size_t w=0;w<ps/8;w++){uint64_t expected=((direct||rw)&&w==0)?0xabcd123456789abcULL:value(w);if(buf[w]!=expected)valid=0;}
      if(sched_getcpu()!=0)valid=0;
      if(!valid){printf("FAIL,%s,%s,%u,state_or_data,%u\n",backend,mode,attempt,tries);failed++;}
      else{printf("SAMPLE,%s,%s,%u,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%u,%d,%d,%d\n",backend,mode,attempt,enter,rd,rr,wr,rwr,tries,en,rn,wn);success++;}
      munmap(buf,ps);
    }
    for(int i=0;i<1000;i++){uint64_t t=ns();uint64_t d=ns()-t;printf("CLOCK,%s,%s,%d,%" PRIu64 "\n",backend,mode,i,d);}
    printf("SUMMARY %s %s success=%u failed=%u\n",backend,mode,success,failed);close(pm);
    return success==1000?0:2;
}
