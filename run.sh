#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ] || [ ! -d .deps/blupe-remote-yam ]; then
  ./setup.sh
fi
exec .venv/bin/python -m agp_remote_yam "$@"
