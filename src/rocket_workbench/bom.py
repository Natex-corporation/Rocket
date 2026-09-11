from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


REQUIRED = (
    "category",
    "item",
    "quantity",
    "manufacturer",
    "mpn",
    "status",
    "validated_utc",
    "datasheet_url",
    "notes",
)


@dataclass(frozen=True)
class BomReport:
    rows: int
    ready: int
    placeholders: int
    errors: tuple[str, ...]


def validate(path: Path) -> BomReport:
    errors: list[str] = []
    ready = placeholders = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED if column not in (reader.fieldnames or [])]
        if missing:
            return BomReport(0, 0, 0, (f"missing columns: {', '.join(missing)}",))
        rows = list(reader)
    for number, row in enumerate(rows, 2):
        try:
            if int(row["quantity"]) <= 0:
                errors.append(f"row {number}: quantity must be positive")
        except ValueError:
            errors.append(f"row {number}: quantity is not an integer")
        status = row["status"].upper()
        if status == "REFERENCE":
            ready += 1
            if row["mpn"].strip().upper() == "TBD":
                errors.append(f"row {number}: reference row cannot use TBD as MPN")
            if not row["validated_utc"].strip():
                errors.append(f"row {number}: reference row needs a validation date")
            if not row["datasheet_url"].strip().startswith("https://"):
                errors.append(f"row {number}: reference row needs an HTTPS evidence URL")
        else:
            placeholders += 1
        if status not in {"REFERENCE", "PLACEHOLDER"}:
            errors.append(f"row {number}: status must be REFERENCE or PLACEHOLDER")
        if not row["mpn"].strip() and status != "PLACEHOLDER":
            errors.append(f"row {number}: missing MPN")
    return BomReport(len(rows), ready, placeholders, tuple(errors))
