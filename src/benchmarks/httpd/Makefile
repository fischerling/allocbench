OBJDIR ?= obj

.PHONY = all clean

all: $(OBJDIR)/html $(OBJDIR)/nginx

$(OBJDIR)/html: html | $(OBJDIR)
	cp -r html $(OBJDIR)/html

$(OBJDIR)/nginx: nginx/nginx.conf | $(OBJDIR)
	mkdir $@
	mkdir $@/logs
	sed "s|OBJDIR|$(OBJDIR)|" $< > $@/nginx.conf

$(OBJDIR):
	mkdir -p $@

clean:
	rm -rf $(OBJDIR)
