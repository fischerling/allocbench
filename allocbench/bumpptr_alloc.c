#include <assert.h>
#include <errno.h>
#include <stddef.h> /* NULL, size_t */
#include <stdint.h> /* uintptr_t */
#include <stdio.h>  /* fprintf */
#include <sys/mman.h> /* mmap */

#define MIN_ALIGNMENT 16

#ifndef MEMSIZE
#define MEMSIZE 1024*4*1024*1024l
#endif

#define unlikely(x)     __builtin_expect((x),0)

typedef struct bumpptr {
	uintptr_t end;
	uintptr_t ptr;
} bumpptr_t;

__thread bumpptr_t* tsd = NULL;

static inline void* bump_up(size_t size, size_t align) {
	assert(align % 2 == 0);

	if (unlikely(tsd == NULL)) {
		void* mem_start = mmap(NULL, MEMSIZE, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_HUGETLB, -1, 0);
		if(mem_start == MAP_FAILED) {
			perror("mmap");
			return NULL;
		}
		tsd = (bumpptr_t*)mem_start;
		tsd->ptr = (uintptr_t)mem_start + sizeof(bumpptr_t);
		tsd->end = (uintptr_t)mem_start + MEMSIZE;
	}

	// align ptr;
	uintptr_t aligned = (tsd->ptr + align - 1) & ~(align - 1);

	uintptr_t new_ptr = aligned + size;
	if (new_ptr > tsd->end) {
		errno = ENOMEM;
		return NULL;
	} else {
		tsd->ptr = new_ptr;
		return (void*)aligned;
	}
}

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
