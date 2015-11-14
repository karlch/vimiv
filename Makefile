VERSION   := 0.0.1

PREFIX    := /usr/local

SRC := vimiv

install:
	mkdir -p $(PREFIX)/bin
	cp vimiv $(PREFIX)/bin
	chmod 755 $(PREFIX)/bin/vimiv
	cp vimivrc.py /etc
	mkdir -p ~/.vimiv
	cp vimivrc.py ~/.vimiv
	cp vimiv.desktop /usr/share/applications

uninstall:
	rm -f $(PREFIX)/bin/vimiv
	rm -f /etc/vimivrc
	rm -f /usr/share/applications/vimiv.desktop
