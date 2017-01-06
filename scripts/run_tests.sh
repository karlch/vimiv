#!/bin/bash
# Run tests for vimiv in Xvfb

# Nicely formatted info message
function print_info() {
    printf "\e[1;34m:: \e[1;37m%s\n\e[0;0m" "$1"
}

# Receive current testimages
(
cd tests 1>/dev/null 2>&1 || exit 1
if [[ -d  "vimiv/testimages" ]]; then
    (
    print_info "Updating testimages"
    cd vimiv 1>/dev/null 2>&1 || exit 1
    git pull
    )
else
    print_info "Receiving testimages"
    git clone --branch=testimages https://github.com/karlch/vimiv
fi
)

function fail_tests() {
    printf "Main test failed.\n"
    kill "$xvfb_pid"
    exit 1
}

# Start Xvfb if possible
if [[ ! -f /tmp/.X42-lock ]]; then
    print_info "Running tests in Xvfb"
    Xvfb :42 -screen 0 800x600x24 1>/dev/null 2>&1 & xvfb_pid="$!"
    # We need this so all directories are generated before running tests.
    DISPLAY=":42" python3 tests/vimiv_testcase.py 1>/dev/null 2>&1 || fail_tests
    DISPLAY=":42" nosetests3 -c .noserc
    kill "$xvfb_pid"
else
    printf "Close the running Xserver running on DISPLAY :42 to start Xvfb.\n"
    exit 1
fi
