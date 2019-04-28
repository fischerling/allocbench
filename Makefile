MAKEFILES = $(shell dirname $(shell find . -name Makefile ! -path ./Makefile ! -path "./build/*"))

OBJDIR = $(PWD)/build

export CC = gcc
export CXX = g++

export WARNFLAGS = -Wall -Wextra
export COMMONFLAGS = -fno-builtin -fPIC -DPIC -pthread
# export OPTFLAGS = -O3 -DNDEBUG
export OPTFLAGS = -O0 -g

export CFLAGS = -I. $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)
export CXXFLAGS = -std=c++11 $(CFLAGS) -fno-exceptions

export LDFLAGS = -pthread -static-libgcc
export LDXXFLAGS = $(LDFLAGS) -static-libstdc++

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
