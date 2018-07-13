#include <assert.h>
#include <malloc.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <semaphore.h>

static size_t _rand() {
	static __thread size_t seed = 123456789;
	size_t a = 1103515245;
	size_t c = 12345;
	size_t m = 1 << 31;
	seed = (a * seed + c) % m;
		return seed;
}

typedef struct Store {
	pthread_mutex_t mutex;
	sem_t free;
	sem_t avail;
	int toconsum;
	int pos;
	void* ptrs[100];
} Store;

typedef struct ThreadArgs {
	bool isconsumer;
	Store* store;
	int allocations;
	int maxsize;
} ThreadArgs;

static void* malloc_then_write(size_t size) {
	void* ptr = malloc(size);
	// Write to ptr
	*((char*)ptr) = '!';
	return ptr;
}

static void read_then_free(void* ptr) {
	// Read before free
	char s __attribute__((unused)) = *((char*)ptr);
	free(ptr);
}
static void* test_thread_func(void* arg) {
	ThreadArgs* args = (ThreadArgs*)arg;
	Store* store = args->store;

	if (args->isconsumer)
	{
		while (__sync_sub_and_fetch(&store->toconsum, 1) > -1)
		{
			sem_wait(&store->avail);
			pthread_mutex_lock(&store->mutex);
			void* ptr = store->ptrs[store->pos];
			store->pos--;
			pthread_mutex_unlock(&store->mutex);
			sem_post(&store->free);
			read_then_free(ptr);
		}
	} else {
		for (int i = 0; i < args->allocations; i++)
		{
			void* ptr = malloc_then_write((_rand() % args->maxsize) + 1);
			sem_wait(&store->free);
			pthread_mutex_lock(&store->mutex);
			store->pos++;
			store->ptrs[store->pos] = ptr;
			pthread_mutex_unlock(&store->mutex);
			sem_post(&store->avail);
		}
	}
	
	return NULL;
}

int main(int argc, char* argv[]) {
	pthread_t* threads;
	int nstores;
	Store* stores;
	int consumers;
	int producers;
	int num_threads;
	int allocations;
	int maxsize;
	struct ThreadArgs* thread_args;

	if (argc < 6) {
		fprintf(stderr, "Usage: %s <num stores> <num consumers> <num producers> <num allocations> <max size>\n", argv[0]);
		return 1;
	}

	nstores = atoi(argv[1]);
	consumers = atoi(argv[2]);
	if (nstores > consumers)
	{
		fprintf(stderr, "Only %d consumers but %d stores!\n", consumers, nstores);
	}

	producers = atoi(argv[3]);
	if (nstores > producers)
	{
		fprintf(stderr, "Only %d producers but %d stores!\n", producers, nstores);
	}

	num_threads = consumers + producers;
	allocations = atoi(argv[4]);
	maxsize = atoi(argv[5]);

	threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));
	thread_args = (ThreadArgs*)malloc(num_threads * sizeof(ThreadArgs));
	stores = (Store*)malloc(nstores * sizeof(Store));
	if (threads == 0 || thread_args == 0 || stores == 0)
	{
		perror("malloc");
		return 1;
	}

	// Init stores
	for (int i = 0; i < nstores; i++)
	{
		stores[i].pos = -1;
		if (0 != pthread_mutex_init(&stores[i].mutex, 0)) { perror("mutex_init"); return 1; }
		if (0 != sem_init(&stores[i].free, 0, 100)) { perror("sem_init"); return 1; }
		if (0 != sem_init(&stores[i].avail, 0, 0)) { perror("sem_init"); return 1; }
	}

	// Build up thread_args
	for (int i = 0; i < num_threads; i++)
	{
		thread_args[i].store = &stores[i % nstores];
		thread_args[i].maxsize = maxsize;
		thread_args[i].allocations = allocations;

		if ( i < producers) {
			thread_args[i].isconsumer = false;
			stores[i % nstores].toconsum += allocations;
		} else
			thread_args[i].isconsumer = true;
	}

	for (int i = 0; i < num_threads; i++) {
		if (0 != pthread_create(&threads[i], NULL, test_thread_func, &thread_args[i])) {
			perror("pthread_create");
			return 1;
		}
	}

	for (int i = 0; i < num_threads; i++) {
		if (0 != pthread_join(threads[i], NULL)) {
			perror("pthread_join");
			return 1;
		}
	}

	FILE* f = stdout;
	if (argc == 7)
		f = fopen(argv[6], "w");
	malloc_info(0, f);
	if (argc == 7)
		fclose(f);

	return 0;
}
