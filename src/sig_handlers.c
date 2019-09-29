#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void abnormal_termination_handler(int signo) {
	exit(signo);
}

static void __attribute__((constructor)) register_handlers(void)
{
	struct sigaction sa, old_sa;
	sa.sa_handler = abnormal_termination_handler;
	sigemptyset(&sa.sa_mask);

	sigaction(SIGABRT, NULL, &old_sa);
	if (old_sa.sa_handler == SIG_DFL) {
		if (sigaction(SIGABRT, &sa, NULL) == -1) {
			perror("sigaction");
			exit(1);
		}
	} else {
		fprintf(stderr, "SIGABRT handler already set");
	}

	sigaction(SIGSEGV, NULL, &old_sa);
	if (old_sa.sa_handler == SIG_DFL) {
		if (sigaction(SIGSEGV, &sa, NULL) == -1) {
			perror("sigaction");
			exit(1);
		}
	} else {
		fprintf(stderr, "SIGSEGV handler already set");
	}
}

