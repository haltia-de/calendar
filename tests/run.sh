#!/bin/sh
# SPDX-License-Identifier: GPL-2.0
set -eu
cd "$(dirname "$0")/.."
# The widget checks need a display: run them on a virtual X server when
# xvfb-run is installed. Without it they are skipped on a headless host.
if command -v xvfb-run >/dev/null 2>&1; then
    exec xvfb-run -a python3 -m unittest discover -s tests -v
fi
exec python3 -m unittest discover -s tests -v
