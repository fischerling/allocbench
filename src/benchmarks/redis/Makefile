OBJDIR ?= obj

unexport CC
unexport CXX
unexport WARNFLAGS
unexport COMMONFLAGS
unexport OPTFLAGS
unexport CFLAGS
unexport CXXFLAGS
unexport LDFLAGS
unexport LDXXFLAGS

.PHONY = all clean

all:
	@echo building redis benchmark
	./build.sh $(OBJDIR) $(REDIS_VERSION)

clean:
	rm -rf $(OBJDIR)
