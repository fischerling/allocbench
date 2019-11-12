#include <errno.h>  /* TODO: set errno */
#include <stddef.h> /* NULL, size_t */
#include <stdint.h> /* uintptr_t */
#include <stdio.h>  /* fprintf */
#include <unistd.h> /* sysconf(_SC_PAGESIZE) */
#include <string.h> /* memset */

#include "bump_alloc.h"

#define MIN_ALIGNMENT 16

#ifdef __cplusplus
extern "C" {
#endif

void* malloc(size_t size) {
	return bump_up(size, MIN_ALIGNMENT);
}

void free(__attribute__ ((unused)) void* ptr) {
}

void* realloc(void* ptr, size_t size) {
	if(ptr == NULL)
		return malloc(size);

	void* new_ptr = bump_up(size, MIN_ALIGNMENT);
	// this may copies to much
	memcpy(new_ptr, ptr, size);
	return new_ptr;
}

void* memalign(size_t alignment, size_t size) {
	return bump_up(size, alignment);
}

int posix_memalign(void **memptr, size_t alignment, size_t size)
{
	void *out;

	if(memptr == NULL) {
		return 22;
	}

	if((alignment % sizeof(void*)) != 0) {
		return 22;
	}

	/* if not power of two */
	if(!((alignment != 0) && !(alignment & (alignment - 1)))) {
		return 22;
	}

	if(size == 0) {
		*memptr = NULL;
		return 0;
	}

	out = bump_up(size, alignment);
	if(out == NULL) {
		return 12;
	}

	*memptr = out;
	return 0;
}

void* calloc(size_t nmemb, size_t size)
{
	void *out;
	size_t fullsize = nmemb * size;

	if((size != 0) && ((fullsize / size) != nmemb)) {
		return NULL;
	}
	
	out = bump_up(fullsize, MIN_ALIGNMENT);
	if(out == NULL) {
		return NULL;
	}

	memset(out, 0, fullsize);
	return out;
}

void* valloc(size_t size)
{
	long ret = sysconf(_SC_PAGESIZE);
	if(ret == -1) {
		return NULL;
	}

	return memalign(ret, size);
}

void* pvalloc(size_t size)
{
	size_t ps, rem, allocsize;

	long ret = sysconf(_SC_PAGESIZE);
	if(ret == -1) {
		return NULL;
	}

	ps = ret;
	rem = size % ps;
	allocsize = size;
	if(rem != 0) {
		allocsize = ps + (size - rem);
	}

	return memalign(ps, allocsize);
}

void* aligned_alloc(size_t alignment, size_t size)
{
	if(alignment > size) {
		return NULL;
	}

	if((size % alignment) != 0) {
		return NULL;
	}

	return memalign(alignment, size);
}

int malloc_stats() {
	fprintf(stderr, "Bump pointer allocator by muhq\n");
	fprintf(stderr, "Memsize: %zu, start address: %p, bump pointer %p\n", MEMSIZE, tsd, tsd->ptr);
	return 0;
}

#ifdef __cplusplus
}
#endif
