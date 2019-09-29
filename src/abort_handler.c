#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void abort_handler(__attribute__((unused)) int signo) {
	fopen("aborted", "w");
}

static void __attribute__((constructor)) register_abort_handler(void)
{
	struct sigaction sa;
	sa.sa_handler = abort_handler;
	sigemptyset(&sa.sa_mask);

	if (sigaction(SIGABRT, &sa, NULL) == -1) {
		perror("sigaction");
		exit(1);
	}
}

