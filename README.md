# Schwab Lot Details Extractor

A Python tool that automates extraction of lot-level position data from the Charles Schwab web UI and produces an analytics-ready CSV with holding period and annualized return metrics.

This is a Python evolution of an in-browser bookmarklet, redesigned for repeatability, clarity, and downstream analysis.

---

## Why This Exists

Schwab’s UI exposes detailed lot-level data that is:
- Not available via standard exports
- Buried behind interactive UI flows
- Difficult to analyze at scale

This tool bridges that gap by:
- Navigating the Schwab Positions UI
- Opening lot details programmatically
- Normalizing data into a flat CSV

---

## What It Extracts

For each equity or option lot:
- Quantity, price, cost basis, market value
- Holding period classification
- Days held
- Days remaining until long-term capital gains
- Annualized return (time-adjusted)

Options are automatically parsed for:
- Expiration date
- Strike price

---

## How It Works

1. Launches a real browser using Playwright
2. Attaches to an authenticated Schwab session
3. Iterates through each position’s “Lot Details” modal
4. Extracts and normalizes table data
5. Writes a single CSV for downstream analysis

No credentials are stored or handled by the script.

---

## Requirements

- Python 3.9+
- Playwright

```bash
pip install playwright
playwright install
