OBJDIR ?= obj

CC ?= gcc

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS ?= -O0 -g

CFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDFLAGS ?= -pthread -static-libgcc

MEMSIZE_KB=$(shell grep -E "MemTotal|SwapTotal" /proc/meminfo | grep -o "[0-9]*"\
	| python -c "import sys; print(sum([int(x) for x in sys.stdin.readlines()]))")
MEMSIZE="$(MEMSIZE_KB) * 1024l"

TOOLS = print_status_on_exit.so exec sig_handlers.so
ALLOCS = bumpptr_alloc.so align_to_cl.so
TARGETS = $(addprefix $(OBJDIR)/allocators/,$(ALLOCS)) $(addprefix $(OBJDIR)/,$(TOOLS))

.PHONY: all clean

all: $(TARGETS)

$(OBJDIR)/allocators/bumpptr_alloc.so: bumpptr_alloc.c malloc.c Makefile
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(CC) $(LDFLAGS) -shared -DMEMSIZE=$(MEMSIZE) $(CFLAGS) -o $@ bumpptr_alloc.c malloc.c

$(OBJDIR)/allocators/align_to_cl.so: align_to_cl.c Makefile
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(CC) $(LDFLAGS) -shared $(CFLAGS) -o $@ $< -ldl

$(OBJDIR)/print_status_on_exit.so: print_status_on_exit.c Makefile
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(CC) $(LDFLAGS) -shared $(CFLAGS) -o $@ $<

$(OBJDIR)/sig_handlers.so: sig_handlers.c Makefile
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(CC) $(LDFLAGS) -shared $(CFLAGS) -o $@ $<

$(OBJDIR)/exec: exec.c Makefile
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(CC) $(LDFLAGS) $(CFLAGS) -o $@ $<

clean:
	rm -rf $(OBJDIR)
