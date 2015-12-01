VERSION   := 0.1.0

PREFIX    := /usr/local
MANPREFIX := $(PREFIX)/share/man

SRC := vimiv

install:
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	cp vimiv $(DESTDIR)$(PREFIX)/bin/
	chmod 755 $(DESTDIR)$(PREFIX)/bin/vimiv
	mkdir -p /etc
	cp vimivrc.py $(DESTDIR)/etc/
	mkdir -p $(DESTDIR)/usr/share/applications
	cp vimiv.desktop $(DESTDIR)/usr/share/applications/
	mkdir -p $(DESTDIR)$(MANPREFIX)/man1
	cp vimiv.1 $(DESTDIR)$(MANPREFIX)/man1/
	chmod 644 $(DESTDIR)$(MANPREFIX)/man1/vimiv.1

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/vimiv
	rm -f $(DESTDIR)/etc/vimivrc.py
	rm -f $(DESTDIR)/usr/share/applications/vimiv.desktop
	rm -f $(DESTDIR)$(MANPREFIX)/man1/vimiv.1
