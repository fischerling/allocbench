#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int size, iterations;

static void* test_thread_func(__attribute__ ((unused)) void* arg) {
	for(int i = 0; i < iterations; i++) {
		free(malloc(size));
	}
	return NULL;
}

int main(int argc, char* argv[]) {
	pthread_t* threads;
	int num_threads;

	if (argc != 4) {
		fprintf(stderr, "Usage: %s <num threads> <iterations> <size>\n", argv[0]);
		return 1;
	}

	num_threads = atoi(argv[1]);
	iterations = atoi(argv[2]);
	size = atoi(argv[3]);

	threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));

	for (int i = 0; i < num_threads; i++) {
		if (0 != pthread_create(&threads[i], NULL, test_thread_func, NULL)) {
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

	return 0;
}
