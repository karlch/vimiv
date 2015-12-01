VERSION   := 0.0.1

PREFIX    := /usr/local

SRC := vimiv

install:
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	cp vimiv $(DESTDIR)$(PREFIX)/bin
	chmod 755 $(DESTDIR)$(PREFIX)/bin/vimiv
	cp vimivrc.py $(DESTDIR)/etc
	cp vimiv.desktop $(DESTDIR)/usr/share/applications

uninstall:
	rm -f $(DESTDIR)/$(PREFIX)/bin/vimiv
	rm -f $(DESTDIR)/etc/vimivrc
	rm -f $(DESTDIR)/usr/share/applications/vimiv.desktop
