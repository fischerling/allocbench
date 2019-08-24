OBJDIR ?= obj

.PHONY = all clean

all:
	cmake -S $(shell pwd) -B $(OBJDIR)
	make -C $(OBJDIR)

clean:
	rm -rf $(OBJDIR)
