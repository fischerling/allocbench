#include <stdlib.h>
#include <stdio.h>

size_t* array;
size_t steps = 1;
int main() {
	for (int i = 0; i < 100; i++) {
		if ((array = realloc(array, sizeof(size_t) * steps * i)) == NULL) {
			perror("realloc");
			return 1;
		}
	}
	return 0;
}
