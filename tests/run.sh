#!/bin/sh
# SPDX-License-Identifier: GPL-2.0
set -eu
cd "$(dirname "$0")/.."
# Use xvfb-run -a sh tests/run.sh for the widget checks on a headless host.
python3 -m unittest discover -s tests -v
