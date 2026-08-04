# SPDX-License-Identifier: GPL-2.0-only
"""
Info page — sensor specifications and about.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
)

from ..theme import *
from ..widgets import make_header, make_description, make_group_box
from ..grpc_client import GrpcClient


class InfoPage(QWidget):
    """Sensor specifications, driver features, and about."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_header("Sensor Information"))
        layout.addWidget(make_description(
            "Technical specifications for the Sony IMX708 image sensor."))

        # Sensor specs
        specs_group = make_group_box("Sensor Specifications")
        specs_layout = QFormLayout(specs_group)
        specs_layout.setSpacing(6)
        specs_layout.setLabelAlignment(Qt.AlignRight)

        specs = [
            ("Sensor", "Sony IMX708-AAJH5-C"),
            ("Resolution", "11.9 MP (4608 \u00d7 2592 active)"),
            ("Pixel Size", "1.4 \u00b5m"),
            ("Optical Format", "1/2.43\""),
            ("Output", "MIPI CSI-2 (4-lane / 2-lane)"),
            ("Bit Depth", "10-bit RAW (RAW10)"),
            ("Frame Rate", "Up to 56 fps (full res), 120 fps (720p)"),
            ("HDR", "2-exposure line-interleaved (up to 4\u00d7 ratio)"),
            ("PDAF", "On-chip phase detection (12\u00d716 grid)"),
            ("I2C Address", "0x1a (fixed)"),
            ("Input Clock", "24 MHz"),
            ("Temperature Range", "\u221220\u00b0C to +80\u00b0C"),
        ]

        for label, value in specs:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {MACOS_SECONDARY}; font-size: 12px; font-weight: 500;")
            val = QLabel(value)
            val.setStyleSheet(f"color: {MACOS_TEXT}; font-size: 13px;")
            val.setWordWrap(True)
            specs_layout.addRow(lbl, val)

        layout.addWidget(specs_group)

        # Mode table
        modes_group = make_group_box("Supported Modes")
        modes_layout = QVBoxLayout(modes_group)

        self.mode_table = QTableWidget(0, 5)
        self.mode_table.setHorizontalHeaderLabels(
            ["Width", "Height", "FPS", "Pixel Rate", "HBlank"])
        self.mode_table.horizontalHeader().setStretchLastSection(True)
        self.mode_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {MACOS_BORDER}; border-radius: 8px;
                font-size: 12px; color: {MACOS_TEXT};
                background: white; gridline-color: {MACOS_SEPARATOR};
            }}
            QHeaderView::section {{
                background: {MACOS_BG}; color: {MACOS_SECONDARY};
                font-weight: 600; padding: 6px;
                border: none; border-bottom: 1px solid {MACOS_BORDER};
            }}
        """)
        self.mode_table.setAlternatingRowColors(True)
        self.mode_table.verticalHeader().setVisible(False)
        self.mode_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.mode_table.setSelectionMode(QTableWidget.NoSelection)

        modes_layout.addWidget(self.mode_table)
        layout.addWidget(modes_group)

        # Populate modes
        self._populate_modes()
        layout.addStretch()

    def _populate_modes(self):
        modes = self.client.get_modes()
        if not modes:
            return

        self.mode_table.setRowCount(len(modes))
        for i, m in enumerate(modes):
            self.mode_table.setItem(i, 0, QTableWidgetItem(str(m['width'])))
            self.mode_table.setItem(i, 1, QTableWidgetItem(str(m['height'])))
            self.mode_table.setItem(i, 2, QTableWidgetItem(str(m['fps'])))
            pr = f"{m.get('pixel_rate', 0) / 1e6:.1f} MHz" if m.get('pixel_rate') else "\u2014"
            self.mode_table.setItem(i, 3, QTableWidgetItem(pr))
            self.mode_table.setItem(i, 4, QTableWidgetItem(str(m.get('hblank', 0))))

        self.mode_table.resizeColumnsToContents()
