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

# Start Xvfb if possible
if [[ ! -f /tmp/.X1-lock ]]; then
    Xvfb -screen 1 800x600x24 :1 & xvfb_pid="$!"
    sleep 2
    DISPLAY=":1" herbstluftwm & herbst_pid="$!"
    sleep 1
    # We need this so all directories are generated before running tests.
    (DISPLAY=":1" python3 tests/main_test.py 1>/dev/null 2>&1 && \
        printf "Vimiv tests can be run.\n\n") || \
        (printf "Main test failed.\n" && exit 1)
    DISPLAY=":1" nosetests
    kill "$xvfb_pid"
    kill "$herbst_pid"
else
    printf "Close the running Xserver running on DISPLAY :1 to start Xvfb.\n"
    exit 1
fi
