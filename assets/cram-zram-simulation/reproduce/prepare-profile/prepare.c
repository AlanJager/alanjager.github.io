#define _GNU_SOURCE
#include <fcntl.h>
#include <inttypes.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;}
static void put(const char*n,const char*v){char p[256];snprintf(p,sizeof(p),"/sys/kernel/tracing/%s",n);int fd=open(p,O_WRONLY|O_TRUNC);if(fd<0){perror(p);exit(2);}if(write(fd,v,strlen(v))!=(ssize_t)strlen(v))exit(2);close(fd);}
static uint64_t value(size_t w){uint64_t v=0x9e3779b97f4a7c15ULL+(w%128);v=(v^(v>>30))*0xbf58476d1ce4e5b9ULL;v=(v^(v>>27))*0x94d049bb133111ebULL;return v^(v>>31);}
int main(int argc,char**argv){if(argc!=2)return 2;int target=atoi(argv[1]);cpu_set_t cp;CPU_ZERO(&cp);CPU_SET(0,&cp);if(sched_setaffinity(0,sizeof(cp),&cp))return 2;
 put("tracing_on","0");put("current_tracer","nop");put("events/enable","0");
 char pid[32],filter[128];snprintf(pid,sizeof(pid),"%d",getpid());put("set_ftrace_pid",pid);snprintf(filter,sizeof(filter),"prev_pid == %d || next_pid == %d",getpid(),getpid());put("events/sched/sched_switch/filter",filter);
 put("buffer_size_kb","8192");put("trace","");put("set_graph_function","__x64_sys_move_pages");
 put("options/funcgraph-abstime","1");put("options/funcgraph-proc","1");put("options/sleep-time","1");
 for(int traced=0;traced<2;traced++){
 if(traced){put("current_tracer","function_graph");put("events/sched/sched_switch/enable","1");put("tracing_on","1");}
 int mark=open("/sys/kernel/tracing/trace_marker",O_WRONLY);
 for(unsigned i=0;i<(traced?40:200);i++){
 uint64_t *b=mmap(NULL,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);if(b==MAP_FAILED)return 2;for(size_t w=0;w<512;w++)b[w]=value(w);
 if(traced){char m[64];int len=snprintf(m,sizeof(m),"MOVE_BEGIN %u\n",i);if(write(mark,m,(size_t)len)!=len)return 2;}
 void*p=b;int status=-999;uint64_t t=ns();long rc=syscall(SYS_move_pages,0,1,&p,&target,&status,0);uint64_t d=ns()-t;
 if(traced){char m[64];int len=snprintf(m,sizeof(m),"MOVE_END %u\n",i);if(write(mark,m,(size_t)len)!=len)return 2;}
 if(rc||status!=target){puts("MOVE_FAIL");return 3;}
 ((volatile uint64_t*)b)[0]=0xfeed123456789abcULL;
 for(size_t w=0;w<512;w++)if(b[w]!=(w==0?0xfeed123456789abcULL:value(w))){puts("DATA_FAIL");return 3;}
 printf("PREPARE_SAMPLE traced=%d attempt=%u ns=%"PRIu64"\n",traced,i,d);munmap(b,4096);
 }
 close(mark);put("tracing_on","0");
 }
 FILE *in=fopen("/sys/kernel/tracing/trace","r"),*out=fopen("/tmp/move.trace","w");if(!in||!out)return 2;char b[4096];size_t n;while((n=fread(b,1,sizeof(b),in)))fwrite(b,1,n,out);fclose(in);fclose(out);puts("PREPARE_DATA_PASS");return 0;
}
