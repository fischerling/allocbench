OBJDIR ?= obj

CC ?= gcc

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS ?= -O3 -DNDEBUG

CFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDFLAGS ?= -pthread -static-libgcc

.PHONY = all clean

all: $(OBJDIR)/trace_run

$(OBJDIR)/trace_run: trace_run.c | $(OBJDIR)
	@echo compiling $@...
	$(CC) $(LDFLAGS) $(CFLAGS) -o $@ $<

$(OBJDIR):
	mkdir -p $@

clean:
	rm -rf $(OBJDIR)
