#define _GNU_SOURCE
#include <errno.h>
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

static int marker;
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
static void mark(const char *v){if(write(marker,v,strlen(v))<0){perror("marker");exit(1);}}
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
static void state(const char *label,void *p,size_t ps) {
    uint64_t v=pte(p,ps);
    printf("STATE %s pte=0x%016" PRIx64 " present=%d swapped=%d node=%d\n",
      label,v,!!(v&(1ULL<<63)),!!(v&(1ULL<<62)),node(p));fflush(stdout);
}
int main(int argc,char **argv) {
    if(argc!=4){fprintf(stderr,"usage: probe cram|zram direct|readwrite|readrepeat node\n");return 1;}
    int cram=!strcmp(argv[1],"cram"),target=atoi(argv[3]);
    int direct=!strcmp(argv[2],"direct"),readwrite=!strcmp(argv[2],"readwrite");
    size_t ps=sysconf(_SC_PAGESIZE);
    uint64_t *buf=mmap(NULL,ps,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(buf==MAP_FAILED){perror("mmap");return 1;}
    for(size_t w=0;w<ps/8;w++)buf[w]=value(w);
    (void)ns();sink=0;
    printf("CASE %s_%s pid=%d target=%p pages=1 bytes=%zu\n",argv[1],argv[2],getpid(),(void*)buf,ps);fflush(stdout);
    put("tracing_on","0");put("buffer_size_kb","4096");put("current_tracer","function_graph");
    put("set_graph_function","cram_migrate_to cram_handle_fault handle_mm_fault do_wp_page do_swap_page __swap_writepage zcomp_compress zcomp_decompress\n");
    char pid[32];snprintf(pid,sizeof(pid),"%d",getpid());put("set_ftrace_pid",pid);
    FILE *gf=fopen("/sys/kernel/tracing/set_graph_function","r");
    if(gf){char line[256];while(fgets(line,sizeof(line),gf))printf("GRAPH_ROOT %s",line);fclose(gf);}
    char filter[64];snprintf(filter,sizeof(filter),"common_pid == %d",getpid());
    put("events/exceptions/page_fault_user/filter",filter);put("events/exceptions/page_fault_user/enable","1");
    put("trace","");put("tracing_on","1");
    marker=open("/sys/kernel/tracing/trace_marker",O_WRONLY);if(marker<0){perror("marker");return 1;}
    mark("ENTER_BEGIN\n");
    if(cram){void *p=buf;int status=-999;
      if(syscall(SYS_move_pages,0,1,&p,&target,&status,0)!=0||status!=target){puts("ENTER_FAIL");return 2;}
    }else {
      unsigned tries=0;
      do {
        if(madvise(buf,ps,MADV_PAGEOUT)){perror("pageout");return 2;}
        tries++;
        if(pte(buf,ps)&(1ULL<<62))break;
        usleep(1000);
      }while(tries<100);
      printf("PAGEOUT_ATTEMPTS %u\n",tries);
    }
    mark("ENTER_END\n");state("entered",buf,ps);
    uint64_t e=pte(buf,ps);
    if(cram ? (!(e&(1ULL<<63))||node(buf)!=target) : (!(e&(1ULL<<62))||(e&(1ULL<<63)))){puts("PRECONDITION_FAIL");return 2;}
    volatile uint64_t *v=buf;
    if(!direct){mark("READ_BEGIN\n");sink=*v;mark("READ_END\n");state("after_read",buf,ps);
      e=pte(buf,ps);if(cram ? node(buf)!=target : (!(e&(1ULL<<63))||(e&(1ULL<<62)))){puts("READ_STATE_FAIL");return 3;}
    }
    if(direct||readwrite){mark("WRITE_BEGIN\n");*v=0xfeed123456789abcULL;mark("WRITE_END\n");state("after_write",buf,ps);
      e=pte(buf,ps);if(!(e&(1ULL<<63))||(e&(1ULL<<62))||(cram&&node(buf)==target)){puts("WRITE_STATE_FAIL");return 3;}
      mark("REPEAT_WRITE_BEGIN\n");*v=0xabcd123456789abcULL;mark("REPEAT_WRITE_END\n");state("after_repeat_write",buf,ps);
    }else{mark("REPEAT_READ_BEGIN\n");sink=*v;mark("REPEAT_READ_END\n");state("after_repeat_read",buf,ps);}
    put("tracing_on","0");
    for(size_t w=0;w<ps/8;w++) {
      uint64_t expected=((direct||readwrite)&&w==0)?0xabcd123456789abcULL:value(w);
      if(buf[w]!=expected){puts("DATA_FAIL");return 4;}
    }
    puts("DATA_PASS");close(marker);munmap(buf,ps);return 0;
}
