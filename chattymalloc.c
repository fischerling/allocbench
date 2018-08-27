#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <signal.h>
#include <sys/syscall.h>
#include <unistd.h>

static void * (*myfn_malloc)(size_t size);
static void * (*myfn_free)(void* ptr);
static void * (*myfn_calloc)(size_t nmemb, size_t size);
static void * (*myfn_realloc)(void *ptr, size_t size);
static void * (*myfn_memalign)(size_t blocksize, size_t bytes);

static int initializing = 0;

// Memory we give out during initialisation
static char tmpbuff[4096];
static unsigned long tmppos = 0;
static unsigned long tmpallocs = 0;

/* Options that can be set in the CHATTYMALLOC_OPTS environment var.
 *
 * store: store call data in memory or dump it with each allocator call */
static bool store = true;
/* sigusr1: dump in memory log in SIGUSR1 handler */
static bool sigusr1 = false;
/* timestamp: get timestamp of each allocator call */
static bool timestamp = false;
/* timestamp: get timestamp of each allocator call */
static char* path = "chattymalloc.data";

void parse_options()
{
	char* options = getenv("CHATTYMALLOC_OPTS");
	if (!options)
		return;

	char* opt = options;
	char* val;
	char c;

	for (int i = 0;; i++)
	{
		c = options[i];
		if (c == ':' || c == '\0')
		{
			if (strncmp(opt, "store", 5) == 0)
			{
				if (strncmp(val, "false", 5) == 0)
					store = false;
			}
			else if (strncmp(opt, "sigusr1", 7) == 0)
			{
				if (strncmp(val, "true", 4) == 0)
					sigusr1 = true;
			}
			else if (strncmp(opt, "timestamp", 9) == 0)
			{
				if (strncmp(val, "true", 4) == 0)
					timestamp = true;
			}
			else
				fprintf(stderr, "Unknown option \n");

			if (c == '\0')
				return;

			opt = options + i + 1;
		}
		else if (c == '=')
		{
			val = options + i + 1;
		}
	}
}

typedef enum { MALLOC, FREE, CALLOC, REALLOC, MEMALIGN } Func;

// Entry in our in memory log
typedef struct Log_entry
{
	time_t time;
	Func function;
	uintptr_t args[3];
} Log_entry;

// Chunk of thread local log entries
typedef struct Log_chunk
{
	struct Log_chunk* next;
	pid_t tid;
	size_t n;
	Log_entry entries[10000];
} Log_chunk;

// List of chunks
static struct Log_chunk* log_start = NULL;
static struct Log_chunk* log_end = NULL;

static __thread pid_t tid;
static __thread Log_chunk* cur_log;

// Flag to prevent recursion
static __thread int prevent_recursion = 0;

static void (*old_signalhandler)(int);

FILE* out;

#ifdef SYS_gettid
static pid_t gettid()
{
	if (!tid)
		tid = syscall(SYS_gettid);
	return tid;
}
#else
#error "SYS_gettid unavailable on this system"
#endif

static void open_output()
{
	out = fopen(path, "w");
	if (!out)
	{
		perror("failed to open output");
		exit(1);
	}
}

static void new_log_chunk (void)
{
	cur_log = myfn_malloc(sizeof(Log_chunk));
	if (!cur_log)
	{
		perror("can't malloc chunk");
		exit(1);
	}

	cur_log->tid = gettid();
	cur_log->n = 0;
	cur_log->next = NULL;

chain: ;
	Log_chunk* old_end = log_end;
	if (!__sync_bool_compare_and_swap(&log_end, old_end, cur_log))
		goto chain;

	if (old_end)
		old_end->next = cur_log;
}

static void write_log (void)
{
	Log_chunk* chunk = log_start;

	prevent_recursion = 1;

	open_output();

	while (chunk)
	{
		for (size_t i = 0; i < chunk->n; i++)
		{
			Log_entry entry = chunk->entries[i];
			fprintf(out, "%lu %d ", entry.time, chunk->tid);
			switch (entry.function)
			{
			case MALLOC:
				fprintf(out, "ma %lu %p\n", entry.args[0], entry.args[1]);
				break;
			case FREE:
				fprintf(out, "f %p\n", entry.args[0]);
				break;
			case CALLOC:
				fprintf(out, "c %lu %lu %p\n", entry.args[0], entry.args[1], entry.args[2]);
				break;
			case REALLOC:
				fprintf(out, "r %p %lu %p\n", entry.args[0], entry.args[1], entry.args[2]);
				break;
			case MEMALIGN:
				fprintf(out, "mm %lu %lu %p\n", entry.args[0], entry.args[1], entry.args[2]);
				break;
			}
		}
		chunk = chunk->next;
	}

	fclose(out);
}

static void sigusr1_handler
(int __attribute__((__unused__)) sig)
{
	write_log();
	pid_t ppid = getppid();
	kill(ppid, SIGUSR1);

	// we are done writing the log
	prevent_recursion = 0;
}

static void init (void)
{
	initializing = 1;

	myfn_malloc     = dlsym(RTLD_NEXT, "malloc");
	myfn_free       = dlsym(RTLD_NEXT, "free");
	myfn_calloc     = dlsym(RTLD_NEXT, "calloc");
	myfn_realloc    = dlsym(RTLD_NEXT, "realloc");
	myfn_memalign   = dlsym(RTLD_NEXT, "memalign");

	if (!myfn_malloc || !myfn_free || !myfn_calloc || !myfn_realloc || !myfn_memalign) 
	{
		fprintf(stderr, "Error in `dlsym`: %s\n", dlerror());
		exit(1);
	}

	initializing = 0;
	// now we can use the real allocator
	prevent_recursion = 1;

	// parse chattymalloc options
	parse_options();

	if (store)
	{
		new_log_chunk();
		log_start = cur_log;
		atexit(write_log);
	}
	else
		open_output();

	if (sigusr1)
	{
		// register USR1 signal handler to dump log
		struct sigaction old;
		struct sigaction sa;

		sigaction(SIGUSR1, NULL, &old);
		old_signalhandler = old.sa_handler;

		memset(&sa, 0, sizeof(sa));
		sa.sa_handler = sigusr1_handler;
		sa.sa_mask = old.sa_mask;

		if (sigaction(SIGUSR1, &sa, NULL) == -1)
		{
			perror("Can't register our SIGUSR1 handler");
			exit(1);
		}
	}

	prevent_recursion = 0;
}

void *malloc (size_t size)
{

	if (myfn_malloc == NULL)
	{
		if (!initializing)
			init();
		else
		{
			if (tmppos + size < sizeof(tmpbuff))
			{
				/* fprintf(stderr, "jcheck: %lu requested during init\n", size); */
				void *retptr = tmpbuff + tmppos;
				tmppos += size;
				++tmpallocs;
				return retptr;
			}
			else
			{
				fprintf(stderr, "jcheck: too much memory requested during initialisation - increase tmpbuff size\n");
				*((int*) NULL) = 1;
				exit(1);
			}
		}
	}

	void *ptr = myfn_malloc(size);

	if (!prevent_recursion)
	{
		struct timespec ts;
		ts.tv_sec = 0;
		ts.tv_nsec = 0;

		if (timestamp)
			clock_gettime(CLOCK_MONOTONIC, &ts);

		if (store)
		{
			if (cur_log == NULL || cur_log->n == 100)
				 new_log_chunk();

			Log_entry* cur_entry = &cur_log->entries[cur_log->n];

			cur_entry->time = ts.tv_nsec;
			cur_entry->function = MALLOC;
			cur_entry->args[0] = (uintptr_t)size;
			cur_entry->args[1] = (uintptr_t)ptr;
			cur_log->n++;
		}
		else
		{
			prevent_recursion = 1;
			fprintf(out, "%lu %d ma %u %p\n", ts.tv_nsec, gettid(), size, ptr);
			prevent_recursion = 0;
		}
	}

	return ptr;
}

void free (void *ptr)
{
	if (myfn_free == NULL)
		init();
	if (!(ptr >= (void*) tmpbuff && ptr <= (void*)(tmpbuff + tmppos)))
	{
		if (!prevent_recursion)
		{
			struct timespec ts;
			ts.tv_sec = 0;
			ts.tv_nsec = 0;

			if (timestamp)
				clock_gettime(CLOCK_MONOTONIC, &ts);

			if (store)
			{
				if (cur_log == NULL || cur_log->n == 100)
					 new_log_chunk();

				Log_entry* cur_entry = &cur_log->entries[cur_log->n];

				cur_entry->time = ts.tv_nsec;
				cur_entry->function = FREE;
				cur_entry->args[0] = (uintptr_t)ptr;
				cur_log->n++;
			}
			else
			{
				prevent_recursion = 1;
				fprintf(out, "%lu %d f %p\n", ts.tv_nsec, gettid(), ptr);
				prevent_recursion = 0;
			}
		}

		myfn_free(ptr);
	}
}

void *realloc (void *ptr, size_t size)
{
	if (myfn_realloc == NULL)
	{
		void *nptr = malloc(size);
		if (nptr && ptr)
		{
			memmove(nptr, ptr, size);
			free(ptr);
		}
		return nptr;
	}

	void *nptr = myfn_realloc(ptr, size);

	if (!prevent_recursion)
	{
		struct timespec ts;
		ts.tv_sec = 0;
		ts.tv_nsec = 0;

		if (timestamp)
			clock_gettime(CLOCK_MONOTONIC, &ts);

		if (store)
		{
			if (cur_log == NULL || cur_log->n == 100)
				 new_log_chunk();

			Log_entry* cur_entry = &cur_log->entries[cur_log->n];

			cur_entry->time = ts.tv_nsec;
			cur_entry->function = REALLOC;
			cur_entry->args[0] = (uintptr_t)ptr;
			cur_entry->args[1] = (uintptr_t)size;
			cur_entry->args[2] = (uintptr_t)nptr;
			cur_log->n++;
		}
		else
		{
			prevent_recursion = 1;
			fprintf(out, "%lu %d r %p %u %p\n", ts.tv_nsec, gettid(), ptr, size, nptr);
			prevent_recursion = 0;
		}
	}

	return nptr;
}

void *calloc (size_t nmemb, size_t size)
{
	if (myfn_calloc == NULL)
	{
		void *ptr = malloc(nmemb*size);
		if (ptr)
			memset(ptr, 0, nmemb*size);
		return ptr;
	}

	void *ptr = myfn_calloc(nmemb, size);

	if (!prevent_recursion)
	{
		struct timespec ts;
		ts.tv_sec = 0;
		ts.tv_nsec = 0;

		if (timestamp)
			clock_gettime(CLOCK_MONOTONIC, &ts);

		if (store)
		{
			if (cur_log == NULL || cur_log->n == 100)
				 new_log_chunk();

			Log_entry* cur_entry = &cur_log->entries[cur_log->n];

			cur_entry->time = ts.tv_nsec;
			cur_entry->function = CALLOC;
			cur_entry->args[0] = (uintptr_t)nmemb;
			cur_entry->args[1] = (uintptr_t)size;
			cur_entry->args[2] = (uintptr_t)ptr;
			cur_log->n++;
		}
		else
		{
			prevent_recursion = 1;
			fprintf(out, "%lu %d c %u %u %p\n", ts.tv_nsec, gettid(), nmemb, size, ptr);
			prevent_recursion = 0;
		}
	}

	return ptr;
}

void *memalign (size_t alignment, size_t size)
{
	// Hopefully this gets never called during init()
	void *ptr = myfn_memalign(alignment, size);

	if (!prevent_recursion)
	{
		struct timespec ts;
		ts.tv_sec = 0;
		ts.tv_nsec = 0;

		if (timestamp)
			clock_gettime(CLOCK_MONOTONIC, &ts);

		if (store)
		{
			if (cur_log == NULL || cur_log->n == 100)
				 new_log_chunk();

			Log_entry* cur_entry = &cur_log->entries[cur_log->n];

			cur_entry->time = ts.tv_nsec;
			cur_entry->function = MEMALIGN;
			cur_entry->args[0] = (uintptr_t)alignment;
			cur_entry->args[1] = (uintptr_t)size;
			cur_entry->args[2] = (uintptr_t)ptr;
			cur_log->n++;
		}
		else
		{
			prevent_recursion = 1;
			fprintf(out, "%lu %d mm %u %u %p\n", ts.tv_nsec, gettid(), alignment, size, ptr);
			prevent_recursion = 0;
		}
	}

	return ptr;
}

