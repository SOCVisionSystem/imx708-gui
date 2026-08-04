# SPDX-License-Identifier: GPL-2.0-only
"""
Registers page — direct register read/write for debugging.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QPushButton, QLineEdit, QTextEdit, QGridLayout,
)

from ..theme import *
from ..widgets import (
    make_header, make_description, make_group_box, make_icon,
    make_primary_button, lineedit_style,
)
from ..grpc_client import GrpcClient


class RegisterPage(QWidget):
    """Raw register read/write."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self._read_history: list = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_header("Register Access"))
        layout.addWidget(make_description(
            "Read and write sensor registers directly. Requires root on the server."))

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
        self.reg_addr.setStyleSheet(lineedit_style())
        addr_val_layout.addWidget(self.reg_addr)

        self.reg_val = QLineEdit("0x00")
        self.reg_val.setStyleSheet(lineedit_style())

        read_btn = make_primary_button("Read", ICON_REFRESH)
        read_btn.clicked.connect(lambda: self._read_custom())
        write_btn = make_primary_button("Write", ICON_CHECK)
        write_btn.clicked.connect(lambda: self._write_custom())

        addr_val_layout.addWidget(self.reg_val)
        addr_val_layout.addWidget(read_btn)
        addr_val_layout.addWidget(write_btn)
        addr_val_layout.addStretch()
        custom_layout.addRow(QLabel("Address / Value"), addr_val_layout)

        layout.addWidget(custom_group)

        # Read history
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMaximumHeight(200)
        self.history_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {MACOS_BORDER}; border-radius: 10px;
                padding: 12px; font-size: 12px; font-family: monospace;
                color: {MACOS_SECONDARY}; background: white;
            }}
        """)
        self.history_text.setText("Read history will appear here")
        layout.addWidget(self.history_text)
        layout.addStretch()

    def _read_reg(self, addr: int):
        if not self.client.connected:
            return
        val = self.client.read_register(addr)
        if val is not None:
            entry = f"0x{addr:04X} \u2192 0x{val:04X}"
            self._read_history.append(entry)
            self.history_text.setText("\n".join(self._read_history[-20:]))

    def _read_custom(self):
        try:
            addr = int(self.reg_addr.text(), 16)
            if addr > 0xFFFF:
                return
            self._read_reg(addr)
        except ValueError:
            pass

    def _write_custom(self):
        if not self.client.connected:
            return
        try:
            addr = int(self.reg_addr.text(), 16)
            val = int(self.reg_val.text(), 16)
            if addr > 0xFFFF or val > 0xFF:
                return
            self.client.write_register(addr, val)
            entry = f"0x{addr:04X} \u2190 0x{val:02X}"
            self._read_history.append(entry)
            self.history_text.setText("\n".join(self._read_history[-20:]))
        except ValueError:
            pass
