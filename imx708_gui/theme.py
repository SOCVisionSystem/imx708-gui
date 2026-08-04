# SPDX-License-Identifier: GPL-2.0-only
"""
Theme tokens, SVG icons, and shared style helpers for the IMX708 GUI.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

# ── macOS Design Tokens ────────────────────────────────────────────────────
MACOS_BG        = "#F5F5F7"
MACOS_SIDEBAR   = "#F2F2F7"
MACOS_CARD      = "#FFFFFF"
MACOS_BORDER    = "#D2D2D7"
MACOS_SEPARATOR = "#E5E5EA"
MACOS_TEXT      = "#1D1D1F"
MACOS_SECONDARY = "#6E6E73"
MACOS_TERTIARY  = "#AEAEB2"
MACOS_BLUE      = "#007AFF"
MACOS_GREEN     = "#30D158"
MACOS_RED       = "#FF3B30"
MACOS_ORANGE    = "#FF9F0A"
MACOS_PURPLE    = "#AF52DE"
MACOS_GRAY      = "#8E8E93"

# ── SVG Icons (SF Symbols style) ──────────────────────────────────────────
ICON_CAMERA = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
  <circle cx="12" cy="13" r="4"/>
</svg>"""

ICON_SLIDERS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
  <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
  <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
  <line x1="2" y1="14" x2="6" y2="14"/><line x1="10" y1="8" x2="14" y2="8"/>
  <line x1="18" y1="16" x2="22" y2="16"/>
</svg>"""

ICON_CAPTURE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6" fill="currentColor" opacity="0.3"/><circle cx="12" cy="12" r="3"/>
</svg>"""

ICON_PALETTE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="13.5" cy="6.5" r="1.5" fill="currentColor" opacity="0.4"/>
  <circle cx="17.5" cy="10.5" r="1.5" fill="currentColor" opacity="0.4"/>
  <circle cx="8.5" cy="7.5" r="1.5" fill="currentColor" opacity="0.4"/>
  <circle cx="6.5" cy="12.5" r="1.5" fill="currentColor" opacity="0.4"/>
  <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-1 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-5.52-4.5-10-10-10z"/>
</svg>"""

ICON_GRID = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
  <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
</svg>"""

ICON_TERMINAL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>
</svg>"""

ICON_INFO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
</svg>"""

ICON_WIFI = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/>
  <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1.5" fill="currentColor"/>
</svg>"""

ICON_PLAY = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"/></svg>"""

ICON_STOP = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="5" width="14" height="14" rx="3"/></svg>"""

ICON_RESET = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
</svg>"""

ICON_CHECK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="20 6 9 17 4 12"/>
</svg>"""

ICON_DOWNLOAD = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
</svg>"""

ICON_REFRESH = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
</svg>"""

ICON_CONNECT = ICON_WIFI


def make_icon(svg: str, size: int = 22, color: str = "#555") -> QIcon:
    """Create a crisp QIcon from SVG data with proper rendering."""
    colored = svg.replace('currentColor', color)
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer = QSvgRenderer(QByteArray(colored.encode()))
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
