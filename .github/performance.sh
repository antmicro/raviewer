#!/bin/bash
set -e

python3 ./tests/performance.py --random --count 10 --size 1000 750 1920 1080 1954 1500 4000 3000 8000 6000 16000 12000
