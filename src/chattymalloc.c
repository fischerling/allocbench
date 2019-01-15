#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static char tmpbuff[1024];
static unsigned long tmppos = 0;
static unsigned long tmpallocs = 0;

static int out = -1;
static int prevent_recursion = 0;

/*=========================================================
 *  * interception points
 *  */

static void * (*myfn_malloc)(size_t size);
static void (*myfn_free)(void* ptr);
static void * (*myfn_calloc)(size_t nmemb, size_t size);
static void * (*myfn_realloc)(void* ptr, size_t size);
static void * (*myfn_memalign)(size_t alignment, size_t size);

static void write_output(const char* fmt, ...)
{
	if (!prevent_recursion)
	{
		prevent_recursion = 1;

		/* lockf(out, F_LOCK, 0); */

		va_list args;
		va_start(args, fmt);
		vdprintf(out, fmt, args);
		va_end(args);

		/* lockf(out, F_ULOCK, 0); */
		prevent_recursion = 0;
	}
}

static void init()
{
	out = open("chattymalloc.data", O_WRONLY | O_TRUNC | O_CREAT, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH);
	if (out == -1)
	{
		fprintf(stderr, "failed to open output file with %d\n", errno);
		exit(1);
	}

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
}

void *malloc(size_t size)
{
	static int initializing = 0;

	if (myfn_malloc == NULL)
	{
		if (!initializing)
		{
			initializing = 1;
			init();
			initializing = 0;

		}
		else
		{
			if (tmppos + size < sizeof(tmpbuff))
			{
				void *retptr = tmpbuff + tmppos;
				tmppos += size;
				++tmpallocs;
				return retptr;
			}
			else
			{
				fprintf(stderr, "%d in %d allocs\n", tmppos, tmpallocs);
				fprintf(stderr, "jcheck: too much memory requested during initialisation - increase tmpbuff size\n");
				exit(1);
			}
		}
	}

	void *ptr = myfn_malloc(size);
	write_output("m %zu %p\n", size, ptr);
	return ptr;
}

void free(void *ptr)
{
	// something wrong if we call free before one of the allocators!
	if (myfn_malloc == NULL)
		init();
	if (!(ptr >= (void*) tmpbuff && ptr <= (void*)(tmpbuff + tmppos)))
	{
		write_output("f %p\n", ptr);
		myfn_free(ptr);
	}
}

void* realloc(void *ptr, size_t size)
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

	void* nptr =  myfn_realloc(ptr, size);
	write_output("r %p %zu %p\n", ptr, size, nptr);
	return nptr;
}

void* calloc(size_t nmemb, size_t size)
{
	if (myfn_calloc == NULL)
	{
		void *ptr = malloc(nmemb*size);
		if (ptr)
			memset(ptr, 0, nmemb*size);
		return ptr;
	}

	void* ptr = myfn_calloc(nmemb, size);
	write_output("c %zu %zu %p\n", nmemb, size, ptr);
	return ptr;
}

void* memalign(size_t alignment, size_t size)
{
	if (myfn_memalign == NULL)
	{
		fprintf(stderr, "called memalign before or during init");
		exit(1);
	}

	void* ptr = myfn_memalign(alignment, size);
	write_output("mm %zu %zu %p\n", alignment, size, ptr);
	return ptr;
}
