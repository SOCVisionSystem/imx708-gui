# SPDX-License-Identifier: GPL-2.0-only
"""
Dashboard page — real-time sensor telemetry and controls.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

import threading
from typing import Dict

from PySide6.QtCore import Qt, QMetaObject, Q_ARG, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QProgressBar, QMessageBox, QApplication,
)

from ..theme import *
from ..widgets import (
    make_header, make_card, make_group_box, make_primary_button,
    make_secondary_button, make_icon, progress_style,
)
from ..grpc_client import GrpcClient


class DashboardPage(QWidget):
    """Elegant dashboard showing sensor status in real-time."""

    def __init__(self, client: GrpcClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()
        self.client.status_updated.connect(self._update_status)
        self.client.connection_changed.connect(self._on_connection_changed)

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
            ("temperature", "Temperature", "0\u00b0C", MACOS_ORANGE, ICON_TERMINAL,
             "Current sensor temperature in degrees Celsius"),
            ("streaming", "Streaming", "Stopped", MACOS_RED, ICON_PLAY,
             "Whether the sensor is actively streaming frames"),
            ("pll", "PLL Lock", "Unlocked", MACOS_RED, ICON_WIFI,
             "Phase-Locked Loop lock status"),
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
        self.res_label = QLabel("\u2014")
        self.fps_label = QLabel("\u2014")

        for label, widget, tooltip in [
            ("Analog Gain", self.gain_label, "Current analog gain value (0\u2013960)"),
            ("Digital Gain", self.dgain_label, "Current digital gain value (256\u201365535)"),
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

        # Action bar
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
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
        self.reset_btn.setToolTip("Perform a soft reset of the sensor")
        self.reset_btn.setFixedHeight(40)
        self.reset_btn.clicked.connect(self._soft_reset)
        self.reset_btn.setEnabled(False)

        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setFixedSize(120, 4)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setStyleSheet(progress_style())
        self.loading_bar.hide()

        action_layout.addWidget(self.connect_btn)
        action_layout.addWidget(self.stream_btn)
        action_layout.addWidget(self.reset_btn)
        action_layout.addWidget(self.loading_bar)
        action_layout.addStretch()

        layout.addLayout(action_layout)
        layout.addStretch()

    def _update_status(self, status: Dict):
        temp = status.get('temperature', 0)
        streaming = status.get('streaming', False)
        pll = status.get('pll_locked', False)
        frames = status.get('frame_count', 0)

        self.status_cards['temperature'].findChild(QLabel, "card_value").setText(f"{temp}\u00b0C")
        self.status_cards['streaming'].findChild(QLabel, "card_value").setText(
            "Active" if streaming else "Stopped")
        self.status_cards['pll'].findChild(QLabel, "card_value").setText(
            "Locked" if pll else "Unlocked")
        self.status_cards['frames'].findChild(QLabel, "card_value").setText(str(frames))

        self.status_cards['streaming'].findChild(QLabel, "card_value").setStyleSheet(
            f"color: {MACOS_GREEN if streaming else MACOS_RED}; font-size: 20px; font-weight: 700;")
        self.status_cards['pll'].findChild(QLabel, "card_value").setStyleSheet(
            f"color: {MACOS_GREEN if pll else MACOS_RED}; font-size: 20px; font-weight: 700;")

        self.gain_label.setText(f"{status.get('gain', 0)}")
        self.dgain_label.setText(f"{status.get('digital_gain', 0)}")
        self.exposure_label.setText(str(status.get('exposure', 0)))
        w = status.get('width', 0)
        h = status.get('height', 0)
        self.res_label.setText(f"{w}\u00d7{h}" if w and h else "\u2014")
        self.fps_label.setText(f"{status.get('fps', 0)} fps")

    def _on_connection_changed(self, connected: bool):
        if not connected and self.client.connected:
            # Connection was lost — update UI state
            self.connect_btn.setText("  Connect")
            self.connect_btn.setIcon(make_icon(ICON_CONNECT, 16, "#FFFFFF"))
            self.stream_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
            self.stream_btn.setText("  Start Stream")
            self.stream_btn.setIcon(make_icon(ICON_PLAY, 16, MACOS_TEXT))

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
