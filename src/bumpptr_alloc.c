#include <errno.h>
#include <stddef.h> /* NULL, size_t */
#include <stdint.h> /* uintptr_t */
#include <stdio.h> /* uintptr_t */
#include <unistd.h> /* sysconf(_SC_PAGESIZE) */
#include <string.h> /* memset */
#include <sys/mman.h> /* memset */

#define MEMSIZE 1024*4*1024*1024l

#ifdef __cplusplus
extern "C" {
#endif

__thread void* mem_start = NULL;
__thread void* mem_end = NULL;

__thread uintptr_t ptr = 0;

void* malloc(size_t size) {
	if(mem_start == NULL) {
		mem_start = mmap(NULL, MEMSIZE, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
		if(mem_start == MAP_FAILED) {
			perror("mmap");
			return NULL;
		}
		ptr = (uintptr_t)mem_start;
	}

	void* ret = (void*)ptr;
	ptr += size;
	return ret;
}

void free(__attribute__ ((unused)) void* ptr) {
}

void* realloc(void* ptr, size_t size) {
	if(ptr == NULL)
		return malloc(size);

	if(size == 0)
		return NULL;

	void* new_ptr = malloc(size);
	// this may copies to much
	memcpy(new_ptr, ptr, size);
	return new_ptr;
}

void* memalign(size_t alignment, size_t size) {
	// bump ptr to alignment and malloc
	ptr = (ptr + (alignment - 1)) & -alignment;
	return malloc(size);
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

	out = memalign(alignment, size);
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
	
	out = malloc(fullsize);
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

#ifdef __cplusplus
}
#endif
