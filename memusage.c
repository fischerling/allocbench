/* Utility to print running total of VmPeak and VmSize of a program */
#define _GNU_SOURCE
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>

#define PATH_MAX 2048

int child_pid;

static int main_loop(char *pidstatus)
{
	char *line;
	char *vmsize;
	char *vmpeak;
	char *vmrss;
	char *vmhwm;

	size_t len;

	FILE *f;

	vmsize = NULL;
	vmpeak = NULL;
	vmrss = NULL;
	vmhwm = NULL;
	line = malloc(128);
	len = 128;

	f = fopen(pidstatus, "r");
	if (!f) return 1;

	/* Read memory size data from /proc/pid/status */
	while (!vmsize || !vmpeak || !vmrss || !vmhwm)
	{
		if (getline(&line, &len, f) == -1)
		{
			/* Some of the information isn't there, die.
			   Hopefully we have at least one measure.  */
			return 1;
		}

		/* Find VmPeak */
		if (!strncmp(line, "VmPeak:", 7))
		{
			vmpeak = strdup(&line[7]);
		}

		/* Find VmSize */
		else if (!strncmp(line, "VmSize:", 7))
		{
			vmsize = strdup(&line[7]);
		}

		/* Find VmRSS */
		else if (!strncmp(line, "VmRSS:", 6))
		{
			vmrss = strdup(&line[7]);
		}

		/* Find VmHWM */
		else if (!strncmp(line, "VmHWM:", 6))
		{
			vmhwm = strdup(&line[7]);
		}
	}
	free(line);

	fclose(f);

	/* Get rid of " kB\n"*/
	len = strlen(vmsize);
	vmsize[len - 4] = 0;
	len = strlen(vmpeak);
	vmpeak[len - 4] = 0;
	len = strlen(vmrss);
	vmrss[len - 4] = 0;
	len = strlen(vmhwm);
	vmhwm[len - 4] = 0;

	/* Output results to stderr */
	fprintf(stderr, "%s;%s;%s;%s\n", vmsize, vmpeak, vmrss, vmhwm);

	free(vmpeak);
	free(vmsize);
	free(vmrss);
	free(vmhwm);

	/* Success */
	return 0;
}

static int usage(char *me)
{
	fprintf(stderr, "%s: filename args\n", me);
	fprintf(stderr, "Run program, and print VmSize, VmPeak, VmRSS and VmHWM (in KiB) to stderr\n");

	return 1;
}

static int child(int argc, char **argv)
{
	char **newargs = malloc(sizeof(char *) * argc);
	int i;

	/* We can't be certain that argv is NULL-terminated, so do that now */
	for (i = 0; i < argc - 1; i++)
	{
		newargs[i] = argv[i+1];
	}
	newargs[argc - 1] = NULL;

	/* Launch the child */
	execvp(argv[1], newargs);

	return 0;
}

static void sig_chld(int dummy)
{
	int status, child_val;
	int pid;

	(void) dummy;

	pid = waitpid(-1, &status, WNOHANG);
	if (pid < 0)
	{
		fprintf(stderr, "waitpid failed\n");
		return;
	}

	/* Only worry about direct child */
	if (pid != child_pid) return;

	/* Get child status value */
	if (WIFEXITED(status))
	{
		fprintf(stderr, "# End memusage\n");
		child_val = WEXITSTATUS(status);
		exit(child_val);
	}
	else if (WIFSIGNALED(status))
	{
		fprintf(stderr, "Child terminated by signal %d\n", WTERMSIG(status));
		exit(1);
	}
}

int main(int argc, char **argv)
{
	char buf[PATH_MAX];

	struct sigaction act;

	if (argc < 2) return usage(argv[0]);

	act.sa_handler = sig_chld;

	/* We don't want to block any other signals */
	sigemptyset(&act.sa_mask);

	act.sa_flags = SA_NOCLDSTOP;

	if (sigaction(SIGCHLD, &act, NULL) < 0)
	{
		perror("sigaction");
		return 1;
	}

	child_pid = fork();

	if (!child_pid) return child(argc, argv);

	snprintf(buf, PATH_MAX, "/proc/%d/status", child_pid);

	fprintf(stderr, "VmSize;VmPeak;VmRSS;VmHWM\n");
	/* Continual scan of proc */
	while (!main_loop(buf))
	{
		/* Wait for 0.1 sec */
		usleep(100000);
	}

	/* This should never be reached we exit when our child exits */
	return 1;
}
