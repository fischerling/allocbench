.PHONY: all clean bench

.DEFAULT_GOAL = all

SRCDIR = src

BENCHSRCDIR = $(SRCDIR)/benchmarks
BENCHMARKS = $(shell dirname $(shell find $(BENCHSRCDIR) -name Makefile))

OBJDIR = $(PWD)/build

CC = gcc
CXX = g++

WARNFLAGS = -Wall -Wextra
COMMONFLAGS = -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS = -O3 -DNDEBUG
# OPTFLAGS = -O0 -g3

CFLAGS = -I. $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)
CXXFLAGS = -std=c++11 $(CFLAGS) -fno-exceptions

LDFLAGS = -pthread -static-libgcc
LDXXFLAGS = $(LDFLAGS) -static-libstdc++

GLIBC_NOTC = $(PWD)/../glibc/glibc-install-nofs/lib

MAKEFILE_LIST = Makefile

.PHONY: all clean $(SRCDIR) $(BENCHMARKS)
all: $(OBJDIR)/ccinfo $(BENCHMARKS) $(SRCDIR)

$(SRCDIR):
	make -C $@ OBJDIR=$(OBJDIR)

$(BENCHMARKS): $(MAKEFILE_LIST)
	$(MAKE) -C $@ all OBJDIR=$(OBJDIR)/$(shell basename $@)

$(OBJDIR)/ccinfo: | $(OBJDIR)
	$(CC) -v 2> $@

$(OBJDIR):
	mkdir -p $@

clean:
	rm -rf $(OBJDIR)
