#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char* argv[]) {
	if (argc < 3) {
		printf("Usage: %s [-p LD_PRELOAD] [-l LD_LIBRARY_PATH] <cmd> [cmd args]\n");
		printf("\tset LD_PRELOAD to ld_preload and call execvp <cmd> [cmd args]\n");
		return 1;
	}

	int i = 1;
	for (; i < argc; i++) {
		// Overwrite LD_PRELOAD.
		if (strncmp(argv[i], "-p", 2) == 0) {
			setenv("LD_PRELOAD", argv[i+1], 1);
			i++;
		// Overwrite LD_LIBRARY_PATH.
		} else if (strncmp(argv[i], "-l", 2) == 0) {
			setenv("LD_LIBRARY_PATH", argv[i+1], 1);
			i++;
		} else {
			break;
		}
	}


	// Run cmd.
	execvp(argv[i], &argv[i]);
}
