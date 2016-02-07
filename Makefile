VERSION   := 0.5.0

PREFIX    := /usr
MANPREFIX := $(PREFIX)/share/man

SRC := vimiv

install:
	rm -rf /usr/lib/python3.5/site-packages/vimiv
	cp -R vimiv /usr/lib/python3.5/site-packages/

uninstall:
	rm -rf /usr/lib/python3.5/site-packages/vimiv
