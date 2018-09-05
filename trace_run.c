#define _LARGEFILE64_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <pthread.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/resource.h>
#include <fcntl.h>
#include <unistd.h>

// #include "malloc.h"
#include <malloc.h>

// #include "mtrace.h"
/* Codes for the simulator/workload programs. Copied from mtrace.h. */
#define C_NOP 0
#define C_DONE 1
#define C_MALLOC 2
#define C_CALLOC 3
#define C_REALLOC 4
#define C_FREE 5
#define C_SYNC_W 6
#define C_SYNC_R 7
#define C_ALLOC_PTRS 8
#define C_ALLOC_SYNCS 9
#define C_NTHREADS 10
#define C_START_THREAD 11
#define C_MEMALIGN 12
#define C_VALLOC 13
#define C_PVALLOC 14
#define C_POSIX_MEMALIGN 15

#if UINTPTR_MAX == 0xffffffffffffffff

#define ticks_t int64_t
/* Setting quick_run to 1 allows the simulator to model
   only the allocation and deallocation accounting via
   atomic_rss. The actual allocations are skipped.  This
   mode is useful to verify the workload file.  */
#define quick_run 0

static __inline__ ticks_t rdtsc_s(void)
{
  unsigned a, d;
  asm volatile("cpuid" ::: "%rax", "%rbx", "%rcx", "%rdx");
  asm volatile("rdtscp" : "=a" (a), "=d" (d));
  return ((unsigned long long)a) | (((unsigned long long)d) << 32);
}

static __inline__ ticks_t rdtsc_e(void)
{
  unsigned a, d;
  asm volatile("rdtscp" : "=a" (a), "=d" (d));
  asm volatile("cpuid" ::: "%rax", "%rbx", "%rcx", "%rdx");
  return ((unsigned long long)a) | (((unsigned long long)d) << 32);
}

#else

#define ticks_t int32_t

static __inline__ ticks_t rdtsc_s(void)
{
  unsigned a, d;
  asm volatile("cpuid" ::: "%ax", "%bx", "%cx", "%dx");
  asm volatile("rdtsc" : "=a" (a), "=d" (d));
  return ((unsigned long)a) | (((unsigned long)d) << 16);
}

static __inline__ ticks_t rdtsc_e(void)
{
  unsigned a, d;
  asm volatile("rdtscp" : "=a" (a), "=d" (d));
  asm volatile("cpuid" ::: "%ax", "%bx", "%cx", "%dx");
  return ((unsigned long)a) | (((unsigned long)d) << 16);
}

#endif

static ticks_t diff_timeval (struct timeval e, struct timeval s)
{
  ticks_t usec;
  if (e.tv_usec < s.tv_usec)
    usec = (e.tv_usec + 1000000 - s.tv_usec) + (e.tv_sec-1 - s.tv_sec)*1000000;
  else
    usec = (e.tv_usec - s.tv_usec) + (e.tv_sec - s.tv_sec)*1000000;
  return usec;
}

#if 1
#define Q1
#define Q2
#else
pthread_mutex_t genmutex = PTHREAD_MUTEX_INITIALIZER;
#define Q1   pthread_mutex_lock(&genmutex)
#define Q2   pthread_mutex_unlock(&genmutex)
#endif

pthread_mutex_t cmutex = PTHREAD_MUTEX_INITIALIZER;
#define NCBUF 10
static char cbuf[NCBUF][30];
static int ci = 0;

char *comma(ticks_t x)
{
  char buf[30], *bs, *bd;
  int l, i, idx;

  pthread_mutex_lock(&cmutex);
  ci = (ci + 1) % NCBUF;
  idx = ci;
  pthread_mutex_unlock(&cmutex);
  bs = buf;
  bd = cbuf[idx];

  sprintf(buf, "%lld", (long long int)x);
  l = strlen(buf);
  i = l;
  while (*bs)
    {
      *bd++ = *bs++;
      i--;
      if (i % 3 == 0 && *bs)
	*bd++ = ',';
    }
  *bd = 0;
  return cbuf[idx];
}

static volatile void **ptrs;
static volatile size_t *sizes;
static size_t n_ptrs;
static volatile char *syncs;
static pthread_mutex_t *mutexes;
static pthread_cond_t *conds;
static size_t n_syncs;

static pthread_mutex_t stat_mutex = PTHREAD_MUTEX_INITIALIZER;
ticks_t malloc_time = 0, malloc_count = 0;
ticks_t calloc_time = 0, calloc_count = 0;
ticks_t realloc_time = 0, realloc_count = 0;
ticks_t free_time = 0, free_count = 0;

size_t ideal_rss = 0;
size_t max_ideal_rss = 0;
static pthread_mutex_t rss_mutex = PTHREAD_MUTEX_INITIALIZER;

void atomic_rss (ssize_t delta)
{
  pthread_mutex_lock (&rss_mutex);
  ideal_rss += delta;
  if (max_ideal_rss < ideal_rss)
    max_ideal_rss = ideal_rss;
  pthread_mutex_unlock (&rss_mutex);
}

pthread_mutex_t stop_mutex = PTHREAD_MUTEX_INITIALIZER;
int threads_done = 0;

//#define dprintf printf
#define dprintf(...) (void)1

//#define mprintf printf
//#define MDEBUG 1
#define mprintf(...) (void)1

#define myabort() my_abort_2(thrc, __LINE__)
void
my_abort_2 (pthread_t thrc, int line)
{
  fprintf(stderr, "Abort thread %p at line %d\n", (void *)thrc, line);
  abort();
}

/*------------------------------------------------------------*/
/* Wrapper around I/O routines */

int io_fd;

#define IOSIZE 65536
#define IOMIN 4096

static pthread_mutex_t io_mutex = PTHREAD_MUTEX_INITIALIZER;

typedef struct {
  unsigned char buf[IOSIZE];
  size_t incr;
  size_t max_incr;
  size_t buf_base;
  size_t buf_idx;
  int saw_eof;
} IOPerThreadType;

IOPerThreadType main_io;
IOPerThreadType *thread_io;

void
io_init (IOPerThreadType *io, size_t file_offset, int incr)
{
  if (incr > IOSIZE)
    incr = IOSIZE;
  if (incr < IOMIN)
    incr = IOMIN;

  io->buf_base = file_offset;
  io->buf_idx = 0;
  io->incr = incr;

  pthread_mutex_lock (&io_mutex);
  lseek64 (io_fd, io->buf_base, SEEK_SET);
  // short read OK, the eof is just to prevent runaways from bad data.
  if (read (io_fd, io->buf, incr) < 0)
    io->saw_eof = 1;
  else
    io->saw_eof = 0;
  pthread_mutex_unlock (&io_mutex);
}

unsigned char
io_read (IOPerThreadType *io)
{
  if (io->buf_idx >= io->incr)
    io_init (io, io->buf_base + io->buf_idx, io->incr);
  if (io->saw_eof)
    return 0xff;
  return io->buf [io->buf_idx++];
}

unsigned char
io_peek (IOPerThreadType *io)
{
  if (io->buf_idx >= io->incr)
    io_init (io, io->buf_base + io->buf_idx, io->incr);
  if (io->saw_eof)
    return 0xff;
  return io->buf [io->buf_idx];
}

size_t
io_pos (IOPerThreadType *io)
{
  return io->buf_base + io->buf_idx;
}

/*------------------------------------------------------------*/

static void
wmem (volatile void *ptr, int count)
{
  char *p = (char *)ptr;
  int i;

  if (!p)
    return;

  for (i=0; i<count; i++)
    p[i] = 0x11;
}
#define xwmem(a,b)

static size_t get_int (IOPerThreadType *io)
{
  size_t rv = 0;
  while (1)
  {
    unsigned char c = io_read (io);
    rv |= (c & 0x7f);
    if (c & 0x80)
      rv <<= 7;
    else
      return rv;
  }
}

static void free_wipe (size_t idx)
{
  char *cp = (char *)ptrs[idx];
  if (cp == NULL)
    return;
  size_t sz = sizes[idx];
  size_t i;
  for (i=0; i<sz; i++)
    {
      if (i % 8 == 1)
	cp[i] = i / 8;
      else
	cp[i] = 0x22;
    }
}

static void *
thread_common (void *my_data_v)
{
  pthread_t thrc = pthread_self ();
  size_t p1, p2, sz, sz2;
  IOPerThreadType *io = (IOPerThreadType *)my_data_v;
  ticks_t my_malloc_time = 0, my_malloc_count = 0;
  ticks_t my_calloc_time = 0, my_calloc_count = 0;
  ticks_t my_realloc_time = 0, my_realloc_count = 0;
  ticks_t my_free_time = 0, my_free_count = 0;
  ticks_t stime, etime;
  int thread_idx = io - thread_io;
#ifdef MDEBUG
  volatile void *tmp;
#endif

  while (1)
    {
      unsigned char this_op = io_peek (io);
      if (io->saw_eof)
	myabort();
      dprintf("op %p:%ld is %d\n", (void *)thrc, io_pos (io),  io_peek (io));
      switch (io_read (io))
	{
	case C_NOP:
	  break;

	case C_DONE:
	  dprintf("op %p:%ld DONE\n", (void *)thrc, io_pos (io));
	  pthread_mutex_lock (&stat_mutex);
	  malloc_time += my_malloc_time;
	  calloc_time += my_calloc_time;
	  realloc_time += my_realloc_time;
	  free_time += my_free_time;
	  malloc_count += my_malloc_count;
	  calloc_count += my_calloc_count;
	  realloc_count += my_realloc_count;
	  free_count += my_free_count;
	  threads_done ++;
	  pthread_mutex_unlock (&stat_mutex);
	  pthread_mutex_lock(&stop_mutex);
	  pthread_mutex_unlock(&stop_mutex);
	  return NULL;

	case C_MEMALIGN:
	  p2 = get_int (io);
	  sz2 = get_int (io);
	  sz = get_int (io);
	  dprintf("op %p:%ld %ld = MEMALIGN %ld %ld\n", (void *)thrc, io_pos (io), p2, sz2, sz);
	  /* we can't force memalign to return NULL (fail), so just skip it.  */
	  if (p2 == 0)
	    break;
	  if (p2 > n_ptrs)
	    myabort();
	  stime = rdtsc_s();
	  Q1;
	  if (ptrs[p2])
	    {
	      if (!quick_run)
		free ((void *)ptrs[p2]);
	      atomic_rss (-sizes[p2]);
	    }
	  if (!quick_run)
	    ptrs[p2] = memalign (sz2, sz);
	  else
	    ptrs[p2] = (void *)p2;
	  /* Verify the alignment matches what is expected.  */
	  if (((size_t)ptrs[p2] & (sz2 - 1)) != 0)
	    myabort ();
	  sizes[p2] = sz;
	  mprintf("%p = memalign(%lx, %lx)\n", ptrs[p2], sz2, sz);
	  Q2;
	  etime = rdtsc_e();
	  if (ptrs[p2] != NULL)
	    atomic_rss (sz);
	  if (etime < stime)
	    {
	      printf("s: %llx e:%llx  d:%llx\n", (long long)stime, (long long)etime, (long long)(etime-stime));
	    }
	  my_malloc_time += etime - stime;
	  my_malloc_count ++;
	  if (!quick_run)
	    wmem(ptrs[p2], sz);
	  break;

	case C_MALLOC:
	  p2 = get_int (io);
	  sz = get_int (io);
	  dprintf("op %p:%ld %ld = MALLOC %ld\n", (void *)thrc, io_pos (io), p2, sz);
	  /* we can't force malloc to return NULL (fail), so just skip it.  */
	  if (p2 == 0)
	    break;
	  if (p2 > n_ptrs)
	    myabort();
	  stime = rdtsc_s();
	  Q1;
	  if (ptrs[p2])
	    {
	      if (!quick_run)
		free ((void *)ptrs[p2]);
	      atomic_rss (-sizes[p2]);
	    }
	  if (!quick_run)
	    ptrs[p2] = malloc (sz);
	  else
	    ptrs[p2] = (void *)p2;
	  sizes[p2] = sz;
	  mprintf("%p = malloc(%lx)\n", ptrs[p2], sz);
	  Q2;
	  etime = rdtsc_e();
	  if (ptrs[p2] != NULL)
	    atomic_rss (sz);
	  if (etime < stime)
	    {
	      printf("s: %llx e:%llx  d:%llx\n", (long long)stime, (long long)etime, (long long)(etime-stime));
	    }
	  my_malloc_time += etime - stime;
	  my_malloc_count ++;
	  if (!quick_run)
	    wmem(ptrs[p2], sz);
	  break;

	case C_CALLOC:
	  p2 = get_int (io);
	  sz = get_int (io);
	  dprintf("op %p:%ld %ld = CALLOC %ld\n", (void *)thrc, io_pos (io), p2, sz);
	  /* we can't force calloc to return NULL (fail), so just skip it.  */
	  if (p2 == 0)
	    break;
	  if (p2 > n_ptrs)
	    myabort();
	  if (ptrs[p2])
	    {
	      if (!quick_run)
		free ((void *)ptrs[p2]);
	      atomic_rss (-sizes[p2]);
	    }
	  stime = rdtsc_s();
	  Q1;
	  if (!quick_run)
	    ptrs[p2] = calloc (sz, 1);
	  else
	    ptrs[p2] = (void *)p2;
	  sizes[p2] = sz;
	  mprintf("%p = calloc(%lx)\n", ptrs[p2], sz);
	  Q2;
	  if (ptrs[p2])
	    atomic_rss (sz);
	  my_calloc_time += rdtsc_e() - stime;
	  my_calloc_count ++;
	  if (!quick_run)
	    wmem(ptrs[p2], sz);
	  break;

	case C_REALLOC:
	  p2 = get_int (io);
	  p1 = get_int (io);
	  sz = get_int (io);
	  dprintf("op %p:%ld %ld = REALLOC %ld %ld\n", (void *)thrc, io_pos (io), p2, p1, sz);
	  if (p1 > n_ptrs)
	    myabort();
	  if (p2 > n_ptrs)
	    myabort();
	  /* we can't force realloc to return NULL (fail), so just skip it.  */
	  if (p2 == 0)
	    break;

	  if (ptrs[p1])
	    atomic_rss (-sizes[p1]);
	  if (!quick_run)
	    free_wipe(p1);
	  stime = rdtsc_s();
	  Q1;
#ifdef MDEBUG
	  tmp = ptrs[p1];
#endif
	  if (!quick_run)
	    ptrs[p2] = realloc ((void *)ptrs[p1], sz);
	  else
	    ptrs[p2] = (void *)p2;
	  sizes[p2] = sz;
	  mprintf("%p = relloc(%p,%lx)\n", ptrs[p2], tmp,sz);
	  Q2;
	  my_realloc_time += rdtsc_e() - stime;
	  my_realloc_count ++;
	  if (!quick_run)
	    wmem(ptrs[p2], sz);
	  if (p1 != p2)
	    ptrs[p1] = 0;
	  if (ptrs[p2])
	    atomic_rss (sizes[p2]);
	  break;

	case C_FREE:
	  p1 = get_int (io);
	  if (p1 > n_ptrs)
	    myabort();
	  dprintf("op %p:%ld FREE %ld\n", (void *)thrc, io_pos (io), p1);
	  if (!quick_run)
	    free_wipe (p1);
	  if (ptrs[p1])
	    atomic_rss (-sizes[p1]);
	  stime = rdtsc_s();
	  Q1;
	  mprintf("free(%p)\n", ptrs[p1]);
	  if (!quick_run)
	    free ((void *)ptrs[p1]);
	  Q2;
	  my_free_time += rdtsc_e() - stime;
	  my_free_count ++;
	  ptrs[p1] = 0;
	  break;

	case C_SYNC_W:
	  p1 = get_int(io);
	  dprintf("op %p:%ld SYNC_W %ld\n", (void *)thrc, io_pos (io), p1);
	  if (p1 > n_syncs)
	    myabort();
	  pthread_mutex_lock (&mutexes[p1]);
	  syncs[p1] = 1;
	  pthread_cond_signal (&conds[p1]);
	  __sync_synchronize ();
	  pthread_mutex_unlock (&mutexes[p1]);
	  break;

	case C_SYNC_R:
	  p1 = get_int(io);
	  dprintf("op %p:%ld SYNC_R %ld\n", (void *)thrc, io_pos (io), p1);
	  if (p1 > n_syncs)
	    myabort();
	  pthread_mutex_lock (&mutexes[p1]);
	  while (syncs[p1] != 1)
	    {
	      pthread_cond_wait (&conds[p1], &mutexes[p1]);
	      __sync_synchronize ();
	    }
	  pthread_mutex_unlock (&mutexes[p1]);
	  break;

	default:
	  printf("op %d - unsupported, thread %d addr %lu\n",
		 this_op, thread_idx, (long unsigned int)io_pos (io));
	  myabort();
	}
    }
}

static void *alloc_mem (size_t amt)
{
  void *rv = mmap (NULL, amt, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
  mlock (rv, amt);
  memset (rv, 0, amt);
  return rv;
}

static pthread_t *thread_ids;

void *
my_malloc (const char *msg, int size, IOPerThreadType *io, size_t *psz, size_t count)
{
  void *rv;
  if (psz)
    count = *psz = get_int (io);
  dprintf ("my_malloc for %s size %d * %ld\n", msg, size, count);
  rv = alloc_mem(size * count);
  if (!rv)
    {
      fprintf(stderr, "calloc(%lu,%lu) failed\n", (long unsigned)size, (long unsigned)*psz);
      exit(1);
    }
  mlock (rv, size * count);
  return rv;
}

static const char * const scan_names[] = {
  "UNUSED",
  "ARENA",
  "HEAP",
  "CHUNK_USED",
  "CHUNK_FREE",
  "FASTBIN_FREE",
  "UNSORTED",
  "TOP",
  "TCACHE",
  "USED"
};

void
malloc_scan_callback (void *ptr, size_t length, int type)
{
  printf("%s: ptr %p length %llx\n", scan_names[type], ptr, (long long)length);
}

#define MY_ALLOC(T, psz)				\
  (typeof (T)) my_malloc (#T, sizeof(*T), &main_io, psz, 0)
#define MY_ALLOCN(T, count)				\
  (typeof (T)) my_malloc (#T, sizeof(*T), &main_io, NULL, count)

int
main(int argc, char **argv)
{
  ticks_t start=0;
  ticks_t end;
  ticks_t usec;
  struct timeval tv_s, tv_e;
  int thread_idx = 0;
  int i;
  size_t n_threads = 0;
  size_t idx;
  struct rusage res_start, res_end;
  int done;
  size_t guessed_io_size = 4096;
  struct stat statb;

  if (argc < 2)
    {
      fprintf(stderr, "Usage: %s <trace2dat.outfile>\n", argv[0]);
      exit(1);
    }
  io_fd = open(argv[1], O_RDONLY);
  if (io_fd < 0)
    {
      fprintf(stderr, "Unable to open %s for reading\n", argv[1]);
      perror("The error was");
      exit(1);
    }
  fstat (io_fd, &statb);

  io_init (&main_io, 0, IOMIN);

  pthread_mutex_lock(&stop_mutex);

  done = 0;
  while (!done)
    {
      switch (io_read (&main_io))
	{
	case C_NOP:
	  break;
	case C_ALLOC_PTRS:
	  ptrs = MY_ALLOC (ptrs, &n_ptrs);
	  sizes = alloc_mem(sizeof(sizes[0]) * n_ptrs);
	  ptrs[0] = 0;
	  break;
	case C_ALLOC_SYNCS:
	  n_syncs = get_int(&main_io);
	  syncs = MY_ALLOCN (syncs, n_syncs);
	  conds = MY_ALLOCN (conds, n_syncs);
	  mutexes = MY_ALLOCN (mutexes, n_syncs);
	  for (idx=0; idx<n_syncs; idx++)
	    {
	      pthread_mutex_init (&mutexes[idx], NULL);
	      pthread_cond_init (&conds[idx], NULL);
	    }
	  break;
	case C_NTHREADS:
	  thread_ids = MY_ALLOC (thread_ids, &n_threads);
	  thread_io = MY_ALLOCN (thread_io, n_threads);
	  guessed_io_size = ((statb.st_size / n_threads) < (1024*1024)) ? 65536 : 4096;
	  /* The next thing in the workscript is thread creation */
	  getrusage (RUSAGE_SELF, &res_start);
	  gettimeofday (&tv_s, NULL);
	  start = rdtsc_s();
	  break;
	case C_START_THREAD:
	  idx = get_int (&main_io);
	  io_init (& thread_io[thread_idx], idx, guessed_io_size);
	  pthread_create (&thread_ids[thread_idx], NULL, thread_common, thread_io + thread_idx);
	  dprintf("Starting thread %lld at offset %lu %lx\n", (long long)thread_ids[thread_idx], (unsigned long)idx, (unsigned long)idx);
	  thread_idx ++;
	  break;
	case C_DONE:
	  do
	    {
	      pthread_mutex_lock (&stat_mutex);
	      i = threads_done;
	      pthread_mutex_unlock (&stat_mutex);
	    } while (i < thread_idx);
	  done = 1;
	  break;
	}
    }
  if (!quick_run)
    {
      end = rdtsc_e();
      gettimeofday (&tv_e, NULL);
      getrusage (RUSAGE_SELF, &res_end);

      printf("%s cycles\n", comma(end - start));
      usec = diff_timeval (tv_e, tv_s);
      printf("%s usec wall time\n", comma(usec));

      usec = diff_timeval (res_end.ru_utime, res_start.ru_utime);
      printf("%s usec across %d thread%s\n",
	     comma(usec), (int)n_threads, n_threads == 1 ? "" : "s");
      printf("%s Kb Max RSS (%s -> %s)\n",
	     comma(res_end.ru_maxrss - res_start.ru_maxrss),
	     comma(res_start.ru_maxrss), comma(res_end.ru_maxrss));
    }
  printf("%s Kb Max Ideal RSS\n", comma (max_ideal_rss / 1024));

  if (malloc_count == 0) malloc_count ++;
  if (calloc_count == 0) calloc_count ++;
  if (realloc_count == 0) realloc_count ++;
  if (free_count == 0) free_count ++;

  if (!quick_run)
    {
      printf("\n");
      printf("sizeof ticks_t is %lu\n", sizeof(ticks_t));
      printf("Avg malloc time: %6s in %10s calls\n", comma(malloc_time/malloc_count), comma(malloc_count));
      printf("Avg calloc time: %6s in %10s calls\n", comma(calloc_time/calloc_count), comma(calloc_count));
      printf("Avg realloc time: %5s in %10s calls\n", comma(realloc_time/realloc_count), comma(realloc_count));
      printf("Avg free time: %8s in %10s calls\n", comma(free_time/free_count), comma(free_count));
      printf("Total call time: %s cycles\n", comma(malloc_time+calloc_time+realloc_time+free_time));
      printf("\n");
    }

#if 0
  /* Free any still-held chunks of memory.  */
  for (idx=0; idx<n_ptrs; idx++)
    if (ptrs[idx])
      {
	free((void *)ptrs[idx]);
	ptrs[idx] = 0;
      }
#endif

#if 0
  /* This will fail (crash) for system glibc but that's OK.  */
  __malloc_scan_chunks(malloc_scan_callback);

  malloc_info (0, stdout);
#endif

#if 0
  /* ...or report them as used.  */
  for (idx=0; idx<n_ptrs; idx++)
    if (ptrs[idx])
      {
	char *p = (char *)ptrs[idx] - 2*sizeof(size_t);
	size_t *sp = (size_t *)p;
	size_t size = sp[1] & ~7;
	malloc_scan_callback (sp, size, 9);
      }
#endif

  /* Now that we've scanned all the per-thread caches, it's safe to
     let them exit and clean up.  */
  pthread_mutex_unlock(&stop_mutex);

  for (i=0; i<thread_idx; i++)
    pthread_join (thread_ids[i], NULL);

  return 0;
}
