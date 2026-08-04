# Contributing to imx708-gui

Thanks for your interest! This is a PySide6 desktop application for the
IMX708 camera sensor. We welcome bug reports, documentation, UI improvements,
and code.

## Quick Start

```bash
git clone https://github.com/SOCVisionSystem/imx708.git
cd imx708/imx708-gui
make deps
make all
make run
```

## Coding Style

- Type hints on all function signatures
- Qt signals for cross-thread communication
- Design tokens in `imx708_gui/theme.py` — never hardcode colors
- Widget factories in `imx708_gui/widgets.py` — never inline stylesheets
- Each page is a separate module in `imx708_gui/pages/`
- SPDX license header on every file

## Pull Request Process

1. Fork the repo, create a feature branch
2. Make your changes
3. Run `make all` to verify stubs generate
4. Submit a PR with a clear description

## Good First Issues

- Dark mode theme
- Frame preview rendering
- Keyboard shortcuts
- Settings persistence improvements
- Unit tests for GrpcClient

## License

GPL-2.0-only. By contributing, you agree to license your contributions
under the same license.
