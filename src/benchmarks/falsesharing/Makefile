OBJDIR ?= obj

CXX ?= g++

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -fPIC -DPIC -pthread -g
OPTFLAGS ?= -O0

CXXFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDXXFLAGS ?= -pthread -static-libgcc -static-libstdc++

HEADER = cpuinfo.h fred.h timer.h

.PHONY = all clean

all: $(OBJDIR)/cache-thrash $(OBJDIR)/cache-scratch

$(OBJDIR)/cache-thrash: cache-thrash.cc $(HEADER) | $(OBJDIR)
	@echo compiling $@...
	$(CXX) $(LDXXFLAGS) $(CXXFLAGS) -o $@ $<

$(OBJDIR)/cache-scratch: cache-scratch.cc $(HEADER) | $(OBJDIR)
	@echo compiling $@...
	$(CXX) $(LDXXFLAGS) $(CXXFLAGS) -o $@ $<

$(OBJDIR):
	mkdir -p $@

clean:
	rm -rf $(OBJDIR)
