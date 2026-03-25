#!/usr/bin/env sh

set -eu

export PYTHONPATH="/app/share/pulse${PYTHONPATH:+:$PYTHONPATH}"

exec python3 -m pulse.main "$@"
