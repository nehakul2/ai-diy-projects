"""Read a bank or card export (CSV) into a simple list of transactions, using only the standard library.

Works with most exports: one signed amount column, or separate money-in / money-out columns.
Long numbers that look like card or account numbers are masked before anything is sent to Claude.
"""
import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime

DATE_NAMES = ("date", "transaction date", "posted date", "posting date", "booking date", "value date")
DESC_NAMES = ("description", "details", "merchant", "name", "payee", "narrative", "memo", "transaction",
              "reference")
AMOUNT_NAMES = ("amount", "value", "transaction amount", "amount (usd)", "amount (gbp)", "amount (eur)")
OUT_NAMES = ("debit", "money out", "paid out", "withdrawal", "withdrawals", "spent", "out")
IN_NAMES = ("credit", "money in", "paid in", "deposit", "deposits", "received", "in")

US_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d %b %Y", "%d %B %Y",
              "%b %d, %Y", "%Y/%m/%d", "%d.%m.%Y"]


@dataclass
class Txn:
    day: date
    description: str
    amount: float  # negative = money out, positive = money in


def _find(headers: list[str], names: tuple[str, ...]) -> str | None:
    low = {h.strip().lower(): h for h in headers}
    for n in names:
        if n in low:
            return low[n]
    for n in names:  # looser match, e.g. "Transaction Description"
        for k, h in low.items():
            if n in k and len(n) > 3:
                return h
    return None


def parse_amount(value: str) -> float | None:
    v = (value or "").strip()
    if not v:
        return None
    neg = v.startswith("(") and v.endswith(")") or v.startswith("-") or v.endswith("-") or v.upper().endswith("DR")
    v = re.sub(r"(?i)\b(cr|dr)\b", "", v)
    v = re.sub(r"[^\d.,]", "", v)
    if not v:
        return None
    if re.search(r",\d{2}$", v) and "." not in v[-3:]:  # 1.234,56 style
        v = v.replace(".", "").replace(",", ".")
    else:
        v = v.replace(",", "")
    try:
        n = float(v)
    except ValueError:
        return None
    return -n if neg else n


def _day_part(value: str, fmt: str) -> str:
    """Drop a time part like '2026-01-05 10:22' or '2026-01-05T10:22:00'."""
    v = value.strip()
    return v if " " in fmt else re.split(r"[\sT]", v)[0]


def _date_format(values: list[str], day_first: bool) -> str:
    formats = US_FORMATS
    if day_first:
        formats = [f for f in US_FORMATS if f.startswith("%d")] + [f for f in US_FORMATS if not f.startswith("%d")]
    for fmt in formats:
        try:
            for v in values:
                datetime.strptime(_day_part(v, fmt), fmt)
            return fmt
        except ValueError:
            continue
    raise ValueError(f"Couldn't read the dates (e.g. '{values[0]}'). Use YYYY-MM-DD, MM/DD/YYYY or DD/MM/YYYY.")


def mask(text: str) -> str:
    """Hide card/account-like numbers (6+ digits) and email addresses."""
    text = re.sub(r"\S+@\S+", "[email]", text)
    return re.sub(r"\d[\d\s-]{4,}\d", lambda m: "#" * 4 if sum(c.isdigit() for c in m.group()) >= 6 else m.group(),
                  text)


def read_export(text: str, day_first: bool = False) -> tuple[list[Txn], list[str]]:
    """Return (transactions, notes). Notes explain any assumptions, such as the sign of amounts."""
    text = text.lstrip("﻿")
    lines = text.splitlines()
    # Some banks put account info above the header: start at the first line with a date-like column name.
    start = next((i for i, line in enumerate(lines[:15]) if "date" in line.lower()), 0)
    try:
        dialect = csv.Sniffer().sniff("\n".join(lines[start:start + 5]), delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(io.StringIO("\n".join(lines[start:])), dialect=dialect))
    if not rows:
        raise ValueError("The file has no rows. Export your transactions as CSV from your bank's website.")
    headers = list(rows[0].keys())
    d_col, desc_col = _find(headers, DATE_NAMES), _find(headers, DESC_NAMES)
    amt_col, out_col, in_col = _find(headers, AMOUNT_NAMES), _find(headers, OUT_NAMES), _find(headers, IN_NAMES)
    if not d_col or not desc_col or not (amt_col or out_col or in_col):
        raise ValueError(f"Couldn't find date, description and amount columns. Columns found: {', '.join(headers)}")
    rows = [r for r in rows if (r.get(d_col) or "").strip()]
    fmt = _date_format([r[d_col] for r in rows], day_first)
    notes = []
    txns = []
    for r in rows:
        if amt_col:
            amount = parse_amount(r.get(amt_col, ""))
        else:
            out_v, in_v = parse_amount(r.get(out_col or "", "")), parse_amount(r.get(in_col or "", ""))
            amount = (abs(in_v) if in_v else 0) - (abs(out_v) if out_v else 0) if (out_v or in_v) else None
        if amount is None:
            continue
        day = datetime.strptime(_day_part(r[d_col], fmt), fmt).date()
        txns.append(Txn(day, mask(" ".join((r.get(desc_col) or "").split())) or "(no description)", amount))
    if not txns:
        raise ValueError("No transactions with amounts found.")
    if amt_col and all(t.amount > 0 for t in txns):
        txns = [Txn(t.day, t.description, -t.amount) for t in txns]
        notes.append("All amounts were positive, so they're treated as spending (typical for card exports). "
                     "Payments to the card show up as income.")
    if fmt.startswith("%m/") and any(t.day.day <= 12 for t in txns):
        notes.append("Dates were read as month/day. If your bank uses day/month, use the day-first option.")
    return sorted(txns, key=lambda t: t.day), notes
