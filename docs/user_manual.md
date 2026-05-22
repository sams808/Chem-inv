# Chem-inv User Manual

## 1. Purpose of Chem-inv
Chem-inv is a local lab inventory tool that helps answer day-to-day questions such as:
- What chemicals do we have?
- Where are they stored?
- Are SDS records missing?
- What hazards are associated with each entry?
- What changed recently?

Chem-inv supports recordkeeping and visibility. It is **not** a replacement for SDS review, the lab chemical hygiene plan, institutional EHS systems, or supervisor instructions.

## 2. Before using the app
Before you start, follow these basic rules:
- Use the lab-approved copy of the app.
- Do **not** manually edit `data/inventory.db`.
- Do **not** move generated database/export/log files unless you know what you are doing.
- Keep GHS pictogram files in `data/ghs_pictograms/`.
- Keep import files in `data/imports/`.

## 3. Opening Chem-inv
1. Open a terminal in the Chem-inv folder.
2. Activate the virtual environment (if your lab uses one).
3. Run `python main.py`.
4. Confirm the app opens in **Regular** mode.

## 4. Regular mode vs Admin mode
Use the correct mode for the task:
- **Regular mode** is for normal browsing and routine updates.
- **Admin mode** is for destructive or bulk operations.
- The app starts in Regular mode.
- Admin mode is not persisted after closing the app.
- Use `Mode > Admin` to request Admin access.
- Do not publish any PIN in this manual.
- Ask the app maintainer or lab manager if Admin access is needed.

Admin-only actions:
- Import CSV
- Replace inventory
- Clear inventory
- Backup database
- Delete chemical

## 5. Finding a chemical
Step-by-step:
1. Click **Inventory**.
2. Use the search box.
3. Search by name, CAS, supplier, notes, hazard text, or location.
4. Use the status filter to narrow results.
5. Click a row to inspect details.

Common columns:
- Name
- CAS
- Quantity
- Unit
- Location
- State
- GHS
- Status

Status meanings:
- `active`: in normal use/storage
- `empty`: container recorded but no usable material remains
- `disposed`: material removed from use/discarded
- `archived`: retained for history, not active circulation
- `error_duplicate`: likely duplicate or data issue needing cleanup

## 6. Reading GHS information
Chem-inv shows hazard information using pictograms when image files are available. If images are missing, it shows GHS text codes as fallback.

GHS quick reference table:

| Code | Meaning |
| --- | --- |
| GHS01 | Explosive |
| GHS02 | Flammable |
| GHS03 | Oxidizer |
| GHS04 | Gas under pressure |
| GHS05 | Corrosive |
| GHS06 | Acute toxicity |
| GHS07 | Irritant / harmful |
| GHS08 | Health hazard |
| GHS09 | Environmental hazard |

GHS pictograms are a quick visual aid only. Always read the SDS before handling chemicals.

## 7. Adding a chemical
Detailed steps:
1. Click **Add Chemical**.
2. Enter the chemical name.
3. Enter CAS if known.
4. Enter formula and supplier if useful.
5. Choose physical state.
6. Enter quantity and unit.
7. Enter location code.
8. Select GHS pictograms based on SDS.
9. Add hazard text and notes.
10. Add SDS path/URL/status if available.
11. Save and confirm the entry appears in Inventory.

Practical guidance:
- Do not invent CAS numbers.
- Leave uncertain fields blank rather than guessing.
- Use notes to document uncertainty or follow-up needed.

## 8. Editing, moving, and status changes
Use these actions based on what happened physically in the lab:
- **Edit**: correct or update record details (name, CAS, quantity, hazards, SDS, etc.).
- **Move**: update `location_code` when storage location changes.
- **Mark Empty**: use when container remains but material is exhausted.
- **Mark Disposed**: use when material has been discarded according to procedure.
- **Archive**: keep a historical record that is no longer active.

## 9. Delete vs Archive
Choose carefully:
- **Archive** keeps history and should be the default for normal lifecycle changes.
- **Delete** permanently removes the row.
- Delete is Admin-only.
- Delete is for mistakes/duplicates, not normal chemical lifecycle.
- Delete actions are logged.

## 10. Importing CSV files
Step-by-step:
1. Put the CSV file in `data/imports/`.
2. Switch to Admin mode.
3. Use `File > Import CSV`.
4. Choose the file.
5. Choose **Append** or **Replace**.

What the modes do:
- **Append** adds rows and can create duplicates.
- **Replace** creates a backup first, clears current inventory, then imports new rows.
- After import, check both Dashboard and Inventory for sanity.

Supported CSV aliases:
- `material_name` -> `name`
- `cas_number` -> `cas`
- `primary_quantity` -> `quantity`
- `primary_unit` -> `unit`
- `location` -> `location_code`
- `hazards_raw` -> `hazard_text`
- `ghs_codes` -> `ghs_codes`
- `active` -> `status`

## 11. Backups and exports
Chem-inv includes routine data-output tools:
- Backup database
- Export Inventory CSV
- Export Active Inventory CSV
- Export Logs CSV

Generated files are written to `data/exports/`.
Always perform a backup before major imports or bulk operations.

## 12. SDS workflow
Use SDS fields consistently:
- **Local SDS path**: points to a local file copy.
- **SDS URL**: points to a trusted online source.
- **Open SDS**: opens local SDS path when configured.
- **Search SDS Online**: helps locate a source when missing.
- **Missing SDS** appears on the Dashboard and should be reviewed regularly.

Users must verify the SDS source is correct and current.

## 13. Logs page
The Logs page provides traceability of actions.

Typical log columns include:
- Timestamp
- Mode
- Action
- Chemical
- CAS
- Details
- User

Logs indicate whether actions happened in Regular or Admin mode. Logs support traceability, but they are not formal EHS records.

## 14. Dashboard
The Dashboard gives a quick quality and status overview.

Cards:
- Total chemicals
- Active
- Missing SDS
- Missing CAS
- Suspicious CAS
- Archived / Disposed

Charts:
- Count by status
- Count by GHS
- Top locations
- Problems overview

After imports or large edits, click **Refresh Dashboard** and review unusual counts before continuing.

## 15. Good lab habits
- Use consistent location codes.
- Avoid duplicate location spellings.
- Keep CAS values clean.
- Do not guess hazards.
- Prefer Archive/Disposed over Delete.
- Backup before bulk work.
- Review dashboard regularly.
- Ask before using Admin mode.

## 16. Troubleshooting
**Q: The app opens empty. What should I check?**  
A: Confirm you are using the expected dataset and that inventory data has been loaded.

**Q: GHS shows text instead of icons. Why?**  
A: Pictogram image files are likely missing from `data/ghs_pictograms/`.

**Q: I see duplicate entries after import. What happened?**  
A: Append mode can add duplicates. Clean up duplicates or use Replace (with backup) when appropriate.

**Q: I cannot import or delete. Why?**  
A: These are Admin-only actions. Request authorized Admin access.

**Q: Dashboard says many SDS are missing. What now?**  
A: Prioritize SDS completion using local paths/URLs and verify each source.

**Q: Logs page is empty. Is that an error?**  
A: Not necessarily. It may mean no logged actions yet in the current dataset.

**Q: A CAS number looks wrong. What should I do?**  
A: Check source documents, correct the record, and leave notes if verification is pending.

## 17. Folder reference
- `main.py`
- `app/`
- `docs/user_manual.md`
- `data/inventory.db`
- `data/imports/`
- `data/ghs_pictograms/`
- `data/sds/`
- `data/exports/`
- `data/logs/`

## 18. Safety note
Always follow the lab chemical hygiene plan, SDS, institutional EHS policies, and supervisor instructions. When in doubt, stop and ask. Chem-inv helps organize information; it does not decide whether a chemical operation is safe.
