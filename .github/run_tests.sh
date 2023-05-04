#!/bin/bash
set -e

pytest -rfEsx tests/ --cov=raviewer
