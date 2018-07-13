.PHONY: all clean bench

.DEFAULT_GOAL = all

C_SOURCES = $(shell find . -name "*.c")
CC_SOURCES = $(shell find . -name "*.cc")

VERBOSE =
OBJDIR = ./build

CC = gcc
CXX = g++

WARNFLAGS = -Wall -Wextra
COMMONFLAGS = -fno-builtin -fPIC -DPIC -pthread
OPTFLAGS = -O3 -DNDEBUG
#OPTFLAGS = -O0 -g3

CXXFLAGS = -std=c++11 -I. $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS) -fno-exceptions
CFLAGS = -I. $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)
#LDFLAGS= -fno-builtin-malloc -fno-builtin-calloc -fno-builtin-realloc -fno-builtin-free

VPATH = $(sort $(dir $(C_SOURCES) $(CC_SOURCES)))

OBJECTS = $(notdir $(CC_SOURCES:.cc=.o)) $(notdir $(C_SOURCES:.c=.o))
OBJPRE = $(addprefix $(OBJDIR)/,$(OBJECTS))
MAKEFILE_LIST = Makefile

all: $(OBJDIR)/bench_loop $(OBJDIR)/memusage $(OBJDIR)/bench_conprod

bench: all
	@if test \( ! \( -d bench.d \) \) ;then mkdir -p bench.d;fi
	bash -c "./bench.py"

$(OBJDIR)/memusage: $(OBJDIR)/memusage.o
	@echo "ld		$@"
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(VERBOSE) $(CC) -o $@ $^

$(OBJDIR)/bench_conprod: $(OBJDIR)/bench_conprod.o
	@echo "ld		$@"
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(VERBOSE) $(CC) -pthread -o $@ $^

$(OBJDIR)/bench_loop: $(OBJDIR)/bench_loop.o
	@echo "ld		$@"
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(VERBOSE) $(CC) -pthread -o $@ $^

$(OBJDIR)/%.o : %.c $(MAKEFILE_LIST)
	@echo "cc		$@"
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(VERBOSE) $(CC) -c $(CFLAGS) -o $@ $<

$(OBJDIR)/%.o : %.cc $(MAKEFILE_LIST)
	@echo "cxx		$@"
	@if test \( ! \( -d $(@D) \) \) ;then mkdir -p $(@D);fi
	$(VERBOSE) $(CXX) -c $(CXXFLAGS) -o $@ $<

clean:
	@echo "rm		$(OBJDIR)"
	$(VERBOSE) rm -rf $(OBJDIR)
	@echo "rm		$(DEPDIR)"
	$(VERBOSE) rm -rf $(DEPDIR)

