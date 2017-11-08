SRC := vimiv

PREFIX    := /usr
MANPREFIX := $(PREFIX)/share/man
LICENSEPREFIX := $(PREFIX)/share/licenses
APPDATAPREFIX := $(PREFIX)/share/appadata

default:
	@printf "There is nothing to do.\n"
	@printf "Run 'sudo make install' to install vimiv.\n"
	@printf "Run 'make options' for a list of all options.\n"

options: help
	@printf "\nOptions:\n"
	@printf "PREFIX = $(PREFIX)\n"
	@printf "MANPREFIX = $(MANPREFIX)\n"
	@printf "DESTDIR = $(DESTDIR)\n"
	@printf "LICENSEPREFIX = $(PREFIX)/share/licenses\n"

help:
	@printf "make help:              Print help.\n"
	@printf "make options:        	Print help and list all options.\n"
	@printf "make install:        	Install $(SRC).\n"
	@printf "make uninstall: 	Uninstall $(SRC).\n"

install:
	python3 setup.py install --root=$(DESTDIR)/ --record=install_log.txt
	install -Dm644 config/vimivrc $(DESTDIR)/etc/vimiv/vimivrc
	install -Dm644 config/keys.conf $(DESTDIR)/etc/vimiv/keys.conf
	install -Dm644 vimiv.desktop $(DESTDIR)/usr/share/applications/vimiv.desktop
	install -Dm644 man/vimiv.1 $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
	gzip -n -9 -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
	install -Dm644 man/vimivrc.5 $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5
	gzip -n -9 -f $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5
	scripts/install_icons.sh $(DESTDIR)
	install -Dm644 LICENSE $(DESTDIR)$(LICENSEPREFIX)/vimiv/LICENSE
	install -Dm644 vimiv.appdata.xml $(DESTDIR)$(APPDATAPREFIX)/vimiv.appdata.xml

uninstall:
	rm -rf $(DESTDIR)/etc/vimiv/
	rm -f $(DESTDIR)/usr/share/applications/vimiv.desktop
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1.gz
	rm -f $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5
	rm -f $(DESTDIR)$(MANPREFIX)/man5/vimivrc.5.gz
	scripts/remove_icons.sh $(DESTDIR)
	scripts/uninstall_pythonpkg.sh
	rm -rf $(DESTDIR)$(LICENSEPREFIX)/vimiv/
	rm -f $(DESTDIR)$(APPDATAPREFIX)/vimiv.appdata.xml

clean:
	rm -rf build vimiv.egg-info/

test:
	@scripts/run_tests.sh

lint:
	pylint vimiv/*.py tests/*.py
	pydocstyle vimiv/*.py vimiv/vimiv tests/*.py
	pycodestyle --config=.pycodestyle vimiv/*.py vimiv/vimiv tests/*.py

spellcheck:
	pylint --disable all --enable spelling --spelling-dict en_GB --spelling-private-dict-file=.spelling_dict.txt vimiv/*.py vimiv/vimiv tests/*.py --score no

spellcheck_add_unknown:
	pylint --disable all --enable spelling --spelling-dict en_GB --spelling-private-dict-file=.spelling_dict.txt --spelling-store-unknown-words=y vimiv/*.py vimiv/vimiv tests/*.py --score no

todo:
	pylint --disable all --enable fixme vimiv/*.py vimiv/vimiv tests/*.py --score no

manpages:
	python3 scripts/generate_manpages.py
