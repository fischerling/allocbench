OBJDIR ?= obj

CC ?= gcc

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS ?= -O3 -DNDEBUG

CFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDFLAGS ?= -pthread -static-libgcc

.PHONY: all clean

all: $(OBJDIR)/print_status_on_exit.so $(OBJDIR)/allocators/bumpptr_alloc.so

$(OBJDIR)/allocators/bumpptr_alloc.so: bumpptr_alloc.c | $(OBJDIR)/allocators
	@echo "Compiling $@...";
	$(CC) $(LDFLAGS) -shared $(CFLAGS) -o $@ $<

$(OBJDIR)/print_status_on_exit.so: print_status_on_exit.c | $(OBJDIR)
	@echo "Compiling $@...";
	$(CC) $(LDFLAGS) -shared -O2 $(CFLAGS) -o $@ $<

$(OBJDIR)/allocators:
	mkdir -p $@

$(OBJDIR):
	mkdir $@

clean:
	rm -rf $(OBJDIR)
