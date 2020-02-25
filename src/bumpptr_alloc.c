#include <errno.h>  /* TODO: set errno */
#include <stddef.h> /* NULL, size_t */
#include <stdint.h> /* uintptr_t */
#include <stdio.h>  /* fprintf */

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

void* memalign(size_t alignment, size_t size) {
	return bump_up(size, alignment);
}

void malloc_stats() {
	fprintf(stderr, "Bump pointer allocator by muhq\n");
	fprintf(stderr, "Memsize: %zu, start address: %p, bump pointer %p\n", MEMSIZE, tsd, tsd->ptr);
}

#ifdef __cplusplus
}
#endif
