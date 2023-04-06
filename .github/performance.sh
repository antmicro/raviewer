#!/bin/bash
set -e

python3 ./tests/performance.py --random --size 1000 750
python3 ./tests/performance.py --random --size 16000 12000 --count 1 10
