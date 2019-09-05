#include <errno.h>
#include <stddef.h> /* NULL, size_t */
#include <stdint.h> /* uintptr_t */
#include <stdio.h> /* fprintf */
#include <stdlib.h> /* exit */
#include <unistd.h> /* sysconf(_SC_PAGESIZE) */
#include <string.h> /* memset */
#include <sys/mman.h> /* mmap */

#define MIN_ALIGNMENT 16

#ifndef MEMSIZE
#define MEMSIZE 1024*4*1024*1024l
#endif

#define unlikely(x)     __builtin_expect((x),0)

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Allocations size < 1024 are 16 byte seperated into 64 bins
 * Allocations size in [1024, 5120) are 64 byte seperated
 * Allocations size in [5120, 21504) are 256 byte seperated
 * Allocations size in [21504, 54272) are 512 byte seperated
 * Allocations bigger than 54272 are not cached
 */
static inline unsigned char size2bin(size_t size) {
	if (size < 1024)
		return size / 16;
	else if (size < 5120)
		return size / 64 + 48;
	else if (size < 21504)
		return size / 256 + 108;
	else
		return size / 512 + 150;
}

static inline size_t bin2size(unsigned char bin) {
	if (bin < 64)
		return (bin + 1) * 16;
	else if (bin < 128)
		return 1024 + (bin - 64) * 64;
	else if (bin < 192)
		return 5120 + (bin - 128) * 256;
	else
		return 21504 + (bin - 192) * 512;
}

typedef struct chunk {
	size_t size;
	struct chunk* next;
} chunk_t;

static inline chunk_t* ptr2chunk(void* ptr) {
	return (chunk_t*)((size_t*)ptr - 1);
}

static inline void* chunk2ptr (chunk_t* chunk) {
	return &chunk->next;
}

typedef struct TLStates {
	uintptr_t ptr;
	chunk_t* bins[256];
} tls_t;


__thread tls_t* tls;

static void init_tls(void) {
	void *mem = mmap(NULL, MEMSIZE, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
	if(mem == MAP_FAILED) {
		perror("mmap");
		exit(1);
	}
	tls = (tls_t*)mem;

	tls->ptr = ((uintptr_t)tls) + sizeof(tls_t);
}

static void* bump_alloc(size_t size) {
	// allocate size header
	tls->ptr += sizeof(size_t);

	// align ptr;
	if (tls->ptr % MIN_ALIGNMENT != 0) {
		size_t mask = MIN_ALIGNMENT -1;
		tls->ptr = (tls->ptr + mask) & ~mask;
	}

	chunk_t* chunk = ptr2chunk((void*)tls->ptr);
	chunk->size = size;
	tls->ptr += size;

	return chunk2ptr(chunk);
}

void* malloc(size_t size) {
	if (unlikely(tls == NULL)) {
		init_tls();
	}

	// cached sizes
	if (size < 54272) {
		unsigned char bin = size2bin(size);
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

	if (ptr == NULL)
		return;

	chunk_t* chunk = ptr2chunk(ptr);

	if (chunk->size < 54272) {
		unsigned char bin = size2bin(chunk->size);
		chunk->next = tls->bins[bin];
		tls->bins[bin] = chunk;
	}
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
	if (unlikely(tls == NULL)) {
		init_tls();
	}
	// align ptr to alignment and allocate using the bumppointer
	size_t mask = alignment - 1;
	tls->ptr = (tls->ptr + mask) & ~mask;
	return bump_alloc(size);
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
	if (out != NULL)
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
	fprintf(stderr, "Memsize: %zu, start address: %p, bump pointer %p\n", MEMSIZE, &tls, tls->ptr);
	return 0;
}

#ifdef __cplusplus
}
#endif
