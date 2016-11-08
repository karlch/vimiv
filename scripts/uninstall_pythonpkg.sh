#!/bin/bash

# Remove the installed python package from /usr/lib/python3.x/site-packages

if [[ -f install_log.txt ]]; then
    rm $(awk '{print "'/'"$0}' install_log.txt)
else
    printf "python-setuptools does not provide an uninstall option.\n"
    printf "To completely remove vimiv you will have to remove all related"
    printf " files from /usr/lib/python3.x/site-packages/.\n"
    printf "A list of files should have been generated during make install"
    printf " in install_log.txt but seems to have been removed.\n"
fi
