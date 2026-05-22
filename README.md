# Chem-inv

Chem-inv is a local desktop application for managing a laboratory chemical inventory. It is built with PySide6 and stores data in a local SQLite database.

The app is meant for day-to-day lab inventory work: finding chemicals, tracking storage locations, checking SDS coverage, reviewing GHS hazards, importing curated CSV inventories, and keeping a simple audit trail of changes.

It is not a replacement for institutional EHS systems, chemical hygiene plans, SDS review, or supervisor approval.

## Current status

Chem-inv is a small lab-focused desktop tool under active development. It is usable for local testing and internal inventory cleanup, but it should be validated against your lab workflow before relying on it for routine operations.

Main features currently implemented:

- Inventory table with search and status filtering
- Add, edit, move, archive, dispose, and delete chemical entries
- Local SQLite database
- CSV import with append or replace mode
- Automatic database backup before destructive import/clear operations
- Regular/Admin mode separation for sensitive actions
- GHS pictogram display with text fallback
- SDS fields, local SDS opening, and online SDS search helper
- Dashboard with inventory quality indicators
- Logs page with Regular/Admin mode recorded in the audit trail
- In-app user manual available from `Help > User Manual`

## Repository layout

```text
Chem-inv/
  main.py                  # Application entry point
  requirements.txt         # Python dependencies
  README.md                # Project overview and developer setup
  docs/
    user_manual.md         # In-app user guide
  app/
    database.py            # SQLite database layer
    import_export.py       # CSV import/export and DB backup helpers
    ui_main.py             # Main PySide6 window
    ui_forms.py            # Add/Edit chemical dialog
    ui_dashboard.py        # Dashboard page
    ui_logs.py             # Logs page
    ui_manual.py           # In-app manual viewer
    ghs_tools.py           # GHS code parsing and pictogram helpers
    sds_tools.py           # SDS opening/search helpers
  data/
    imports/               # Put source CSV files here
    ghs_pictograms/        # Put GHS01.png through GHS09.png here
    sds/                   # Optional local SDS storage
    exports/               # Generated backups and CSV exports
    logs/                  # Generated text log output
    inventory.db           # Generated local SQLite database, not versioned
```

Generated files in `data/exports/`, `data/logs/`, local SDS files, and `data/inventory.db` should normally stay out of Git.

## Installation

Recommended environment: Python 3.11 on Windows.

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Linux/macOS, the equivalent is usually:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Running the app

```bash
python main.py
```

The app creates and uses a local database at:

```text
data/inventory.db
```

The app starts in Regular mode. Sensitive actions require Admin mode.

## First setup checklist

Before importing real inventory data:

1. Install dependencies in a virtual environment.
2. Add GHS pictogram files to `data/ghs_pictograms/`.
3. Put source CSV inventory files in `data/imports/`.
4. Launch the app with `python main.py`.
5. Open `Help > User Manual` and review the user workflow.
6. Switch to Admin mode only when you need import, replace, clear, backup, or delete operations.

## GHS pictograms

The Inventory table and Add/Edit dialog use GHS pictograms when image files are available.

Expected filenames:

```text
GHS01.png
GHS02.png
GHS03.png
GHS04.png
GHS05.png
GHS06.png
GHS07.png
GHS08.png
GHS09.png
```

Place them in:

```text
data/ghs_pictograms/
```

If a pictogram image is missing, the app displays the GHS code as text fallback instead of failing.

## CSV import

CSV import is available from:

```text
File > Import CSV
```

Import is an Admin-only action.

Supported modes:

- **Append to current inventory**: adds rows to the existing database. Importing the same file twice can create duplicates.
- **Replace current inventory**: creates a backup, clears the inventory, then imports the selected CSV.

The importer supports the current cleaned inventory CSV format and common aliases, including:

| CSV column | Database field |
| --- | --- |
| `material_name` | `name` |
| `cas_number` | `cas` |
| `primary_quantity` | `quantity` |
| `primary_unit` | `unit` |
| `location` | `location_code` |
| `hazards_raw` | `hazard_text` |
| `ghs_codes` | `ghs_codes` |
| `active` | `status` |

Additional inventory metadata may be preserved in `notes`, depending on the source CSV.

## Regular and Admin modes

Chem-inv separates routine work from sensitive actions.

Regular mode is for normal inventory use: browsing, searching, viewing details, adding/editing entries, moving chemicals, status updates, Logs, Dashboard, and SDS lookup.

Admin mode is required for actions that can overwrite or remove data:

- Import CSV
- Replace inventory during import
- Clear inventory
- Backup database
- Delete chemical

Admin mode is entered through:

```text
Mode > Admin
```

The Admin PIN is intentionally not documented in this README. Ask the app maintainer or lab manager if you need Admin access.

## Dashboard

The Dashboard page provides a quick inventory health check:

- Total chemicals
- Active entries
- Missing SDS
- Missing CAS
- Suspicious CAS format
- Archived / Disposed entries
- Count by status
- Count by GHS
- Top locations
- Problems overview

Use `Refresh Dashboard` after imports or bulk edits.

## Logs

The Logs page displays the SQLite audit trail. Logs include:

- Timestamp
- Mode: Regular or Admin
- Action
- Chemical name
- CAS
- Details
- User

Logs are useful for traceability, but they are not a formal compliance record.

## User manual

A lab-user-facing manual is included in the app:

```text
Help > User Manual
```

The source markdown is stored at:

```text
docs/user_manual.md
```

The manual is intended for non-technical lab users and focuses on practical workflows rather than implementation details.

## Development notes

Useful checks before committing:

```bash
python -m compileall app main.py
```

If tests are available in the local checkout:

```bash
pytest
```

Recommended development workflow:

1. Create a feature or hotfix branch.
2. Keep each pull request small and focused.
3. Run compile/test checks.
4. Avoid committing generated database, export, log, or SDS files.
5. Review UI changes manually before merging.

## Files that should not normally be committed

Do not commit local/generated files such as:

```text
data/inventory.db
data/exports/*
data/logs/*
data/sds/*
```

The folders may exist in the repository so the app has a predictable structure, but generated contents should remain local unless the lab intentionally decides otherwise.

## Safety note

Chem-inv organizes inventory information. It does not decide whether a chemical operation is safe.

Always follow the lab chemical hygiene plan, SDS, institutional EHS policies, and supervisor instructions. When in doubt, stop and ask.
