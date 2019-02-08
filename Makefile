MAKEFILES = $(shell dirname $(shell find . -name Makefile ! -path ./Makefile ! -path "./build/*"))

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

.PHONY: all clean $(MAKEFILES)
all: $(OBJDIR)/ccinfo  $(MAKEFILES)

$(MAKEFILES):
	$(MAKE) -C $@ OBJDIR=$(OBJDIR)/$(shell echo $@ | sed s/src//)

$(OBJDIR)/ccinfo: | $(OBJDIR)
	$(CC) -v 2> $@

$(OBJDIR):
	mkdir -p $@

clean:
	rm -rf $(OBJDIR)
