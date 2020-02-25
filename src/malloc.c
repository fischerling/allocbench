#include <malloc.h>   /* memalign */
#include <stdlib.h>   /* malloc, free */
#include <stddef.h>   /* NULL, size_t */
#include <stdint.h>   /* uintptr_t */
#include <string.h>   /* memcpy */
#include <unistd.h>   /* sysconf */

#ifdef __cplusplus
extern "C" {
#endif

void* realloc(void* ptr, size_t size) {
	if(ptr == NULL)
		return malloc(size);

	void* new_ptr = malloc(size);
	// this may copies to much
	memcpy(new_ptr, ptr, size);
	return new_ptr;
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

	out = malloc(size);
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
