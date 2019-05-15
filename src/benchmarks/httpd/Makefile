OBJDIR ?= obj

.PHONY = all clean

all: $(OBJDIR)/html $(OBJDIR)/php $(OBJDIR)/etc/nginx $(OBJDIR)/etc/php $(OBJDIR)/logs $(OBJDIR)/run

$(OBJDIR)/html: html | $(OBJDIR)
	cp -r html $(OBJDIR)/html

$(OBJDIR)/php: php | $(OBJDIR)
	cp -r php $(OBJDIR)/php

$(OBJDIR)/logs: | $(OBJDIR)
	mkdir -p $@

$(OBJDIR)/run: | $(OBJDIR)
	mkdir -p $@

$(OBJDIR)/etc/nginx: etc/nginx/nginx.conf | $(OBJDIR)/etc
	mkdir -p $@
	sed "s|OBJDIR|$(OBJDIR)|" $< > $@/nginx.conf

$(OBJDIR)/etc/php: etc/php/php.ini etc/php/php-fpm.conf etc/php/php-fpm.d/www.conf | $(OBJDIR)
	mkdir -p $@/php-fpm.d/
	sed "s|OBJDIR|$(OBJDIR)|" etc/php/php.ini > $@/php.ini
	sed "s|OBJDIR|$(OBJDIR)|" etc/php/php-fpm.conf > $@/php-fpm.conf
	sed "s|OBJDIR|$(OBJDIR)|" etc/php/php-fpm.d/www.conf > $@/php-fpm.d/www.conf

$(OBJDIR):
	mkdir -p $@

$(OBJDIR)/etc:
	mkdir -p $@

clean:
	rm -rf $(OBJDIR)
