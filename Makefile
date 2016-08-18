SRC := vimiv
VERSION   := 0.6.1

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
	install -Dm644 config/vimivrc $(DESTDIR)/etc/vimiv/vimivrc
	install -Dm644 config/keys.conf $(DESTDIR)/etc/vimiv/keys.conf
	install -Dm644 vimiv.desktop $(DESTDIR)/usr/share/applications/vimiv.desktop
	install -Dm644 man/vimiv.1 $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
	install -Dm644 man/vimivrc.5 $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5
	icons/install_icons.sh $(DESTDIR)

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/vimiv
	rm -rf $(DESTDIR)/etc/vimiv/
	rm -f $(DESTDIR)/usr/share/applications/vimiv.desktop
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1.gz
	rm -f $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5
	rm -f $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5.gz
	icons/remove_icons.sh $(DESTDIR)
	@printf "python-setuptools does not provide an uninstall option.\n"
	@printf "To completely remove vimiv you will have to remove all related"
	@printf " files from /usr/lib/python3.x/site-packages/.\n"
	@printf "A list of files should have been generated during make install"
	@printf " in install_log.txt.\n"

test:
	@tests/run_tests.sh

lint:
	pylint vimiv/*.py vimiv/vimiv tests/*.py
	pydocstyle vimiv/*.py vimiv/vimiv tests/*.py
	pycodestyle --config=.pycodestyle vimiv/*.py vimiv/vimiv tests/*.py
