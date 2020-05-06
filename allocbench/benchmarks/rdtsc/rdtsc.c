#define _GNU_SOURCE             /* See feature_test_macros(7) */
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/sysinfo.h>

int mode = 0;
int size = 64;
int iterations = 100000;
int num_cpus;

static __inline__ int64_t rdtsc_s(void)
{
	unsigned a, d;
	asm volatile("cpuid" ::: "%rax", "%rbx", "%rcx", "%rdx");
	asm volatile("rdtsc" : "=a" (a), "=d" (d));
	return ((unsigned long)a) | (((unsigned long)d) << 32);
}

static __inline__ int64_t rdtsc_e(void)
{
	unsigned a, d;
	asm volatile("rdtscp" : "=a" (a), "=d" (d));
	asm volatile("cpuid" ::: "%rax", "%rbx", "%rcx", "%rdx");
	return ((unsigned long)a) | (((unsigned long)d) << 32);
}

static void* test_thread_func(void* arg) {
	int64_t clock_before, clock_after;
	void* p;

	int64_t* clocks = malloc(iterations * sizeof(int64_t));
	if (!clocks)
		abort();

	// set cpu affinity to prevent cpu switching
	int64_t tid = (int64_t) arg;
	cpu_set_t my_cpu;
	/* Skip CPU0 - let the OS run on that one */
	int my_cpu_num = (tid % (num_cpus-1))+1;

	CPU_ZERO (&my_cpu);
	/* CPU_SET (my_cpu_num, &my_cpu); */
	CPU_SET (3, &my_cpu);
	if (sched_setaffinity (0, sizeof(my_cpu), &my_cpu) == -1)
	  perror ("setaffinity failed");

	for(int i = 0; i < iterations; i++) {
		clock_before = rdtsc_s();
		p = malloc(size);
		clock_after = rdtsc_e();

		// measure potentially cached allocations
		if (mode)
			free(p);

		clocks[i] = clock_after - clock_before;
	}

	for(int i = 0; i < iterations; i++) {
		printf("malloc(%d): %d cycles\n", size, clocks[i]);
	}

	return NULL;
}

int main(int argc, char* argv[]) {
	pthread_t* threads;
	int num_threads = 1;

	num_cpus = get_nprocs();

	if (argc > 5) {
		fprintf(stderr, "Usage: %s <iterations> <size> <num threads>\n", argv[0]);
		return 1;
	}

	if (argc > 1) {
		if (strncmp(argv[1], "cached", strlen("cached")) == 0) mode = 1;
	}
	if (argc > 2) iterations = atoi(argv[2]);
	if (argc > 3) size = atoi(argv[3]);
	if (argc > 4) num_threads = atoi(argv[4]);

	fprintf(stderr, "iterations = %d; size = %d; threads = %d\n", iterations, size, num_threads);

	threads = (pthread_t*) malloc(num_threads * sizeof(pthread_t));

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
