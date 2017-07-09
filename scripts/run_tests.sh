#!/bin/bash
# Run tests for vimiv in Xvfb

# Nicely formatted info message
function print_info() {
    printf "\e[1;34m:: \e[1;37m%s\n\e[0;0m" "$1"
}

# Print fail message and exit
function fail() {
    printf "\e[1;31merror: \e[1;37m%s\n\e[0;0m" "$1"
    exit 1
}

hash nosetests3 2>/dev/null || fail "nosetests3 command is not available"
hash Xvfb 2>/dev/null || fail "Xvfb command is not available"

# Receive current testimages
test -d tests || fail "test module not found"

if [[ -d  "tests/vimiv/testimages" ]]; then
    print_info "Updating testimages"
    git --git-dir=tests/vimiv/.git/ --work-tree=tests/vimiv pull
else
    print_info "Receiving testimages"
    git clone --branch=testimages https://github.com/karlch/vimiv tests/vimiv
fi

# Start Xvfb if possible
if [[ ! -f /tmp/.X42-lock ]]; then
    print_info "Running tests in Xvfb"
    Xvfb :42 -screen 0 800x600x24 1>/dev/null 2>&1 &
    xvfb_pid="$!"

    # We need this so all directories are generated before running tests.
    if ! DISPLAY=":42" python3 tests/vimiv_testcase.py 1>/dev/null 2>&1; then
        kill "$xvfb_pid"
        fail "Main test failed."
    fi

    DISPLAY=":42" nosetests3 -c .noserc
    kill "$xvfb_pid"
else
    fail "Close the running Xserver running on DISPLAY :42 to start Xvfb."
fi
