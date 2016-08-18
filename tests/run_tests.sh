#!/bin/bash

# Runs tests for vimiv in Xvfb

# Receive current testimages
(
cd tests 1>/dev/null 2>&1 || exit 1
if [[ -d  "vimiv/testimages" ]]; then
    (
    printf "updating testimages\n"
    cd vimiv 1>/dev/null 2>&1 || exit 1
    git pull
    )
else
    printf "receiving testimages\n"
    git clone --branch=testimages https://github.com/karlch/vimiv
fi
)

# Start Xvfb if necessary
if [[ ! -f /tmp/.X1-lock ]]; then
    Xvfb -screen 1 800x600x24 :1 &
    sleep 2
    herbstluftwm &
    sleep 1
fi
DISPLAY=":1" nosetests
