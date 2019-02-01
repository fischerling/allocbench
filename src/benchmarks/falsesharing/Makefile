OBJDIR ?= obj

CXX ?= g++

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS ?= -O3 -DNDEBUG

CXXFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDXXFLAGS ?= -pthread -static-libgcc -static-libstdc++

HEADER = cpuinfo.h fred.h timer.h

.PHONY = all clean

all: $(OBJDIR)/cache-thrash $(OBJDIR)/cache-scratch

$(OBJDIR)/cache-thrash: cache-thrash.cc $(HEADER) | $(OBJDIR)
	$(CXX) $(LDXXFLAGS) $(CXXFLAGS) -o $@ $<

$(OBJDIR)/cache-scratch: cache-scratch.cc $(HEADER) | $(OBJDIR)
	$(CXX) $(LDXXFLAGS) $(CXXFLAGS) -o $@ $<

$(OBJDIR):
	mkdir $@

clean:
	rm -rf $(OBJDIR)
