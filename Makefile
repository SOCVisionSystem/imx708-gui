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
# NOT "build/": that is setuptools' own scratch directory and it wipes the
# generated stubs during packaging.
PROTO_DIR  := $(GUI_DIR)/imx708_proto
CLIENT_PY  := $(GUI_DIR)/imx708_client.py
SERVER     ?= localhost:50051

# Prefer uv when it is available, otherwise drive the system interpreter.
# RUN is used consistently below; it used to be computed and then ignored.
ifeq ($(shell command -v uv 2>/dev/null),)
RUN := python3 -m
RUNNER := python3
else
RUN := uv run python -m
RUNNER := uv run python
endif

.PHONY: all clean distclean run exe deps help

all: $(PROTO_DIR)/imx708_pb2.py

# No "|| echo [WARN]" here: swallowing a protoc failure produced a GUI that
# started up and then reported "gRPC or proto modules not available".
$(PROTO_DIR)/imx708_pb2.py: proto/imx708.proto
	@echo "Generating gRPC stubs..."
	@mkdir -p $(PROTO_DIR)
	$(RUN) grpc_tools.protoc \
		-I$(GUI_DIR)/proto \
		--python_out=$(PROTO_DIR) \
		--grpc_python_out=$(PROTO_DIR) \
		$(GUI_DIR)/proto/imx708.proto
	@touch $(PROTO_DIR)/__init__.py

# .venv/ is deliberately left alone: "make clean" should not destroy the
# developer's environment and force a full re-download.
clean:
	rm -rf $(PROTO_DIR)
	rm -rf build/ dist/ __pycache__/ *.spec *.egg-info/

distclean: clean
	rm -rf .venv/

run: all
	@echo "Starting IMX708 GUI client..."
	$(RUNNER) $(CLIENT_PY) --server $(SERVER)

exe: all
	@echo "Building standalone executable..."
	$(RUN) PyInstaller --onefile --windowed \
		--name "IMX708Cam" \
		--add-data "$(PROTO_DIR)/imx708_pb2.py:." \
		--add-data "$(PROTO_DIR)/imx708_pb2_grpc.py:." \
		$(CLIENT_PY)

deps:
	@echo "Syncing dependencies with uv..."
	uv sync
	@echo "Dependencies ready."

help:
	@echo "IMX708 GUI Client (uv-managed)"
	@echo ""
	@echo "Targets:"
	@echo "  all       Generate gRPC stubs (default)"
	@echo "  clean     Remove build artifacts (keeps .venv)"
	@echo "  distclean Remove build artifacts and .venv"
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
