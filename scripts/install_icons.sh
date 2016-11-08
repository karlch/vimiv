#!/bin/sh

# Copy all vimiv icons to the correct icon directory

DESTDIR=$1

for i in 16 32 64 128 256 512; do
    install -Dm644 icons/vimiv_${i}x${i}.png ${DESTDIR}/usr/share/icons/hicolor/${i}x${i}/apps/vimiv.png
done

install -Dm644 icons/vimiv.svg ${DESTDIR}/usr/share/icons/hicolor/scalable/apps/vimiv.svg
