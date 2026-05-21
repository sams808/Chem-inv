import re

CAS_RE = re.compile(r"^(\d{2,7})-(\d{2})-(\d)$")


def normalize_cas(cas: str) -> str:
    return (cas or "").strip().replace(" ", "")


def is_valid_cas_format(cas: str) -> bool:
    return bool(CAS_RE.match(normalize_cas(cas)))


def is_valid_cas_checksum(cas: str) -> bool:
    m = CAS_RE.match(normalize_cas(cas))
    if not m:
        return False
    body = "".join(m.groups()[:-1])
    checksum = int(m.group(3))
    total = sum((i + 1) * int(d) for i, d in enumerate(reversed(body)))
    return total % 10 == checksum


def detect_excel_date_corrupted_cas(cas: str) -> bool:
    cas = normalize_cas(cas)
    return bool(re.match(r"^\d{2}-\d{2}-\d{3,7}$", cas)) and not is_valid_cas_format(cas)


def suggest_cas_repair(cas: str) -> str | None:
    if not detect_excel_date_corrupted_cas(cas):
        return None
    p = normalize_cas(cas).split("-")
    fixed = f"{p[2]}-{p[1]}-{p[0][-1]}"
    return fixed if is_valid_cas_format(fixed) else None
