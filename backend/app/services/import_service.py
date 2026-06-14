import csv
import io
import uuid
from datetime import date

from app.models.category import Category


def parse_csv_preview(content: bytes) -> dict:
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return {"headers": [], "rows": [], "total_rows": 0}
    headers = rows[0]
    data_rows = rows[1:]
    return {
        "headers": headers,
        "rows": [r for r in data_rows[:5]],
        "total_rows": len(data_rows),
    }


def parse_csv_rows(
    content: bytes,
    date_col: int,
    amount_col: int,
    category_col: int | None,
    note_col: int | None,
    categories: list[Category],
) -> tuple[list[dict], int]:
    """Returns (valid_rows, skipped_count). Rows have tx_date, amount_cents, category_id, note."""
    cat_by_name = {c.name.lower(): c.id for c in categories}

    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    all_rows = list(reader)
    data_rows = all_rows[1:] if all_rows else []

    valid: list[dict] = []
    skipped = 0
    for row in data_rows:
        try:
            tx_date = date.fromisoformat(row[date_col].strip())
            amount_str = row[amount_col].strip().replace(",", ".").lstrip("+-")
            amount_cents = round(float(amount_str) * 100)
            if amount_cents <= 0:
                skipped += 1
                continue

            category_id: uuid.UUID | None = None
            if category_col is not None and category_col < len(row):
                cat_name = row[category_col].strip().lower()
                category_id = cat_by_name.get(cat_name)

            note: str | None = None
            if note_col is not None and note_col < len(row):
                raw = row[note_col].strip()
                if raw:
                    note = raw[:500]

            valid.append({
                "tx_date": tx_date,
                "amount_cents": amount_cents,
                "category_id": category_id,
                "note": note,
            })
        except (IndexError, ValueError, OverflowError):
            skipped += 1

    return valid, skipped
