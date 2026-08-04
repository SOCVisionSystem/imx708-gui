# SPDX-License-Identifier: GPL-2.0-only
"""
imx708_client - Cross-platform PySide6 GUI for IMX708 camera sensor

Copyright (C) 2026 SoC Centric

Author: Sandesh <sandesh@soccentric.com>

macOS-like GUI with sidebar navigation, SVG icons, and gRPC streaming.
Tests and verifies every feature of the Sony IMX708 sensor.

Usage:
    python imx708_client.py [--server localhost:50051]

Build executable:
    pip install pyinstaller
    pyinstaller --onefile --windowed --icon=icon.icns imx708_client.py
"""

import sys
import os
import json
import time
import struct
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# Try to import PySide6
try:
    from PySide6.QtCore import (
        Qt, QThread, Signal, QObject, QTimer, QSize, QByteArray,
        QPropertyAnimation, QEasingCurve, QRect, QPoint
    )
    from PySide6.QtGui import (
        QAction, QColor, QFont, QIcon, QPainter, QPixmap,
        QPalette, QBrush, QLinearGradient, QFontDatabase,
        QCursor, QPen
    )
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QSlider, QComboBox, QGroupBox, QGridLayout,
        QFormLayout, QTabWidget, QTextEdit, QStatusBar, QMenuBar,
        QMenu, QFileDialog, QMessageBox, QCheckBox, QSpinBox,
        QDoubleSpinBox, QScrollArea, QFrame, QSplitter, QListWidget,
        QListWidgetItem, QStackedWidget, QToolButton, QSizePolicy,
        QProgressBar, QLineEdit, QPlainTextEdit
    )
except ImportError:
    print("PySide6 is required. Install with: pip install PySide6")
    sys.exit(1)

# Try to import gRPC
try:
    import grpc
    from grpc import insecure_channel
    HAVE_GRPC = True
except ImportError:
    HAVE_GRPC = False
    print("gRPC not available. Install with: pip install grpcio grpcio-tools")

# Try to import proto modules
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'build'))
    import imx708_pb2
    import imx708_pb2_grpc
    HAVE_PROTO = True
except ImportError:
    HAVE_PROTO = False
    print("Proto modules not found. Generate with: ./build.sh")


# ---------------------------------------------------------------------------
# SVG Icons (inline, macOS-style)
# ---------------------------------------------------------------------------

ICON_CAMERA = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
  <circle cx="12" cy="13" r="4"/>
</svg>"""

ICON_SETTINGS = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <circle cx="12" cy="12" r="3"/>
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
</svg>"""

ICON_PLAY = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
  <polygon points="5 3 19 12 5 21 5 3"/>
</svg>"""

ICON_STOP = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
  <rect x="4" y="4" width="16" height="16" rx="2"/>
</svg>"""

ICON_CAPTURE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="6" fill="currentColor"/>
</svg>"""

ICON_CHART = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="18" y1="20" x2="18" y2="10"/>
  <line x1="12" y1="20" x2="12" y2="4"/>
  <line x1="6" y1="20" x2="6" y2="14"/>
</svg>"""

ICON_INFO = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <circle cx="12" cy="12" r="10"/>
  <line x1="12" y1="16" x2="12" y2="12"/>
  <line x1="12" y1="8" x2="12.01" y2="8"/>
</svg>"""

ICON_WIFI = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
  <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
  <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
  <circle cx="12" cy="20" r="1" fill="currentColor"/>
</svg>"""

ICON_SLIDERS = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="4" y1="21" x2="4" y2="14"/>
  <line x1="4" y1="10" x2="4" y2="3"/>
  <line x1="12" y1="21" x2="12" y2="12"/>
  <line x1="12" y1="8" x2="12" y2="3"/>
  <line x1="20" y1="21" x2="20" y2="16"/>
  <line x1="20" y1="12" x2="20" y2="3"/>
  <line x1="1" y1="14" x2="7" y2="14"/>
  <line x1="9" y1="8" x2="15" y2="8"/>
  <line x1="17" y1="16" x2="23" y2="16"/>
</svg>"""

ICON_TERMINAL = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <polyline points="4 17 10 11 4 5"/>
  <line x1="12" y1="19" x2="20" y2="19"/>
</svg>"""

ICON_PALETTE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <circle cx="13.5" cy="6.5" r="0.5" fill="currentColor"/>
  <circle cx="17.5" cy="10.5" r="0.5" fill="currentColor"/>
  <circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/>
  <circle cx="6.5" cy="12.5" r="0.5" fill="currentColor"/>
  <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-1 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-5.52-4.5-10-10-10z"/>
</svg>"""

ICON_GRID = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <rect x="3" y="3" width="7" height="7"/>
  <rect x="14" y="3" width="7" height="7"/>
  <rect x="14" y="14" width="7" height="7"/>
  <rect x="3" y="14" width="7" height="7"/>
</svg>"""


def make_icon(svg: str, size: int = 24, color: str = "#555") -> QIcon:
    """Create a QIcon from SVG data."""
    colored = svg.replace('currentColor', color)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    try:
        from PySide6.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(QByteArray(colored.encode()))
        renderer.render(painter)
    except ImportError:
        pass
    painter.end()
    return QIcon(pixmap)


# ---------------------------------------------------------------------------
# gRPC Client Thread
# ---------------------------------------------------------------------------

class GrpcClient(QObject):
    """gRPC client running in a background thread."""
    status_updated = Signal(dict)
    frame_received = Signal(dict)
    connection_changed = Signal(bool)
    log_message = Signal(str)

    def __init__(self, server_addr: str = "localhost:50051"):
        super().__init__()
        self.server_addr = server_addr
        self._channel = None
        self._stub = None
        self._connected = False
        self._running = False
        self._status_thread = None
        self._frame_thread = None

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        if not HAVE_GRPC or not HAVE_PROTO:
            self.log_message.emit("gRPC or proto modules not available")
            return False
        try:
            self._channel = insecure_channel(self.server_addr)
            self._stub = imx708_pb2_grpc.Imx708ServiceStub(self._channel)
            # Test connection
            resp = self._stub.GetStatus(imx708_pb2.Empty(), timeout=2)
            self._connected = True
            self.connection_changed.emit(True)
            self.log_message.emit(f"Connected to {self.server_addr}")
            return True
        except Exception as e:
            self._connected = False
            self.connection_changed.emit(False)
            self.log_message.emit(f"Connection failed: {e}")
            return False

    def disconnect(self):
        self._running = False
        if self._channel:
            self._channel.close()
        self._connected = False
        self.connection_changed.emit(False)

    # ---- Unary RPCs ----

    def get_status(self) -> Optional[Dict]:
        if not self._stub:
            return None
        try:
            resp = self._stub.GetStatus(imx708_pb2.Empty(), timeout=5)
            return {
                'temperature': resp.temperature,
                'frame_count': resp.frame_count,
                'pll_locked': resp.pll_locked,
                'streaming': resp.streaming,
                'error': resp.error,
                'gain': resp.gain,
                'digital_gain': resp.digital_gain,
                'exposure': resp.exposure,
                'width': resp.width,
                'height': resp.height,
                'fps': resp.fps,
            }
        except Exception as e:
            self.log_message.emit(f"get_status error: {e}")
            return None

    def get_modes(self) -> List[Dict]:
        if not self._stub:
            return []
        try:
            resp = self._stub.GetModes(imx708_pb2.Empty(), timeout=5)
            return [
                {
                    'index': m.index, 'width': m.width, 'height': m.height,
                    'code': m.code, 'fps': m.fps, 'hblank': m.hblank,
                    'vblank': m.vblank, 'bit_depth': m.bit_depth,
                    'pixel_rate': m.pixel_rate
                }
                for m in resp.modes
            ]
        except Exception as e:
            self.log_message.emit(f"get_modes error: {e}")
            return []

    def start_stream(self) -> bool:
        if not self._stub:
            return False
        try:
            resp = self._stub.StartStream(imx708_pb2.Empty(), timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"start_stream error: {e}")
            return False

    def stop_stream(self) -> bool:
        if not self._stub:
            return False
        try:
            resp = self._stub.StopStream(imx708_pb2.Empty(), timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"stop_stream error: {e}")
            return False

    def set_gain(self, analog: int, digital: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.GainConfig(analog_gain=analog, digital_gain=digital)
            resp = self._stub.SetGain(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_gain error: {e}")
            return False

    def set_exposure(self, exposure: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.ExposureConfig(exposure=exposure)
            resp = self._stub.SetExposure(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_exposure error: {e}")
            return False

    def set_test_pattern(self, pattern: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.TestPatternConfig(pattern=pattern)
            resp = self._stub.SetTestPattern(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_test_pattern error: {e}")
            return False

    def set_hdr(self, mode: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.HdrConfig(mode=mode)
            resp = self._stub.SetHdr(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_hdr error: {e}")
            return False

    def soft_reset(self) -> bool:
        if not self._stub:
            return False
        try:
            resp = self._stub.SoftReset(imx708_pb2.Empty(), timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"soft_reset error: {e}")
            return False

    def capture_frame(self) -> Optional[Dict]:
        if not self._stub:
            return None
        try:
            req = imx708_pb2.CaptureParams()
            resp = self._stub.CaptureFrame(req, timeout=30)
            return {
                'width': resp.width,
                'height': resp.height,
                'stride': resp.stride,
                'format': resp.format,
                'timestamp_ns': resp.timestamp_ns,
                'frame_number': resp.frame_number,
                'gain': resp.gain,
                'exposure': resp.exposure,
                'data': resp.data,
            }
        except Exception as e:
            self.log_message.emit(f"capture_frame error: {e}")
            return None

    def read_register(self, reg: int) -> Optional[int]:
        if not self._stub:
            return None
        try:
            req = imx708_pb2.RegisterAccess(reg=reg)
            resp = self._stub.ReadRegister(req, timeout=5)
            return resp.val
        except Exception as e:
            self.log_message.emit(f"read_register error: {e}")
            return None

    def write_register(self, reg: int, val: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.RegisterAccess(reg=reg, val=val)
            resp = self._stub.WriteRegister(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"write_register error: {e}")
            return False

    # ---- Streaming RPCs ----

    def start_status_stream(self):
        """Start streaming sensor status updates."""
        if self._running or not self._stub:
            return
        self._running = True
        self._status_thread = threading.Thread(target=self._status_loop, daemon=True)
        self._status_thread.start()

    def stop_status_stream(self):
        self._running = False

    def _status_loop(self):
        try:
            for event in self._stub.StreamStatus(imx708_pb2.Empty()):
                if not self._running:
                    break
                if event.HasField('status_update'):
                    s = event.status_update
                    self.status_updated.emit({
                        'temperature': s.temperature,
                        'frame_count': s.frame_count,
                        'pll_locked': s.pll_locked,
                        'streaming': s.streaming,
                        'error': s.error,
                        'gain': s.gain,
                        'digital_gain': s.digital_gain,
                        'exposure': s.exposure,
                    })
        except Exception as e:
            if self._running:
                self.log_message.emit(f"Status stream ended: {e}")
        self._running = False


# ---------------------------------------------------------------------------
# Sidebar Widget
# ---------------------------------------------------------------------------

class SidebarButton(QPushButton):
    """macOS-style sidebar button."""
    def __init__(self, text: str, icon_svg: str, parent=None):
        super().__init__(parent)
        self.setIcon(make_icon(icon_svg, 20, "#007AFF"))
        self.setText(f"  {text}")
        self.setFixedHeight(36)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 6px 12px;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                color: #333;
                background: transparent;
            }
            QPushButton:hover {
                background: #E8E8E8;
            }
            QPushButton:checked {
                background: #007AFF;
                color: white;
            }
        """)
        self.setCheckable(True)


class SidebarWidget(QWidget):
    """macOS-style sidebar with icon buttons."""
    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet("""
            SidebarWidget {
                background: #F5F5F7;
                border-right: 1px solid #D2D2D7;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 20, 8, 20)
        layout.setSpacing(2)

        # App title
        title = QLabel("IMX708 Camera")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1D1D1F;
            padding: 8px 12px 16px 12px;
        """)
        layout.addWidget(title)

        # Navigation buttons
        self.buttons = []
        nav_items = [
            ("Dashboard", ICON_CAMERA),
            ("Controls", ICON_SLIDERS),
            ("Capture", ICON_CAPTURE),
            ("Image", ICON_PALETTE),
            ("Test Patterns", ICON_GRID),
            ("Registers", ICON_TERMINAL),
            ("Info", ICON_INFO),
        ]

        for text, icon_svg in nav_items:
            btn = SidebarButton(text, icon_svg)
            btn.clicked.connect(lambda checked, b=btn, i=len(self.buttons): self._on_click(b, i))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

        # Connection status
        self.conn_label = QLabel("○ Disconnected")
        self.conn_label.setStyleSheet("""
            color: #FF3B30;
            font-size: 11px;
            padding: 8px 12px;
        """)
        layout.addWidget(self.conn_label)

        # Select first
        if self.buttons:
            self.buttons[0].setChecked(True)

    def _on_click(self, btn: SidebarButton, index: int):
        for b in self.buttons:
            b.setChecked(b == btn)
        self.page_changed.emit(index)

    def set_connected(self, connected: bool):
        if connected:
            self.conn_label.setText("● Connected")
            self.conn_label.setStyleSheet("""
                color: #30D158;
                font-size: 11px;
                padding: 8px 12px;
            """)
        else:
            self.conn_label.setText("○ Disconnected")
            self.conn_label.setStyleSheet("""
                color: #FF3B30;
                font-size: 11px;
                padding: 8px 12px;
            """)


# ---------------------------------------------------------------------------
# Dashboard Page
# ---------------------------------------------------------------------------

class DashboardPage(QWidget):
    """Main dashboard showing sensor status in real-time."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()

        # Connect status updates
        self.client.status_updated.connect(self._update_status)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("Sensor Dashboard")
        header.setStyleSheet("font-size: 22px; font-weight: 600; color: #1D1D1F;")
        layout.addWidget(header)

        # Status cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.status_cards = {}
        card_data = [
            ("temperature", "Temperature", "0°C", "#FF9F0A"),
            ("streaming", "Streaming", "Stopped", "#30D158"),
            ("pll", "PLL", "Unlocked", "#FF3B30"),
            ("frames", "Frames", "0", "#007AFF"),
        ]

        for key, title, value, color in card_data:
            card = self._create_card(title, value, color)
            cards_layout.addWidget(card)
            self.status_cards[key] = card

        layout.addLayout(cards_layout)

        # Gain/Exposure info
        info_group = QGroupBox("Current Settings")
        info_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px; font-weight: 600;
                color: #1D1D1F; border: 1px solid #D2D2D7;
                border-radius: 8px; margin-top: 12px;
                padding: 16px 12px 12px 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px; padding: 0 6px;
            }
        """)
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)

        self.gain_label = QLabel("0")
        self.dgain_label = QLabel("0")
        self.exposure_label = QLabel("0")
        self.res_label = QLabel("N/A")

        for label, widget in [
            ("Analog Gain:", self.gain_label),
            ("Digital Gain:", self.dgain_label),
            ("Exposure:", self.exposure_label),
            ("Resolution:", self.res_label),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #6E6E73; font-size: 12px;")
            widget.setStyleSheet("color: #1D1D1F; font-size: 13px; font-weight: 500;")
            info_layout.addRow(lbl, widget)

        layout.addWidget(info_group)

        # Control buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.connect_btn = QPushButton(" Connect")
        self.connect_btn.setIcon(make_icon(ICON_WIFI, 16, "#30D158"))
        self.connect_btn.clicked.connect(self._toggle_connect)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px; border-radius: 8px;
                border: 1px solid #D2D2D7; font-size: 13px;
                background: white; color: #1D1D1F;
            }
            QPushButton:hover { background: #F5F5F7; }
        """)

        self.stream_btn = QPushButton(" Start Stream")
        self.stream_btn.setIcon(make_icon(ICON_PLAY, 16, "#30D158"))
        self.stream_btn.clicked.connect(self._toggle_stream)
        self.stream_btn.setEnabled(False)
        self.stream_btn.setStyleSheet(self.connect_btn.styleSheet())

        self.reset_btn = QPushButton(" Soft Reset")
        self.reset_btn.clicked.connect(self._soft_reset)
        self.reset_btn.setEnabled(False)
        self.reset_btn.setStyleSheet(self.connect_btn.styleSheet())

        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.stream_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _create_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: white; border-radius: 12px;
                border: 1px solid #D2D2D7;
            }}
        """)
        card.setMinimumSize(140, 100)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #6E6E73; font-size: 11px;")

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 700;")
        val_lbl.setObjectName("value")

        cl.addWidget(title_lbl)
        cl.addWidget(val_lbl)
        cl.addStretch()

        return card

    def _update_status(self, status: Dict):
        temp = status.get('temperature', 0)
        streaming = status.get('streaming', False)
        pll = status.get('pll_locked', False)
        frames = status.get('frame_count', 0)

        # Update cards
        self.status_cards['temperature'].findChild(QLabel, "value").setText(f"{temp}°C")
        self.status_cards['streaming'].findChild(QLabel, "value").setText(
            "Active" if streaming else "Stopped")
        self.status_cards['pll'].findChild(QLabel, "value").setText(
            "Locked" if pll else "Unlocked")
        self.status_cards['frames'].findChild(QLabel, "value").setText(str(frames))

        # Update info
        self.gain_label.setText(f"{status.get('gain', 0)} (0x{status.get('gain', 0):04x})")
        self.dgain_label.setText(f"{status.get('digital_gain', 0)} (0x{status.get('digital_gain', 0):04x})")
        self.exposure_label.setText(str(status.get('exposure', 0)))

    def _toggle_connect(self):
        if self.client.connected:
            self.client.disconnect()
            self.connect_btn.setText(" Connect")
            self.stream_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
        else:
            if self.client.connect():
                self.connect_btn.setText(" Disconnect")
                self.stream_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.client.start_status_stream()

    def _toggle_stream(self):
        if self.client.connected:
            st = self.client.get_status()
            if st and st.get('streaming'):
                self.client.stop_stream()
                self.stream_btn.setText(" Start Stream")
                self.stream_btn.setIcon(make_icon(ICON_PLAY, 16, "#30D158"))
            else:
                self.client.start_stream()
                self.stream_btn.setText(" Stop Stream")
                self.stream_btn.setIcon(make_icon(ICON_STOP, 16, "#FF3B30"))

    def _soft_reset(self):
        if self.client.connected:
            self.client.soft_reset()


# ---------------------------------------------------------------------------
# Controls Page
# ---------------------------------------------------------------------------

class ControlsPage(QWidget):
    """Gain, exposure, HDR controls."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Sensor Controls")
        header.setStyleSheet("font-size: 22px; font-weight: 600; color: #1D1D1F;")
        layout.addWidget(header)

        # Gain control
        gain_group = QGroupBox("Gain Control")
        gain_group.setStyleSheet("""
            QGroupBox { font-size: 13px; font-weight: 600; color: #1D1D1F;
                border: 1px solid #D2D2D7; border-radius: 8px;
                margin-top: 12px; padding: 16px 12px 12px 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)
        gain_layout = QFormLayout(gain_group)

        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 960)
        self.gain_slider.setValue(0)
        self.gain_slider.valueChanged.connect(self._on_gain_changed)

        self.gain_spin = QSpinBox()
        self.gain_spin.setRange(0, 960)
        self.gain_spin.valueChanged.connect(self.gain_slider.setValue)

        gain_layout.addRow("Analog Gain:", self.gain_slider)
        gain_layout.addRow("Value:", self.gain_spin)

        self.dgain_slider = QSlider(Qt.Horizontal)
        self.dgain_slider.setRange(0x100, 0xFFFF)
        self.dgain_slider.setValue(0x100)
        self.dgain_slider.valueChanged.connect(self._on_dgain_changed)

        self.dgain_spin = QSpinBox()
        self.dgain_spin.setRange(0x100, 0xFFFF)
        self.dgain_spin.setValue(0x100)
        self.dgain_spin.valueChanged.connect(self.dgain_slider.setValue)

        gain_layout.addRow("Digital Gain:", self.dgain_slider)
        gain_layout.addRow("Value:", self.dgain_spin)

        apply_gain = QPushButton("Apply Gain")
        apply_gain.clicked.connect(self._apply_gain)
        apply_gain.setStyleSheet("""
            QPushButton { padding: 8px 16px; border-radius: 8px;
                border: 1px solid #007AFF; background: #007AFF;
                color: white; font-size: 13px; }
            QPushButton:hover { background: #0066CC; }
        """)
        gain_layout.addRow(apply_gain)

        layout.addWidget(gain_group)

        # Exposure control
        exp_group = QGroupBox("Exposure Control")
        exp_group.setStyleSheet(gain_group.styleSheet())
        exp_layout = QFormLayout(exp_group)

        self.exp_slider = QSlider(Qt.Horizontal)
        self.exp_slider.setRange(8, 0xFFFF)
        self.exp_slider.setValue(0x640)
        self.exp_slider.valueChanged.connect(
            lambda v: self.exp_spin.setValue(v))

        self.exp_spin = QSpinBox()
        self.exp_spin.setRange(8, 0xFFFF)
        self.exp_spin.setValue(0x640)
        self.exp_spin.valueChanged.connect(self.exp_slider.setValue)

        exp_layout.addRow("Exposure:", self.exp_slider)
        exp_layout.addRow("Value:", self.exp_spin)

        apply_exp = QPushButton("Apply Exposure")
        apply_exp.clicked.connect(self._apply_exposure)
        apply_exp.setStyleSheet(apply_gain.styleSheet())
        exp_layout.addRow(apply_exp)

        layout.addWidget(exp_group)

        # HDR control
        hdr_group = QGroupBox("HDR Mode")
        hdr_group.setStyleSheet(gain_group.styleSheet())
        hdr_layout = QFormLayout(hdr_group)

        self.hdr_combo = QComboBox()
        self.hdr_combo.addItems(["Off", "On"])
        hdr_layout.addRow("HDR:", self.hdr_combo)

        apply_hdr = QPushButton("Apply HDR")
        apply_hdr.clicked.connect(self._apply_hdr)
        apply_hdr.setStyleSheet(apply_gain.styleSheet())
        hdr_layout.addRow(apply_hdr)

        layout.addWidget(hdr_group)
        layout.addStretch()

    def _on_gain_changed(self, v):
        self.gain_spin.setValue(v)

    def _on_dgain_changed(self, v):
        self.dgain_spin.setValue(v)

    def _apply_gain(self):
        if self.client.connected:
            self.client.set_gain(self.gain_slider.value(), self.dgain_slider.value())

    def _apply_exposure(self):
        if self.client.connected:
            self.client.set_exposure(self.exp_slider.value())

    def _apply_hdr(self):
        if self.client.connected:
            self.client.set_hdr(self.hdr_combo.currentIndex())


# ---------------------------------------------------------------------------
# Capture Page
# ---------------------------------------------------------------------------

class CapturePage(QWidget):
    """Frame capture and save."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Frame Capture")
        header.setStyleSheet("font-size: 22px; font-weight: 600; color: #1D1D1F;")
        layout.addWidget(header)

        # Capture controls
        cap_group = QGroupBox("Capture Settings")
        cap_group.setStyleSheet("""
            QGroupBox { font-size: 13px; font-weight: 600; color: #1D1D1F;
                border: 1px solid #D2D2D7; border-radius: 8px;
                margin-top: 12px; padding: 16px 12px 12px 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)
        cap_layout = QFormLayout(cap_group)

        self.cap_count = QSpinBox()
        self.cap_count.setRange(1, 100)
        self.cap_count.setValue(1)
        cap_layout.addRow("Frames:", self.cap_count)

        self.cap_format = QComboBox()
        self.cap_format.addItems(["RAW10", "PGM"])
        cap_layout.addRow("Format:", self.cap_format)

        btn_layout = QHBoxLayout()

        self.capture_btn = QPushButton(" Capture")
        self.capture_btn.setIcon(make_icon(ICON_CAPTURE, 20, "white"))
        self.capture_btn.clicked.connect(self._capture)
        self.capture_btn.setStyleSheet("""
            QPushButton { padding: 10px 24px; border-radius: 8px;
                background: #007AFF; color: white; font-size: 14px;
                font-weight: 500; }
            QPushButton:hover { background: #0066CC; }
        """)

        self.save_btn = QPushButton(" Save...")
        self.save_btn.clicked.connect(self._save)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton { padding: 10px 24px; border-radius: 8px;
                border: 1px solid #D2D2D7; background: white;
                color: #1D1D1F; font-size: 14px; }
            QPushButton:hover { background: #F5F5F7; }
        """)

        btn_layout.addWidget(self.capture_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()

        cap_layout.addRow(btn_layout)

        layout.addWidget(cap_group)

        # Frame info
        self.frame_info = QTextEdit()
        self.frame_info.setReadOnly(True)
        self.frame_info.setMaximumHeight(120)
        self.frame_info.setStyleSheet("""
            QTextEdit { border: 1px solid #D2D2D7; border-radius: 8px;
                padding: 8px; font-size: 12px; color: #6E6E73; }
        """)
        self.frame_info.setText("No frames captured yet")
        layout.addWidget(self.frame_info)

        layout.addStretch()

        self._last_frame = None

    def _capture(self):
        if not self.client.connected:
            return
        count = self.cap_count.value()
        frames = []
        for i in range(count):
            frame = self.client.capture_frame()
            if frame:
                frames.append(frame)
                self._last_frame = frame

        if frames:
            self.frame_info.setText(
                f"Captured {len(frames)} frame(s)\n"
                f"Size: {frames[0]['width']}x{frames[0]['height']}\n"
                f"Data: {len(frames[0].get('data', b''))} bytes\n"
                f"Gain: {frames[0].get('gain', 0)}, "
                f"Exposure: {frames[0].get('exposure', 0)}"
            )
            self.save_btn.setEnabled(True)

    def _save(self):
        if not self._last_frame:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Frame", "capture.raw", "Raw (*.raw);;All Files (*)")
        if path:
            data = self._last_frame.get('data', b'')
            with open(path, 'wb') as f:
                f.write(data)
            self.frame_info.append(f"\nSaved to: {path}")


# ---------------------------------------------------------------------------
# Test Pattern Page
# ---------------------------------------------------------------------------

class TestPatternPage(QWidget):
    """Test pattern controls."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Test Patterns")
        header.setStyleSheet("font-size: 22px; font-weight: 600; color: #1D1D1F;")
        layout.addWidget(header)

        desc = QLabel("Select a test pattern to verify sensor output.")
        desc.setStyleSheet("color: #6E6E73; font-size: 13px;")
        layout.addWidget(desc)

        # Pattern grid
        patterns = [
            ("Disabled", ICON_GRID, 0),
            ("Color Bars", ICON_PALETTE, 1),
            ("Solid Color", ICON_PALETTE, 2),
            ("Grey Bars", ICON_GRID, 3),
            ("PN9", ICON_GRID, 4),
        ]

        grid = QGridLayout()
        grid.setSpacing(8)

        self.pattern_btns = []
        for i, (name, icon, val) in enumerate(patterns):
            btn = QPushButton(f"  {name}")
            btn.setIcon(make_icon(icon, 24, "#007AFF"))
            btn.setCheckable(True)
            btn.setFixedSize(160, 60)
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #D2D2D7; border-radius: 8px;
                    background: white; font-size: 12px; color: #1D1D1F;
                    text-align: left; padding: 8px;
                }
                QPushButton:hover { background: #F5F5F7; }
                QPushButton:checked {
                    border: 2px solid #007AFF;
                    background: #E8F0FE;
                }
            """)
            btn.clicked.connect(lambda checked, v=val: self._select_pattern(v))
            grid.addWidget(btn, i // 3, i % 3)
            self.pattern_btns.append(btn)

        layout.addLayout(grid)

        # Color controls
        color_group = QGroupBox("Solid Color Settings")
        color_group.setStyleSheet("""
            QGroupBox { font-size: 13px; font-weight: 600; color: #1D1D1F;
                border: 1px solid #D2D2D7; border-radius: 8px;
                margin-top: 12px; padding: 16px 12px 12px 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)
        color_layout = QFormLayout(color_group)

        self.color_r = QSpinBox()
        self.color_r.setRange(0, 0xFFF)
        self.color_r.setValue(0xFFF)
        color_layout.addRow("Red:", self.color_r)

        self.color_b = QSpinBox()
        self.color_b.setRange(0, 0xFFF)
        self.color_b.setValue(0xFFF)
        color_layout.addRow("Blue:", self.color_b)

        layout.addWidget(color_group)
        layout.addStretch()

    def _select_pattern(self, val: int):
        for btn in self.pattern_btns:
            btn.setChecked(False)
        if val < len(self.pattern_btns):
            self.pattern_btns[val].setChecked(True)
        if self.client.connected:
            self.client.set_test_pattern(val)


# ---------------------------------------------------------------------------
# Register Page
# ---------------------------------------------------------------------------

class RegisterPage(QWidget):
    """Raw register read/write."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Register Access")
        header.setStyleSheet("font-size: 22px; font-weight: 600; color: #1D1D1F;")
        layout.addWidget(header)

        desc = QLabel("Read and write sensor registers directly (requires root on server).")
        desc.setStyleSheet("color: #6E6E73; font-size: 13px;")
        layout.addWidget(desc)

        # Known registers
        known_group = QGroupBox("Known Registers")
        known_group.setStyleSheet("""
            QGroupBox { font-size: 13px; font-weight: 600; color: #1D1D1F;
                border: 1px solid #D2D2D7; border-radius: 8px;
                margin-top: 12px; padding: 16px 12px 12px 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)
        known_layout = QGridLayout(known_group)

        known_regs = [
            ("CHIP_ID", 0x0016), ("MODE_SELECT", 0x0100),
            ("ORIENTATION", 0x0101), ("TEMPERATURE", 0x013A),
            ("EXPOSURE", 0x0202), ("ANALOG_GAIN", 0x0204),
            ("DIGITAL_GAIN", 0x020E), ("FRAME_LENGTH", 0x0340),
            ("LINE_LENGTH", 0x0342), ("TEST_PATTERN", 0x0600),
        ]

        for i, (name, addr) in enumerate(known_regs):
            btn = QPushButton(f"0x{addr:04X} {name}")
            btn.setStyleSheet("""
                QPushButton { border: 1px solid #D2D2D7; border-radius: 6px;
                    padding: 6px 12px; font-size: 11px; color: #1D1D1F;
                    background: white; text-align: left; }
                QPushButton:hover { background: #F5F5F7; }
            """)
            btn.clicked.connect(lambda checked, a=addr: self._read_reg(a))
            known_layout.addWidget(btn, i // 2, i % 2)

        layout.addWidget(known_group)

        # Custom register access
        custom_group = QGroupBox("Custom Access")
        custom_group.setStyleSheet(known_group.styleSheet())
        custom_layout = QFormLayout(custom_group)

        reg_addr_layout = QHBoxLayout()
        self.reg_addr = QLineEdit("0x0000")
        self.reg_addr.setStyleSheet("""
            QLineEdit { border: 1px solid #D2D2D7; border-radius: 6px;
                padding: 6px 8px; font-size: 13px; }
        """)
        reg_addr_layout.addWidget(self.reg_addr)

        self.reg_val = QLineEdit("0x0000")
        self.reg_val.setStyleSheet(self.reg_addr.styleSheet())
        reg_addr_layout.addWidget(self.reg_val)

        custom_layout.addRow("Register:", reg_addr_layout)

        btn_layout = QHBoxLayout()
        read_btn = QPushButton("Read")
        read_btn.clicked.connect(self._read_custom)
        read_btn.setStyleSheet("""
            QPushButton { padding: 8px 16px; border-radius: 8px;
                border: 1px solid #007AFF; background: #007AFF;
                color: white; font-size: 13px; }
            QPushButton:hover { background: #0066CC; }
        """)

        write_btn = QPushButton("Write")
        write_btn.clicked.connect(self._write_custom)
        write_btn.setStyleSheet("""
            QPushButton { padding: 8px 16px; border-radius: 8px;
                border: 1px solid #FF9F0A; background: #FF9F0A;
                color: white; font-size: 13px; }
            QPushButton:hover { background: #E68A00; }
        """)

        btn_layout.addWidget(read_btn)
        btn_layout.addWidget(write_btn)
        btn_layout.addStretch()
        custom_layout.addRow(btn_layout)

        layout.addWidget(custom_group)

        # Results
        self.reg_result = QTextEdit()
        self.reg_result.setReadOnly(True)
        self.reg_result.setMaximumHeight(150)
        self.reg_result.setStyleSheet("""
            QTextEdit { border: 1px solid #D2D2D7; border-radius: 8px;
                padding: 8px; font-size: 12px; font-family: monospace;
                color: #1D1D1F; background: #F5F5F7; }
        """)
        layout.addWidget(self.reg_result)

        layout.addStretch()

    def _read_reg(self, addr: int):
        if not self.client.connected:
            return
        val = self.client.read_register(addr)
        if val is not None:
            self.reg_result.append(f"REG[0x{addr:04X}] = 0x{val:04X} ({val})")

    def _read_custom(self):
        try:
            addr = int(self.reg_addr.text(), 16)
            self._read_reg(addr)
        except ValueError:
            self.reg_result.append("Invalid address")

    def _write_custom(self):
        try:
            addr = int(self.reg_addr.text(), 16)
            val = int(self.reg_val.text(), 16)
            if self.client.write_register(addr, val):
                self.reg_result.append(f"REG[0x{addr:04X}] <- 0x{val:04X}")
        except ValueError:
            self.reg_result.append("Invalid value")


# ---------------------------------------------------------------------------
# Info Page
# ---------------------------------------------------------------------------

class InfoPage(QWidget):
    """Sensor information and about."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("About IMX708")
        header.setStyleSheet("font-size: 22px; font-weight: 600; color: #1D1D1F;")
        layout.addWidget(header)

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setStyleSheet("""
            QTextEdit { border: 1px solid #D2D2D7; border-radius: 8px;
                padding: 12px; font-size: 13px; color: #1D1D1F;
                background: white; }
        """)
        info_text.setHtml("""
        <h2>Sony IMX708</h2>
        <p>Back-illuminated and stacked CMOS 12-megapixel image sensor.</p>
        <ul>
        <li><b>Resolution:</b> 4608 × 2592 (11.9 MP)</li>
        <li><b>Pixel Size:</b> 1.4 μm × 1.4 μm</li>
        <li><b>Optical Format:</b> 1/2.43"</li>
        <li><b>Output:</b> RAW10, MIPI CSI-2 (2/4 lanes)</li>
        <li><b>HDR:</b> Up to 3 MP output</li>
        <li><b>Autofocus:</b> Phase Detection (PDAF)</li>
        <li><b>Features:</b> QBC Re-mosaic, 2D DPC, LSC</li>
        </ul>
        <h3>Driver Features</h3>
        <ul>
        <li>V4L2 sub-device with 24 controls</li>
        <li>9 sensor modes (up to 240fps)</li>
        <li>gRPC remote control API</li>
        <li>Cross-platform GUI client</li>
        <li>Frame capture and recording</li>
        <li>Configuration profiles</li>
        <li>Fault injection and debugfs</li>
        </ul>
        <p><i>Version 0.1.0 — GPL-2.0-only</i></p>
        """)
        layout.addWidget(info_text)

        # Modes table
        self.modes_table = QTextEdit()
        self.modes_table.setReadOnly(True)
        self.modes_table.setMaximumHeight(200)
        self.modes_table.setStyleSheet("""
            QTextEdit { border: 1px solid #D2D2D7; border-radius: 8px;
                padding: 8px; font-size: 12px; font-family: monospace;
                color: #1D1D1F; background: #F5F5F7; }
        """)
        layout.addWidget(self.modes_table)

        refresh_btn = QPushButton("Refresh Modes")
        refresh_btn.clicked.connect(self._refresh_modes)
        refresh_btn.setStyleSheet("""
            QPushButton { padding: 8px 16px; border-radius: 8px;
                border: 1px solid #007AFF; background: #007AFF;
                color: white; font-size: 13px; }
            QPushButton:hover { background: #0066CC; }
        """)
        layout.addWidget(refresh_btn)

        layout.addStretch()

    def _refresh_modes(self):
        if not self.client.connected:
            return
        modes = self.client.get_modes()
        text = "Available Modes:\n" + "=" * 50 + "\n"
        for m in modes:
            text += f"  [{m['index']}] {m['width']}x{m['height']} @ {m['fps']}fps\n"
            text += f"       Code: 0x{m['code']:x}, {m['bit_depth']}-bit\n"
            text += f"       Pixel Rate: {m['pixel_rate']/1e6:.1f} MHz\n"
        self.modes_table.setText(text)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Main application window with macOS-like design."""

    def __init__(self, server_addr: str = "localhost:50051"):
        super().__init__()
        self.server_addr = server_addr
        self.client = GrpcClient(server_addr)
        self.setup_ui()
        self.setup_menu()

    def setup_ui(self):
        self.setWindowTitle("IMX708 Camera Controller")
        self.setMinimumSize(900, 650)
        self.setStyleSheet("""
            QMainWindow { background: #F5F5F7; }
        """)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.page_changed.connect(self._switch_page)
        self.sidebar.set_connected(False)
        main_layout.addWidget(self.sidebar)

        # Content area
        self.stack = QStackedWidget()

        self.pages = [
            DashboardPage(self.client),
            ControlsPage(self.client),
            CapturePage(self.client),
            TestPatternPage(self.client),
            RegisterPage(self.client),
            InfoPage(self.client),
        ]

        for page in self.pages:
            self.stack.addWidget(page)

        main_layout.addWidget(self.stack, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar { background: #F5F5F7; border-top: 1px solid #D2D2D7;
                font-size: 11px; color: #6E6E73; padding: 2px 8px; }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Disconnected — Click Connect on Dashboard")

        # Connect client signals
        self.client.connection_changed.connect(self._on_connection_changed)
        self.client.log_message.connect(self._on_log)

    def setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { background: #F5F5F7; border-bottom: 1px solid #D2D2D7;
                font-size: 12px; padding: 2px; }
            QMenuBar::item:selected { background: #007AFF; color: white; }
            QMenu { background: white; border: 1px solid #D2D2D7; }
            QMenu::item:selected { background: #007AFF; color: white; }
        """)

        file_menu = menubar.addMenu("File")
        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(lambda: self.pages[0]._toggle_connect())
        file_menu.addAction(connect_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = menubar.addMenu("View")
        for i, name in enumerate(["Dashboard", "Controls", "Capture",
                                    "Test Patterns", "Registers", "Info"]):
            action = QAction(name, self)
            action.triggered.connect(lambda checked, idx=i: self._switch_page(idx))
            view_menu.addAction(action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About IMX708", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _switch_page(self, index: int):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)

    def _on_connection_changed(self, connected: bool):
        self.sidebar.set_connected(connected)
        if connected:
            self.status_bar.showMessage(f"Connected to {self.server_addr}")
        else:
            self.status_bar.showMessage("Disconnected")

    def _on_log(self, msg: str):
        self.status_bar.showMessage(msg, 5000)

    def _show_about(self):
        QMessageBox.about(self, "About IMX708",
            "IMX708 Camera Controller v0.1.0\n\n"
            "Cross-platform GUI for Sony IMX708 sensor\n"
            "Raspberry Pi Camera Module 3\n\n"
            "GPL-2.0-only")

    def closeEvent(self, event):
        self.client.disconnect()
        event.accept()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="IMX708 Camera GUI Client")
    parser.add_argument("--server", default="localhost:50051",
                        help="gRPC server address (default: localhost:50051)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # macOS-like font
    font = QFont()
    font.setFamily("SF Pro Display" if sys.platform == "darwin" else "Segoe UI")
    font.setPointSize(13)
    app.setFont(font)

    window = MainWindow(args.server)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
