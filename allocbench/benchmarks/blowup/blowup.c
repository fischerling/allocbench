#include <malloc.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NUM_THREADS 10
#define LIFE_DATA (1024l * 1024 * 100) // 100 MiB
#define ALLOCATIONS 100000l // 100000
#define MAX_SIZE (1024l * 16) // 16KiB

typedef struct chunk {
	struct chunk* next;
	char data[];
} chunk_t;

static inline size_t rand_size()
{
	return (rand() % MAX_SIZE) + sizeof(chunk_t);
}

static void do_work()
{
	chunk_t* head = NULL;
	chunk_t* tail = NULL;
	size_t to_allocate = LIFE_DATA;

	// allocate life data
	while(to_allocate > 0) {
		size_t size = rand_size();
		if (size > to_allocate)
			size = to_allocate;

		to_allocate -= size;
		chunk_t* cur = (chunk_t*) malloc(size);
		// touch memory
		memset(&cur->data, 0, size - sizeof(struct chunk*));

		if(!head) {
			head = tail = cur;
		}
		else {
			tail->next = cur;
			tail = cur;
		}
	}

	// Do some random allocations to change the allocators state
	for(int i = 0; i < ALLOCATIONS; i++)
	{
		free(malloc(rand_size()));
	}

	// free life data
	do {
		chunk_t* next = head->next;
		free(head);
		head = next;
	} while(head != tail);

	// Do some random allocations to change the allocators state
	for(int i = 0; i < ALLOCATIONS; i++)
	{
		free(malloc(rand_size()));
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
