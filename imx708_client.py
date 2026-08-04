# SPDX-License-Identifier: GPL-2.0-only
"""
IMX708 GUI — Cross-platform PySide6 desktop client for Sony IMX708 camera sensor.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>

Usage:
    python imx708_client.py [--server localhost:50051]
"""

import sys
import os
import argparse

from PySide6.QtWidgets import QApplication

from imx708_gui.main_window import MainWindow


def main():
    parser = argparse.ArgumentParser(
        description="IMX708 Camera Sensor GUI Client")
    parser.add_argument(
        "--server", default=os.environ.get("IMX708_SERVER", "localhost:50051"),
        help="gRPC server address (host:port, default: localhost:50051)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("IMX708 Camera")
    app.setOrganizationName("SoC Centric")
    app.setOrganizationDomain("soccentric.com")

    window = MainWindow(server_addr=args.server)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
