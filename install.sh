#!/bin/sh
# SPDX-License-Identifier: GPL-2.0
# Install b8k-calendar into a root file system: sh install.sh [ROOT]
# (ROOT empty or / for this system). The tablet shell's build runs it for
# its image. It needs Python 3 with PyGObject (GTK 3) only.
set -eu
root=${1:-}
root=${root%/}
here=$(cd "$(dirname "$0")" && pwd)
install -D -m 755 "$here/b8k-calendar" "$root/usr/local/bin/b8k-calendar"
install -D -m 644 "$here/calendar.svg" "$root/usr/local/share/b8k/calendar.svg"
install -D -m 644 "$here/calendar.conf" "$root/usr/local/share/b8k/apps.d/calendar.conf"
