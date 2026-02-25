# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - 2026-02-25

### Added

- Initial GitHub release scaffold:
  - `README.md`
  - `.gitignore`
  - `.gitattributes`
  - `CHANGELOG.md`
  - `RELEASE.md`

### Fixed

- `script.py`: ensured `on_window_closed` is defined before `main()` execution path so close-event handler wiring is available when the window is shown.
