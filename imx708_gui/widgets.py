# SPDX-License-Identifier: GPL-2.0-only
"""
Custom widgets and shared UI component factories for the IMX708 GUI.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QCursor, QPen, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame, QVBoxLayout, QHBoxLayout,
    QGroupBox, QProgressBar,
)

from .theme import *


# ═══════════════════════════════════════════════════════════════════════════
# Custom macOS-style Slider
# ═══════════════════════════════════════════════════════════════════════════

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
            track_y = (h - track_h) // 2
            track_rect = QRectF(4, track_y, w - 8, track_h)

            path = QPainterPath()
            path.addRoundedRect(track_rect, track_h / 2, track_h / 2)
            painter.fillPath(path, self._track_color)

            ratio = (self._value - self._minimum) / max(1, self._maximum - self._minimum)
            fill_w = max(0, track_rect.width() * ratio)
            if fill_w > 0:
                fill_rect = QRectF(track_rect.x(), track_rect.y(), fill_w, track_rect.height())
                fill_path = QPainterPath()
                fill_path.addRoundedRect(fill_rect, track_h / 2, track_h / 2)
                painter.fillPath(fill_path, self._accent_color)

            knob_x = track_rect.x() + fill_w - knob_r
            knob_x = max(knob_r, min(w - knob_r - 4, knob_x))
            knob_center = QPointF(knob_x, h / 2)

            shadow_path = QPainterPath()
            shadow_path.addEllipse(knob_center, knob_r + 1, knob_r + 1)
            painter.fillPath(shadow_path, self._knob_shadow)

            knob_path = QPainterPath()
            knob_path.addEllipse(knob_center, knob_r, knob_r)
            painter.fillPath(knob_path, self._knob_color)
            painter.setPen(QPen(QColor("#C7C7CC"), 0.5))
            painter.drawPath(knob_path)
        else:
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


# ═══════════════════════════════════════════════════════════════════════════
# macOS-style Sidebar
# ═══════════════════════════════════════════════════════════════════════════

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
                QPushButton:hover {{ background: #0066CC; }}
            """)
            self.setIcon(make_icon(self._icon_svg, 20, "#FFFFFF"))
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 5px 14px; border: none;
                    border-radius: 8px; font-size: 13px; font-weight: 400;
                    color: {MACOS_TEXT}; background: transparent;
                }}
                QPushButton:hover {{ background: {MACOS_SEPARATOR}; }}
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

        # App icon + title
        title_frame = QWidget()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(8, 0, 8, 12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(make_icon(ICON_CAMERA, 28, MACOS_BLUE).pixmap(28, 28))
        title_layout.addWidget(icon_lbl)

        title_text = QLabel("IMX708")
        title_text.setStyleSheet(f"""
            font-size: 16px; font-weight: 700; color: {MACOS_TEXT};
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
        status_frame.setObjectName("statusFrame")
        status_frame.setStyleSheet(f"""
            QFrame#statusFrame {{
                background: white; border-radius: 8px;
                border: 1px solid {MACOS_BORDER}; padding: 8px;
            }}
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 8, 10, 8)
        status_layout.setSpacing(8)

        self.status_dot = QLabel("\u25cf")
        self.status_dot.setStyleSheet(f"color: {MACOS_RED}; font-size: 12px;")
        status_layout.addWidget(self.status_dot)

        self.status_text = QLabel("Disconnected")
        self.status_text.setStyleSheet(f"""
            font-size: 12px; font-weight: 500; color: {MACOS_SECONDARY};
        """)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        layout.addWidget(status_frame)

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


# ═══════════════════════════════════════════════════════════════════════════
# Shared UI Component Factories
# ═══════════════════════════════════════════════════════════════════════════

def make_card(title: str, value: str, color: str, icon_svg: str = None) -> QFrame:
    """Create a beautiful macOS-style info card."""
    card = QFrame()
    card.setObjectName("statCard")
    card.setStyleSheet(f"""
        QFrame#statCard {{
            background: white; border-radius: 10px;
            border: 1px solid {MACOS_BORDER};
        }}
    """)
    card.setMinimumSize(130, 110)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(4)

    if icon_svg:
        icon_lbl = QLabel()
        icon_lbl.setPixmap(make_icon(icon_svg, 18, color).pixmap(18, 18))
        layout.addWidget(icon_lbl)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"color: {MACOS_SECONDARY}; font-size: 12px; font-weight: 500;")
    layout.addWidget(title_lbl)

    val_lbl = QLabel(value)
    val_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 700;")
    val_lbl.setObjectName("card_value")
    layout.addWidget(val_lbl)
    layout.addStretch()

    return card


def make_group_box(title: str) -> QGroupBox:
    """Create a macOS-style group box with & escaped."""
    gb = QGroupBox(title.replace("&", "&&"))
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
        QPushButton:hover {{ background: #0066CC; }}
        QPushButton:pressed {{ background: #0055B3; }}
        QPushButton:focus {{ outline: 2px solid #66B2FF; outline-offset: 2px; }}
        QPushButton:disabled {{ background: #B0B0B0; color: #E0E0E0; }}
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
        QPushButton:hover {{ background: {MACOS_BG}; }}
        QPushButton:pressed {{ background: {MACOS_SEPARATOR}; }}
        QPushButton:focus {{ border-color: {MACOS_BLUE}; outline: 2px solid #66B2FF; }}
        QPushButton:disabled {{ background: {MACOS_BG}; color: {MACOS_TERTIARY}; }}
    """)
    return btn


def make_header(text: str) -> QLabel:
    """Create a macOS-style page header."""
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        font-size: 20px; font-weight: 700; color: {MACOS_TEXT};
        letter-spacing: -0.3px;
    """)
    return lbl


def make_description(text: str) -> QLabel:
    """Create a macOS-style description label."""
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {MACOS_SECONDARY}; font-size: 13px;")
    lbl.setWordWrap(True)
    return lbl


def combo_style(min_width: int = 120) -> str:
    """Shared macOS-style QComboBox stylesheet."""
    return f"""
        QComboBox {{
            padding: 6px 12px; border: 1px solid {MACOS_BORDER};
            border-radius: 8px; background: white; font-size: 13px;
            min-width: {min_width}px;
        }}
        QComboBox:hover {{ border-color: {MACOS_BLUE}; }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox QAbstractItemView {{
            border: 1px solid {MACOS_BORDER}; border-radius: 8px;
            background: white; selection-background-color: {MACOS_BLUE};
            selection-color: white; padding: 4px;
        }}
    """


def spinbox_style() -> str:
    """Shared macOS-style QSpinBox stylesheet."""
    return f"""
        QSpinBox {{
            padding: 4px 8px; border: 1px solid {MACOS_BORDER};
            border-radius: 6px; background: white; font-size: 12px;
            min-width: 70px;
        }}
        QSpinBox:hover {{ border-color: {MACOS_BLUE}; }}
        QSpinBox:focus {{ border-color: {MACOS_BLUE}; background: #F0F5FF; }}
    """


def checkbox_style() -> str:
    """Shared macOS-style QCheckBox stylesheet."""
    return f"""
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
    """


def lineedit_style() -> str:
    """Shared macOS-style QLineEdit stylesheet."""
    return f"""
        QLineEdit {{
            border: 1px solid {MACOS_BORDER}; border-radius: 8px;
            padding: 8px 12px; font-size: 13px; font-family: monospace;
            background: white; min-width: 100px;
        }}
        QLineEdit:focus {{
            border-color: {MACOS_BLUE};
            background: #F0F5FF;
        }}
    """


def progress_style() -> str:
    """Indeterminate progress bar style."""
    return f"""
        QProgressBar {{
            border: none; border-radius: 2px;
            background: {MACOS_SEPARATOR};
        }}
        QProgressBar::chunk {{
            background: {MACOS_BLUE}; border-radius: 2px;
        }}
    """
