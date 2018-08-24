#define _GNU_SOURCE
#include <dlfcn.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

char tmpbuff[1024];
unsigned long tmppos = 0;
unsigned long tmpallocs = 0;

/*=========================================================
 *  * interception points
 *  */

static void * (*myfn_malloc)(size_t size);
static void   (*myfn_free)(void *ptr);

static void print_status(void)
{
	char buf[4096];

	FILE* status = fopen("/proc/self/status", "r");
	if (status == NULL)
	{
		perror("fopen status");
		exit(1);
	}

	FILE* output = fopen("status", "w");
	if (output == NULL)
	{
		perror("fopen output file");
		exit(1);
	}

	while (!feof(status))
	{
		fgets(&buf, 4096, status);
		fprintf(output, "%s", buf);
	}
	fclose(status);
}

static void init()
{
	myfn_malloc     = dlsym(RTLD_NEXT, "malloc");
	myfn_free       = dlsym(RTLD_NEXT, "free");

	if (!myfn_malloc || !myfn_free)
	{
		fprintf(stderr, "Error in `dlsym`: %s\n", dlerror());
		exit(1);
	}
	atexit(print_status);
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

			fprintf(stdout, "jcheck: allocated %lu bytes of temp memory in %lu chunks during initialization\n", tmppos, tmpallocs);
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
				fprintf(stdout, "jcheck: too much memory requested during initialisation - increase tmpbuff size\n");
				exit(1);
			}
		}
	}

	return myfn_malloc(size);
}

void free(void *ptr)
{
	// something wrong if we call free before one of the allocators!
	if (myfn_malloc == NULL)
		init();
	if (ptr >= (void*) tmpbuff && ptr <= (void*)(tmpbuff + tmppos))
		fprintf(stdout, "freeing temp memory\n");
	else
		myfn_free(ptr);
}

