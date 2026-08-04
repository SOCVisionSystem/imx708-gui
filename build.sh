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
PROTO_OUT="${GUI_DIR}/imx708_proto"
MODE="${1:-}"

echo "=== IMX708 GUI Client ==="
echo ""

# Pick a runner. Note the two forms are NOT interchangeable: "uv run" takes a
# command name, plain Python needs "-m". The old fallback built the nonsense
# command "python3 -m pip grpc_tools.protoc".
if command -v uv &>/dev/null; then
    PROTOC_CMD=(uv run python -m grpc_tools.protoc)
    RUN_CMD=(uv run)
else
    echo "  [WARN] uv not found. Install with:"
    echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  Falling back to the system interpreter..."
    PROTOC_CMD=(python3 -m grpc_tools.protoc)
    RUN_CMD=(python3 -m)
fi

# Generate gRPC stubs. Failures here are fatal: the GUI silently degrades to
# "gRPC or proto modules not available" if the stubs are missing, so hiding
# the error behind 2>/dev/null made the problem far harder to diagnose.
echo "[1/3] Generating gRPC stubs..."
mkdir -p "${PROTO_OUT}"
"${PROTOC_CMD[@]}" \
    -I"${GUI_DIR}/proto" \
    --python_out="${PROTO_OUT}" \
    --grpc_python_out="${PROTO_OUT}" \
    "${GUI_DIR}/proto/imx708.proto"
touch "${PROTO_OUT}/__init__.py"
echo "  Stubs generated in imx708_proto/"

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
    "${RUN_CMD[@]}" pyinstaller --onefile --windowed \
        --name "IMX708Cam" \
        --icon "${GUI_DIR}/app_icon.png" \
        --add-data "${PROTO_OUT}/imx708_pb2.py:imx708_proto" \
        --add-data "${PROTO_OUT}/imx708_pb2_grpc.py:imx708_proto" \
        --add-data "${PROTO_OUT}/__init__.py:imx708_proto" \
        --hidden-import "google.protobuf" \
        --hidden-import "google.protobuf.descriptor" \
        --hidden-import "google.protobuf.message" \
        --hidden-import "grpc" \
        --hidden-import "grpc._channel" \
        --hidden-import "grpc._cython" \
        "${GUI_DIR}/imx708_client.py"
fi

echo ""
echo "=== Ready ==="
echo "Run: make run SERVER=<pi-ip>:50051"
