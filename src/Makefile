OBJDIR ?= obj

CC ?= gcc

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS ?= -O0 -g

CFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDFLAGS ?= -pthread -static-libgcc

MEMSIZE_KB=$(shell free -t | tail -1 | tr -s ' ' | cut -d ' ' -f 2)
MEMSIZE=$(shell echo $(MEMSIZE_KB)"* 1024" | bc)

.PHONY: all clean

all: $(OBJDIR)/print_status_on_exit.so $(OBJDIR)/allocators/bumpptr_alloc.so

$(OBJDIR)/allocators/bumpptr_alloc.so: bumpptr_alloc.c Makefile | $(OBJDIR)/allocators
	@echo "Compiling $@...";
	$(CC) $(LDFLAGS) -shared -DMEMSIZE=$(MEMSIZE) $(CFLAGS) -o $@ $<
	# $(CC) $(LDFLAGS) -shared $(CFLAGS) -o $@ $<

$(OBJDIR)/print_status_on_exit.so: print_status_on_exit.c Makefile | $(OBJDIR)
	@echo "Compiling $@...";
	$(CC) $(LDFLAGS) -shared $(CFLAGS) -o $@ $<

$(OBJDIR)/allocators:
	mkdir -p $@

$(OBJDIR):
	mkdir $@

clean:
	rm -rf $(OBJDIR)
