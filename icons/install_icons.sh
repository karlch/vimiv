#!/bin/sh

for i in 16 32 64 128 256 512; do
    cp icons/vimiv_${i}x${i}.png /usr/share/icons/hicolor/${i}x${i}/apps/vimiv.png
done

cp icons/vimiv.svg /usr/share/icons/hicolor/scalable/apps/vimiv.svg
