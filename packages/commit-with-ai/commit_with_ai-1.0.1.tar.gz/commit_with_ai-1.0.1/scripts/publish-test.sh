#!/bin/zsh

SCRIPT_DIR=$(dirname "$0")

cd "${SCRIPT_DIR}/../"

source .env.test

rm -rf dist/
uv build
uv publish ./dist/*

# test:
# uvx --index-url https://test.pypi.org/simple/ \
#     --extra-index-url https://pypi.org/simple/ \
#     git-auto-commit
