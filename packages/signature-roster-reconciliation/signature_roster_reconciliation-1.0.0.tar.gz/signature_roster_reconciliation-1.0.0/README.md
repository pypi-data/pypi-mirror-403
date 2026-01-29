# Signature Roster Reconciliation

A tool for reconciling Program Director roster data against Shopify order data to identify ordering issues.

## Installation

```bash
pip install signature-roster-reconciliation
```

## Usage

```bash
signature-reconcile roster.xlsx orders.xlsx --output report.xlsx
```

### Options

- `--roster-sheet SHEET` - Specify which sheet to use from the roster file
- `--output FILE` - Output filename (default: reconciliation_report.xlsx)
- `--misspelling-threshold N` - Similarity threshold for misspelling detection (0-1, default: 0.7)

## What It Detects

| Issue | Description |
|-------|-------------|
| Not Ordered | Players on roster who haven't placed an order |
| True Duplicates | Same player with multiple uniform orders |
| Sibling Orders | Family members ordering (informational) |
| Wrong Team | Player ordered for a different team |
| Misspellings | Name variations between roster and order |
| Size Outliers | Unusual sizes compared to team average |
| Uniform Mismatches | Order number doesn't match roster |

## Output

Generates an Excel report with multiple tabs:
- Summary
- Not Ordered
- True Duplicates
- Sibling Orders
- Wrong Team
- Potential Misspellings
- Size Outliers
- Uniform Number Mismatches
- Team Summary
- Data Quality Warnings
- Processed Roster Data
- Processed Orders Data

## License

MIT License - Signature Athletics
