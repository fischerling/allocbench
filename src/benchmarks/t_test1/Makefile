# Makefile for t-test1 from ptmalloc, version 2
# by Florian Fischer 2019
# derived from
# Makefile for ptmalloc, version 2
# by Wolfram Gloger 1996-1999, 2001, 2002, 2003, 2004, 2006

OBJDIR ?= obj

CC ?= cc

SYS_FLAGS  = -D_GNU_SOURCE=1
OPT_FLAGS  ?= -g -O # -O2
WARN_FLAGS ?= -Wall -Wstrict-prototypes

# Flags for the test programs
T_FLAGS   = -DTEST=1

# Thread flags.
# See the platform-specific targets below.
THR_FLAGS = -DUSE_TSD_DATA_HACK -D_REENTRANT
THR_LIBS  = -lpthread

RM        = rm -f

CFLAGS ?= $(SYS_FLAGS) $(OPT_FLAGS) $(WARN_FLAGS) $(THR_FLAGS)

all: $(OBJDIR)/t-test1

$(OBJDIR)/t-test1: t-test1.c t-test.h | $(OBJDIR)
	@echo compiling $@
	$(CC) $(CFLAGS) $(T_FLAGS) t-test1.c $(THR_LIBS) -o $@

$(OBJDIR):
	mkdir -p $@

clean:
	$(RM) -rf $(OBJDIR)
