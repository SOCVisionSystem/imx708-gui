# SPDX-License-Identifier: GPL-2.0-only
"""
Main window — orchestrates sidebar navigation and page switching.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

import sys
import os
from typing import List

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QStatusBar, QLabel,
)

from .theme import *
from .widgets import SidebarWidget
from .grpc_client import GrpcClient
from .pages.dashboard import DashboardPage
from .pages.controls import ControlsPage
from .pages.capture import CapturePage
from .pages.image import ImagePage
from .pages.patterns import TestPatternPage
from .pages.registers import RegisterPage
from .pages.info import InfoPage


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(self, server_addr: str = "localhost:50051"):
        super().__init__()
        self.server_addr = server_addr
        self.client = GrpcClient(server_addr)
        self.pages: List[QWidget] = []

        self._init_window()
        self._init_ui()
        self._connect_signals()
        self._restore_settings()

    def _init_window(self):
        self.setWindowTitle("IMX708 Camera")
        self.setMinimumSize(900, 620)
        self.resize(1100, 720)
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {MACOS_BG};
            }}
            QStatusBar {{
                background: {MACOS_SIDEBAR};
                border-top: 1px solid {MACOS_BORDER};
                font-size: 12px; color: {MACOS_SECONDARY};
            }}
        """)

    def _init_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = SidebarWidget()
        main_layout.addWidget(self.sidebar)

        # Stacked pages
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)

        # Create pages
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

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Disconnected")
        self.status_bar.addPermanentWidget(self.status_label)

        self.log_label = QLabel("")
        self.status_bar.addWidget(self.log_label, 1)

    def _connect_signals(self):
        self.sidebar.page_changed.connect(self.stack.setCurrentIndex)
        self.client.connection_changed.connect(self._on_connection_changed)
        self.client.log_message.connect(self._on_log_message)

    def _on_connection_changed(self, connected: bool):
        self.sidebar.set_connected(connected)
        self.status_label.setText("Connected" if connected else "Disconnected")
        self.status_label.setStyleSheet(
            f"color: {MACOS_GREEN}; font-weight: 600;" if connected
            else f"color: {MACOS_RED}; font-weight: 600;"
        )

    def _on_log_message(self, msg: str):
        self.log_label.setText(msg)

    def _restore_settings(self):
        settings = QSettings("SoC Centric", "IMX708 Camera")
        geometry = settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        settings = QSettings("SoC Centric", "IMX708 Camera")
        settings.setValue("window/geometry", self.saveGeometry())
        self.client.disconnect()
        super().closeEvent(event)
