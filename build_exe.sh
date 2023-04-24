#!/bin/bash

# Delete the dist directory if it exists
if [ -d "dist" ]; then
    rm -r dist
fi

# Build the executable with pyinstaller using the "onefile" option
pyinstaller -F --collect-submodules=pydicom --icon=images/logo.ico --noconsole GUIshortCardiac.py --onefile

# Build the executable with pyinstaller using the "onedir" option
pyinstaller -F --collect-submodules=pydicom --icon=images/logo.ico --noconsole GUIshortCardiac.py --onedir
