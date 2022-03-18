#!/bin/bash
set -e

if [ -d raviewer ]; then python3 -m yapf -ipr raviewer/; fi
if [ -d tests ]; then python3 -m yapf -ipr tests/; fi
test $(git status --porcelain | wc -l) -eq 0 || { git diff; false; }
