import os
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent / "chemical_inventory_app"
os.chdir(app_dir)
sys.path.insert(0, str(app_dir))

from main import main

main()
