SRC := vimiv

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
	scripts/install_icons.sh $(DESTDIR)

uninstall:
	rm -rf $(DESTDIR)/etc/vimiv/
	rm -f $(DESTDIR)/usr/share/applications/vimiv.desktop
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1.gz
	rm -f $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5
	rm -f $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5.gz
	scripts/remove_icons.sh $(DESTDIR)
	scripts/uninstall_pythonpkg.sh

test:
	@scripts/run_tests.sh

lint:
	pylint vimiv/*.py vimiv/vimiv tests/*.py
	pydocstyle vimiv/*.py vimiv/vimiv tests/*.py
	pycodestyle --config=.pycodestyle vimiv/*.py vimiv/vimiv tests/*.py
