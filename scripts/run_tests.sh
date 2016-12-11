#!/bin/bash

# Run tests for vimiv in Xvfb

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
if [[ ! -f /tmp/.X42-lock ]]; then
    Xvfb :42 -screen 0 800x600x24 1>/dev/null 2>&1 & xvfb_pid="$!"
    sleep 1
    DISPLAY=":42" openbox & openbox_pid="$!"
    sleep 1

    # # We need this so all directories are generated before running tests.
    (DISPLAY=":42" python3 tests/vimiv_testcase.py 1>/dev/null 2>&1 && \
        printf "Vimiv tests can be run.\n\n" && DISPLAY=":42" nosetests3) || \
        (printf "Main test failed.\n" && exit 1)

    kill "$openbox_pid"
    kill "$xvfb_pid"
    printf "Killed Xvfb.\n"
else
    printf "Close the running Xserver running on DISPLAY :42 to start Xvfb.\n"
    exit 1
fi
