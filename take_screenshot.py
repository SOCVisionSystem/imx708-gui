#!/usr/bin/env python3
"""
Take a screenshot of the IMX708 GUI after it has fully rendered.
Usage: python3 take_screenshot.py [--server host:port]
"""
import sys
import os
import time
import argparse

# Add build dir to path for proto stubs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'build'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'imx708_proto'))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QWindow
from PySide6.QtWidgets import QApplication

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', default='localhost:50051')
    parser.add_argument('--output', default='screenshot.png')
    args = parser.parse_args()

    # Set server address before importing the client
    os.environ['IMX708_SERVER'] = args.server

    app = QApplication(sys.argv)

    # Import the main window AFTER QApplication is created
    from imx708_client import MainWindow

    window = MainWindow()
    window.show()

    # Wait for the window to fully render
    def capture():
        # Process events to ensure full render
        app.processEvents()
        time.sleep(0.5)
        app.processEvents()

        # Grab the window
        screen = app.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(window.winId())
            pixmap.save(args.output, 'PNG')
            print(f"Screenshot saved to {args.output} ({pixmap.width()}x{pixmap.height()})")
        else:
            print("ERROR: No primary screen found")
        app.quit()

    QTimer.singleShot(2000, capture)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
