from pathlib import Path

ALLOWED_GHS = [f"GHS0{i}" for i in range(1, 10)]
ALLOWED_GHS_SET = set(ALLOWED_GHS)
GHS_LABELS = {
    "GHS01": "Explosive",
    "GHS02": "Flammable",
    "GHS03": "Oxidizer",
    "GHS04": "Gas under pressure",
    "GHS05": "Corrosive",
    "GHS06": "Acute toxicity",
    "GHS07": "Irritant / harmful",
    "GHS08": "Health hazard",
    "GHS09": "Environmental hazard",
}


def parse_ghs_codes(ghs_codes: str | None) -> list[str]:
    if not ghs_codes:
        return []
    seen = set()
    parsed = []
    for code in str(ghs_codes).replace(",", ";").split(";"):
        normalized = code.strip().upper()
        if normalized and normalized not in seen:
            seen.add(normalized)
            parsed.append(normalized)
    return parsed


def sort_ghs_codes(codes: list[str]) -> list[str]:
    order = {code: idx for idx, code in enumerate(ALLOWED_GHS)}
    return sorted(codes, key=lambda c: order.get(c, 999))


def validate_ghs_codes(ghs_codes: str | None) -> list[str]:
    return [c for c in parse_ghs_codes(ghs_codes) if c not in ALLOWED_GHS_SET]


def ghs_label(code: str) -> str:
    return GHS_LABELS.get(code.upper(), "Unknown hazard")


def get_pictogram_path(code: str, base_dir: Path) -> Path:
    return base_dir / "data" / "ghs_pictograms" / f"{code.upper()}.png"
