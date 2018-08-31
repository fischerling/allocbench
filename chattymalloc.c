#define _GNU_SOURCE
#include <dlfcn.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char tmpbuff[1024];
unsigned long tmppos = 0;
unsigned long tmpallocs = 0;

FILE* out = NULL;

/*=========================================================
 *  * interception points
 *  */

static void * (*myfn_malloc)(size_t size);
static void * (*myfn_free)(void* ptr);

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

	if (!myfn_malloc || !myfn_free)
	{
		fprintf(stderr, "Error in `dlsym`: %s\n", dlerror());
		exit(1);
	}
}

void *malloc(size_t size)
{
	static int initializing = 0;
	static int in_fprintf = 0;

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
