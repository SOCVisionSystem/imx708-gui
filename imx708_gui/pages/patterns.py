# SPDX-License-Identifier: GPL-2.0-only
"""
Test patterns page.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QPushButton, QSpinBox, QGridLayout,
)

from ..theme import *
from ..widgets import (
    make_header, make_description, make_group_box, make_icon, spinbox_style,
)
from ..grpc_client import GrpcClient


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
        layout.addWidget(make_description(
            "Select a test pattern to verify sensor output and signal integrity."))

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

        grid.setColumnStretch(3, 1)
        layout.addLayout(grid)

        # Color controls
        color_group = make_group_box("Solid Color Settings")
        color_layout = QFormLayout(color_group)
        color_layout.setSpacing(8)
        color_layout.setLabelAlignment(Qt.AlignRight)

        self.color_r = QSpinBox()
        self.color_r.setRange(0, 0xFFF)
        self.color_r.setValue(0xFFF)
        self.color_r.setToolTip("Red channel value (0\u20134095)")
        self.color_r.setStyleSheet(spinbox_style())
        color_layout.addRow(QLabel("Red"), self.color_r)

        self.color_b = QSpinBox()
        self.color_b.setRange(0, 0xFFF)
        self.color_b.setValue(0xFFF)
        self.color_b.setToolTip("Blue channel value (0\u20134095)")
        self.color_b.setStyleSheet(spinbox_style())
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
