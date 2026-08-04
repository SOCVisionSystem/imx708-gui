# SPDX-License-Identifier: GPL-2.0-only
#
# Makefile - IMX708 GUI client (managed with uv)
#
# Targets:
#   all       Generate gRPC stubs
#   run       Launch the GUI client
#   exe       Build standalone executable with PyInstaller
#   deps      Sync dependencies with uv
#   clean     Remove build artifacts
#   help      Show help
#

GUI_DIR    := $(CURDIR)
BUILD_DIR  := $(GUI_DIR)/build
CLIENT_PY  := $(GUI_DIR)/imx708_client.py
UV        := $(shell command -v uv 2>/dev/null || echo "pip")

.PHONY: all clean run exe deps help

all: $(BUILD_DIR)/imx708_pb2.py

$(BUILD_DIR)/imx708_pb2.py: proto/imx708.proto
	@echo "Generating gRPC stubs..."
	@mkdir -p $(BUILD_DIR)
	uv run grpc_tools.protoc \
		-I$(GUI_DIR)/proto \
		--python_out=$(BUILD_DIR) \
		--grpc_python_out=$(BUILD_DIR) \
		$(GUI_DIR)/proto/imx708.proto 2>/dev/null || \
	python3 -m grpc_tools.protoc \
		-I$(GUI_DIR)/proto \
		--python_out=$(BUILD_DIR) \
		--grpc_python_out=$(BUILD_DIR) \
		$(GUI_DIR)/proto/imx708.proto 2>/dev/null || \
	echo "  [WARN] Install grpcio-tools: uv sync"
	@touch $(BUILD_DIR)/__init__.py

clean:
	rm -rf $(BUILD_DIR)
	rm -rf dist/ __pycache__/ *.spec .venv/

run: all
	@echo "Starting IMX708 GUI client..."
	uv run python $(CLIENT_PY) --server $(SERVER)

exe: all
	@echo "Building standalone executable..."
	uv run pyinstaller --onefile --windowed \
		--name "IMX708Cam" \
		--add-data "$(BUILD_DIR)/imx708_pb2.py:." \
		--add-data "$(BUILD_DIR)/imx708_pb2_grpc.py:." \
		$(CLIENT_PY) 2>/dev/null || \
	echo "  [WARN] pyinstaller not available. Install with: uv tool install pyinstaller"

deps:
	@echo "Syncing dependencies with uv..."
	uv sync
	@echo "Dependencies ready."

help:
	@echo "IMX708 GUI Client (uv-managed)"
	@echo ""
	@echo "Targets:"
	@echo "  all       Generate gRPC stubs (default)"
	@echo "  clean     Remove build artifacts"
	@echo "  run       Launch GUI (use SERVER=ip:port)"
	@echo "  exe       Build standalone executable"
	@echo "  deps      Sync dependencies with uv"
	@echo ""
	@echo "Examples:"
	@echo "  make deps              # install dependencies"
	@echo "  make run SERVER=192.168.1.100:50051"
	@echo "  make exe"
	@echo ""
	@echo "First time setup:"
	@echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
	@echo "  make deps"
