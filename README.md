# Category Parameter Auditor (pyRevit Extension)

This repository contains a pyRevit extension that audits text parameters by category and reports elements that fail checks (`Missing` and/or `Empty`).

## Contents

- `Audit and Test.extension/`
  - `Audit.tab/Audit.panel/Auditor.pushbutton/`
    - `script.py` (UI wiring + command actions)
    - `ui.xaml` (WPF UI)
    - `lib/audit_engine.py` (collection, filtering, audit helpers)

## Requirements

- Revit 2022+
- pyRevit (IronPython 2.7 runtime)

## Install (Local Development)

1. Clone this repository.
2. Copy or symlink `Audit and Test.extension` into your pyRevit Extensions directory.
3. Reload pyRevit.
4. Run from the `Audit` tab, `Audit` panel, `Auditor` button.

Common extensions path on Windows:

- `%APPDATA%\\pyRevit\\Extensions\\`

## Usage

1. Choose scope (`Active View` or `Whole Model`).
2. Select category and click `Load Elements`.
3. Optionally filter by family and type.
4. Select a text parameter.
5. Choose failure rules:
   - `Fail on Missing`
   - `Fail on Empty`
6. Run `Audit Selected Parameter`.
7. Review, select, isolate, or export failed elements to CSV.

## Release Notes

See `CHANGELOG.md`.

## License

No license file is currently included. Add a `LICENSE` before publishing publicly if you want to grant reuse rights.
