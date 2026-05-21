# Chem-inv

Application desktop (PySide6) de gestion d'inventaire chimique avec base SQLite locale.

## Installation (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

## Import CSV

1. Placer les fichiers CSV dans `data/imports/`.
2. Lancer l'application.
3. Dans le menu, utiliser **File > Import CSV**.

L'import gère les en-têtes alternatifs (ex: `material_name`, `cas_number`, `primary_quantity`, etc.) et ignore les lignes vides/séparateurs provenant d'anciens exports Excel.

## Pictogrammes GHS

Placer les fichiers `GHS01.png` à `GHS09.png` dans `data/ghs_pictograms/`.

## Base SQLite

La base locale est créée à `data/inventory.db`.
Ce fichier est généré localement et **ne doit pas être versionné**.

## Mode Admin

- L'application démarre en **Mode: Normal**.
- Les actions sensibles (Import CSV, Clear Inventory, Backup Database) nécessitent le mode Admin.
- PIN temporaire par défaut: `1234` (stocké en SHA-256 dans `settings.admin_pin_hash`).
- **TODO sécurité**: remplacer ce PIN temporaire avant déploiement labo réel.

