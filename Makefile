.PHONY: all clean bench

.DEFAULT_GOAL = all

SRCDIR=benchmarks
BENCH_C_SOURCES = $(shell find $(SRCDIR) -name "*.c")
BENCH_CC_SOURCES = $(shell find $(SRCDIR) -name "*.cc")

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

VPATH = $(sort $(dir $(BENCH_C_SOURCES) $(BENCH_CC_SOURCES)))

GLIBC_NOTC = $(PWD)/../glibc/glibc-install-notc/lib

BENCH_OBJECTS = $(notdir $(BENCH_CC_SOURCES:.cc=.o)) $(notdir $(BENCH_C_SOURCES:.c=.o))
BENCH_OBJPRE = $(addprefix $(OBJDIR)/,$(BENCH_OBJECTS))
MAKEFILE_LIST = Makefile

BENCH_TARGETS = $(BENCH_OBJPRE:.o=) $(BENCH_OBJPRE:.o=-glibc-notc)

all: $(BENCH_TARGETS) $(OBJDIR)/chattymalloc.so $(OBJDIR)/print_status_on_exit.so

$(OBJDIR)/print_status_on_exit.so: print_status_on_exit.c $(MAKEFILE_LIST)
	$(CC) -shared $(CFLAGS) -o $@ $< -ldl

$(OBJDIR)/chattymalloc.so: chattymalloc.c $(MAKEFILE_LIST)
	$(CC) -shared $(CFLAGS) -o $@ $< -ldl

$(OBJDIR)/cache-thrash: $(OBJDIR)/cache-thrash.o
	$(CXX) -pthread -o $@ $^

$(OBJDIR)/cache-thrash-glibc-notc: $(OBJDIR)/cache-thrash
	cp $< $@
	patchelf --set-interpreter $(GLIBC_NOTC)/ld-linux-x86-64.so.2 $@
	patchelf --set-rpath $(GLIBC_NOTC) $@

$(OBJDIR)/cache-scratch: $(OBJDIR)/cache-scratch.o
	$(CXX) -pthread -o $@ $^

$(OBJDIR)/cache-scratch-glibc-notc: $(OBJDIR)/cache-scratch
	cp $< $@
	patchelf --set-interpreter $(GLIBC_NOTC)/ld-linux-x86-64.so.2 $@
	patchelf --set-rpath $(GLIBC_NOTC) $@

$(OBJDIR)/bench_loop: $(OBJDIR)/bench_loop.o
	$(CC) -pthread -o $@ $^

$(OBJDIR)/bench_loop-glibc-notc: $(OBJDIR)/bench_loop
	cp $< $@
	patchelf --set-interpreter $(GLIBC_NOTC)/ld-linux-x86-64.so.2 $@
	patchelf --set-rpath $(GLIBC_NOTC) $@

$(OBJDIR)/%.o : %.c $(OBJDIR) $(MAKEFILE_LIST)
	$(CC) -c $(CFLAGS) -o $@ $<

$(OBJDIR)/%.o : %.cc $(OBJDIR) $(MAKEFILE_LIST)
	$(CXX) -c $(CXXFLAGS) -o $@ $<

$(OBJDIR):
	mkdir -p $@

clean:
	rm -rf $(OBJDIR)
	rm -rf $(DEPDIR)

