# SPDX-License-Identifier: GPL-2.0-only
"""
Controls page — gain, exposure, HDR settings.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QComboBox,
)

from ..theme import *
from ..widgets import (
    make_header, make_description, make_group_box, make_primary_button,
    MacSlider, combo_style,
)
from ..grpc_client import GrpcClient


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
        layout.addWidget(make_description(
            "Adjust gain, exposure, and HDR settings for the IMX708 sensor."))

        # Gain control
        gain_group = make_group_box("Gain Control")
        gain_layout = QFormLayout(gain_group)
        gain_layout.setSpacing(12)
        gain_layout.setLabelAlignment(Qt.AlignRight)

        self.gain_slider = MacSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 960)
        self.gain_slider.setValue(0)
        self.gain_slider.setAccentColor(MACOS_BLUE)
        self.gain_slider.setToolTip("Analog gain: 0\u2013960 (higher = brighter)")

        gain_val_layout = QHBoxLayout()
        self.gain_value = QLabel("0")
        self.gain_value.setStyleSheet(f"color: {MACOS_BLUE}; font-size: 14px; font-weight: 700;")
        self.gain_value.setFixedWidth(50)
        gain_val_layout.addWidget(self.gain_slider)
        gain_val_layout.addWidget(self.gain_value)
        self.gain_slider.valueChanged.connect(lambda v: self.gain_value.setText(str(v)))
        gain_layout.addRow(QLabel("Analog Gain"), gain_val_layout)

        self.dgain_slider = MacSlider(Qt.Horizontal)
        self.dgain_slider.setRange(0x100, 0xFFFF)
        self.dgain_slider.setValue(0x100)
        self.dgain_slider.setAccentColor(MACOS_PURPLE)
        self.dgain_slider.setToolTip("Digital gain: 256\u201365535 (higher = brighter)")

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
        apply_gain_row = QHBoxLayout()
        apply_gain_row.addWidget(apply_gain)
        apply_gain_row.addStretch()
        gain_layout.addRow("", apply_gain_row)
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
        self.exp_slider.setToolTip("Exposure: 8\u201365535 line units (higher = longer exposure)")

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
        apply_exp_row = QHBoxLayout()
        apply_exp_row.addWidget(apply_exp)
        apply_exp_row.addStretch()
        exp_layout.addRow("", apply_exp_row)
        layout.addWidget(exp_group)

        # HDR control
        hdr_group = make_group_box("HDR Mode")
        hdr_layout = QFormLayout(hdr_group)
        hdr_layout.setSpacing(12)
        hdr_layout.setLabelAlignment(Qt.AlignRight)

        self.hdr_combo = QComboBox()
        self.hdr_combo.addItems(["Off", "On"])
        self.hdr_combo.setToolTip("Enable or disable High Dynamic Range mode")
        self.hdr_combo.setStyleSheet(combo_style())
        hdr_layout.addRow(QLabel("HDR Mode"), self.hdr_combo)

        apply_hdr = make_primary_button("Apply HDR", ICON_CHECK)
        apply_hdr.setToolTip("Send the HDR mode selection to the sensor")
        apply_hdr.clicked.connect(self._apply_hdr)
        apply_hdr_row = QHBoxLayout()
        apply_hdr_row.addWidget(apply_hdr)
        apply_hdr_row.addStretch()
        hdr_layout.addRow("", apply_hdr_row)
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
