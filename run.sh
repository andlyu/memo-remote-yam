#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ] || [ ! -d .deps/blupe-remote-yam ]; then
  ./setup.sh
fi
if ! .venv/bin/python -c 'import importlib.util; raise SystemExit(importlib.util.find_spec("sentence_transformers") is None)' >/dev/null 2>&1; then
  ./setup.sh
fi
exec .venv/bin/python -m agp_remote_yam "$@"
