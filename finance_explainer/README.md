# Personal finance explainer

Export your transactions from your bank or card website as a CSV, and get a
plain-English picture of your spending:

- **the big picture**: money in vs money out
- **where your money goes**, by category and merchant
- **month-to-month changes** and what caused them
- **subscriptions and regular payments**, with the yearly cost, flagging ones that went up
- **3 practical ideas**, with a rough monthly saving

All the sums happen in plain Python, so the numbers are exact. Claude only
labels each transaction with a category and writes the explanation from the
totals. The exact tables are shown underneath, so you can check them.

## Try it

From the repo root:

```bash
python -m finance_explainer.main finance_explainer/examples/sample_bank_export.csv
python -m finance_explainer.main ~/Downloads/statement.csv
python -m finance_explainer.main statement.csv --currency "£" --day-first --context "Rent is split with a flatmate"
```

It reads most bank exports: one signed amount column, or separate money in and
money out columns, with commas or semicolons, and account details above the
header row. If every amount is positive (common for card exports), they're
treated as spending. Use `--day-first` if your dates are day/month.

Transfers between your own accounts, card payments and savings are left out
of spending. Refunds reduce spending in their category.

## Privacy

Your file stays on your computer. Only the distinct transaction descriptions
(to categorise them) and the calculated totals (to explain them) are sent to
Claude. Numbers that look like card or account numbers (6 or more digits) and
email addresses are masked first. The sample export is made-up data.

This explains your spending; it's not financial advice.

## Ideas to improve it

- Set a monthly budget per category and see how you're tracking.
- Compare two exports, such as this year vs last year.
