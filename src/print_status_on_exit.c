#define _GNU_SOURCE
#include <dlfcn.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

static void print_status(void)
{
	char buf[4096];

	FILE* status = fopen("/proc/self/status", "r");
	if (status == NULL)
	{
		perror("fopen status");
		exit(1);
	}

	FILE* output = fopen("status", "a");
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

static void __attribute__((constructor)) init()
{
	atexit(print_status);
}

