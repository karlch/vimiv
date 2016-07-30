SRC := vimiv
VERSION   := 0.6

PREFIX    := /usr
MANPREFIX := $(PREFIX)/share/man

default:
	@printf "There is nothing to do.\n"
	@printf "Run sudo make install to install vimiv.\n"
	@printf "Run make options for a list of all options.\n"

options: help
	@printf "\nOptions:\n"
	@printf "PREFIX = $(PREFIX)\n"
	@printf "MANPREFIX = $(MANPREFIX)\n"
	@printf "DESTDIR = $(DESTDIR)\n"

help:
	@printf "make help:     	Print help.\n"
	@printf "make options:        	Print help and list all options.\n"
	@printf "make install:        	Install $(SRC).\n"
	@printf "make uninstall: 	Uninstall $(SRC).\n"

install:
	python3 setup.py install --root=$(DESTDIR)/ --record=install_log.txt
	mkdir -p $(DESTDIR)/etc/vimiv
	cp config/vimivrc $(DESTDIR)/etc/vimiv/
	cp config/keys.conf $(DESTDIR)/etc/vimiv/
	mkdir -p $(DESTDIR)/usr/share/applications
	cp vimiv.desktop $(DESTDIR)/usr/share/applications/
	mkdir -p $(DESTDIR)$(MANPREFIX)/man1
	cp man/vimiv.1 $(DESTDIR)$(MANPREFIX)/man1/
	chmod 644 $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
	mkdir -p $(DESTDIR)$(MANPREFIX)/man5
	cp man/vimivrc.5 $(DESTDIR)$(MANPREFIX)/man5/
	chmod 644 $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/vimiv
	rm -rf $(DESTDIR)/etc/vimiv/
	rm -f $(DESTDIR)/usr/share/applications/vimiv.desktop
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1.gz
	rm -f $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5
	rm -f $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5.gz
	@printf "python-setuptools does not provide an uninstall option.\n"
	@printf "To completely remove vimiv you will have to remove all related"
	@printf " files from /usr/lib/python3.x/site-packages/.\n"
	@printf "A list of files should have been generated during make install"
	@printf " in install_log.txt.\n"

test:
	@nosetests

lint:
	@pylint vimiv/*.py vimiv/vimiv tests/*.py
