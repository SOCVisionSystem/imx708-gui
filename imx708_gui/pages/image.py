# SPDX-License-Identifier: GPL-2.0-only
"""
Image page — brightness, contrast, white balance, flip controls.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QSpinBox, QCheckBox,
)

from ..theme import *
from ..widgets import (
    make_header, make_description, make_group_box, make_primary_button,
    make_secondary_button, make_icon, spinbox_style, checkbox_style,
)
from ..grpc_client import GrpcClient


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
        layout.addWidget(make_description(
            "Adjust brightness, contrast, white balance, and more."))

        # Adjustments
        adj_group = make_group_box("Adjustments")
        adj_layout = QFormLayout(adj_group)
        adj_layout.setSpacing(8)
        adj_layout.setLabelAlignment(Qt.AlignRight)

        for name, label, lo, hi in self.SLIDERS:
            spin = QSpinBox()
            spin.setRange(lo, hi)
            spin.setToolTip(f"{label}: range {lo} to {hi}")
            spin.setStyleSheet(spinbox_style())
            self.spins[name] = spin
            adj_layout.addRow(QLabel(label), spin)

        layout.addWidget(adj_group)

        # White Balance & Orientation
        wb_group = make_group_box("White Balance && Orientation")
        wb_layout = QFormLayout(wb_group)
        wb_layout.setSpacing(8)
        wb_layout.setLabelAlignment(Qt.AlignRight)

        self.auto_wb_check = QCheckBox("Automatic white balance")
        self.auto_wb_check.setChecked(True)
        self.auto_wb_check.setToolTip("Automatically adjust white balance")
        self.auto_wb_check.setStyleSheet(checkbox_style())
        self.auto_wb_check.toggled.connect(self._on_auto_wb_toggled)
        wb_layout.addRow(self.auto_wb_check)

        self.wb_spin = QSpinBox()
        self.wb_spin.setRange(2800, 10000)
        self.wb_spin.setValue(6500)
        self.wb_spin.setSuffix(" K")
        self.wb_spin.setEnabled(False)
        self.wb_spin.setToolTip("White balance color temperature (2800K\u201310000K)")
        self.wb_spin.setStyleSheet(spinbox_style())
        wb_layout.addRow(QLabel("Temperature"), self.wb_spin)

        self.hflip_check = QCheckBox("Horizontal flip")
        self.hflip_check.setToolTip("Mirror the image horizontally")
        self.hflip_check.setStyleSheet(checkbox_style())
        self.vflip_check = QCheckBox("Vertical flip")
        self.vflip_check.setToolTip("Mirror the image vertically")
        self.vflip_check.setStyleSheet(checkbox_style())
        wb_layout.addRow(self.hflip_check)
        wb_layout.addRow(self.vflip_check)

        layout.addWidget(wb_group)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        refresh_btn = make_secondary_button("  Refresh", ICON_REFRESH)
        refresh_btn.setToolTip("Refresh current settings from the sensor")
        refresh_btn.clicked.connect(self.refresh)
        apply_btn = make_primary_button("  Apply", ICON_CHECK)
        apply_btn.setToolTip("Apply all settings to the sensor")
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
