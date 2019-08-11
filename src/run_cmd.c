#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char* argv[]) {
	if (argc < 3) {
		printf("Usage: %s <ld_preload> <cmd> [cmd args]\n");
		printf("\tset LD_PRELOAD to ld_preload and call execvp <cmd> [cmd args]\n");
		return 1;
	}

	// Overwrite LD_PRELOAD.
	setenv("LD_PRELOAD", argv[1], 1);

	// Run cmd.
	execvp(argv[2], &argv[2]);
}
