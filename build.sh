#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
#
# build.sh - Build the IMX708 GUI client (uv-managed)
#
# Usage:
#   ./build.sh              # generate gRPC stubs
#   ./build.sh --exe        # build standalone executable
#   ./build.sh --deps       # sync dependencies
#
# Prerequisites:
#   curl -LsSf https://astral.sh/uv/install.sh | sh
#

set -euo pipefail

GUI_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-}"

echo "=== IMX708 GUI Client ==="
echo ""

# Check for uv
if ! command -v uv &>/dev/null; then
    echo "  [WARN] uv not found. Install with:"
    echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  Falling back to pip..."
    UV_CMD="python3 -m pip"
else
    UV_CMD="uv run"
fi

# Generate gRPC stubs
echo "[1/3] Generating gRPC stubs..."
mkdir -p "${GUI_DIR}/build"
$UV_CMD grpc_tools.protoc \
    -I"${GUI_DIR}/proto" \
    --python_out="${GUI_DIR}/build" \
    --grpc_python_out="${GUI_DIR}/build" \
    "${GUI_DIR}/proto/imx708.proto" 2>/dev/null || {
    echo "  [WARN] grpc_tools not available. Run: make deps"
}
touch "${GUI_DIR}/build/__init__.py"
echo "  Stubs generated in build/"

# Sync deps if requested
if [ "$MODE" = "--deps" ]; then
    echo ""
    echo "[2/3] Syncing dependencies..."
    uv sync
fi

# Build executable if requested
if [ "$MODE" = "--exe" ]; then
    echo ""
    echo "[2/3] Building executable..."
    $UV_CMD pyinstaller --onefile --windowed \
        --name "IMX708Cam" \
        --add-data "${GUI_DIR}/build/imx708_pb2.py:." \
        --add-data "${GUI_DIR}/build/imx708_pb2_grpc.py:." \
        "${GUI_DIR}/imx708_client.py" 2>/dev/null || {
        echo "  [WARN] pyinstaller not available."
        echo "  Install: uv tool install pyinstaller"
    }
fi

echo ""
echo "=== Ready ==="
echo "Run: make run SERVER=<pi-ip>:50051"
