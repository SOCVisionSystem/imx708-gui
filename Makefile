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
PROTO_DIR  := $(GUI_DIR)/imx708_proto
CLIENT_PY  := $(GUI_DIR)/imx708_client.py
GUI_PKG    := $(GUI_DIR)/imx708_gui
SERVER     ?= localhost:50051

# Install paths
DESTDIR    ?=
PREFIX     ?= /usr/local
BINDIR     := $(DESTDIR)$(PREFIX)/bin
APPDIR     := $(DESTDIR)$(PREFIX)/share/applications
ICONDIR    := $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps

# Binary names
EXE_NAME   := imx708-cam
EXE_BIN    := imx708-cam-bin
EXE_SRC    := $(GUI_DIR)/dist/IMX708Cam

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
	find $(GUI_PKG) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

distclean: clean
	rm -rf .venv/

run: all
	@echo "Starting IMX708 GUI client..."
	$(RUNNER) $(CLIENT_PY) --server $(SERVER)

# PyInstaller's --add-data separator is ":" everywhere except Windows,
# which needs ";" (colon collides with drive letters like "C:"). Destination
# is imx708_proto/ to match build.sh and the sys.path setup in imx708_client.py.
ifeq ($(OS),Windows_NT)
DATA_SEP := ;
else
DATA_SEP := :
endif

exe: all
	@echo "Building standalone executable..."
	$(RUN) PyInstaller --onefile --windowed \
		--name "IMX708Cam" \
		--add-data "$(PROTO_DIR)/imx708_pb2.py$(DATA_SEP)imx708_proto" \
		--add-data "$(PROTO_DIR)/imx708_pb2_grpc.py$(DATA_SEP)imx708_proto" \
		--add-data "$(PROTO_DIR)/__init__.py$(DATA_SEP)imx708_proto" \
		$(CLIENT_PY)

deps:
	@echo "Syncing dependencies with uv..."
	uv sync
	@echo "Dependencies ready."

# ═══════════════════════════════════════════════════════════════════════════
# Install / Uninstall
# ═══════════════════════════════════════════════════════════════════════════

.PHONY: install uninstall

install: exe
	@echo "━━━ Installing IMX708 Camera GUI ━━━"
	@echo "  Binary:  $(BINDIR)/$(EXE_BIN)"
	@echo "  Wrapper: $(BINDIR)/$(EXE_NAME)"
	@echo "  Desktop: $(APPDIR)/$(EXE_NAME).desktop"
	@echo "  Icon:    $(ICONDIR)/$(EXE_NAME).png"
	@echo ""
	install -d $(BINDIR)
	install -m 755 $(EXE_SRC) $(BINDIR)/$(EXE_BIN)
	install -m 755 packaging/$(EXE_NAME).sh $(BINDIR)/$(EXE_NAME)
	install -d $(APPDIR)
	install -m 644 packaging/$(EXE_NAME).desktop $(APPDIR)/
	@if [ -f app_icon.png ]; then \
		install -d $(ICONDIR) && \
		install -m 644 app_icon.png $(ICONDIR)/$(EXE_NAME).png; \
	fi
	@echo ""
	@echo "Installation complete."
	@echo "Run: $(EXE_NAME) --server <host>:<port>"

uninstall:
	@echo "━━━ Uninstalling IMX708 Camera GUI ━━━"
	rm -f $(BINDIR)/$(EXE_BIN)
	rm -f $(BINDIR)/$(EXE_NAME)
	rm -f $(APPDIR)/$(EXE_NAME).desktop
	rm -f $(ICONDIR)/$(EXE_NAME).png
	@echo "Uninstall complete."

help:
	@echo "IMX708 GUI Client (uv-managed)"
	@echo ""
	@echo "Targets:"
	@echo "  all       Generate gRPC stubs (default)"
	@echo "  clean     Remove build artifacts (keeps .venv)"
	@echo "  distclean Remove build artifacts and .venv"
	@echo "  run       Launch GUI (use SERVER=ip:port)"
	@echo "  exe       Build standalone executable"
	@echo "  install   Install executable + desktop entry (sudo)"
	@echo "  uninstall Remove installed files (sudo)"
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
