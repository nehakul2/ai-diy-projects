"""Categorise transactions with Claude, then do all the sums in plain Python."""
import json
import re
from collections import defaultdict
from statistics import median

from common.claude import ask
from finance_explainer.bank import Txn
from finance_explainer.prompt import CATEGORISE_SCHEMA, CATEGORISE_SYSTEM, EXPLAIN_SYSTEM

NOT_SPENDING = {"Income", "Transfers & savings"}
BATCH = 150


def categorise(txns: list[Txn]) -> dict[str, dict]:
    """Label each distinct description once. Returns {description: {"merchant", "category"}}."""
    unique = list(dict.fromkeys(t.description for t in txns))
    labels: dict[str, dict] = {}
    # Tell Claude whether each one was money in or out; it helps with refunds vs purchases.
    signs = {t.description: ("in" if t.amount > 0 else "out") for t in txns}
    for i in range(0, len(unique), BATCH):
        chunk = unique[i:i + BATCH]
        listing = "\n".join(f"{n + 1}. [{signs[d]}] {d}" for n, d in enumerate(chunk))
        data = json.loads(ask(CATEGORISE_SYSTEM, listing, schema=CATEGORISE_SCHEMA, effort="low"))
        for d, lab in zip(chunk, data["labels"]):  # match by position; Claude may tidy the text
            labels[d] = {"merchant": lab["merchant"] or d, "category": lab["category"]}
    for t in txns:  # anything missed
        labels.setdefault(t.description, {"merchant": t.description, "category": "Other"})
    return labels


def _key(merchant: str) -> str:
    return re.sub(r"[^a-z ]", "", merchant.lower()).strip()


def recurring(txns: list[Txn], labels: dict[str, dict]) -> list[dict]:
    """Payments to the same merchant in 2+ different months with similar amounts."""
    groups: dict[str, list[Txn]] = defaultdict(list)
    for t in txns:
        if t.amount < 0 and labels[t.description]["category"] not in NOT_SPENDING:
            groups[_key(labels[t.description]["merchant"])].append(t)
    found = []
    for items in groups.values():
        months = {(t.day.year, t.day.month) for t in items}
        amounts = [-t.amount for t in items]
        typical = median(amounts)
        if len(months) >= 2 and len(items) <= len(months) + 1 and all(abs(a - typical) <= 0.15 * typical
                                                                       for a in amounts):
            latest = max(items, key=lambda t: t.day)
            found.append({"merchant": labels[latest.description]["merchant"],
                          "category": labels[latest.description]["category"], "typical": round(typical, 2),
                          "latest": round(-latest.amount, 2), "per_year": round(typical * 12, 2),
                          "went_up": -latest.amount > min(amounts) + 0.01, "months_seen": len(months)})
    return sorted(found, key=lambda r: -r["per_year"])


def summarise(txns: list[Txn], labels: dict[str, dict]) -> dict:
    by_cat: dict[str, float] = defaultdict(float)
    by_month: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_merchant: dict[str, float] = defaultdict(float)
    income = spending = 0.0
    for t in txns:
        lab = labels[t.description]
        month = f"{t.day:%Y-%m}"
        if lab["category"] == "Transfers & savings":
            by_month[month]["Transfers & savings"] += t.amount
            continue
        if t.amount > 0:
            if lab["category"] == "Income":
                income += t.amount
                by_month[month]["Income"] += t.amount
                continue
            # A refund: reduce spending in its category.
        spent = -t.amount
        spending += spent
        by_cat[lab["category"]] += spent
        by_month[month][lab["category"]] += spent
        by_merchant[lab["merchant"]] += spent
    months = sorted(by_month)
    r2 = lambda d: {k: round(v, 2) for k, v in sorted(d.items(), key=lambda kv: -kv[1])}  # noqa: E731
    return {
        "from": txns[0].day.isoformat(), "to": txns[-1].day.isoformat(), "transactions": len(txns),
        "months": len(months), "income": round(income, 2), "spending": round(spending, 2),
        "net": round(income - spending, 2), "by_category": r2(by_cat),
        "top_merchants": dict(list(r2(by_merchant).items())[:12]),
        "by_month": {m: r2({k: v for k, v in by_month[m].items() if k not in NOT_SPENDING})
                     | {"_total_spending": round(sum(v for k, v in by_month[m].items() if k not in NOT_SPENDING), 2),
                        "_income": round(by_month[m].get("Income", 0), 2)} for m in months},
        "recurring": recurring(txns, labels),
    }


def explain(summary: dict, currency: str = "$", context: str = "") -> str:
    user = (f"Currency: {currency}\n" + (f"About me: {context}\n" if context.strip() else "")
            + json.dumps(summary, indent=1))
    return ask(EXPLAIN_SYSTEM, user)


def money(x: float, currency: str = "$") -> str:
    return f"-{currency}{-x:,.0f}" if x < 0 else f"{currency}{x:,.0f}"


def tables(summary: dict, currency: str = "$") -> str:
    """The exact numbers, as Markdown tables, to show alongside Claude's explanation."""
    lines = [f"## The numbers ({summary['from']} to {summary['to']}, {summary['transactions']} transactions)", "",
             f"Money in **{money(summary['income'], currency)}** · money out **{money(summary['spending'], currency)}**"
             f" · difference **{money(summary['net'], currency)}**", "",
             "| Category | Spent | Share |", "|---|---|---|"]
    total = summary["spending"] or 1
    for cat, v in summary["by_category"].items():
        lines.append(f"| {cat} | {money(v, currency)} | {v / total:.0%} |")
    if summary["months"] > 1:
        lines += ["", "| Month | Money in | Money out |", "|---|---|---|"]
        for m, d in summary["by_month"].items():
            lines.append(f"| {m} | {money(d['_income'], currency)} | {money(d['_total_spending'], currency)} |")
    if summary["recurring"]:
        lines += ["", "| Regular payment | Usually | Per year |", "|---|---|---|"]
        for r in summary["recurring"]:
            up = " (went up)" if r["went_up"] else ""
            lines.append(f"| {r['merchant']}{up} | {currency}{r['typical']:,.2f} | {money(r['per_year'], currency)} |")
    return "\n".join(lines)
