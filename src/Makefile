OBJDIR ?= obj

CC ?= gcc

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS ?= -O3 -DNDEBUG

CFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDFLAGS ?= -pthread -static-libgcc

.PHONY: all clean

all: $(OBJDIR)/print_status_on_exit.so $(OBJDIR)/chattymalloc.so

$(OBJDIR)/print_status_on_exit.so: print_status_on_exit.c | $(OBJDIR)
	$(CC) $(LDFLAGS) -shared $(CFLAGS) -o $@ $<

$(OBJDIR)/chattymalloc.so: chattymalloc.c | $(OBJDIR)
	$(CC) $(LDFLAGS) -shared $(CFLAGS) -o $@ $<

$(OBJDIR):
	mkdir $@

clean:
	rm -rf $(OBJDIR)
