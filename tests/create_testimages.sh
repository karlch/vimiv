#!/bin/bash

# Simple script to fetch the images used in vimiv's testsuite

cd tests 1>/dev/null 2>&1
if [[ -d  "vimiv/testimages" ]]; then
    printf "updating testimages\n"
    cd vimiv 1>/dev/null 2>&1
    git pull
    cd ..
else
    printf "receiving testimages\n"
    git clone --branch=testimages https://github.com/karlch/vimiv
fi
cd ..
