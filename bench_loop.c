#include <assert.h>
#include <malloc.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>


static size_t _rand() {
	static __thread size_t seed = 123456789;
	size_t a = 1103515245;
	size_t c = 12345;
	size_t m = 1 << 31;
	seed = (a * seed + c) % m;
		return seed;
}

/*
* Available Benchmarks:
* 1.x: do malloc()/free() in a loop
*	1:   simple loop
*	1.1: keep num_kept_allocations befor freeing
*	1.2: keep num_kept_allocations then free all stored
*/

typedef struct ThreadArgs {
	double benchmark;
	int allocations;
	int num_kept_allocations;
	int max_size;
} ThreadArgs;

static void* malloc_then_write(size_t size) {
	void* ptr = malloc(size);
	// Write to ptr
	*((char*)ptr) = '!';
	return ptr;
}

static void read_then_free(void* ptr) {
	// Read before free
	char s = *((char*)ptr);
	free(ptr);
}
static void* test_thread_func(void* arg) {
	ThreadArgs* args = (ThreadArgs*)arg;
	void** ptrs = (void**)calloc(args->num_kept_allocations, sizeof(void*));

	for(int i = 0; i < args->allocations; i++) {
		int pos = i % args->num_kept_allocations;

		if (args->benchmark == 1.1) {
			if (i >= args->num_kept_allocations) {
				read_then_free(ptrs[pos]);
			}
		}

		if (args->benchmark == 1.2) {
			if (pos == 0 && ptrs[pos] != NULL) {
				for (size_t y = 0; y < args->num_kept_allocations; y++) {
					read_then_free(ptrs[y]);
				}
			}
		}

		ptrs[pos] = malloc_then_write((_rand() % args->max_size) + 1);

		if (args->benchmark == 1.0) {
			read_then_free(ptrs[pos]);
		}
	}
	return NULL;
}

int main(int argc, char* argv[]) {
	pthread_t* threads;
	int num_threads;
	struct ThreadArgs thread_args;

	if (argc < 6) {
		fprintf(stderr, "Usage: %s <benchmark> <num threads> <num allocations> <max size> <num of stored allocations>\n", argv[0]);
		return 1;
	}

	thread_args.benchmark = atof(argv[1]);
	num_threads = atoi(argv[2]);
	thread_args.allocations = atoi(argv[3]);
	thread_args.max_size = atoi(argv[4]);
	thread_args.num_kept_allocations = atoi(argv[5]);

	threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));

	for (int i = 0; i < num_threads; i++) {
		if (0 != pthread_create(&threads[i], NULL, test_thread_func, &thread_args)) {
			return 1;
		}
	}

	for(int i = 0; i < num_threads; i++) {
		if (0 != pthread_join(threads[i], NULL)) {
			return 1;
		}
	}

#ifndef NSTATS
	FILE* f = fopen("stats", "w");
	malloc_info(0, f);
	fclose(f);
#endif
}
