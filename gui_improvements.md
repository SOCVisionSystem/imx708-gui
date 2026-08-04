---
name: pyside6-elegant-ui
description: Use this skill when building, styling, or reviewing a PySide6 desktop application UI (Mac/Windows/Linux) to achieve a polished, native macOS-style light theme — sidebar navigation, top action bar, full menu bar, typography, spacing, and icon rules. Trigger on requests to "make this app look better", "style my PySide6 app", "fix the UI/theme", or any PySide6 visual/UX design task.
---

# PySide6 Elegant Cross-Platform Desktop UI

## Purpose
Produce a PySide6 desktop app (macOS/Windows/Linux) that looks native, deliberate,
and premium — a 9/10 first impression. This is a design/engineering ruleset,
not a one-off style guide. Apply it to every screen, every widget, every state.

## Core Philosophy
- Every pixel is a decision — no default-Qt widget ships unstyled.
- Consistency beats cleverness: one spacing system, one type scale, one icon
  set, one accent color, applied everywhere with no exceptions.
- Whitespace is a feature. Cramped UI reads as amateur; generous spacing reads
  as premium.
- Native feel over "web dashboard in a desktop window." Mimic macOS HIG
  (System Settings / Big Sur–Sonoma era) as the baseline reference.

---

## 1. Layout & Spacing — Zero-Cramp Rule
**Must do**
- 8px base grid for all margins/padding (8, 12, 16, 24, 32). No arbitrary values.
- Outer window/container padding: 16–24px minimum — content never touches edges.
- Card/panel internal padding: 16–20px all sides, 8–10px corner radius.
- Sibling widget gaps: 8px (tight groups, e.g. icon+label), 12–16px (related
  fields), 24–32px (separate sections).
- Explicit `setSpacing()` and `setContentsMargins()` on every layout — never
  rely on Qt defaults (inconsistent across platforms, often 0).
- Forms: consistent label→input gap (4–6px), row→row gap (12–16px), labels
  aligned the same way (right- or top-aligned) everywhere — never mixed.
- Scrollable areas get internal padding; content never hugs the scrollbar or
  viewport edge.
- Test every screen at minimum window size — spacing must hold on resize, no
  elements slamming together.

**Must not do**
- Never let two widgets touch at 0px gap unless intentionally one visual unit
  (e.g. a segmented control).
- Never `setContentsMargins(0,0,0,0)` on a top-level layout unless deliberately
  full-bleed (e.g. a toolbar strip).
- Never hardcode absolute widget positions — let layouts + `setMinimumSize()`
  on the window handle resize behavior.
- Never mix padding values arbitrarily across equivalent components.

---

## 2. Text — Zero-Clip Rule (non-negotiable)
- **Never let any label, button, or field clip, silently truncate, or wrap
  unexpectedly.** Every text container must be sized to its content, or
  content must be intentionally elided with `Qt::ElideRight` **plus** a
  tooltip showing the full string.
- Use `QFontMetrics` to measure text and size containers — never guess a
  fixed width.
- Buttons auto-size to label + icon + padding, unless part of a uniform
  button group — then size to the *longest* label in that group.
- Table/list columns: interactive resize enabled, minimum width derived from
  measured content, not a guessed constant.
- Test with the longest realistic string per field (including longer
  localized strings, not just English) — no overlap with icons, borders, or
  neighboring widgets.
- Menu items follow the same rule — no truncated menu text.

---

## 3. Typography
- One font family app-wide, bundled (e.g. Inter or equivalent) rather than
  relying on OS defaults, which differ visually across Mac/Windows/Linux.
- Fixed type scale — never ad hoc sizes:
  - Caption/meta: 12px
  - Body: 13–14px
  - Section header: 16px semibold
  - Page title: 20–22px semibold
- Weight discipline: regular for body, medium for labels/buttons, semibold
  for headers only. Never bold body text for emphasis — use color or a
  weight step instead.
- Set explicit `QFont` point sizes; disable any dynamic auto-scaling that
  causes inconsistent tiny/huge text between widgets.

---

## 4. Color & Theme (macOS Light)
- Background: `#F5F5F7` | Surface: `#FFFFFF` | Border: `#D1D1D6`
- Primary text: `#1D1D1F` | Secondary text: `#6E6E73`
- Accent (primary actions, active states, focus): `#007AFF`
- Destructive only (delete/stop-danger): `#FF3B30` — never decorative
- One accent color total, used consistently for: active tab, primary button,
  focus ring, selected state, links. No competing "brand" color.
- Disabled state: 40% opacity, no layout collapse — element keeps its slot.
- Never use pure black (`#000000`) text or unstyled native gray dialogs that
  clash with the rest of the theme.

---

## 5. Icons
- SVG only — crisp on Retina/HiDPI, never raster/PNG.
- One consistent icon set/style app-wide (same stroke width, same visual
  weight) — never mix filled and outline styles.
- Recolor icons programmatically per state (active/inactive/hover) rather
  than shipping separate colored files per state.
- Icon + label always vertically centered and baseline-aligned — check
  explicitly, Qt's default alignment is often off by a pixel or two.

---

## 6. Sidebar (Vertical Tab Navigation)
- Vertical icon+label tabs, fixed width (~72–220px, collapsible if feasible).
- Large tap targets: min 44–48px height, 12–16px padding.
- Active tab: filled rounded accent background or left accent bar, icon
  tinted accent color.
- Inactive tab: gray icon (`#8E8E93`), no background.
- Hover: light gray background (`#EFEFF4`).
- Implement as checkable/auto-exclusive buttons (tab-group behavior), icons
  via SVG resources for clean HiDPI scaling.

---

## 7. Top Action Bar (Start/Stop/etc.)
- Horizontal row of large action buttons (min 40–48px height).
- Icon (20–24px SVG) + short label, rounded rect background, 8px icon-label
  gap, 16–20px horizontal padding.
- Primary action (e.g. Start): filled accent, white icon/text.
- Secondary/neutral (e.g. Stop): outlined or neutral gray; red reserved for
  destructive/danger only.
- Disabled: 40% opacity, non-interactive.
- Same SVG icon set as sidebar — no mismatched icon styles across the app.

---

## 8. Menu Bar (File, Edit, View, Tools, Help, etc.)
- Use native `QMenuBar` — on macOS it merges into the system menu bar
  automatically; don't fight this with custom-drawn menus.
- Standard order: **File, Edit, View, Tools/[app-specific], Window (macOS),
  Help.**
- **File**: New, Open, Save, Save As, Recent Files, Preferences (Win/Linux
  only — macOS Preferences lives in the app menu), Import/Export, Quit.
- **Edit**: Undo, Redo, Cut, Copy, Paste, Select All, Find.
- **View**: Toggle sidebar/toolbar, zoom, theme toggle, layout options.
- **Tools**: app-specific utilities/settings.
- **Help**: Documentation, About, Check for Updates, Report Issue.
- Every action gets its platform-standard shortcut via
  `QKeySequence.StandardKey` (never hardcode `Ctrl+` — let Qt map
  Cmd/Ctrl correctly per OS).
- Group related items with separators; no long undifferentiated lists.
- Disable unavailable actions — never hide them (hiding reads as "feature is
  gone").
- Checkable items (e.g. "Show Sidebar") stay synced to actual app state via
  `setCheckable(True)` / `setChecked()`.
- Menu icons, if used, match the app's single SVG icon set.
- On macOS, set `QAction.MenuRole` correctly so About/Preferences/Quit route
  into the app menu automatically — never manually duplicate them under
  File/Edit.
- Menu bar = complete command set; toolbar/sidebar = frequent subset. Core
  actions should be reachable both ways, not menu-only.

---

## 9. Components — General Rules
- Buttons: min height 32px (secondary) / 40px (primary), 6–8px radius,
  icon+label with 8px gap.
- Inputs: min height 32–36px, 1px border, 6px radius, clear focus state
  (accent border + subtle glow).
- Every interactive element has 3 visible states minimum: default, hover,
  pressed/active — plus a focus state for keyboard navigation.
- Subtle transitions on hover/state-change (150–200ms) where Qt allows — no
  dead, instant state flips.
- Loading/busy states show a spinner/progress indicator and disable relevant
  controls — never freeze silently.
- Destructive/irreversible actions require a themed confirmation dialog, not
  a raw OS message box.
- Dialogs/popups use the same visual language (colors, type scale, spacing)
  as the main window.

---

## 10. Cross-Platform Discipline
- Test spacing and font rendering on all three OSes — Windows renders fonts
  heavier, Linux varies by desktop environment.
- Enable high-DPI scaling (`Qt.AA_EnableHighDpiScaling`); SVG-only icons so
  nothing blurs on Retina.
- Adjust per-platform only via explicit `platform.system()` branches — never
  assume visual parity across OSes.
- Don't fight native window chrome unless fully committing to a custom
  frameless window (proper drag regions, native traffic-light buttons on
  macOS).

---

## 11. Implementation Structure
- One centralized QSS theme file (`theme_light.qss`) loaded once at startup
  — no scattered inline `setStyleSheet()` calls.
- Reusable custom widget classes (`SidebarButton`, `ActionButton`, etc.) so
  sizing/spacing is enforced structurally, not per-instance.

---

## 12. Pre-Ship Checklist
Run this against every screen before calling it done:
1. Does any text clip, overlap, or get cut at max realistic length?
2. Is every spacing value a multiple of the 8px grid?
3. Is there exactly one accent color, applied consistently?
4. Are all icons the same style/weight/size?
5. Do buttons/inputs meet minimum click-target sizes?
6. Does every interactive element have hover + pressed + disabled + focus
   states styled?
7. Does the menu bar follow standard order, shortcuts, and macOS menu-role
   routing?
8. Does it look consistent in spirit across Mac/Windows/Linux (not
   pixel-identical, but equally polished)?
9. Would a stranger call this "a native Mac app" unprompted?