---
name: trading-log-sync
description: >-
  Fast one-command Google Sheets synchronization for Creatures of Sonaria stand check-ins
  into Trading Log and Analytics. Use whenever the user uploads Mon's Stand screenshots
  or reports a stand/liquid/price update for the Trading Log spreadsheet.
---

# Trading Log & Analytics Fast Sync Skill

Use this skill whenever the user uploads stand screenshots or gives a Creatures of Sonaria stock update.

## Spreadsheet Reference

- **Spreadsheet ID:** Configurable via `TRADING_LOG_SHEET_ID` env var or `--sheet-id` (defaults to configured Trading Log sheet)
- **Primary CLI Script:** `~/vibe/trading-log-analytics/scripts/sync_stock.py`
- **Zero-Emoji Policy:** Do NOT include emojis in any response, table, or file.
- **Formatting Invariant:** Standard Arial 10pt regular font, uniform 1px `SOLID` gridlines (`#D0D6DE`), no heavy divider borders. (`sync_stock.py` applies this automatically.)

## Fast 1-Command Execution Workflow

1. **Extract from Screenshots / User Input:**
   - Read the **Liquid Mushrooms** balance from the top bar.
   - Read each stand card's **Item Name**, **Quantity** (`x...`), and **Selling Price**.
   - Use the local timestamp from `<ADDITIONAL_METADATA>` formatted as `YYYY-MM-DD HH:MM:SS`.
   - Do **not** run sequential `gsheets readonly read` or `inspect-cell` calls beforehand, and do **not** write a custom per-stock Python script from scratch.

2. **Execute `sync_stock.py` in One Call:**
   Run `--apply` directly (or `--dry-run` first only if uncertain about ambiguous numbers):

   ```bash
   python3 ~/vibe/trading-log-analytics/scripts/sync_stock.py \
     --liquid <LIQUID_MUSH> \
     --timestamp "<YYYY-MM-DD HH:MM:SS>" \
     --item "<Item 1>=<Qty>@<Price>" \
     --item "<Item 2>=<Qty>@<Price>" \
     ... \
     --apply
   ```

   What `sync_stock.py --apply` handles automatically in ~2–3 seconds:
   - Concurrent preflight across `Trading Log`, `Stand Sell Log`, `Analytics`, and `Slots`
   - Auto-incrementing `Stock #` and exact target rows
   - Freezing prior `Trading Log` Column `H` if it still holds `=Analytics!$C$13`
   - Automatic midnight date rollover in `Analytics` Section 3 (freezes previous day's `B:C` and appends today's `=C13` & `=C13-Slots!F3`)
   - Appending `Trading Log` (Cols `A:H`) and `Stand Sell Log` (Cols `A:F`)
   - Applying exact `Arial 10pt`, alignments, number formats, and `1px SOLID #D0D6DE` borders via `raw-batch`
   - Scanning all 7 tabs (`Analytics`, `Trading Log`, `Stand Sell Log`, `Buy Orders & Inv`, `Slots`, `Item Totals`, `_ChartData`) for `#REF!`, `#VALUE!`, `#N/A`, `#DIV/0!`, `#NAME?`, `#ERROR!`
   - Returning full verified JSON with item-by-item deltas and live net worth

3. **Report Result:**
   Summarize the verified JSON output cleanly (Portfolio Valuation & Performance table, Stand Selling Inventory table, Sales & Restocking Delta, and Spreadsheet Health Confirmation).
