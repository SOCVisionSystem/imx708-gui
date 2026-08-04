# SPDX-License-Identifier: GPL-2.0-only
"""
imx708_client - Elegant macOS-inspired PySide6 GUI for IMX708 camera sensor

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>

A beautiful, native-feeling macOS-inspired desktop application for controlling
the Sony IMX708 12MP camera sensor over gRPC. Features a polished sidebar
with SF Symbols-style SVG icons, real-time telemetry cards, and full sensor
control — designed to look and feel like a first-class macOS application.

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
        QPropertyAnimation, QEasingCurve, QRect, QPoint, QMargins,
        QMetaObject, Q_ARG, Slot
    )
    from PySide6.QtGui import (
        QAction, QColor, QFont, QIcon, QPainter, QPixmap,
        QPalette, QBrush, QLinearGradient, QFontDatabase,
        QCursor, QPen, QPainterPath, QFontMetrics, QKeySequence
    )
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QSlider, QComboBox, QGroupBox, QGridLayout,
        QFormLayout, QTabWidget, QTextEdit, QStatusBar, QMenuBar,
        QMenu, QFileDialog, QMessageBox, QCheckBox, QSpinBox,
        QDoubleSpinBox, QScrollArea, QFrame, QSplitter, QListWidget,
        QListWidgetItem, QStackedWidget, QToolButton, QSizePolicy,
        QProgressBar, QLineEdit, QPlainTextEdit, QGraphicsDropShadowEffect,
        QDialog
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
    # For PyInstaller bundled executable
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    sys.path.insert(0, os.path.join(base_path, 'imx708_proto'))
    sys.path.insert(0, os.path.join(base_path, 'build'))
    sys.path.insert(0, base_path)
    
    import imx708_pb2
    import imx708_pb2_grpc
    HAVE_PROTO = True
except ImportError as e:
    HAVE_PROTO = False
    print(f"Proto modules not found: {e}. Generate with: ./build.sh")


# =========================================================================
# macOS Design Tokens
# =========================================================================

# macOS Big Sur+ color palette
MACOS_BG        = "#F5F5F7"       # Window background
MACOS_SIDEBAR   = "#F2F2F7"       # Sidebar background
MACOS_CARD      = "#FFFFFF"       # Card background
MACOS_BORDER    = "#D2D2D7"       # Subtle border
MACOS_SEPARATOR = "#E5E5EA"       # Separator line
MACOS_TEXT      = "#1D1D1F"       # Primary text
MACOS_SECONDARY = "#6E6E73"       # Secondary text
MACOS_TERTIARY  = "#AEAEB2"       # Tertiary text
MACOS_BLUE      = "#007AFF"       # Accent blue
MACOS_GREEN     = "#30D158"       # Success green
MACOS_RED       = "#FF3B30"       # Error red
MACOS_ORANGE    = "#FF9F0A"       # Warning orange
MACOS_PURPLE    = "#AF52DE"       # Purple accent
MACOS_GRAY      = "#8E8E93"       # Gray

# Card shadow
CARD_SHADOW = """
    background: white; border: 1px solid %s; border-radius: 12px;
""" % MACOS_BORDER

# =========================================================================
# SF Symbols-style SVG Icons (elegant, thin, macOS-style)
# =========================================================================

ICON_CAMERA = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
  <circle cx="12" cy="13" r="4"/>
</svg>"""

ICON_SLIDERS = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <line x1="4" y1="21" x2="4" y2="14"/>
  <line x1="4" y1="10" x2="4" y2="3"/>
  <line x1="12" y1="21" x2="12" y2="12"/>
  <line x1="12" y1="8" x2="12" y2="3"/>
  <line x1="20" y1="21" x2="20" y2="16"/>
  <line x1="20" y1="12" x2="20" y2="3"/>
  <line x1="2" y1="14" x2="6" y2="14"/>
  <line x1="10" y1="8" x2="14" y2="8"/>
  <line x1="18" y1="16" x2="22" y2="16"/>
</svg>"""

ICON_CAPTURE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="6" fill="currentColor" opacity="0.3"/>
  <circle cx="12" cy="12" r="3"/>
</svg>"""

ICON_PALETTE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="13.5" cy="6.5" r="1.5" fill="currentColor" opacity="0.4"/>
  <circle cx="17.5" cy="10.5" r="1.5" fill="currentColor" opacity="0.4"/>
  <circle cx="8.5" cy="7.5" r="1.5" fill="currentColor" opacity="0.4"/>
  <circle cx="6.5" cy="12.5" r="1.5" fill="currentColor" opacity="0.4"/>
  <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-1 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-5.52-4.5-10-10-10z"/>
</svg>"""

ICON_GRID = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="3" width="7" height="7" rx="1"/>
  <rect x="14" y="3" width="7" height="7" rx="1"/>
  <rect x="14" y="14" width="7" height="7" rx="1"/>
  <rect x="3" y="14" width="7" height="7" rx="1"/>
</svg>"""

ICON_TERMINAL = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="4 17 10 11 4 5"/>
  <line x1="12" y1="19" x2="20" y2="19"/>
</svg>"""

ICON_INFO = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <line x1="12" y1="16" x2="12" y2="12"/>
  <line x1="12" y1="8" x2="12.01" y2="8"/>
</svg>"""

ICON_WIFI = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
  <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
  <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
  <circle cx="12" cy="20" r="1.5" fill="currentColor"/>
</svg>"""

ICON_PLAY = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
  <polygon points="6 3 20 12 6 21 6 3"/>
</svg>"""

ICON_STOP = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
  <rect x="5" y="5" width="14" height="14" rx="3"/>
</svg>"""

ICON_RESET = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="23 4 23 10 17 10"/>
  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
</svg>"""

ICON_CHECK = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="20 6 9 17 4 12"/>
</svg>"""

ICON_DOWNLOAD = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
  <polyline points="7 10 12 15 17 10"/>
  <line x1="12" y1="15" x2="12" y2="3"/>
</svg>"""

ICON_REFRESH = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="23 4 23 10 17 10"/>
  <polyline points="1 20 1 14 7 14"/>
  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
</svg>"""

ICON_CONNECT = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
  <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
  <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
  <circle cx="12" cy="20" r="1.5" fill="currentColor"/>
</svg>"""


def make_icon(svg: str, size: int = 22, color: str = "#555") -> QIcon:
    """Create a crisp QIcon from SVG data with proper rendering."""
    colored = svg.replace('currentColor', color)
    # Render at 2x for retina clarity
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.setRenderHint(QPainter.Antialiasing)
    from PySide6.QtSvg import QSvgRenderer
    renderer = QSvgRenderer(QByteArray(colored.encode()))
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))


# =========================================================================
# Custom macOS-style Slider
# =========================================================================

class MacSlider(QWidget):
    """A beautiful macOS-style slider with gradient fill and rounded knob."""

    valueChanged = Signal(int)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 100
        self._value = 0
        self._orientation = orientation
        self._pressed = False
        self._accent_color = QColor(MACOS_BLUE)
        self._track_color = QColor("#E5E5EA")
        self._knob_color = QColor("#FFFFFF")
        self._knob_shadow = QColor(0, 0, 0, 30)

        if orientation == Qt.Horizontal:
            self.setFixedHeight(28)
            self.setMinimumWidth(120)
        else:
            self.setFixedWidth(28)
            self.setMinimumHeight(120)

        self.setCursor(QCursor(Qt.PointingHandCursor))

    def setRange(self, minimum: int, maximum: int):
        self._minimum = minimum
        self._maximum = maximum
        self.update()

    def setValue(self, value: int):
        value = max(self._minimum, min(self._maximum, value))
        if value != self._value:
            self._value = value
            self.valueChanged.emit(value)
            self.update()

    def value(self) -> int:
        return self._value

    def setAccentColor(self, color: str):
        self._accent_color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        track_h = 4
        knob_r = 8

        if self._orientation == Qt.Horizontal:
            # Track
            track_y = (h - track_h) // 2
            track_rect = QRectF(4, track_y, w - 8, track_h)

            # Background track
            path = QPainterPath()
            path.addRoundedRect(track_rect, track_h / 2, track_h / 2)
            painter.fillPath(path, self._track_color)

            # Filled track
            ratio = (self._value - self._minimum) / max(1, self._maximum - self._minimum)
            fill_w = max(0, track_rect.width() * ratio)
            if fill_w > 0:
                fill_rect = QRectF(track_rect.x(), track_rect.y(), fill_w, track_rect.height())
                fill_path = QPainterPath()
                fill_path.addRoundedRect(fill_rect, track_h / 2, track_h / 2)
                painter.fillPath(fill_path, self._accent_color)

            # Knob shadow
            knob_x = track_rect.x() + fill_w - knob_r
            knob_x = max(knob_r, min(w - knob_r - 4, knob_x))
            knob_center = QPointF(knob_x, h / 2)

            shadow_path = QPainterPath()
            shadow_path.addEllipse(knob_center, knob_r + 1, knob_r + 1)
            painter.fillPath(shadow_path, self._knob_shadow)

            # Knob
            knob_path = QPainterPath()
            knob_path.addEllipse(knob_center, knob_r, knob_r)
            painter.fillPath(knob_path, self._knob_color)
            painter.setPen(QPen(QColor("#C7C7CC"), 0.5))
            painter.drawPath(knob_path)

        else:
            # Vertical track
            track_x = (w - track_h) // 2
            track_rect = QRectF(track_x, 4, track_h, h - 8)

            path = QPainterPath()
            path.addRoundedRect(track_rect, track_h / 2, track_h / 2)
            painter.fillPath(path, self._track_color)

            ratio = (self._value - self._minimum) / max(1, self._maximum - self._minimum)
            fill_h = max(0, track_rect.height() * ratio)
            if fill_h > 0:
                fill_rect = QRectF(track_rect.x(), track_rect.bottom() - fill_h,
                                   track_rect.width(), fill_h)
                fill_path = QPainterPath()
                fill_path.addRoundedRect(fill_rect, track_h / 2, track_h / 2)
                painter.fillPath(fill_path, self._accent_color)

            knob_y = track_rect.bottom() - fill_h
            knob_center = QPointF(w / 2, knob_y)

            shadow_path = QPainterPath()
            shadow_path.addEllipse(knob_center, knob_r + 1, knob_r + 1)
            painter.fillPath(shadow_path, self._knob_shadow)

            knob_path = QPainterPath()
            knob_path.addEllipse(knob_center, knob_r, knob_r)
            painter.fillPath(knob_path, self._knob_color)
            painter.setPen(QPen(QColor("#C7C7CC"), 0.5))
            painter.drawPath(knob_path)

        painter.end()

    def _pos_to_value(self, pos):
        w = self.width()
        h = self.height()
        if self._orientation == Qt.Horizontal:
            track_x = 4
            track_w = w - 8
            ratio = (pos.x() - track_x) / max(1, track_w)
        else:
            track_y = 4
            track_h = h - 8
            ratio = 1.0 - (pos.y() - track_y) / max(1, track_h)
        ratio = max(0.0, min(1.0, ratio))
        return int(self._minimum + ratio * (self._maximum - self._minimum))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self.setValue(self._pos_to_value(event.position()))

    def mouseMoveEvent(self, event):
        if self._pressed:
            self.setValue(self._pos_to_value(event.position()))

    def mouseReleaseEvent(self, event):
        self._pressed = False


# =========================================================================
# macOS-style Sidebar
# =========================================================================

class SidebarButton(QPushButton):
    """Elegant macOS-style sidebar button with pill shape."""

    def __init__(self, text: str, icon_svg: str, parent=None):
        super().__init__(parent)
        self._icon_svg = icon_svg
        self._icon_color = MACOS_GRAY
        self.setIcon(make_icon(icon_svg, 20, self._icon_color))
        self.setText(text)
        self.setFixedHeight(34)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setCheckable(True)
        self._update_style(False)

    def _update_style(self, checked: bool):
        if checked:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 5px 14px; border: none;
                    border-radius: 8px; font-size: 13px; font-weight: 500;
                    color: white; background: {MACOS_BLUE};
                }}
                QPushButton:hover {{
                    background: #0066CC;
                }}
            """)
            self.setIcon(make_icon(self._icon_svg, 20, "#FFFFFF"))
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 5px 14px; border: none;
                    border-radius: 8px; font-size: 13px; font-weight: 400;
                    color: {MACOS_TEXT}; background: transparent;
                }}
                QPushButton:hover {{
                    background: {MACOS_SEPARATOR};
                }}
            """)
            self.setIcon(make_icon(self._icon_svg, 20, MACOS_GRAY))

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style(checked)


class SidebarWidget(QWidget):
    """Elegant macOS-style sidebar with SF Symbols icons."""

    page_changed = Signal(int)

    NAV_ITEMS = [
        ("Dashboard", ICON_CAMERA, "Real-time sensor telemetry and controls"),
        ("Controls",   ICON_SLIDERS, "Gain, exposure, and HDR settings"),
        ("Capture",    ICON_CAPTURE, "Frame capture and save to file"),
        ("Image",      ICON_PALETTE, "Brightness, contrast, white balance, flip"),
        ("Patterns",   ICON_GRID, "Test pattern generator"),
        ("Registers",  ICON_TERMINAL, "Direct register read/write (debug)"),
        ("Info",       ICON_INFO, "Sensor specifications and about"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(f"""
            SidebarWidget {{
                background: {MACOS_SIDEBAR};
                border-right: 1px solid {MACOS_BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(2)

        # App icon + title area
        title_frame = QWidget()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(8, 0, 8, 12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(make_icon(ICON_CAMERA, 28, MACOS_BLUE).pixmap(28, 28))
        title_layout.addWidget(icon_lbl)

        title_text = QLabel("IMX708")
        title_text.setStyleSheet(f"""
            font-size: 17px; font-weight: 700; color: {MACOS_TEXT};
            letter-spacing: -0.5px;
        """)
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        layout.addWidget(title_frame)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {MACOS_SEPARATOR}; max-height: 1px;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(8)

        # Navigation buttons
        self.buttons = []
        for text, icon_svg, tooltip in self.NAV_ITEMS:
            btn = SidebarButton(text, icon_svg)
            btn.setToolTip(tooltip)
            btn.clicked.connect(
                lambda checked, b=btn, i=len(self.buttons): self._on_click(b, i))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

        # Connection status indicator
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background: white; border-radius: 8px;
                border: 1px solid {MACOS_BORDER}; padding: 8px;
            }}
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 8, 10, 8)
        status_layout.setSpacing(8)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {MACOS_RED}; font-size: 12px;")
        status_layout.addWidget(self.status_dot)

        self.status_text = QLabel("Disconnected")
        self.status_text.setStyleSheet(f"""
            font-size: 12px; font-weight: 500; color: {MACOS_SECONDARY};
        """)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        layout.addWidget(status_frame)

        # Select first item
        if self.buttons:
            self.buttons[0].setChecked(True)

    def _on_click(self, btn: SidebarButton, index: int):
        for b in self.buttons:
            b.setChecked(b == btn)
        self.page_changed.emit(index)

    def set_connected(self, connected: bool):
        if connected:
            self.status_dot.setStyleSheet(f"color: {MACOS_GREEN}; font-size: 12px;")
            self.status_text.setText("Connected")
            self.status_text.setStyleSheet(f"""
                font-size: 12px; font-weight: 500; color: {MACOS_GREEN};
            """)
        else:
            self.status_dot.setStyleSheet(f"color: {MACOS_RED}; font-size: 12px;")
            self.status_text.setText("Disconnected")
            self.status_text.setStyleSheet(f"""
                font-size: 12px; font-weight: 500; color: {MACOS_SECONDARY};
            """)


# =========================================================================
# Shared UI Components
# =========================================================================

def make_card(title: str, value: str, color: str, icon_svg: str = None) -> QFrame:
    """Create a beautiful macOS-style info card."""
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background: white; border-radius: 12px;
            border: 1px solid {MACOS_BORDER};
        }}
    """)
    card.setMinimumSize(130, 110)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(4)

    if icon_svg:
        icon_lbl = QLabel()
        icon_lbl.setPixmap(make_icon(icon_svg, 18, color).pixmap(18, 18))
        layout.addWidget(icon_lbl)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"color: {MACOS_SECONDARY}; font-size: 12px; font-weight: 500;")
    layout.addWidget(title_lbl)

    val_lbl = QLabel(value)
    val_lbl.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 700;")
    val_lbl.setObjectName("card_value")
    layout.addWidget(val_lbl)
    layout.addStretch()

    return card


def make_group_box(title: str) -> QGroupBox:
    """Create a macOS-style group box."""
    gb = QGroupBox(title)
    gb.setStyleSheet(f"""
        QGroupBox {{
            font-size: 16px; font-weight: 600; color: {MACOS_TEXT};
            border: 1px solid {MACOS_BORDER}; border-radius: 10px;
            margin-top: 14px; padding: 18px 14px 14px 14px;
            background: white;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin; left: 14px; padding: 0 8px;
            background: white;
        }}
    """)
    return gb


def make_primary_button(text: str, icon_svg: str = None) -> QPushButton:
    """Create a macOS-style blue primary button."""
    btn = QPushButton(text)
    if icon_svg:
        btn.setIcon(make_icon(icon_svg, 16, "#FFFFFF"))
    btn.setStyleSheet(f"""
        QPushButton {{
            padding: 8px 18px; border-radius: 8px;
            border: none; background: {MACOS_BLUE};
            color: white; font-size: 13px; font-weight: 500;
            min-height: 32px;
        }}
        QPushButton:hover {{
            background: #0066CC;
        }}
        QPushButton:pressed {{
            background: #0055B3;
        }}
        QPushButton:focus {{
            outline: 2px solid #66B2FF;
            outline-offset: 2px;
        }}
        QPushButton:disabled {{
            background: #B0B0B0; color: #E0E0E0;
        }}
    """)
    return btn


def make_secondary_button(text: str, icon_svg: str = None) -> QPushButton:
    """Create a macOS-style secondary button."""
    btn = QPushButton(text)
    if icon_svg:
        btn.setIcon(make_icon(icon_svg, 16, MACOS_TEXT))
    btn.setStyleSheet(f"""
        QPushButton {{
            padding: 8px 18px; border-radius: 8px;
            border: 1px solid {MACOS_BORDER}; background: white;
            color: {MACOS_TEXT}; font-size: 13px; font-weight: 500;
            min-height: 32px;
        }}
        QPushButton:hover {{
            background: {MACOS_BG};
        }}
        QPushButton:pressed {{
            background: {MACOS_SEPARATOR};
        }}
        QPushButton:focus {{
            border-color: {MACOS_BLUE};
            outline: 2px solid #66B2FF;
        }}
        QPushButton:disabled {{
            background: {MACOS_BG}; color: {MACOS_TERTIARY};
        }}
    """)
    return btn


def make_header(text: str) -> QLabel:
    """Create a macOS-style page header."""
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        font-size: 22px; font-weight: 700; color: {MACOS_TEXT};
        letter-spacing: -0.3px;
    """)
    return lbl


def make_description(text: str) -> QLabel:
    """Create a macOS-style description label."""
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {MACOS_SECONDARY}; font-size: 13px;")
    lbl.setWordWrap(True)
    return lbl


# =========================================================================
# gRPC Client Thread
# =========================================================================

class GrpcClient(QObject):
    """gRPC client running in a background thread."""
    status_updated = Signal(dict)
    frame_received = Signal(dict)
    connection_changed = Signal(bool)
    log_message = Signal(str)

    MAX_MESSAGE_BYTES = 100 * 1024 * 1024

    CHANNEL_OPTIONS = [
        ("grpc.max_receive_message_length", MAX_MESSAGE_BYTES),
        ("grpc.max_send_message_length", MAX_MESSAGE_BYTES),
    ]

    def __init__(self, server_addr: str = "localhost:50051"):
        super().__init__()
        self.server_addr = server_addr
        self._channel = None
        self._stub = None
        self._connected = False
        self._running = False
        self._status_thread = None
        self._frame_thread = None
        self._status_call = None

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        if not HAVE_GRPC or not HAVE_PROTO:
            self.log_message.emit("gRPC or proto modules not available")
            return False
        try:
            self._channel = insecure_channel(
                self.server_addr, options=self.CHANNEL_OPTIONS)
            self._stub = imx708_pb2_grpc.Imx708ServiceStub(self._channel)
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
        self.stop_status_stream()
        if self._channel:
            self._channel.close()
            self._channel = None
        self._stub = None
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

    def soft_reset(self) -> bool:
        if not self._stub:
            return False
        try:
            resp = self._stub.SoftReset(imx708_pb2.Empty(), timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"soft_reset error: {e}")
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

    def capture_frame(self) -> Optional[Dict]:
        if not self._stub:
            return None
        try:
            req = imx708_pb2.CaptureParams(
                width=4608, height=2592, format=0, num_frames=1)
            resp = self._stub.CaptureFrame(req, timeout=30)
            return {
                'width': resp.width, 'height': resp.height,
                'stride': resp.stride, 'format': resp.format,
                'timestamp_ns': resp.timestamp_ns,
                'frame_number': resp.frame_number,
                'gain': resp.gain, 'exposure': resp.exposure,
                'data': resp.data,
            }
        except Exception as e:
            self.log_message.emit(f"capture_frame error: {e}")
            return None

    def read_register(self, addr: int) -> Optional[int]:
        if not self._stub:
            return None
        try:
            req = imx708_pb2.RegisterAccess(reg=addr)
            resp = self._stub.ReadRegister(req, timeout=5)
            return resp.val
        except Exception as e:
            self.log_message.emit(f"read_register error: {e}")
            return None

    def write_register(self, addr: int, val: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.RegisterAccess(reg=addr, val=val)
            resp = self._stub.WriteRegister(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"write_register error: {e}")
            return False

    def get_image_processing(self) -> Optional[Dict]:
        if not self._stub:
            return None
        try:
            resp = self._stub.GetImageProcessing(imx708_pb2.Empty(), timeout=5)
            return {
                'brightness': resp.brightness,
                'contrast': resp.contrast,
                'saturation': resp.saturation,
                'hue': resp.hue,
                'sharpness': resp.sharpness,
                'gamma': resp.gamma,
                'auto_wb': resp.auto_wb,
                'wb_temperature': resp.wb_temperature,
                'hflip': resp.hflip,
                'vflip': resp.vflip,
            }
        except Exception as e:
            self.log_message.emit(f"get_image_processing error: {e}")
            return None

    def set_image_processing(self, **kwargs) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.ImageProcessingConfig(**kwargs)
            resp = self._stub.SetImageProcessing(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_image_processing error: {e}")
            return False

    # ---- Streaming RPCs ----

    def start_status_stream(self):
        if not self._stub or self._running:
            return
        self._running = True
        self._status_thread = threading.Thread(target=self._status_loop, daemon=True)
        self._status_thread.start()

    def stop_status_stream(self):
        self._running = False
        if self._status_call:
            self._status_call.cancel()
        if self._status_thread and self._status_thread.is_alive():
            self._status_thread.join(timeout=2)

    def _status_loop(self):
        try:
            self._status_call = self._stub.StreamStatus(
                imx708_pb2.Empty(), timeout=86400)
            for event in self._status_call:
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
                        'width': s.width,
                        'height': s.height,
                        'fps': s.fps,
                    })
        except Exception as e:
            if self._running:
                self.log_message.emit(f"Status stream ended: {e}")
        finally:
            self._status_call = None
            self._running = False


# =========================================================================
# Dashboard Page
# =========================================================================

class DashboardPage(QWidget):
    """Elegant dashboard showing sensor status in real-time."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()
        self.client.status_updated.connect(self._update_status)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_header("Sensor Dashboard"))

        # Status cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        self.status_cards = {}
        card_data = [
            ("temperature", "Temperature", "0°C", MACOS_ORANGE, ICON_TERMINAL,
             "Current sensor temperature in degrees Celsius"),
            ("streaming", "Streaming", "Stopped", MACOS_RED, ICON_PLAY,
             "Whether the sensor is actively streaming frames"),
            ("pll", "PLL Lock", "Unlocked", MACOS_RED, ICON_WIFI,
             "Phase-Locked Loop lock status — must be locked for operation"),
            ("frames", "Frames", "0", MACOS_BLUE, ICON_CAPTURE,
             "Total frame count since stream started"),
        ]

        for key, title, value, color, icon, tooltip in card_data:
            card = make_card(title, value, color, icon)
            card.setToolTip(tooltip)
            cards_layout.addWidget(card)
            self.status_cards[key] = card

        layout.addLayout(cards_layout)

        # Current Settings card
        settings_group = make_group_box("Current Settings")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(8)
        settings_layout.setLabelAlignment(Qt.AlignRight)

        self.gain_label = QLabel("0")
        self.dgain_label = QLabel("0")
        self.exposure_label = QLabel("0")
        self.res_label = QLabel("—")
        self.fps_label = QLabel("—")

        for label, widget, tooltip in [
            ("Analog Gain", self.gain_label, "Current analog gain value (0–960)"),
            ("Digital Gain", self.dgain_label, "Current digital gain value (256–65535)"),
            ("Exposure", self.exposure_label, "Current exposure in line units"),
            ("Resolution", self.res_label, "Current sensor resolution in pixels"),
            ("Frame Rate", self.fps_label, "Current frames per second"),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {MACOS_SECONDARY}; font-size: 12px; font-weight: 500;")
            lbl.setToolTip(tooltip)
            widget.setStyleSheet(f"color: {MACOS_TEXT}; font-size: 13px; font-weight: 600;")
            settings_layout.addRow(lbl, widget)

        layout.addWidget(settings_group)

        # Top Action Bar (macOS-style)
        action_bar = QFrame()
        action_bar.setStyleSheet(f"""
            QFrame {{
                background: white; border-radius: 10px;
                border: 1px solid {MACOS_BORDER};
            }}
        """)
        action_bar.setFixedHeight(56)
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(12, 8, 12, 8)
        action_layout.setSpacing(8)

        self.connect_btn = make_primary_button("  Connect", ICON_CONNECT)
        self.connect_btn.setToolTip("Connect or disconnect from the gRPC server")
        self.connect_btn.setFixedHeight(40)
        self.connect_btn.clicked.connect(self.toggle_connect)

        self.stream_btn = make_secondary_button("  Start Stream", ICON_PLAY)
        self.stream_btn.setToolTip("Start or stop the video stream from the sensor")
        self.stream_btn.setFixedHeight(40)
        self.stream_btn.clicked.connect(self._toggle_stream)
        self.stream_btn.setEnabled(False)

        self.reset_btn = make_secondary_button("  Soft Reset", ICON_RESET)
        self.reset_btn.setToolTip("Perform a soft reset of the sensor (stops stream)")
        self.reset_btn.setFixedHeight(40)
        self.reset_btn.clicked.connect(self._soft_reset)
        self.reset_btn.setEnabled(False)

        # Loading indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)  # Indeterminate
        self.loading_bar.setFixedSize(120, 4)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none; border-radius: 2px;
                background: {MACOS_SEPARATOR};
            }}
            QProgressBar::chunk {{
                background: {MACOS_BLUE}; border-radius: 2px;
            }}
        """)
        self.loading_bar.hide()

        action_layout.addWidget(self.connect_btn)
        action_layout.addWidget(self.stream_btn)
        action_layout.addWidget(self.reset_btn)
        action_layout.addWidget(self.loading_bar)
        action_layout.addStretch()

        layout.addWidget(action_bar)
        layout.addStretch()

    def _update_status(self, status: Dict):
        temp = status.get('temperature', 0)
        streaming = status.get('streaming', False)
        pll = status.get('pll_locked', False)
        frames = status.get('frame_count', 0)

        # Update cards
        self.status_cards['temperature'].findChild(QLabel, "card_value").setText(f"{temp}°C")
        self.status_cards['streaming'].findChild(QLabel, "card_value").setText(
            "Active" if streaming else "Stopped")
        self.status_cards['pll'].findChild(QLabel, "card_value").setText(
            "Locked" if pll else "Unlocked")
        self.status_cards['frames'].findChild(QLabel, "card_value").setText(str(frames))

        # Update colors
        self.status_cards['streaming'].findChild(QLabel, "card_value").setStyleSheet(
            f"color: {MACOS_GREEN if streaming else MACOS_RED}; font-size: 26px; font-weight: 700;")
        self.status_cards['pll'].findChild(QLabel, "card_value").setStyleSheet(
            f"color: {MACOS_GREEN if pll else MACOS_RED}; font-size: 26px; font-weight: 700;")

        # Update info
        self.gain_label.setText(f"{status.get('gain', 0)}")
        self.dgain_label.setText(f"{status.get('digital_gain', 0)}")
        self.exposure_label.setText(str(status.get('exposure', 0)))
        w = status.get('width', 0)
        h = status.get('height', 0)
        self.res_label.setText(f"{w}×{h}" if w and h else "—")
        self.fps_label.setText(f"{status.get('fps', 0)} fps")

    def toggle_connect(self):
        if self.client.connected:
            self.client.disconnect()
            self.connect_btn.setText("  Connect")
            self.connect_btn.setIcon(make_icon(ICON_CONNECT, 16, "#FFFFFF"))
            self.stream_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
            self.loading_bar.hide()
        else:
            self.connect_btn.setEnabled(False)
            self.loading_bar.show()
            self.client.log_message.emit("Connecting...")
            QApplication.processEvents()

            # Run connection in background to keep UI responsive
            import threading
            def _do_connect():
                success = self.client.connect()
                QMetaObject.invokeMethod(
                    self, "_on_connect_finished", Qt.QueuedConnection,
                    Q_ARG(bool, success)
                )
            threading.Thread(target=_do_connect, daemon=True).start()

    @Slot(bool)
    def _on_connect_finished(self, success: bool):
        self.loading_bar.hide()
        self.connect_btn.setEnabled(True)
        if success:
            self.connect_btn.setText("  Disconnect")
            self.connect_btn.setIcon(make_icon(ICON_STOP, 16, "#FFFFFF"))
            self.stream_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            self.client.start_status_stream()
        else:
            self.client.log_message.emit("Connection failed")

    def _toggle_stream(self):
        if self.client.connected:
            st = self.client.get_status()
            if st and st.get('streaming'):
                self.client.stop_stream()
                self.stream_btn.setText("  Start Stream")
                self.stream_btn.setIcon(make_icon(ICON_PLAY, 16, MACOS_TEXT))
            else:
                self.client.start_stream()
                self.stream_btn.setText("  Stop Stream")
                self.stream_btn.setIcon(make_icon(ICON_STOP, 16, MACOS_RED))

    def _soft_reset(self):
        if not self.client.connected:
            return
        reply = QMessageBox.question(
            self, "Soft Reset",
            "Are you sure you want to soft-reset the sensor?\n\n"
            "This will stop any active stream and reset all settings.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.client.soft_reset()


# =========================================================================
# Controls Page
# =========================================================================

class ControlsPage(QWidget):
    """Gain, exposure, HDR controls with elegant sliders."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_header("Sensor Controls"))
        layout.addWidget(make_description("Adjust gain, exposure, and HDR settings for the IMX708 sensor."))

        # Gain control
        gain_group = make_group_box("Gain Control")
        gain_layout = QFormLayout(gain_group)
        gain_layout.setSpacing(12)
        gain_layout.setLabelAlignment(Qt.AlignRight)

        # Analog gain
        self.gain_slider = MacSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 960)
        self.gain_slider.setValue(0)
        self.gain_slider.setAccentColor(MACOS_BLUE)
        self.gain_slider.setToolTip("Analog gain: 0–960 (higher = brighter)")

        gain_val_layout = QHBoxLayout()
        self.gain_value = QLabel("0")
        self.gain_value.setStyleSheet(f"color: {MACOS_BLUE}; font-size: 14px; font-weight: 700;")
        self.gain_value.setFixedWidth(50)
        gain_val_layout.addWidget(self.gain_slider)
        gain_val_layout.addWidget(self.gain_value)

        self.gain_slider.valueChanged.connect(lambda v: self.gain_value.setText(str(v)))
        gain_layout.addRow(QLabel("Analog Gain"), gain_val_layout)

        # Digital gain
        self.dgain_slider = MacSlider(Qt.Horizontal)
        self.dgain_slider.setRange(0x100, 0xFFFF)
        self.dgain_slider.setValue(0x100)
        self.dgain_slider.setAccentColor(MACOS_PURPLE)
        self.dgain_slider.setToolTip("Digital gain: 256–65535 (higher = brighter)")

        dgain_val_layout = QHBoxLayout()
        self.dgain_value = QLabel("256")
        self.dgain_value.setStyleSheet(f"color: {MACOS_PURPLE}; font-size: 14px; font-weight: 700;")
        self.dgain_value.setFixedWidth(50)
        dgain_val_layout.addWidget(self.dgain_slider)
        dgain_val_layout.addWidget(self.dgain_value)

        self.dgain_slider.valueChanged.connect(lambda v: self.dgain_value.setText(str(v)))
        gain_layout.addRow(QLabel("Digital Gain"), dgain_val_layout)

        apply_gain = make_primary_button("Apply Gain", ICON_CHECK)
        apply_gain.setToolTip("Send the current gain values to the sensor")
        apply_gain.clicked.connect(self._apply_gain)
        gain_layout.addRow("", apply_gain)

        layout.addWidget(gain_group)

        # Exposure control
        exp_group = make_group_box("Exposure Control")
        exp_layout = QFormLayout(exp_group)
        exp_layout.setSpacing(12)
        exp_layout.setLabelAlignment(Qt.AlignRight)

        self.exp_slider = MacSlider(Qt.Horizontal)
        self.exp_slider.setRange(8, 0xFFFF)
        self.exp_slider.setValue(0x640)
        self.exp_slider.setAccentColor(MACOS_ORANGE)
        self.exp_slider.setToolTip("Exposure: 8–65535 line units (higher = longer exposure)")

        exp_val_layout = QHBoxLayout()
        self.exp_value = QLabel("1600")
        self.exp_value.setStyleSheet(f"color: {MACOS_ORANGE}; font-size: 14px; font-weight: 700;")
        self.exp_value.setFixedWidth(50)
        exp_val_layout.addWidget(self.exp_slider)
        exp_val_layout.addWidget(self.exp_value)

        self.exp_slider.valueChanged.connect(lambda v: self.exp_value.setText(str(v)))
        exp_layout.addRow(QLabel("Exposure"), exp_val_layout)

        apply_exp = make_primary_button("Apply Exposure", ICON_CHECK)
        apply_exp.setToolTip("Send the current exposure value to the sensor")
        apply_exp.clicked.connect(self._apply_exposure)
        exp_layout.addRow("", apply_exp)

        layout.addWidget(exp_group)

        # HDR control
        hdr_group = make_group_box("HDR Mode")
        hdr_layout = QFormLayout(hdr_group)
        hdr_layout.setSpacing(12)
        hdr_layout.setLabelAlignment(Qt.AlignRight)

        self.hdr_combo = QComboBox()
        self.hdr_combo.addItems(["Off", "On"])
        self.hdr_combo.setToolTip("Enable or disable High Dynamic Range mode")
        self.hdr_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px 12px; border: 1px solid {MACOS_BORDER};
                border-radius: 8px; background: white; font-size: 13px;
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {MACOS_BLUE};
            }}
            QComboBox::drop-down {{
                border: none; width: 24px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {MACOS_BORDER}; border-radius: 8px;
                background: white; selection-background-color: {MACOS_BLUE};
                selection-color: white; padding: 4px;
            }}
        """)
        hdr_layout.addRow(QLabel("HDR Mode"), self.hdr_combo)

        apply_hdr = make_primary_button("Apply HDR", ICON_CHECK)
        apply_hdr.setToolTip("Send the HDR mode selection to the sensor")
        apply_hdr.clicked.connect(self._apply_hdr)
        hdr_layout.addRow("", apply_hdr)

        layout.addWidget(hdr_group)
        layout.addStretch()

    def _apply_gain(self):
        if self.client.connected:
            self.client.set_gain(self.gain_slider.value(), self.dgain_slider.value())

    def _apply_exposure(self):
        if self.client.connected:
            self.client.set_exposure(self.exp_slider.value())

    def _apply_hdr(self):
        if self.client.connected:
            self.client.set_hdr(self.hdr_combo.currentIndex())


# =========================================================================
# Capture Page
# =========================================================================

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

        layout.addWidget(make_header("Frame Capture"))
        layout.addWidget(make_description("Capture single frames or bursts from the sensor."))

        # Capture settings
        cap_group = make_group_box("Capture Settings")
        cap_layout = QFormLayout(cap_group)
        cap_layout.setSpacing(12)
        cap_layout.setLabelAlignment(Qt.AlignRight)

        self.cap_count = QSpinBox()
        self.cap_count.setRange(1, 100)
        self.cap_count.setValue(1)
        self.cap_count.setToolTip("Number of frames to capture in a single burst")
        self.cap_count.setStyleSheet(f"""
            QSpinBox {{
                padding: 6px 12px; border: 1px solid {MACOS_BORDER};
                border-radius: 8px; background: white; font-size: 13px;
                min-width: 80px;
            }}
            QSpinBox:hover {{ border-color: {MACOS_BLUE}; }}
            QSpinBox:focus {{ border-color: {MACOS_BLUE}; background: #F0F5FF; }}
            QSpinBox::up-button, QSpinBox::down-button {{
                border: none; width: 20px;
            }}
        """)
        cap_layout.addRow(QLabel("Number of Frames"), self.cap_count)

        self.cap_format = QComboBox()
        self.cap_format.addItems(["RAW10", "PGM"])
        self.cap_format.setToolTip("Output format for captured frames")
        self.cap_format.setStyleSheet(self.hdr_combo.styleSheet() if hasattr(self, 'hdr_combo') else f"""
            QComboBox {{
                padding: 6px 12px; border: 1px solid {MACOS_BORDER};
                border-radius: 8px; background: white; font-size: 13px;
                min-width: 120px;
            }}
        """)
        cap_layout.addRow(QLabel("Format"), self.cap_format)

        btn_row = QHBoxLayout()
        self.capture_btn = make_primary_button("  Capture", ICON_CAPTURE)
        self.capture_btn.clicked.connect(self._capture)

        self.save_btn = make_secondary_button("  Save to File...", ICON_DOWNLOAD)
        self.save_btn.clicked.connect(self._save)
        self.save_btn.setEnabled(False)

        # Capture loading indicator
        self.capture_loading = QProgressBar()
        self.capture_loading.setRange(0, 0)  # Indeterminate
        self.capture_loading.setFixedSize(120, 4)
        self.capture_loading.setTextVisible(False)
        self.capture_loading.setStyleSheet(f"""
            QProgressBar {{
                border: none; border-radius: 2px;
                background: {MACOS_SEPARATOR};
            }}
            QProgressBar::chunk {{
                background: {MACOS_BLUE}; border-radius: 2px;
            }}
        """)
        self.capture_loading.hide()

        btn_row.addWidget(self.capture_btn)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.capture_loading)
        btn_row.addStretch()
        cap_layout.addRow("", btn_row)

        layout.addWidget(cap_group)

        # Frame info
        self.frame_info = QTextEdit()
        self.frame_info.setReadOnly(True)
        self.frame_info.setMaximumHeight(130)
        self.frame_info.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {MACOS_BORDER}; border-radius: 10px;
                padding: 12px; font-size: 12px; color: {MACOS_SECONDARY};
                background: white;
            }}
        """)
        self.frame_info.setText("No frames captured yet")
        layout.addWidget(self.frame_info)

        layout.addStretch()

        self._last_frame = None

    def _capture(self):
        if not self.client.connected:
            return
        self.capture_btn.setEnabled(False)
        self.capture_loading.show()
        QApplication.processEvents()

        count = self.cap_count.value()
        frames = []
        for i in range(count):
            frame = self.client.capture_frame()
            if frame:
                frames.append(frame)
                self._last_frame = frame

        self.capture_loading.hide()
        self.capture_btn.setEnabled(True)

        if frames:
            self.frame_info.setText(
                f"Captured {len(frames)} frame(s)\n"
                f"Size: {frames[0]['width']}×{frames[0]['height']}\n"
                f"Data: {len(frames[0].get('data', b'')):,} bytes\n"
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


# =========================================================================
# Image Page
# =========================================================================

class ImagePage(QWidget):
    """Image-processing controls (brightness, contrast, white balance, flip)."""

    SLIDERS = (
        ("brightness", "Brightness", -100, 100),
        ("contrast", "Contrast", -100, 100),
        ("saturation", "Saturation", -100, 100),
        ("hue", "Hue", -180, 180),
        ("sharpness", "Sharpness", -100, 100),
        ("gamma", "Gamma", 100, 300),
    )

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.spins: Dict[str, QSpinBox] = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_header("Image Processing"))
        layout.addWidget(make_description("Adjust brightness, contrast, white balance, and more."))

        # Adjustments
        adj_group = make_group_box("Adjustments")
        adj_layout = QFormLayout(adj_group)
        adj_layout.setSpacing(8)
        adj_layout.setLabelAlignment(Qt.AlignRight)

        for name, label, lo, hi in self.SLIDERS:
            spin = QSpinBox()
            spin.setRange(lo, hi)
            spin.setToolTip(f"{label}: range {lo} to {hi}")
            spin.setStyleSheet(f"""
                QSpinBox {{
                    padding: 4px 8px; border: 1px solid {MACOS_BORDER};
                    border-radius: 6px; background: white; font-size: 12px;
                    min-width: 70px;
                }}
                QSpinBox:hover {{ border-color: {MACOS_BLUE}; }}
                QSpinBox:focus {{ border-color: {MACOS_BLUE}; background: #F0F5FF; }}
            """)
            self.spins[name] = spin
            adj_layout.addRow(QLabel(label), spin)

        layout.addWidget(adj_group)

        # White Balance & Orientation
        wb_group = make_group_box("White Balance & Orientation")
        wb_layout = QFormLayout(wb_group)
        wb_layout.setSpacing(8)
        wb_layout.setLabelAlignment(Qt.AlignRight)

        self.auto_wb_check = QCheckBox("Automatic white balance")
        self.auto_wb_check.setChecked(True)
        self.auto_wb_check.setToolTip("Automatically adjust white balance based on scene lighting")
        self.auto_wb_check.setStyleSheet(f"""
            QCheckBox {{
                font-size: 13px; color: {MACOS_TEXT};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px; border-radius: 4px;
                border: 1px solid {MACOS_BORDER};
            }}
            QCheckBox::indicator:checked {{
                background: {MACOS_BLUE}; border-color: {MACOS_BLUE};
            }}
        """)
        self.auto_wb_check.toggled.connect(self._on_auto_wb_toggled)
        wb_layout.addRow(self.auto_wb_check)

        self.wb_spin = QSpinBox()
        self.wb_spin.setRange(2800, 10000)
        self.wb_spin.setValue(6500)
        self.wb_spin.setSuffix(" K")
        self.wb_spin.setEnabled(False)
        self.wb_spin.setToolTip("White balance color temperature in Kelvin (2800K–10000K)")
        self.wb_spin.setStyleSheet(f"""
            QSpinBox {{
                padding: 4px 8px; border: 1px solid {MACOS_BORDER};
                border-radius: 6px; background: white; font-size: 12px;
                min-width: 90px;
            }}
            QSpinBox:hover {{ border-color: {MACOS_BLUE}; }}
            QSpinBox:focus {{ border-color: {MACOS_BLUE}; background: #F0F5FF; }}
        """)
        wb_layout.addRow(QLabel("Temperature"), self.wb_spin)

        self.hflip_check = QCheckBox("Horizontal flip")
        self.hflip_check.setToolTip("Mirror the image horizontally")
        self.hflip_check.setStyleSheet(self.auto_wb_check.styleSheet())
        self.vflip_check = QCheckBox("Vertical flip")
        self.vflip_check.setToolTip("Mirror the image vertically")
        self.vflip_check.setStyleSheet(self.auto_wb_check.styleSheet())
        wb_layout.addRow(self.hflip_check)
        wb_layout.addRow(self.vflip_check)

        layout.addWidget(wb_group)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        refresh_btn = make_secondary_button("  Refresh", ICON_REFRESH)
        refresh_btn.setToolTip("Refresh current image processing settings from the sensor")
        refresh_btn.clicked.connect(self.refresh)
        apply_btn = make_primary_button("  Apply", ICON_CHECK)
        apply_btn.setToolTip("Apply all image processing settings to the sensor")
        apply_btn.clicked.connect(self._apply)
        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(apply_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()

    def _on_auto_wb_toggled(self, checked: bool):
        self.wb_spin.setEnabled(not checked)

    def refresh(self):
        if not self.client.connected:
            return
        cfg = self.client.get_image_processing()
        if not cfg:
            return
        for name, spin in self.spins.items():
            spin.setValue(int(cfg.get(name, spin.value())))
        self.auto_wb_check.setChecked(bool(cfg.get('auto_wb', True)))
        wb = int(cfg.get('wb_temperature', 0))
        if wb:
            self.wb_spin.setValue(wb)
        self.hflip_check.setChecked(bool(cfg.get('hflip', False)))
        self.vflip_check.setChecked(bool(cfg.get('vflip', False)))

    def _apply(self):
        if not self.client.connected:
            return
        values = {name: spin.value() for name, spin in self.spins.items()}
        values.update(
            auto_wb=self.auto_wb_check.isChecked(),
            wb_temperature=self.wb_spin.value(),
            hflip=self.hflip_check.isChecked(),
            vflip=self.vflip_check.isChecked(),
        )
        self.client.set_image_processing(**values)


# =========================================================================
# Test Pattern Page
# =========================================================================

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

        layout.addWidget(make_header("Test Patterns"))
        layout.addWidget(make_description("Select a test pattern to verify sensor output and signal integrity."))

        # Pattern grid
        patterns = [
            ("Disabled", ICON_STOP, 0),
            ("Color Bars", ICON_PALETTE, 1),
            ("Solid Color", ICON_PALETTE, 2),
            ("Grey Bars", ICON_GRID, 3),
            ("PN9", ICON_GRID, 4),
        ]

        grid = QGridLayout()
        grid.setSpacing(10)

        self.pattern_btns = []
        for i, (name, icon, val) in enumerate(patterns):
            btn = QPushButton(f"  {name}")
            btn.setIcon(make_icon(icon, 22, MACOS_BLUE))
            btn.setCheckable(True)
            btn.setFixedSize(170, 64)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setToolTip(f"Set test pattern to '{name}'")
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: 1px solid {MACOS_BORDER}; border-radius: 10px;
                    background: white; font-size: 12px; font-weight: 500;
                    color: {MACOS_TEXT}; text-align: left; padding: 10px 14px;
                }}
                QPushButton:hover {{
                    background: {MACOS_BG};
                    border-color: {MACOS_BLUE};
                }}
                QPushButton:checked {{
                    border: 2px solid {MACOS_BLUE};
                    background: #E8F0FE;
                }}
            """)
            btn.clicked.connect(lambda checked, v=val: self._select_pattern(v))
            grid.addWidget(btn, i // 3, i % 3)
            self.pattern_btns.append(btn)

        layout.addLayout(grid)

        # Color controls
        color_group = make_group_box("Solid Color Settings")
        color_layout = QFormLayout(color_group)
        color_layout.setSpacing(8)
        color_layout.setLabelAlignment(Qt.AlignRight)

        self.color_r = QSpinBox()
        self.color_r.setRange(0, 0xFFF)
        self.color_r.setValue(0xFFF)
        self.color_r.setToolTip("Red channel value for solid color pattern (0–4095)")
        self.color_r.setStyleSheet(f"""
                QSpinBox {{
                    padding: 4px 8px; border: 1px solid {MACOS_BORDER};
                    border-radius: 6px; background: white; font-size: 12px;
                    min-width: 80px;
                }}
                QSpinBox:hover {{ border-color: {MACOS_BLUE}; }}
                QSpinBox:focus {{ border-color: {MACOS_BLUE}; background: #F0F5FF; }}
            """)
        color_layout.addRow(QLabel("Red"), self.color_r)

        self.color_b = QSpinBox()
        self.color_b.setRange(0, 0xFFF)
        self.color_b.setValue(0xFFF)
        self.color_b.setToolTip("Blue channel value for solid color pattern (0–4095)")
        self.color_b.setStyleSheet(self.color_r.styleSheet())
        color_layout.addRow(QLabel("Blue"), self.color_b)

        layout.addWidget(color_group)
        layout.addStretch()

    def _select_pattern(self, val: int):
        for btn in self.pattern_btns:
            btn.setChecked(False)
        if val < len(self.pattern_btns):
            self.pattern_btns[val].setChecked(True)
        if self.client.connected:
            self.client.set_test_pattern(val)


# =========================================================================
# Register Page
# =========================================================================

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

        layout.addWidget(make_header("Register Access"))
        layout.addWidget(make_description("Read and write sensor registers directly. Requires root on the server."))

        # Known registers
        known_group = make_group_box("Known Registers")
        known_layout = QGridLayout(known_group)
        known_layout.setSpacing(6)

        known_regs = [
            ("CHIP_ID", 0x0016), ("MODE_SELECT", 0x0100),
            ("ORIENTATION", 0x0101), ("TEMPERATURE", 0x013A),
            ("EXPOSURE", 0x0202), ("ANALOG_GAIN", 0x0204),
            ("DIGITAL_GAIN", 0x020E), ("FRAME_LENGTH", 0x0340),
            ("LINE_LENGTH", 0x0342), ("TEST_PATTERN", 0x0600),
        ]

        for i, (name, addr) in enumerate(known_regs):
            btn = QPushButton(f"0x{addr:04X}  {name}")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setToolTip(f"Read register 0x{addr:04X} ({name})")
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: 1px solid {MACOS_BORDER}; border-radius: 8px;
                    padding: 8px 14px; font-size: 12px; font-weight: 500;
                    color: {MACOS_TEXT}; background: white; text-align: left;
                }}
                QPushButton:hover {{
                    background: {MACOS_BG};
                    border-color: {MACOS_BLUE};
                }}
            """)
            btn.clicked.connect(lambda checked, a=addr: self._read_reg(a))
            known_layout.addWidget(btn, i // 2, i % 2)

        layout.addWidget(known_group)

        # Custom register access
        custom_group = make_group_box("Custom Access")
        custom_layout = QFormLayout(custom_group)
        custom_layout.setSpacing(10)
        custom_layout.setLabelAlignment(Qt.AlignRight)

        addr_val_layout = QHBoxLayout()
        addr_val_layout.setSpacing(10)

        self.reg_addr = QLineEdit("0x0000")
        self.reg_addr.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {MACOS_BORDER}; border-radius: 8px;
                padding: 8px 12px; font-size: 13px; font-family: monospace;
                background: white; min-width: 100px;
            }}
            QLineEdit:focus {{
                border-color: {MACOS_BLUE};
                background: #F0F5FF;
            }}
        """)
        addr_val_layout.addWidget(self.reg_addr)

        self.reg_val = QLineEdit("0x00")
        self.reg_val.setStyleSheet(self.reg_addr.styleSheet())
        addr_val_layout.addWidget(self.reg_val)

        custom_layout.addRow(QLabel("Address / Value"), addr_val_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        read_btn = make_primary_button("  Read", ICON_DOWNLOAD)
        read_btn.setToolTip("Read the value at the specified register address")
        read_btn.clicked.connect(self._read_custom)

        write_btn = QPushButton("  Write")
        write_btn.setIcon(make_icon(ICON_CHECK, 16, "#FFFFFF"))
        write_btn.setToolTip("Write the specified value to the register address")
        write_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 8px 18px; border-radius: 8px;
                border: none; background: {MACOS_ORANGE};
                color: white; font-size: 13px; font-weight: 500;
            }}
            QPushButton:hover {{ background: #E68A00; }}
        """)
        write_btn.clicked.connect(self._write_custom)

        btn_layout.addWidget(read_btn)
        btn_layout.addWidget(write_btn)
        btn_layout.addStretch()
        custom_layout.addRow("", btn_layout)

        layout.addWidget(custom_group)

        # Results
        self.reg_result = QTextEdit()
        self.reg_result.setReadOnly(True)
        self.reg_result.setMaximumHeight(150)
        self.reg_result.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {MACOS_BORDER}; border-radius: 10px;
                padding: 12px; font-size: 12px; font-family: monospace;
                color: {MACOS_TEXT}; background: {MACOS_BG};
            }}
        """)
        layout.addWidget(self.reg_result)

        layout.addStretch()

    def _read_reg(self, addr: int):
        if not self.client.connected:
            return
        val = self.client.read_register(addr)
        if val is not None:
            self.reg_result.append(f"REG[0x{addr:04X}] = 0x{val:02X} ({val})")

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
                self.reg_result.append(f"REG[0x{addr:04X}] ← 0x{val:02X}")
        except ValueError:
            self.reg_result.append("Invalid value")


# =========================================================================
# Info Page
# =========================================================================

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

        layout.addWidget(make_header("About IMX708"))

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {MACOS_BORDER}; border-radius: 10px;
                padding: 16px; font-size: 13px; color: {MACOS_TEXT};
                background: white;
            }}
        """)
        info_text.setHtml(f"""
        <h2 style="color: {MACOS_TEXT}; margin-bottom: 8px;">Sony IMX708</h2>
        <p style="color: {MACOS_SECONDARY}; line-height: 1.6;">
        Back-illuminated and stacked CMOS 12-megapixel image sensor.
        </p>
        <table style="width: 100%; border-collapse: collapse; margin-top: 12px;">
        <tr><td style="padding: 6px 12px; color: {MACOS_SECONDARY};"><b>Resolution</b></td>
            <td style="padding: 6px 12px; color: {MACOS_TEXT};">4608 × 2592 (11.9 MP)</td></tr>
        <tr><td style="padding: 6px 12px; color: {MACOS_SECONDARY};"><b>Pixel Size</b></td>
            <td style="padding: 6px 12px; color: {MACOS_TEXT};">1.4 μm × 1.4 μm</td></tr>
        <tr><td style="padding: 6px 12px; color: {MACOS_SECONDARY};"><b>Optical Format</b></td>
            <td style="padding: 6px 12px; color: {MACOS_TEXT};">1/2.43"</td></tr>
        <tr><td style="padding: 6px 12px; color: {MACOS_SECONDARY};"><b>Output</b></td>
            <td style="padding: 6px 12px; color: {MACOS_TEXT};">RAW10, MIPI CSI-2 (2/4 lanes)</td></tr>
        <tr><td style="padding: 6px 12px; color: {MACOS_SECONDARY};"><b>HDR</b></td>
            <td style="padding: 6px 12px; color: {MACOS_TEXT};">Up to 3 MP output</td></tr>
        <tr><td style="padding: 6px 12px; color: {MACOS_SECONDARY};"><b>Autofocus</b></td>
            <td style="padding: 6px 12px; color: {MACOS_TEXT};">Phase Detection (PDAF)</td></tr>
        </table>
        <h3 style="color: {MACOS_TEXT}; margin-top: 20px; margin-bottom: 8px;">Driver Features</h3>
        <ul style="color: {MACOS_SECONDARY}; line-height: 1.8;">
        <li>V4L2 sub-device with 24 controls</li>
        <li>9 sensor modes (up to 240fps)</li>
        <li>gRPC remote control API</li>
        <li>Cross-platform GUI client</li>
        <li>Frame capture and recording</li>
        <li>Configuration profiles</li>
        <li>Fault injection and debugfs</li>
        </ul>
        <p style="color: {MACOS_TERTIARY}; font-size: 12px; margin-top: 16px;">
        <i>Version 0.1.0 — GPL-2.0-only</i>
        </p>
        """)
        layout.addWidget(info_text)

        # Modes table
        self.modes_table = QTextEdit()
        self.modes_table.setReadOnly(True)
        self.modes_table.setMaximumHeight(180)
        self.modes_table.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {MACOS_BORDER}; border-radius: 10px;
                padding: 12px; font-size: 12px; font-family: monospace;
                color: {MACOS_TEXT}; background: {MACOS_BG};
            }}
        """)
        layout.addWidget(self.modes_table)

        refresh_btn = make_primary_button("  Refresh Modes", ICON_REFRESH)
        refresh_btn.setToolTip("Fetch the latest list of supported sensor modes from the server")
        refresh_btn.clicked.connect(self._refresh_modes)
        layout.addWidget(refresh_btn)

        layout.addStretch()

    def _refresh_modes(self):
        if not self.client.connected:
            return
        modes = self.client.get_modes()
        text = "Available Modes:\n" + "═" * 50 + "\n"
        for m in modes:
            text += f"  [{m['index']}] {m['width']}×{m['height']} @ {m['fps']} fps\n"
            text += f"       Code: 0x{m['code']:x}, {m['bit_depth']}-bit\n"
            text += f"       Pixel Rate: {m['pixel_rate']/1e6:.1f} MHz\n"
        self.modes_table.setText(text)


# =========================================================================
# Server Configuration Manager
# =========================================================================

CONFIG_DIR = Path.home() / ".config" / "imx708-gui"
CONFIG_FILE = CONFIG_DIR / "servers.json"

def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_servers() -> List[Dict]:
    """Load saved server configurations."""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('servers', [])
        except Exception:
            pass
    return []

def save_servers(servers: List[Dict]):
    """Save server configurations."""
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'servers': servers}, f, indent=2)
    except Exception as e:
        print(f"Failed to save servers: {e}")

def get_last_server() -> str:
    """Get last used server address."""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_server', 'localhost:50051')
        except Exception:
            pass
    return 'localhost:50051'

def set_last_server(addr: str):
    """Set last used server address."""
    ensure_config_dir()
    try:
        data = {'servers': load_servers(), 'last_server': addr}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save last server: {e}")


# =========================================================================
# Connection Dialog
# =========================================================================

class ConnectionDialog(QDialog):
    """macOS-style dialog for managing server connections."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Server Connections")
        self.setModal(True)
        self.setFixedSize(520, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background: {MACOS_BG};
            }}
        """)
        
        self.servers = load_servers()
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QLabel("Server Connections")
        header.setStyleSheet(f"""
            font-size: 20px; font-weight: 700; color: {MACOS_TEXT};
        """)
        layout.addWidget(header)

        desc = QLabel("Manage gRPC server connections for IMX708 cameras.")
        desc.setStyleSheet(f"color: {MACOS_SECONDARY}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Server list
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {MACOS_BORDER}; border-radius: 10px;
                background: white; padding: 8px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px 12px; border-radius: 6px;
                margin: 2px;
            }}
            QListWidget::item:selected {{
                background: {MACOS_BLUE}; color: white;
            }}
            QListWidget::item:hover {{
                background: {MACOS_SEPARATOR};
            }}
        """)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self._on_connect)
        layout.addWidget(self.list_widget, 1)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.add_btn = make_primary_button("  Add Server", ICON_DOWNLOAD)
        self.add_btn.setToolTip("Add a new gRPC server to the list")
        self.add_btn.clicked.connect(self._on_add)

        self.edit_btn = make_secondary_button("  Edit", ICON_SLIDERS)
        self.edit_btn.setToolTip("Edit the selected server's name or address")
        self.edit_btn.clicked.connect(self._on_edit)
        self.edit_btn.setEnabled(False)

        self.remove_btn = make_secondary_button("  Remove", ICON_STOP)
        self.remove_btn.setToolTip("Remove the selected server from the list")
        self.remove_btn.clicked.connect(self._on_remove)
        self.remove_btn.setEnabled(False)

        self.test_btn = make_secondary_button("  Test", ICON_REFRESH)
        self.test_btn.setToolTip("Test the connection to the selected server")
        self.test_btn.clicked.connect(self._on_test)
        self.test_btn.setEnabled(False)

        self.connect_btn = make_primary_button("  Connect", ICON_CONNECT)
        self.connect_btn.setToolTip("Connect to the selected server")
        self.connect_btn.clicked.connect(self._on_connect)
        self.connect_btn.setEnabled(False)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.test_btn)
        btn_layout.addWidget(self.connect_btn)

        layout.addLayout(btn_layout)

        # Close button
        close_btn = make_secondary_button("  Done", ICON_CHECK)
        close_btn.clicked.connect(self.accept)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def refresh_list(self):
        self.list_widget.clear()
        for server in self.servers:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, server)
            
            # Create custom widget for each item
            widget = QWidget()
            w_layout = QHBoxLayout(widget)
            w_layout.setContentsMargins(8, 4, 8, 4)
            w_layout.setSpacing(10)

            # Status indicator
            status_lbl = QLabel("●")
            status_lbl.setStyleSheet(f"color: {MACOS_TERTIARY}; font-size: 12px;")
            status_lbl.setFixedWidth(16)
            w_layout.addWidget(status_lbl)

            # Server info
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            
            name_lbl = QLabel(server.get('name', 'Unnamed'))
            name_lbl.setStyleSheet(f"font-weight: 600; color: {MACOS_TEXT}; font-size: 13px;")
            info_layout.addWidget(name_lbl)

            addr_lbl = QLabel(server.get('address', ''))
            addr_lbl.setStyleSheet(f"color: {MACOS_SECONDARY}; font-size: 12px; font-family: monospace;")
            info_layout.addWidget(addr_lbl)

            w_layout.addLayout(info_layout)
            w_layout.addStretch()

            # Last connected
            last = server.get('last_connected')
            if last:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(last)
                    last_str = dt.strftime("%b %d, %H:%M")
                except Exception:
                    last_str = last
                last_lbl = QLabel(last_str)
                last_lbl.setStyleSheet(f"color: {MACOS_TERTIARY}; font-size: 12px;")
                w_layout.addWidget(last_lbl)

            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        # Select first item
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_selection_changed(self):
        has_selection = len(self.list_widget.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.remove_btn.setEnabled(has_selection)
        self.test_btn.setEnabled(has_selection)
        self.connect_btn.setEnabled(has_selection)

    def _get_selected_server(self) -> Optional[Dict]:
        items = self.list_widget.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.UserRole)

    def _on_add(self):
        dialog = ServerEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            server = dialog.get_server_data()
            self.servers.append(server)
            save_servers(self.servers)
            self.refresh_list()
            # Select the new item
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)

    def _on_edit(self):
        server = self._get_selected_server()
        if not server:
            return
        dialog = ServerEditDialog(self, server)
        if dialog.exec() == QDialog.Accepted:
            updated = dialog.get_server_data()
            # Find and update
            for i, s in enumerate(self.servers):
                if s.get('address') == server.get('address') and s.get('name') == server.get('name'):
                    self.servers[i] = updated
                    break
            save_servers(self.servers)
            self.refresh_list()

    def _on_remove(self):
        server = self._get_selected_server()
        if not server:
            return
        
        name = server.get('name', 'this server')
        reply = QMessageBox.question(
            self, "Remove Server",
            f"Remove '{name}' from the server list?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.servers = [s for s in self.servers if s != server]
            save_servers(self.servers)
            self.refresh_list()

    def _on_test(self):
        server = self._get_selected_server()
        if not server:
            return
        
        addr = server.get('address', '')
        self.test_btn.setText("  Testing...")
        self.test_btn.setEnabled(False)
        QApplication.processEvents()

        # Test connection in background
        import threading
        def test():
            client = GrpcClient(addr)
            success = client.connect()
            client.disconnect()
            # Update UI on main thread
            QMetaObject.invokeMethod(
                self, "_on_test_result", Qt.QueuedConnection,
                Q_ARG(bool, success), Q_ARG(str, addr)
            )
        
        threading.Thread(target=test, daemon=True).start()

    @Slot(bool, str)
    def _on_test_result(self, success: bool, addr: str):
        self.test_btn.setText("  Test")
        self.test_btn.setEnabled(True)
        
        # Update status in list
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            server = item.data(Qt.UserRole)
            if server.get('address') == addr:
                widget = self.list_widget.itemWidget(item)
                if widget:
                    status_lbl = widget.findChild(QLabel)
                    if status_lbl:
                        status_lbl.setStyleSheet(
                            f"color: {MACOS_GREEN if success else MACOS_RED}; font-size: 12px;"
                        )
                        status_lbl.setText("●")
                break
        
        QMessageBox.information(
            self, "Connection Test",
            f"Connection to {addr} {'succeeded' if success else 'failed'}."
        )

    def _on_connect(self):
        server = self._get_selected_server()
        if not server:
            return
        self.selected_server = server
        self.accept()

    def get_selected_server(self) -> Optional[Dict]:
        return getattr(self, 'selected_server', None)


class ServerEditDialog(QDialog):
    """Dialog for adding/editing a server."""
    
    def __init__(self, parent=None, server: Dict = None):
        super().__init__(parent)
        self.server = server or {}
        self.setWindowTitle("Edit Server" if server else "Add Server")
        self.setModal(True)
        self.setFixedWidth(420)
        self.setStyleSheet(f"""
            QDialog {{
                background: {MACOS_BG};
            }}
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Form
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Living Room Camera")
        self.name_edit.setText(self.server.get('name', ''))
        self.name_edit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {MACOS_BORDER}; border-radius: 8px;
                padding: 8px 12px; font-size: 13px; background: white;
            }}
            QLineEdit:focus {{
                border-color: {MACOS_BLUE};
                background: #F0F5FF;
            }}
        """)
        form.addRow(self._make_label("Name"), self.name_edit)

        # Address
        self.addr_edit = QLineEdit()
        self.addr_edit.setPlaceholderText("192.168.1.42:50051")
        self.addr_edit.setText(self.server.get('address', ''))
        self.addr_edit.setStyleSheet(self.name_edit.styleSheet())
        form.addRow(self._make_label("Address"), self.addr_edit)

        layout.addLayout(form)

        # Help text
        help_text = QLabel(
            "Enter the IP address and port of the Raspberry Pi running the IMX708 gRPC server."
            " Default port is 50051. Example: 192.168.1.42:50051"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet(f"color: {MACOS_SECONDARY}; font-size: 12px;")
        layout.addWidget(help_text)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = make_secondary_button("Cancel", ICON_STOP)
        cancel_btn.setToolTip("Discard changes and close")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = make_primary_button("Save", ICON_CHECK)
        save_btn.setToolTip("Save the server configuration")
        save_btn.clicked.connect(self._validate_and_accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-weight: 500; color: {MACOS_TEXT}; font-size: 13px;")
        return lbl

    def _validate_and_accept(self):
        name = self.name_edit.text().strip()
        addr = self.addr_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a server name.")
            self.name_edit.setFocus()
            return

        if not addr:
            QMessageBox.warning(self, "Invalid Address", "Please enter a server address.")
            self.addr_edit.setFocus()
            return

        # Basic address validation
        if ':' not in addr:
            QMessageBox.warning(self, "Invalid Address", "Address must be in format host:port (e.g., 192.168.1.42:50051).")
            self.addr_edit.setFocus()
            return

        self.accept()

    def get_server_data(self) -> Dict:
        return {
            'name': self.name_edit.text().strip(),
            'address': self.addr_edit.text().strip(),
            'last_connected': None
        }


# =========================================================================
# Main Window
# =========================================================================

class MainWindow(QMainWindow):
    """Main application window with elegant macOS-inspired design."""

    def __init__(self, server_addr: str = None):
        super().__init__()
        # Use last server from config if not provided
        if server_addr is None:
            server_addr = get_last_server()
        self.server_addr = server_addr
        self.client = GrpcClient(server_addr)
        self.setup_ui()
        self.setup_menu()

    def setup_ui(self):
        self.setWindowTitle("IMX708 Camera Controller")
        self.setMinimumSize(960, 680)
        self.resize(1100, 740)
        self.setStyleSheet(f"""
            QMainWindow {{ background: {MACOS_BG}; }}
        """)

        # Set application window icon
        self.setWindowIcon(make_icon(ICON_CAMERA, 32, MACOS_BLUE))

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

        # Content area with subtle shadow separator
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background: {MACOS_BG};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {MACOS_BG};")

        self.pages = [
            DashboardPage(self.client),
            ControlsPage(self.client),
            CapturePage(self.client),
            ImagePage(self.client),
            TestPatternPage(self.client),
            RegisterPage(self.client),
            InfoPage(self.client),
        ]

        for page in self.pages:
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {MACOS_BG}; border-top: 1px solid {MACOS_BORDER};
                font-size: 12px; color: {MACOS_SECONDARY}; padding: 2px 12px;
            }}
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Disconnected — Click Connect on Dashboard")

        main_layout.addWidget(content_widget, 1)

        # Connect client signals
        self.client.connection_changed.connect(self._on_connection_changed)
        self.client.log_message.connect(self._on_log)

    def setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background: {MACOS_BG}; border-bottom: 1px solid {MACOS_BORDER};
                font-size: 13px; padding: 2px 4px;
            }}
            QMenuBar::item {{
                padding: 4px 10px; border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background: {MACOS_BLUE}; color: white;
            }}
            QMenu {{
                background: white; border: 1px solid {MACOS_BORDER};
                border-radius: 8px; padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px; border-radius: 4px;
            }}
            QMenu::item:selected {{
                background: {MACOS_BLUE}; color: white;
            }}
            QMenu::separator {{
                height: 1px; background: {MACOS_SEPARATOR};
                margin: 4px 8px;
            }}
        """)

        # ── File ──
        file_menu = menubar.addMenu("File")

        # Servers submenu
        servers_menu = file_menu.addMenu("Servers")

        manage_action = QAction("Manage Servers...", self)
        manage_action.setShortcut("Ctrl+M")
        manage_action.triggered.connect(self._show_server_dialog)
        servers_menu.addAction(manage_action)

        servers_menu.addSeparator()

        # Quick connect to recent servers
        self.recent_actions = []
        self._update_recent_servers_menu(servers_menu)

        file_menu.addSeparator()

        # Preferences (macOS: routes to app menu automatically)
        prefs_action = QAction("Preferences...", self)
        prefs_action.setMenuRole(QAction.PreferencesRole)
        prefs_action.setShortcut("Ctrl+,")
        prefs_action.triggered.connect(self._show_server_dialog)
        file_menu.addAction(prefs_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setMenuRole(QAction.QuitRole)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # ── Edit ──
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cut", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        edit_menu.addAction(select_all_action)

        # ── View ──
        view_menu = menubar.addMenu("View")

        self.view_actions = []
        for i, name in enumerate(["Dashboard", "Controls", "Capture", "Image",
                                    "Test Patterns", "Registers", "Info"]):
            action = QAction(name, self)
            action.setCheckable(True)
            if i == 0:
                action.setChecked(True)
            action.triggered.connect(lambda checked, idx=i: self._switch_page(idx))
            view_menu.addAction(action)
            self.view_actions.append(action)

        view_menu.addSeparator()

        toggle_sidebar_action = QAction("Toggle Sidebar", self)
        toggle_sidebar_action.setCheckable(True)
        toggle_sidebar_action.setChecked(True)
        toggle_sidebar_action.setShortcut("Ctrl+\\")
        toggle_sidebar_action.triggered.connect(self._toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)

        # ── Tools ──
        tools_menu = menubar.addMenu("Tools")

        connect_action = QAction("Connect to Server", self)
        connect_action.setShortcut("Ctrl+R")
        connect_action.triggered.connect(self.pages[0].toggle_connect)
        tools_menu.addAction(connect_action)

        start_stream_action = QAction("Start/Stop Stream", self)
        start_stream_action.setShortcut("Ctrl+Shift+S")
        start_stream_action.triggered.connect(self._toggle_stream_from_menu)
        tools_menu.addAction(start_stream_action)

        tools_menu.addSeparator()

        soft_reset_action = QAction("Soft Reset Sensor", self)
        soft_reset_action.setShortcut("Ctrl+Shift+R")
        soft_reset_action.triggered.connect(self._soft_reset_from_menu)
        tools_menu.addAction(soft_reset_action)

        # ── Window (macOS) ──
        window_menu = menubar.addMenu("Window")

        minimize_action = QAction("Minimize", self)
        minimize_action.setShortcut("Ctrl+M")
        minimize_action.triggered.connect(self.showMinimized)
        window_menu.addAction(minimize_action)

        zoom_action = QAction("Zoom", self)
        zoom_action.triggered.connect(self.showMaximized)
        window_menu.addAction(zoom_action)

        window_menu.addSeparator()

        # ── Help ──
        help_menu = menubar.addMenu("Help")

        docs_action = QAction("IMX708 Documentation", self)
        docs_action.setShortcut("F1")
        docs_action.triggered.connect(self._show_docs)
        help_menu.addAction(docs_action)

        help_menu.addSeparator()

        about_action = QAction("About IMX708", self)
        about_action.setMenuRole(QAction.AboutRole)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _update_recent_servers_menu(self, menu):
        """Update the recent servers submenu."""
        # Remove old actions
        for action in self.recent_actions:
            menu.removeAction(action)
        self.recent_actions.clear()

        servers = load_servers()
        for server in servers[:5]:  # Show max 5 recent
            action = QAction(f"{server['name']} ({server['address']})", self)
            action.triggered.connect(lambda checked, s=server: self._connect_to_server(s))
            menu.addAction(action)
            self.recent_actions.append(action)

        if servers:
            menu.addSeparator()

        clear_action = QAction("Clear Recent", self)
        clear_action.triggered.connect(self._clear_recent_servers)
        menu.addAction(clear_action)
        self.recent_actions.append(clear_action)

    def _clear_recent_servers(self):
        """Clear recent servers from config."""
        save_servers([])
        # Rebuild the menu bar to refresh
        self.setup_menu()

    def _show_server_dialog(self):
        """Show the server management dialog."""
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            server = dialog.get_selected_server()
            if server:
                self._connect_to_server(server)

    def _connect_to_server(self, server: Dict):
        """Connect to a selected server."""
        addr = server['address']
        name = server['name']
        
        # Disconnect current
        if self.client.connected:
            self.client.disconnect()
        
        # Update client
        self.server_addr = addr
        self.client = GrpcClient(addr)
        
        # Reconnect signals
        self.client.connection_changed.connect(self._on_connection_changed)
        self.client.log_message.connect(self._on_log)
        
        # Update pages with new client
        for page in self.pages:
            page.client = self.client
        
        # Update sidebar
        self.sidebar.set_connected(False)
        
        # Auto-connect
        self.pages[0].toggle_connect()
        
        # Save as last used
        set_last_server(addr)
        
        # Update last connected timestamp
        from datetime import datetime
        servers = load_servers()
        for s in servers:
            if s['address'] == addr and s['name'] == name:
                s['last_connected'] = datetime.now().isoformat()
                break
        save_servers(servers)
        
        # Update recent menu — rebuild to refresh
        self.setup_menu()

    def _switch_page(self, index: int):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            # Update View menu check states
            if hasattr(self, 'view_actions'):
                for i, action in enumerate(self.view_actions):
                    action.setChecked(i == index)

    def _toggle_sidebar(self, visible: bool):
        """Toggle sidebar visibility."""
        self.sidebar.setVisible(visible)

    def _toggle_stream_from_menu(self):
        """Toggle stream from menu bar."""
        if self.client.connected:
            self.pages[0]._toggle_stream()

    def _soft_reset_from_menu(self):
        """Soft reset with confirmation from menu bar."""
        if not self.client.connected:
            return
        reply = QMessageBox.question(
            self, "Soft Reset",
            "Are you sure you want to soft-reset the sensor?\n\n"
            "This will stop any active stream and reset all settings.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.client.soft_reset()
            self.status_bar.showMessage("Sensor soft reset completed", 3000)

    def _show_docs(self):
        """Show documentation link."""
        QMessageBox.information(
            self, "IMX708 Documentation",
            "Documentation is available at:\n\n"
            "https://github.com/soccentric/imx708\n\n"
            "See the README.md and docs/ folder for details."
        )

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


# =========================================================================
# Entry Point
# =========================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="IMX708 Camera GUI Client")
    parser.add_argument("--server", default=None,
                        help="gRPC server address (default: from config, or localhost:50051)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Set application icon (used for window icon on some platforms)
    app.setWindowIcon(make_icon(ICON_CAMERA, 32, MACOS_BLUE))

    # macOS-like font
    font = QFont()
    font.setFamilies(["SF Pro Display", "Helvetica Neue", "Segoe UI", "Arial"])
    font.setPointSize(13)
    app.setFont(font)

    window = MainWindow(args.server)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
