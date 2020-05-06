OBJDIR ?= obj

CC ?= gcc

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -pthread
OPTFLAGS ?= -O0 -g

CFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDFLAGS ?= -pthread -static-libgcc

.PHONY = all clean

all: $(OBJDIR)/loop

$(OBJDIR)/loop: loop.c Makefile | $(OBJDIR)
	@echo compiling $@...
	$(CC) $(LDFLAGS) $(CFLAGS) -o $@ $<

$(OBJDIR):
	mkdir -p $@

clean:
	rm -rf $(OBJDIR)
