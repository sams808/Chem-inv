import webbrowser
from pathlib import Path
from urllib.parse import quote_plus


def open_local_sds(path):
    if not path:
        return False
    p = Path(path)
    if not p.exists():
        return False
    webbrowser.open(p.resolve().as_uri())
    return True


def attach_local_sds(chemical_id, pdf_path):
    return {"chemical_id": chemical_id, "sds_local_path": str(Path(pdf_path))}


def build_search_urls(name, cas):
    q = quote_plus(cas or name or "")
    return [
        f"https://pubchem.ncbi.nlm.nih.gov/#query={q}",
        f"https://www.fishersci.com/us/en/catalog/search/products?keyword={q}",
        f"https://www.sigmaaldrich.com/US/en/search/{q}",
        f"https://www.chemicalsafety.com/sds-search/?q={q}",
    ]
