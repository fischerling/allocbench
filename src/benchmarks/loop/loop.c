#include <assert.h>
#include <malloc.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


static size_t _rand() {
	static __thread size_t seed = 123456789;
	size_t a = 1103515245;
	size_t c = 12345;
	size_t m = 1 << 31;
	seed = (a * seed + c) % m;
	return seed;
}

typedef struct ThreadArgs {
	double benchmark;
	int allocations;
	int max_size;
} ThreadArgs;

static void* malloc_then_write(size_t size) {
	void* ptr = malloc(size);
	// Write to ptr
	/* *((char*)ptr) = '!'; */
	return ptr;
}

static void read_then_free(void* ptr) {
	// Read before free
	/* char s __attribute__((unused)) = *((char*)ptr); */
	free(ptr);
}
static void* test_thread_func(void* arg) {
	ThreadArgs* args = (ThreadArgs*)arg;

	for(int i = 0; i < args->allocations; i++) {
		void* ptr = malloc_then_write((_rand() % args->max_size) + 1);
		read_then_free(ptr);
	}
	return NULL;
}

int main(int argc, char* argv[]) {
	pthread_t* threads;
	int num_threads;
	struct ThreadArgs thread_args;

	if (argc < 4) {
		fprintf(stderr, "Usage: %s <num threads> <num allocations> <max size>\n", argv[0]);
		return 1;
	}

	num_threads = atoi(argv[1]);
	thread_args.allocations = atoi(argv[2]);
	thread_args.max_size = atoi(argv[3]);

	threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));

	for (int i = 0; i < num_threads; i++) {
		if (0 != pthread_create(&threads[i], NULL, test_thread_func, &thread_args)) {
			perror("pthread_create");
			return 1;
		}
	}

	for(int i = 0; i < num_threads; i++) {
		if (0 != pthread_join(threads[i], NULL)) {
			perror("pthread_join");
			return 1;
		}
	}

	if (argc == 5)
	{
		FILE* f = stdout;
		if (strcmp(argv[4],"stdout") != 0)
			f = fopen(argv[4], "w");
		malloc_info(0, f);
		if (strcmp(argv[4],"stdout") != 0)
			fclose(f);
	}

	return 0;
}
