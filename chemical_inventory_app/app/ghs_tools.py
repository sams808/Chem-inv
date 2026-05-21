from pathlib import Path

ALLOWED_GHS = {f"GHS0{i}" for i in range(1, 10)}


def parse_ghs_codes(ghs_codes: str) -> list[str]:
    if not ghs_codes:
        return []
    return [x.strip().upper() for x in ghs_codes.replace(",", ";").split(";") if x.strip()]


def validate_ghs_codes(ghs_codes: str) -> list[str]:
    return [c for c in parse_ghs_codes(ghs_codes) if c not in ALLOWED_GHS]


def get_pictogram_path(code: str, base_dir: Path) -> Path:
    return base_dir / "data" / "ghs_pictograms" / f"{code}.png"
