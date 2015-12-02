VERSION   := 0.1.0

PREFIX    := /usr
MANPREFIX := $(PREFIX)/share/man

SRC := vimiv

install:
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	cp vimiv $(DESTDIR)$(PREFIX)/bin/
	chmod 755 $(DESTDIR)$(PREFIX)/bin/vimiv
	mkdir -p $(DESTDIR)/etc/vimiv
	cp vimivrc.py $(DESTDIR)/etc/vimiv/
	mkdir -p $(DESTDIR)/usr/share/applications
	cp vimiv.desktop $(DESTDIR)/usr/share/applications/
	mkdir -p $(DESTDIR)$(MANPREFIX)/man1
	cp vimiv.1 $(DESTDIR)$(MANPREFIX)/man1/
	chmod 644 $(DESTDIR)$(MANPREFIX)/man1/vimiv.1

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/vimiv
	rm -rf $(DESTDIR)/etc/vimiv/vimivrc.py
	rm -f $(DESTDIR)/usr/share/applications/vimiv.desktop
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
