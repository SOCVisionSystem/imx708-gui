#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
#
# imx708-cam - Wrapper script for the IMX708 Camera GUI
#
# Installed to /usr/local/bin/imx708-cam by "make install".
# Launches the PyInstaller-bundled executable with any passed arguments.
#

EXEC_DIR="$(dirname "$(readlink -f "$0")")"
EXEC="${EXEC_DIR}/imx708-cam-bin"

if [ ! -x "$EXEC" ]; then
    echo "Error: IMX708 Camera executable not found at $EXEC" >&2
    echo "Reinstall with: sudo make install" >&2
    exit 1
fi

exec "$EXEC" "$@"
