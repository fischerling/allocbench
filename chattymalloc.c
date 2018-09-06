#define _GNU_SOURCE
#include <dlfcn.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char tmpbuff[1024];
static unsigned long tmppos = 0;
static unsigned long tmpallocs = 0;

static FILE* out = NULL;
static int in_fprintf = 0;

/*=========================================================
 *  * interception points
 *  */

static void * (*myfn_malloc)(size_t size);
static void (*myfn_free)(void* ptr);
static void * (*myfn_calloc)(size_t nmemb, size_t size);
static void * (*myfn_realloc)(void* ptr, size_t size);

static void init()
{
	out = fopen("chattymalloc.data", "w");
	if (out == NULL)
	{
		fprintf(stderr, "failed to open output file\n");
		exit(1);
	}

	myfn_malloc     = dlsym(RTLD_NEXT, "malloc");
	myfn_free       = dlsym(RTLD_NEXT, "free");
	myfn_calloc       = dlsym(RTLD_NEXT, "calloc");
	myfn_realloc       = dlsym(RTLD_NEXT, "realloc");

	if (!myfn_malloc || !myfn_free || !myfn_calloc || !myfn_realloc)
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
				fprintf(stderr, "jcheck: too much memory requested during initialisation - increase tmpbuff size\n");
				exit(1);
			}
		}
	}

	if (!in_fprintf)
	{
		in_fprintf = 1;
		fprintf(out, "%d\n", size);
		in_fprintf = 0;
	}
	void *ptr = myfn_malloc(size);
	return ptr;
}

void free(void *ptr)
{
	// something wrong if we call free before one of the allocators!
	if (myfn_malloc == NULL)
		init();
	if (!(ptr >= (void*) tmpbuff && ptr <= (void*)(tmpbuff + tmppos)))
		myfn_free(ptr);
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

	if (!in_fprintf)
	{
		in_fprintf = 1;
		fprintf(out, "%d\n", size);
		in_fprintf = 0;
	}
	return myfn_realloc(ptr, size);
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

	if (!in_fprintf)
	{
		in_fprintf = 1;
		fprintf(out, "%d\n", size*nmemb);
		in_fprintf = 0;
	}
	return myfn_calloc(nmemb, size);
}
