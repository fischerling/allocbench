OBJDIR ?= obj

CC ?= gcc

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS ?= -O3 -DNDEBUG

CFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDFLAGS ?= -pthread -static-libgcc

.PHONY: all clean

all: $(OBJDIR)
	@echo building targets

$(OBJDIR):
	mkdir $@

clean:
	rm -rf $(OBJDIR)
