OBJDIR ?= obj

CXX ?= g++

WARNFLAGS ?= -Wall -Wextra
COMMONFLAGS ?= -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS ?= -O3 -DNDEBUG

CXXFLAGS ?= $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)

LDXXFLAGS ?= -pthread -static-libgcc -static-libstdc++

.PHONY: all clean

all: $(OBJDIR)/larson

$(OBJDIR)/larson: larson.cc | $(OBJDIR)
	$(CXX) $(LDXXFLAGS) $(CXXFLAGS) -o $@ $<

$(OBJDIR):
	mkdir $@

clean:
	rm -rf $(OBJDIR)
