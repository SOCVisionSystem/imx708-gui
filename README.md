# imx708-gui

Cross-platform PySide6 desktop application for controlling the Sony IMX708
camera sensor over gRPC. macOS-inspired design with real-time telemetry
and full sensor control.

## Summary

The imx708-gui is a cross-platform desktop application built with PySide6
that provides a beautiful macOS-inspired interface for controlling the
Sony IMX708 camera sensor over gRPC. The application connects to the
imx708-server gRPC daemon and provides real-time telemetry display, full
sensor configuration, frame capture, and diagnostic tools through an
intuitive sidebar navigation system. The GUI is structured as a Python
package with 13 modules including a theme system with macOS design tokens
and SVG icons, custom-painted widgets like the MacSlider with gradient
fill and rounded knob, and a thread-safe GrpcClient that uses Qt signals
for cross-thread communication. Seven screens provide access to all
sensor features: a Dashboard with live status cards and connection
controls, Controls with gain/exposure/HDR sliders, Capture with frame
acquisition and save-to-file, Image Processing with brightness, contrast,
white balance, and flip controls, Test Patterns with a 5-pattern grid
selector, Registers with known register quick-access and custom read/write
with history, and Info with sensor specifications and a mode table. The
application supports standalone executable builds via PyInstaller with
system-wide install support including a .desktop file for the application
menu and a wrapper script. Window geometry is persisted via QSettings,
and the server address can be configured via command-line argument or the
IMX708_SERVER environment variable.

## Features

- macOS-inspired design with custom-painted MacSlider widget featuring
  gradient fill, rounded knob, and drop shadow
- Sidebar navigation with 7 screens: Dashboard, Controls, Capture, Image
  Processing, Test Patterns, Registers, and Info
- SVG icons rendered at 2x resolution for crisp display on retina screens
- Thread-safe GrpcClient using Qt signals for cross-thread communication
  with auto-reconnect on stream drop
- Real-time telemetry via gRPC streaming with live status cards for
  temperature, streaming state, PLL lock, and frame count
- Dashboard with connect/disconnect, start/stop stream, and soft reset
  controls with loading indicator
- Analog gain slider with range 0-960 and digital gain slider with range
  256-65535
- Exposure slider with range 8-65535 line units and HDR mode toggle
- Frame capture with single and burst mode up to 100 frames
- Save captured frames to file with custom filename and location
- Image processing controls for brightness, contrast, saturation, hue,
  sharpness, and gamma
- White balance with auto/manual toggle and color temperature from
  2800K to 10000K
- Horizontal and vertical flip controls
- Test pattern grid with 5 patterns: Disabled, Color Bars, Solid Color,
  Grey Bars, and PN9
- Per-channel color component control for solid color patterns
- Register read/write with known register quick-access buttons for 10
  key registers
- Custom register read/write with hex input and read history log
- Sensor info page with specifications table and supported modes table
- Standalone executable via PyInstaller with 143 MB self-contained binary
- System-wide install support with .desktop file, wrapper script, and
  app icon
- QSettings persistence for window geometry across sessions
- IMX708_SERVER environment variable for server address configuration
- gRPC stubs generation via protoc with Makefile and build.sh automation
- Pinned dependency versions in requirements.txt and pyproject.toml with
  uv.lock for reproducible installs
- SPDX license headers on every source file with GPL-2.0-only licensing
