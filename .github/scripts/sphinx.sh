#!/usr/bin/env sh

set -e

cd $(dirname $0)/../../docs

pip3 install --user -r requirements.sphinx.txt

make SPHINXOPTS="-A commit=$GITHUB_SHA -A branch=$GITHUB_REF_NAME" html latex
