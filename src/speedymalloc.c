#include <assert.h>
#include <errno.h>
#include <stddef.h> /* NULL, size_t */
#include <stdint.h> /* uintptr_t */
#include <stdio.h> /* fprintf */
#include <stdlib.h> /* exit */
#include <string.h> /* memset */
#include <sys/mman.h> /* mmap */

#define MIN_ALIGNMENT 16

#ifdef DONTNEED
#define MY_MADVISE_FREE MADV_DONTNEED
#else
#define MY_MADVISE_FREE MADV_FREE
#endif

#ifndef MEMSIZE
#define MEMSIZE 1024*4*1024*1024l
#endif

#ifndef NO_WILLNEED
#define WILLNEED_SIZE 32 * 1024 * 1024
#endif

// sizeof(tls_t) == 4096
#define CACHE_BINS 511
// max cached object: 511 * 64 - 1 = 32703
#define CACHE_BIN_SEPERATION 64

#define unlikely(x)     __builtin_expect((x),0)
#define PAGE_SIZE 4096

#ifdef __cplusplus
extern "C" {
#endif

typedef struct chunk {
	size_t size; // Size header field for internal use
	struct chunk* next;
} chunk_t;

static inline chunk_t* ptr2chunk(void* ptr) {
	return (chunk_t*)((uintptr_t)ptr - sizeof(size_t));
}

static inline void* chunk2ptr (chunk_t* chunk) {
	return (void*)((uintptr_t)chunk + sizeof(size_t));
}

static inline uintptr_t alignup (uintptr_t ptr, size_t alignment) {
	size_t mask = alignment -1;
	return (ptr + mask) & ~mask;
}

typedef struct TLStates {
	uintptr_t ptr;
	chunk_t* bins[CACHE_BINS];
} tls_t;

__thread tls_t* tls;
__thread uintptr_t next_willneed;

static inline int size2bin(size_t size) {
	assert(size > 0 && size < CACHE_BINS * CACHE_BIN_SEPERATION);
	return (size - 1) / CACHE_BIN_SEPERATION;
}

static inline size_t bin2size(int bin) {
	assert(bin >= 0 && bin < CACHE_BINS);
	return (bin + 1) * CACHE_BIN_SEPERATION;
}

static void init_tls(void) {
	void *mem = mmap(NULL, MEMSIZE, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
	if (mem == MAP_FAILED) {
		perror("mmap");
		exit(1);
	}
	tls = (tls_t*)mem;

	tls->ptr = ((uintptr_t)tls) + sizeof(tls_t);
#ifndef NO_WILLNEED
	next_willneed = tls->ptr;
#endif
}

static void* bump_alloc(size_t size) {
	// allocate size header
	tls->ptr += sizeof(size_t);

	// align ptr
	tls->ptr = alignup(tls->ptr, MIN_ALIGNMENT);

#ifndef NO_WILLNEED
	if(unlikely(tls->ptr >= next_willneed)) {
		madvise((void*)next_willneed, WILLNEED_SIZE, MADV_WILLNEED);
		next_willneed += WILLNEED_SIZE;
	}
#endif

	void* ptr = (void*)tls->ptr;
	ptr2chunk(ptr)->size = size;
	tls->ptr += size;

	return ptr;
}

void* malloc(size_t size) {
	if (unlikely(tls == NULL)) {
		init_tls();
	}

	// cached sizes
	if (size < CACHE_BINS * CACHE_BIN_SEPERATION) {
		int bin = size2bin(size);
		if (tls->bins[bin] != NULL) {
			chunk_t* chunk = tls->bins[bin];
			// remove first chunk from list
			tls->bins[bin] = chunk->next;
			return chunk2ptr(chunk);
		}
		return bump_alloc(bin2size(bin));
	}

	return bump_alloc(size);
}

void free(void* ptr) {
	if (unlikely(tls == NULL)) {
		init_tls();
	}

	if (ptr == NULL) {
		return;
	}

	chunk_t* chunk = ptr2chunk(ptr);

	if (chunk->size < CACHE_BINS * CACHE_BIN_SEPERATION) {
		int bin = size2bin(chunk->size);
		chunk->next = tls->bins[bin];
		tls->bins[bin] = chunk;
	}
#ifndef NO_FREE
	else {
		size_t size = chunk->size;
		size -= ((uintptr_t)ptr % PAGE_SIZE); // size without part before a page boundry
		size -= size % PAGE_SIZE; // size without part after a page boundry

		void* page_start = (void*)alignup((uintptr_t)ptr, PAGE_SIZE);
		//fprintf(stderr, "ptr: %p, s: %ux, pages: %ux, page_ptr: %p\n",
		//        ptr, chunk->size, size, page_start);
		madvise(page_start, size, MY_MADVISE_FREE);
	}
#endif
}

void* memalign(size_t alignment, size_t size) {
	/* if not power of two */
	if (!((alignment != 0) && !(alignment & (alignment - 1)))) {
		return NULL;
	}

	if (unlikely(tls == NULL)) {
		init_tls();
	}

	// allocate size header
	tls->ptr += sizeof(size_t);

	tls->ptr = alignup(tls->ptr, alignment);

	void* ptr = (void*)tls->ptr;
	ptr2chunk(ptr)->size = size;
	tls->ptr += size;

	return ptr;
}

void malloc_stats() {
	fprintf(stderr, "speedymalloc allocator by muhq\n");
	fprintf(stderr, "Memsize: %zu, start address: %p, bump pointer %p\n", MEMSIZE, tls, tls->ptr);
}

#ifdef __cplusplus
}
#endif
