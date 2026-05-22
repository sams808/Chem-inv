# Chem-inv User Manual

## 1. What Chem-inv is
Chem-inv is a local desktop inventory manager for laboratory chemicals.

- It uses a local SQLite database for storage.
- It is designed for tracking chemicals, locations, GHS hazards, SDS status, and audit logs.
- It is not a replacement for institutional safety systems or official EHS requirements.

## 2. Basic workflow
A typical day-to-day workflow is:

1. Launch the app with `python main.py`.
2. Start in Regular mode.
3. View inventory in the main table.
4. Search or filter inventory to find entries quickly.
5. Select a chemical to view detailed information.
6. Add or edit chemical entries as needed.
7. Move products by updating `location_code`.
8. Mark products as empty, disposed, or archived when status changes.

## 3. Regular vs Admin mode
Chem-inv separates normal operation from restricted operations.

- The app starts in Regular mode.
- Admin mode is accessed through `Mode > Admin`.
- Temporary PIN default is `1234`.
- Admin mode is not persisted after closing the app.

Admin-only operations include:

- Import CSV
- Replace inventory
- Clear inventory
- Backup database
- Delete chemical

Regular mode allows normal browsing, searching, viewing logs/dashboard, adding/editing/moving unless changed later.

## 4. Inventory table
The inventory table includes these key columns:

- Name
- CAS
- Quantity
- Unit
- Location
- State
- GHS
- Status

### GHS pictograms
- Pictograms are loaded from `data/ghs_pictograms/`.
- Expected filenames are `GHS01.png` through `GHS09.png`.
- If a pictogram file is missing, Chem-inv shows the GHS code text as fallback.

## 5. Add/Edit Chemical
The Add/Edit form supports the following fields:

- `name`
- `CAS`
- `formula`
- `supplier`
- `physical_state` (dropdown: solid/liquid/gas)
- `quantity`
- `unit`
- `location_code`
- GHS selector
- `hazard_text`
- `notes`
- SDS local path / SDS URL / SDS status
- `status`

GHS codes are stored as semicolon-separated values, for example `GHS02;GHS07`.

## 6. CSV import
CSV import is designed for batch data loading.

- CSV files should be placed in `data/imports/`.
- Import is Admin-only.

Import modes:

- **Append to current inventory**
- **Replace current inventory**

Replace mode creates a backup first, then clears existing inventory before importing.

Expected import aliases:

- `material_name` -> `name`
- `cas_number` -> `cas`
- `primary_quantity` -> `quantity`
- `primary_unit` -> `unit`
- `location` -> `location_code`
- `hazards_raw` -> `hazard_text`
- `ghs_codes` -> `ghs_codes`
- `active` -> `status`

Extra metadata kept in notes:

- `family`
- `hazard_tags`
- `hazard_rank_0_5`
- `quantity_gas_ft3`
- `quantity_liquid_l`
- `quantity_solid_kg`

## 7. Backups, exports, and generated files
Chem-inv keeps all data local.

- Local DB is `data/inventory.db`.
- Backups go to `data/exports/`.
- Exports go to `data/exports/`.
- Logs are stored in SQLite and text log outputs.
- Generated files should not be committed to Git.

## 8. SDS management
SDS handling is available directly in the app.

- SDS local path field stores local document references.
- SDS URL field stores online SDS links.
- **Open SDS** button opens configured local SDS path.
- **Search SDS Online** button performs a web search for SDS resources.
- Missing SDS appears in dashboard summaries and can be filtered.

## 9. Logs page
The Logs page provides an action history.

- Logs show audit trail data from SQLite.
- Log columns include:
  - Timestamp
  - Mode
  - Action
  - Chemical
  - CAS
  - Details
  - User
- Mode can be Regular or Admin.
- Logs support traceability but are not a formal EHS compliance record.

## 10. Dashboard
The dashboard provides quick operational visibility.

Summary cards include:

- Total chemicals
- Active
- Missing SDS
- Missing CAS
- Suspicious CAS
- Archived / Disposed

Plots include:

- Count by status
- Count by GHS
- Top locations
- Problems overview

Use **Refresh Dashboard** to update metrics after data changes.

## 11. Delete vs Archive
Use status changes carefully:

- Archive keeps a chemical in the database with status `archived`.
- Delete permanently removes the row from inventory.
- Delete is Admin-only.
- Delete actions are still logged.

## 12. Recommended lab practices
Recommended usage patterns:

- Use consistent `location_code` conventions.
- Keep GHS pictograms installed and complete.
- Review Missing SDS dashboard indicators regularly.
- Prefer Archive/Disposed over Delete unless entry data is incorrect.
- Backup before major imports.
- Perform a quick audit after CSV import.
- Use notes for unusual storage conditions or hazards.
- Do not rely on this app alone for emergency response.

## 13. Troubleshooting
Common issues and checks:

- **App starts empty**: import CSV data or verify `data/inventory.db` exists and is populated.
- **GHS shows text codes**: pictogram PNGs are missing in `data/ghs_pictograms/`.
- **CSV import creates duplicates**: use Replace inventory mode or clear inventory first.
- **Admin PIN not accepted**: verify temporary PIN/default settings.
- **Logs empty**: no actions have been performed yet, or DB/log data was reset.
- **Dashboard empty**: inventory data is not loaded.

## 14. File/folder reference
Quick path reference:

- `main.py`
- `app/`
- `data/imports/`
- `data/ghs_pictograms/`
- `data/sds/`
- `data/exports/`
- `data/logs/`
- `data/inventory.db`
