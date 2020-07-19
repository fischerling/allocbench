SRCDIR = allocbench

PYTHONFILES = $(shell find -name "*.py" -not -path "./cache/*" -not -path "./build/*" -not -path "./.git/*")

MAKEFILES = $(shell dirname $(shell find $(SRCDIR)/ -name Makefile))
CMAKELISTS = $(shell dirname $(shell find $(SRCDIR)/ -name CMakeLists.txt))

OBJDIR = $(PWD)/build

export CC = gcc
export CXX = g++

export WARNFLAGS = -Wall -Wextra
export COMMONFLAGS = -fno-builtin -fPIC -DPIC -pthread
export OPTFLAGS = -O3 -DNDEBUG -fomit-frame-pointer

export CFLAGS = -I. $(OPTFLAGS) $(WARNFLAGS) $(COMMONFLAGS)
export CXXFLAGS = -std=c++11 $(CFLAGS) -fno-exceptions

export LDFLAGS = -pthread -static-libgcc
export LDXXFLAGS = $(LDFLAGS) -static-libstdc++

.PHONY: all clean pylint format tags\
	check check-format check-pylint check-mypy\
	test integration-test\
	 $(MAKEFILES) $(CMAKELISTS)

all: $(OBJDIR)/ccinfo $(MAKEFILES) $(CMAKELISTS)

$(CMAKELISTS):
	$(eval BENCHDIR=$(OBJDIR)$(shell echo $@ | sed s/$(SRCDIR)//))
	@if test \( ! \( -d $(BENCHDIR) \) \) ;then mkdir -p $(BENCHDIR);fi
ifneq (,$(findstring s,$(MAKEFLAGS)))
	cd $(BENCHDIR); cmake $(PWD)/$@ >/dev/null
else
	cd $(BENCHDIR); cmake $(PWD)/$@
endif
	$(MAKE) -C $(BENCHDIR)

$(MAKEFILES):
	$(eval BENCHDIR=$(OBJDIR)$(shell echo $@ | sed s/$(SRCDIR)//))
	@if test \( ! \( -d $(BENCHDIR) \) \) ;then mkdir -p $(BENCHDIR);fi
	$(MAKE) -C $@ OBJDIR=$(OBJDIR)$(shell echo $@ | sed s/$(SRCDIR)//)

$(OBJDIR)/ccinfo: | $(OBJDIR)
	$(CC) -v 2> $@

$(OBJDIR):
	mkdir -p $@

clean:
	rm -rf $(OBJDIR)

check-pylint:
	pylint --rcfile=.pylint.rc -j 0 $(PYTHONFILES) || ./tools/check-pylint $$?

format:
	yapf -i $(PYTHONFILES)

check-format:
	yapf -d $(PYTHONFILES)

check-mypy:
	mypy --ignore-missing-imports $(PYTHONFILES)

tags:
	ctags -R --exclude="build/*" --exclude="cache/*" --exclude="doc/*" --exclude="results/*"

integration-test:
	python3 -m unittest discover -s tests/integration

test: all integration-test

check: check-pylint check-format check-mypy test
