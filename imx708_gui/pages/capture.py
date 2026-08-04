# SPDX-License-Identifier: GPL-2.0-only
"""
Capture page — frame capture with preview and save.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

import threading
from typing import Optional, Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QComboBox, QSpinBox, QTextEdit, QProgressBar, QFileDialog,
)

from ..theme import *
from ..widgets import (
    make_header, make_description, make_group_box, make_primary_button,
    make_secondary_button, make_icon, combo_style, progress_style,
)
from ..grpc_client import GrpcClient


class CapturePage(QWidget):
    """Frame capture and save with preview."""

    _capture_finished = Signal(list)

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self._last_frame: Optional[Dict] = None
        self.setup_ui()
        self._capture_finished.connect(self._on_capture_finished)

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
            QSpinBox::up-button, QSpinBox::down-button {{ border: none; width: 20px; }}
        """)
        cap_layout.addRow(QLabel("Number of Frames"), self.cap_count)

        self.cap_format = QComboBox()
        self.cap_format.addItems(["RAW10", "PGM"])
        self.cap_format.setToolTip("Output format for captured frames")
        self.cap_format.setStyleSheet(combo_style())
        cap_layout.addRow(QLabel("Format"), self.cap_format)

        btn_row = QHBoxLayout()
        self.capture_btn = make_primary_button("  Capture", ICON_CAPTURE)
        self.capture_btn.clicked.connect(self._capture)

        self.save_btn = make_secondary_button("  Save to File...", ICON_DOWNLOAD)
        self.save_btn.clicked.connect(self._save)
        self.save_btn.setEnabled(False)

        self.capture_loading = QProgressBar()
        self.capture_loading.setRange(0, 0)
        self.capture_loading.setFixedSize(120, 4)
        self.capture_loading.setTextVisible(False)
        self.capture_loading.setStyleSheet(progress_style())
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

    def _capture(self):
        if not self.client.connected:
            return
        self.capture_btn.setEnabled(False)
        self.capture_loading.show()

        count = self.cap_count.value()

        def _do_capture():
            frames = []
            for _ in range(count):
                frame = self.client.capture_frame()
                if frame:
                    frames.append(frame)
            self._capture_finished.emit(frames)

        threading.Thread(target=_do_capture, daemon=True).start()

    def _on_capture_finished(self, frames: list):
        self.capture_loading.hide()
        self.capture_btn.setEnabled(True)

        if frames:
            self._last_frame = frames[-1]
            data_size = len(frames[0].get('data', b''))
            self.frame_info.setText(
                f"Captured {len(frames)} frame(s)\n"
                f"Size: {frames[0]['width']}\u00d7{frames[0]['height']}\n"
                f"Data: {data_size:,} bytes\n"
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
