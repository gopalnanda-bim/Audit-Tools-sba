## Parameter Auditor – SDA

**pyRevit extension for auditing text parameters and identifying missing or empty values in Revit models.**

---

## Who is this for?

This extension is designed for:

- Electrical planners (Elektroplaner)  
- BIM modellers working in TGA projects  
- BIM coordinators and QA engineers responsible for data validation  

---

## Background: Data Quality in Revit Models

In BIM projects, parameter data is often:

- incomplete or missing  
- inconsistently filled across elements  
- difficult to validate at scale  

Poor data quality can lead to:

- incorrect schedules and reports  
- coordination issues between disciplines  
- delays in execution planning  

Manual checking of parameters is:

- time-consuming  
- unreliable  
- not scalable for large models  

---

## What this tool does

This tool audits **text parameters by category** and identifies elements that fail validation checks.

It allows users to:

- detect missing parameters  
- detect empty parameter values  
- filter and review affected elements efficiently  

---

## Features

### Flexible Scope Selection

- Audit elements in:
  - Active View  
  - Entire Model  

---

### Category-Based Filtering

- Select a category  
- Load elements dynamically  
- Optionally filter by:
  - Family  
  - Type  

---

### Parameter Validation

- Select any text parameter  
- Apply validation rules:
  - Fail on Missing  
  - Fail on Empty  

---

### Clear Audit Results

- Displays all failing elements  
- Allows:
  - selection  
  - isolation in view  
  - further inspection  

---

### Export Capability

- Export failed elements to CSV  
- Enables external analysis and reporting  

---

## Typical Use Cases

- Checking completeness of shared parameters  
- Validating MEP / TGA data before submission  
- Ensuring consistent parameter usage across families  
- Preparing models for schedules and documentation  

---

## Why this matters in practice

Reliable parameter data is critical for:

- accurate schedules  
- coordination between disciplines  
- downstream workflows (AVA, BIM coordination, facility management)  

This tool helps ensure **data consistency and model reliability** with minimal manual effort.

---

## Requirements

- Autodesk Revit 2022 or newer  
- pyRevit (IronPython 2.7)  

---

## Installation

1. Install pyRevit  
   https://docs.pyrevitlabs.io/  

2. Clone this repository  

3. Copy or symlink the extension into:

   %APPDATA%\pyRevit\Extensions\

4. Reload pyRevit  

---

## Usage

1. Choose scope (Active View or Whole Model)  
2. Select a category and click **Load Elements**  
3. Optionally filter by family and type  
4. Select a text parameter  
5. Choose validation rules:
   - Fail on Missing  
   - Fail on Empty  
6. Run audit  
7. Review results and optionally export to CSV  

---

## Project Structure

```
Audit and Test.extension/
└── Audit.tab/
    └── Audit.panel/
        └── Auditor.pushbutton/
            ├── script.py
            ├── ui.xaml
            └── lib/
                └── audit_engine.py
```

---

## Roadmap (planned)

- Support for additional parameter types  
- Advanced filtering (multi-conditions / AND-OR logic)  
- Integrated gap and duplicate detection  
- Improved UI for large datasets  

---

## License

No license file is currently included.

Add a LICENSE file before public distribution if you want to allow reuse.
