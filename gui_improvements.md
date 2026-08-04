# GUI Design & Verification Standard

This project's PySide6 UI standard has moved out of this file and into a
personal Claude Code skill so it applies to every GUI project automatically,
not just this one:

```
~/.claude/skills/pyside6-elegant-gui/SKILL.md
~/.claude/skills/pyside6-elegant-gui/references/design-system.md
~/.claude/skills/pyside6-elegant-gui/references/pitfalls.md
```

`design-system.md` is this file's original content (spacing, typography,
color, icons, sidebar/toolbar/menu-bar patterns, pre-ship checklist),
carried over unchanged in substance. `pitfalls.md` is new: a catalog of the
specific Qt/PySide6 defects found and fixed in `imx708_client.py` during the
2026-08-04 elegance/correctness pass (QSS selector-leak bugs, a
paintEvent crash, layout stretch traps, `QListWidget` row-sizing quirks,
threading freezes, PyInstaller packaging bugs, and more) — each with the
exact rule and fix, so they don't get reintroduced or repeated in another
project.

Claude Code loads this skill automatically for PySide6/PyQt work in any
project on this machine; there's nothing project-specific left to keep
here.
