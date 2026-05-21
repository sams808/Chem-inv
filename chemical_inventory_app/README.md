# Lab Chemical Inventory Manager

A local PySide6 desktop application for managing university chemical inventory with SQLite persistence.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## CSV format

Expected columns (optional except `name`):

- name
- cas
- formula
- supplier
- quantity
- unit
- physical_state
- location_room
- location_cabinet
- location_shelf
- location_detail
- hazard_text
- ghs_codes
- notes
- sds_local_path
- sds_url
- sds_status
- status

Unknown columns are ignored. Empty strings are converted to NULL-like values. Quantity is parsed as float when possible.

## GHS pictograms

Add files to `data/ghs_pictograms/` named `GHS01.png` to `GHS09.png`.
If files are missing, the app shows GHS codes as text and keeps running.

## SDS files

Store local SDS PDFs under `data/sds/` (or another accessible path) and attach path per chemical.

## Not implemented yet

- SDS web scraping/crawling (intentionally excluded)
- Advanced authentication/permissions
- Multi-user synchronization

## Notes

- SQLite is the source of truth after import.
- Source CSV files are never modified in place.
- Import performs database backup first.
