# Changelog

## 0.1.0 (2026-08-04)

### Added
- macOS-inspired PySide6 desktop application
- Custom MacSlider widget with gradient fill and rounded knob
- Sidebar navigation with 7 screens (Dashboard, Controls, Capture,
  Image Processing, Test Patterns, Registers, Info)
- Thread-safe GrpcClient with Qt signals for cross-thread communication
- Real-time telemetry via gRPC streaming
- Frame capture with burst mode and save to file
- Full sensor control (gain, exposure, HDR, test patterns, ISP)
- Register read/write with read history
- Sensor info page with mode table
- Standalone executable via PyInstaller
- System-wide install support (.desktop file, wrapper script)
- QSettings persistence for window geometry
- IMX708_SERVER environment variable support
- gRPC stubs generation via protoc

### Fixed
- QCursor import from QtWidgets instead of QtGui
- pyproject.toml package discovery (packages.find → py-modules)
- Makefile proto output directory (build/ → imx708_proto/)
- Protoc failure no longer silently swallowed
- CSS scoping on card widgets (unscoped QFrame rules)
- GroupBox title ampersand escaping
- Capture page now runs in background thread
- Pinned dependency versions to prevent import errors
