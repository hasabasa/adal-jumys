"""Компанияларды CSV-дан импорттау (топ-500 ірі жұмыс беруші т.б.).

CSV форматы (бірінші жол - тақырып):
bin,name,city,address,oked

Қолдану: uv run python -m app.scripts.import_companies data/top500.csv
Бар БСН өткізіліп жіберіледі (қайта жүргізу қауіпсіз), чексумы қате жол
қабылданбай есепке жазылады.
"""

import asyncio
import csv
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.session import async_session
from app.models import Company
from app.services.bin_check import is_valid_bin


async def import_csv(path: Path) -> dict[str, int]:
    stats = {"created": 0, "skipped_existing": 0, "invalid_bin": 0}
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    async with async_session() as db:
        existing = set(
            (await db.scalars(select(Company.bin))).all()
        )
        for row in rows:
            company_bin = (row.get("bin") or "").strip()
            name = (row.get("name") or "").strip()
            if not is_valid_bin(company_bin) or not name:
                stats["invalid_bin"] += 1
                continue
            if company_bin in existing:
                stats["skipped_existing"] += 1
                continue
            db.add(
                Company(
                    bin=company_bin,
                    name=name,
                    city=(row.get("city") or "").strip() or None,
                    address=(row.get("address") or "").strip() or None,
                    oked=(row.get("oked") or "").strip() or None,
                    source="registry_import",
                )
            )
            existing.add(company_bin)
            stats["created"] += 1
        await db.commit()
    return stats


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Файл табылмады: {csv_path}")
        sys.exit(1)
    result = asyncio.run(import_csv(csv_path))
    print(
        f"Құрылды: {result['created']}, бар еді: {result['skipped_existing']}, "
        f"жарамсыз: {result['invalid_bin']}"
    )
