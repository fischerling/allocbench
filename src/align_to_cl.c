/*
Copyright 2018-2020 Florian Fischer <florian.fl.fischer@fau.de>

This file is part of allocbench.

allocbench is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

allocbench is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with allocbench.  If not, see <http://www.gnu.org/licenses/>.
*/

#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define CACHE_LINE 64

static char tmpbuff[4096];
static unsigned long tmppos = 0;
static unsigned long tmpallocs = 0;

/*=========================================================
 * intercepted functions
 */

static void* (*next_malloc)(size_t size);
static void  (*next_free)(void* ptr);
static void* (*next_calloc)(size_t nmemb, size_t size);
static void* (*next_realloc)(void* ptr, size_t size);
static void* (*next_memalign)(size_t alignment, size_t size);
static int   (*next_posix_memalign)(void** memptr, size_t alignment, size_t size);
static void* (*next_valloc)(size_t size);
static void* (*next_pvalloc)(size_t size);
static void* (*next_aligned_alloc)(size_t alignment, size_t size);
static int   (*next_malloc_stats)();

static void __attribute__((constructor))
init()
{
  next_malloc = dlsym(RTLD_NEXT, "malloc");
  next_free = dlsym(RTLD_NEXT, "free");
  next_calloc = dlsym(RTLD_NEXT, "calloc");
  next_realloc = dlsym(RTLD_NEXT, "realloc");
  next_memalign = dlsym(RTLD_NEXT, "memalign");
  next_posix_memalign = dlsym(RTLD_NEXT, "posix_memalign");
  next_valloc = dlsym(RTLD_NEXT, "valloc");
  next_pvalloc = dlsym(RTLD_NEXT, "pvalloc");
  next_aligned_alloc = dlsym(RTLD_NEXT, "aligned_alloc");
  next_malloc_stats = dlsym(RTLD_NEXT, "malloc_stats");

  if (!next_malloc || !next_free || !next_calloc || !next_realloc ||
      !next_memalign) {
    fprintf(stderr, "Can't load core functions with `dlsym`: %s\n", dlerror());
    exit(1);
  }
  if (!next_posix_memalign)
    fprintf(stderr, "Can't load posix_memalign with `dlsym`: %s\n", dlerror());
  if (!next_valloc)
    fprintf(stderr, "Can't load valloc with `dlsym`: %s\n", dlerror());
  if (!next_pvalloc)
    fprintf(stderr, "Can't load pvalloc with `dlsym`: %s\n", dlerror());
  if (!next_aligned_alloc)
    fprintf(stderr, "Can't load aligned_alloc with `dlsym`: %s\n", dlerror());
  if (!next_malloc_stats)
    fprintf(stderr, "Can't load malloc_stats with `dlsym`: %s\n", dlerror());
}

static void align_up_size(size_t* size)
{
  size_t s = *size;
  size_t a = (s + CACHE_LINE + 1) & ~(CACHE_LINE - 1);
  *size = a;
}

void*
malloc(size_t size)
{
  static int initializing = 0;

  if (next_malloc == NULL) {
    if (!initializing) {
      initializing = 1;
      init();
      initializing = 0;

    } else {
        void* retptr = tmpbuff + tmppos;
        tmppos += size;
        ++tmpallocs;

      if (tmppos < sizeof(tmpbuff)) {
        return retptr;
      } else {
        fprintf(stderr, "%d in %d allocs\n", tmppos, tmpallocs);
        fprintf(stderr,
                "jcheck: too much memory requested during initialisation - "
                "increase tmpbuff size\n");
        exit(1);
      }
    }
  }

  align_up_size(&size);
  void* ptr = next_malloc(size);
  return ptr;
}

void
free(void* ptr)
{
  // something wrong if we call free before one of the allocators!
  if (next_malloc == NULL)
    init();
  if (!(ptr >= (void*)tmpbuff && ptr <= (void*)(tmpbuff + tmppos))) {
    next_free(ptr);
  }
}

void*
realloc(void* ptr, size_t size)
{
  if (next_realloc == NULL) {
    void* nptr = malloc(size);
    if (nptr && ptr) {
      memmove(nptr, ptr, size);
      free(ptr);
    }
    return nptr;
  }

  align_up_size(&size);
  void* nptr = next_realloc(ptr, size);
  return nptr;
}

void*
calloc(size_t nmemb, size_t size)
{
  if (next_calloc == NULL) {
    void* ptr = malloc(nmemb * size);
    if (ptr)
      memset(ptr, 0, nmemb * size);
    return ptr;
  }

  align_up_size(&size);
  void* ptr = next_calloc(nmemb, size);
  return ptr;
}

void*
memalign(size_t alignment, size_t size)
{
  if (next_memalign == NULL) {
    fprintf(stderr, "called memalign before or during init\n");
    exit(1);
  }

  align_up_size(&size);
  void* ptr = next_memalign(alignment, size);
  return ptr;
}

int
posix_memalign(void** memptr, size_t alignment, size_t size)
{
  if (next_posix_memalign == NULL) {
    fprintf(stderr, "called posix_memalign before or during init\n");
    exit(1);
  }

  align_up_size(&size);
  int ret = next_posix_memalign(memptr, alignment, size);
  return ret;
}

void*
valloc(size_t size)
{
  if (next_valloc == NULL) {
    fprintf(stderr, "called valloc before or during init");
    exit(1);
  }

  align_up_size(&size);
  void* ptr = next_valloc(size);
  return ptr;
}

void*
pvalloc(size_t size)
{
  if (next_pvalloc == NULL) {
    fprintf(stderr, "called pvalloc before or during init\n");
    exit(1);
  }

  align_up_size(&size);
  void* ptr = next_pvalloc(size);
  return ptr;
}

void*
aligned_alloc(size_t alignment, size_t size)
{
  if (next_aligned_alloc == NULL) {
    fprintf(stderr, "called aligned_alloc before or during init\n");
    exit(1);
  }

  align_up_size(&size);
  void* ptr = next_aligned_alloc(alignment, size);
  return ptr;
}

int
malloc_stats()
{
  if (next_malloc_stats == NULL) {
    fprintf(stderr, "called malloc_stats before or during init\n");
    exit(1);
  }

  fprintf(stderr, "align_to_cl by muhq\n");
  return next_malloc_stats();
}
