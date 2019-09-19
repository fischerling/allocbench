#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NUM_THREADS 10
#define ALLOCATIONS 1024 * 100
#define SIZE 1024

static void do_work()
{
	void** ptrs;

	ptrs = malloc(sizeof(void*) * ALLOCATIONS);
	if (ptrs == NULL) {
		perror("malloc");
		return;
	}

	for(int i = 0; i < ALLOCATIONS; i++)
	{
		ptrs[i] = malloc(SIZE);
		memset(ptrs[i], 0, SIZE);
	}

	for(int i = 0; i < ALLOCATIONS; i++)
	{
		free(malloc(SIZE));
	}

	for(int i = 0; i < ALLOCATIONS; i++)
	{
		/* memset(ptrs[i], 0, SIZE); */
		free(ptrs[i]);
	}

	for(int i = 0; i < ALLOCATIONS; i++)
	{
		free(malloc(SIZE));
	}

	return;
}

static void* thread_func(void* arg)
{
	unsigned int* thread_id = (unsigned int*)arg;
	pthread_t next_thread;

	printf("thread %d doing work\n", *thread_id);
	do_work();

	if (*thread_id == NUM_THREADS)
		return NULL;

	printf("thread %d spawning new thread work\n", *thread_id);
	*thread_id = (*thread_id) + 1;
	if (0 != pthread_create(&next_thread, NULL, thread_func, arg)) {
		perror("pthread_create");
		return NULL;
	}

	printf("thread %d joining thread %d work\n", *thread_id-1, *thread_id);
	if (0 != pthread_join(next_thread, NULL)) {
		perror("pthread_join");
		return NULL;
	}

	return NULL;
}

int main()
{
	unsigned int thread_count = 0;
	pthread_t first;

	do_work();

	if (0 != pthread_create(&first, NULL, thread_func, &thread_count)) {
		perror("pthread_create");
		return 1;
	}

	if (0 != pthread_join(first, NULL)) {
		perror("pthread_join");
		return 1;
	}

	return 0;
}
