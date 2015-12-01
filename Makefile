VERSION   := 0.1.0

PREFIX    := /usr/local

SRC := vimiv

install:
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	cp vimiv $(DESTDIR)$(PREFIX)/bin
	chmod 755 $(DESTDIR)$(PREFIX)/bin/vimiv
	mkdir -p /etc
	cp vimivrc.py $(DESTDIR)/etc
	mkdir -p $(DESTDIR)/usr/share/applications
	cp vimiv.desktop $(DESTDIR)/usr/share/applications

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/vimiv
	rm -f $(DESTDIR)/etc/vimivrc.py
	rm -f $(DESTDIR)/usr/share/applications/vimiv.desktop
