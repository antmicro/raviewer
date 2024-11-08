#!/bin/bash
set -e

mkdir -p export
python3 ./tests/export.py resources -w 500 1001 -d export
