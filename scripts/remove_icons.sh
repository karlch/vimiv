#!/bin/sh

# Remove all vimiv icons from the system directory

DESTDIR=$1

for i in 16 32 64 128 256 512; do
    rm ${DESTDIR}/usr/share/icons/hicolor/${i}x${i}/apps/vimiv.png
done

rm ${DESTDIR}/usr/share/icons/hicolor/scalable/apps/vimiv.svg
