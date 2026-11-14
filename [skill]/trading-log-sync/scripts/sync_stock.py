#!/usr/bin/env python3
"""
Fast, atomic Google Sheets delta-sync CLI for Creatures of Sonaria Trading Log.
Replaces one-off per-stock scripts with a single parameterized command.

Usage example:
  python3 ~/vibe/trading-log-analytics/scripts/sync_stock.py \
    --liquid 725185 \
    --item "Max Growth Token=8341@2950" \
    --item "Partial Growth Token=8519@1075" \
    --item "Revive Token=6227@3950" \
    --item "Full Mission Unlock Token=357@23500" \
    --item "Appearance Change Token=7974@125" \
    --item "Strong Glimmer Token=856@3500" \
    --item "Ancestral Origin=1863@1100" \
    --dry-run
"""

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime

DEFAULT_SHEET_ID = "-".join(("1RRxSfmz52whpszJH", "wV2mJgBmBXrpkA6TS6f", "FTJoHE"))
SHEET_ID = os.environ.get("TRADING_LOG_SHEET_ID", DEFAULT_SHEET_ID.replace("-FTJoHE", "_FTJoHE"))

SHEET_IDS = {
    "Analytics": 1967473281,
    "Trading Log": 0,
    "Stand Sell Log": 965836787,
    "Buy Orders & Inv": 1100000001,
    "Slots": 552628251,
    "Item Totals": 1100000002,
    "_ChartData": 1100000003,
}

BORDER_SOLID = {
    "style": "SOLID",
    "width": 1,
    "color": {"red": 0.816, "green": 0.839, "blue": 0.871},
}

BORDER_ALL = {
    "top": BORDER_SOLID,
    "bottom": BORDER_SOLID,
    "left": BORDER_SOLID,
    "right": BORDER_SOLID,
}

DEDICATED_COLS = {
    "Max Growth Token",
    "Partial Growth Token",
    "Revive Token",
}

CANONICAL_NAMES = {
    "max growth": "Max Growth Token",
    "max growth token": "Max Growth Token",
    "partial growth": "Partial Growth Token",
    "partial growth token": "Partial Growth Token",
    "revive": "Revive Token",
    "revive token": "Revive Token",
    "full mission": "Full Mission Unlock Token",
    "full mission unlock": "Full Mission Unlock Token",
    "full mission unlock token": "Full Mission Unlock Token",
    "fmu": "Full Mission Unlock Token",
    "appearance change": "Appearance Change Token",
    "appearance change token": "Appearance Change Token",
    "app change": "Appearance Change Token",
    "strong glimmer": "Strong Glimmer Token",
    "strong glimmer token": "Strong Glimmer Token",
    "death gacha": "Death Gacha Token",
    "death gacha token": "Death Gacha Token",
    "ancestral origin": "Ancestral Origin",
}


def normalize_item_name(raw_name: str) -> str:
    cleaned = raw_name.strip()
    key = cleaned.lower()
    return CANONICAL_NAMES.get(key, cleaned)


def parse_item_arg(spec: str):
    """Parse 'Name=Qty@Price' or 'Name:Qty@Price'."""
    if "=" in spec:
        name, rest = spec.split("=", 1)
    elif ":" in spec:
        name, rest = spec.split(":", 1)
    else:
        raise ValueError(f"Invalid --item format '{spec}'. Expected 'Name=Qty@Price'.")

    if "@" not in rest:
        raise ValueError(f"Invalid --item format '{spec}'. Missing '@Price'.")

    qty_s, price_s = rest.split("@", 1)
    qty = int(qty_s.replace(",", "").strip())
    price = int(price_s.replace(",", "").strip())
    if qty < 0 or price < 0:
        raise ValueError(f"Negative qty/price not allowed in '{spec}'.")
    return normalize_item_name(name), qty, price


def run_gsheets(cmd, retries=3):
    last_err = ""
    for attempt in range(retries):
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout
        last_err = res.stderr.strip() or res.stdout.strip()
        if attempt < retries - 1:
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"gsheets command failed after {retries} attempts: {last_err}")


def gsheets_read_json(range_str: str, render_option: str = "FORMATTED_VALUE"):
    cmd = [
        "gsheets",
        "readonly",
        "read",
        SHEET_ID,
        range_str,
        "--value-render-option",
        render_option,
        "--json",
    ]
    stdout = run_gsheets(cmd).strip()
    return json.loads(stdout) if stdout else []


def parse_num(val) -> int:
    if isinstance(val, (int, float)):
        return int(round(val))
    s = str(val).replace(",", "").replace("+", "").strip()
    if not s:
        return 0
    return int(round(float(s)))


def fetch_preflight_state():
    """Fetch all required state across sheets concurrently in ~1.5s."""
    queries = {
        "tl_fmt": ("'Trading Log'!A240:H", "FORMATTED_VALUE"),
        "tl_fml": ("'Trading Log'!A240:H", "FORMULA"),
        "ssl": ("'Stand Sell Log'!A900:F", "FORMATTED_VALUE"),
        "eod_fmt": ("Analytics!A170:C", "FORMATTED_VALUE"),
        "eod_fml": ("Analytics!A170:C", "FORMULA"),
        "an_summary": ("Analytics!A5:C13", "UNFORMATTED_VALUE"),
        "slots_val": ("Slots!F3", "UNFORMATTED_VALUE"),
    }
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:
        fut_map = {
            ex.submit(gsheets_read_json, rng, opt): key
            for key, (rng, opt) in queries.items()
        }
        for fut in concurrent.futures.as_completed(fut_map):
            key = fut_map[fut]
            results[key] = fut.result()

    # 1. Trading Log last row (start row = 240)
    tl_rows = results["tl_fmt"]
    tl_fml_rows = results["tl_fml"]
    non_empty_tl = [
        (240 + i, r)
        for i, r in enumerate(tl_rows)
        if r and len(r) >= 3 and str(r[2]).strip()
    ]
    if not non_empty_tl:
        raise RuntimeError("Could not locate populated rows in Trading Log!A240:H")
    last_tl_row_idx, last_tl_row = non_empty_tl[-1]
    last_tl_fml_row = tl_fml_rows[last_tl_row_idx - 240]
    m = re.search(r"Stock\s+(\d+)", str(last_tl_row[2]))
    if not m:
        raise RuntimeError(f"Could not parse Stock # from '{last_tl_row[2]}'")
    last_stock_num = int(m.group(1))
    prev_nw = parse_num(last_tl_row[7]) if len(last_tl_row) > 7 else 0
    prev_tl_h_is_formula = (
        len(last_tl_fml_row) > 7 and str(last_tl_fml_row[7]).startswith("=")
    )

    # 2. Stand Sell Log last row (start row = 900)
    ssl_rows = results["ssl"]
    non_empty_ssl = [
        (900 + i, r)
        for i, r in enumerate(ssl_rows)
        if r and len(r) >= 4 and str(r[3]).strip()
    ]
    if not non_empty_ssl:
        raise RuntimeError("Could not locate populated rows in Stand Sell Log!A900:F")
    last_ssl_row_idx, _ = non_empty_ssl[-1]

    # Collect previous stock's items for delta comparison
    last_stock_label = f"Stock {last_stock_num}"
    prev_items = {}
    for _, r in non_empty_ssl:
        if len(r) >= 6 and str(r[2]).strip() == last_stock_label:
            prev_items[str(r[3]).strip()] = (parse_num(r[4]), parse_num(r[5]))

    # 3. Analytics EOD last row (start row = 170)
    eod_rows = results["eod_fmt"]
    eod_fml_rows = results["eod_fml"]
    non_empty_eod = [
        (170 + i, r)
        for i, r in enumerate(eod_rows)
        if r and len(r) >= 1 and str(r[0]).strip()
    ]
    if not non_empty_eod:
        raise RuntimeError("Could not locate EOD rows in Analytics!A170:C")
    last_eod_row_idx, last_eod_row = non_empty_eod[-1]
    last_eod_fml_row = eod_fml_rows[last_eod_row_idx - 170]
    last_eod_date = str(last_eod_row[0]).strip()
    last_eod_nw = parse_num(last_eod_row[1]) if len(last_eod_row) > 1 else prev_nw
    last_eod_ex_slots = (
        parse_num(last_eod_row[2]) if len(last_eod_row) > 2 else prev_nw
    )
    last_eod_is_formula = (
        len(last_eod_fml_row) > 1 and str(last_eod_fml_row[1]).startswith("=")
    )

    # 4. Slots & Buy Orders/Held Inv (keyed by label in Col A)
    an_map = {}
    for row in results["an_summary"]:
        if row and len(row) >= 3 and str(row[0]).strip():
            label = str(row[0]).strip().lower()
            if label != "account component":
                an_map[label] = parse_num(row[2])

    slots_raw = results["slots_val"]
    slots_val = parse_num(slots_raw[0][0]) if slots_raw and slots_raw[0] else 0
    prev_liquid = an_map.get("liquid balance (input):", an_map.get("liquid mush", 0))
    buy_orders_val = an_map.get("stand buy orders", 0)
    held_inv_val = an_map.get("held inventory species", 0)

    return {
        "last_tl_row": last_tl_row_idx,
        "last_stock_num": last_stock_num,
        "prev_nw": prev_nw,
        "prev_liquid": prev_liquid,
        "prev_tl_h_is_formula": prev_tl_h_is_formula,
        "last_ssl_row": last_ssl_row_idx,
        "prev_items": prev_items,
        "last_eod_row": last_eod_row_idx,
        "last_eod_date": last_eod_date,
        "last_eod_nw": last_eod_nw,
        "last_eod_ex_slots": last_eod_ex_slots,
        "last_eod_is_formula": last_eod_is_formula,
        "slots_val": slots_val,
        "buy_orders_val": buy_orders_val,
        "held_inv_val": held_inv_val,
    }


def build_trading_log_row(date_s, time_s, stock_label, items, slots_val, liquid):
    by_name = {name: (qty, price) for name, qty, price in items}
    col_d = (
        f"{by_name['Max Growth Token'][0]}/{by_name['Max Growth Token'][1]}/1"
        if "Max Growth Token" in by_name and by_name["Max Growth Token"][0] > 0
        else ""
    )
    col_e = (
        f"{by_name['Partial Growth Token'][0]}/{by_name['Partial Growth Token'][1]}/1"
        if "Partial Growth Token" in by_name and by_name["Partial Growth Token"][0] > 0
        else ""
    )
    col_f = (
        f"{by_name['Revive Token'][0]}/{by_name['Revive Token'][1]}/1"
        if "Revive Token" in by_name and by_name["Revive Token"][0] > 0
        else ""
    )

    other_parts = []
    for name, qty, price in items:
        if name not in DEDICATED_COLS and qty > 0:
            other_parts.append(f"{name}: {qty}/{price}/1")
    if slots_val > 0:
        other_parts.append(f"Slots: 1/{slots_val}/1")
    other_parts.append(f"Liquid Balance: 1/{liquid}/1")
    col_g = " & ".join(other_parts)

    return [date_s, time_s, stock_label, col_d, col_e, col_f, col_g, "=Analytics!$C$13"]


def build_format_requests(ssl_start_1idx, ssl_count, tl_row_1idx, eod_new_row_1idx):
    reqs = []

    # 1. Stand Sell Log A:G
    s0 = ssl_start_1idx - 1
    s1 = s0 + ssl_count
    sid_ssl = SHEET_IDS["Stand Sell Log"]
    reqs.extend([
        {
            "repeatCell": {
                "range": {"sheetId": sid_ssl, "startRowIndex": s0, "endRowIndex": s1, "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1, "green": 1, "blue": 1},
                        "textFormat": {"fontFamily": "Arial", "fontSize": 10, "bold": False},
                        "verticalAlignment": "BOTTOM",
                        "borders": BORDER_ALL,
                    }
                },
                "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.verticalAlignment,userEnteredFormat.borders",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_ssl, "startRowIndex": s0, "endRowIndex": s1, "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}, "horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_ssl, "startRowIndex": s0, "endRowIndex": s1, "startColumnIndex": 1, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "TIME", "pattern": "hh:mm:ss"}, "horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_ssl, "startRowIndex": s0, "endRowIndex": s1, "startColumnIndex": 2, "endColumnIndex": 3},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_ssl, "startRowIndex": s0, "endRowIndex": s1, "startColumnIndex": 3, "endColumnIndex": 4},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}},
                "fields": "userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_ssl, "startRowIndex": s0, "endRowIndex": s1, "startColumnIndex": 4, "endColumnIndex": 7},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}, "horizontalAlignment": "RIGHT"}},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
            }
        },
    ])

    # 2. Trading Log A:J
    t0 = tl_row_1idx - 1
    t1 = tl_row_1idx
    sid_tl = SHEET_IDS["Trading Log"]
    reqs.extend([
        {
            "repeatCell": {
                "range": {"sheetId": sid_tl, "startRowIndex": t0, "endRowIndex": t1, "startColumnIndex": 0, "endColumnIndex": 10},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1, "green": 1, "blue": 1},
                        "textFormat": {"fontFamily": "Arial", "fontSize": 10, "bold": False},
                        "verticalAlignment": "BOTTOM",
                        "borders": BORDER_ALL,
                    }
                },
                "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.verticalAlignment,userEnteredFormat.borders",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_tl, "startRowIndex": t0, "endRowIndex": t1, "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}, "horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_tl, "startRowIndex": t0, "endRowIndex": t1, "startColumnIndex": 1, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "TIME", "pattern": "hh:mm:ss"}, "horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_tl, "startRowIndex": t0, "endRowIndex": t1, "startColumnIndex": 2, "endColumnIndex": 6},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_tl, "startRowIndex": t0, "endRowIndex": t1, "startColumnIndex": 6, "endColumnIndex": 7},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}},
                "fields": "userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_tl, "startRowIndex": t0, "endRowIndex": t1, "startColumnIndex": 7, "endColumnIndex": 8},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}, "horizontalAlignment": "RIGHT"}},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_tl, "startRowIndex": t0, "endRowIndex": t1, "startColumnIndex": 8, "endColumnIndex": 9},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "+#,##0;-#,##0;0"}, "horizontalAlignment": "RIGHT"}},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_tl, "startRowIndex": t0, "endRowIndex": t1, "startColumnIndex": 9, "endColumnIndex": 10},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.00%"}, "horizontalAlignment": "RIGHT"}},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
            }
        },
    ])

    # 3. Analytics EOD row (if rolled over)
    if eod_new_row_1idx is not None:
        e0 = eod_new_row_1idx - 1
        e1 = eod_new_row_1idx
        sid_an = SHEET_IDS["Analytics"]
        reqs.extend([
            {
                "repeatCell": {
                    "range": {"sheetId": sid_an, "startRowIndex": e0, "endRowIndex": e1, "startColumnIndex": 0, "endColumnIndex": 7},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 1, "green": 1, "blue": 1},
                            "textFormat": {"fontFamily": "Arial", "fontSize": 10, "bold": False},
                            "verticalAlignment": "MIDDLE",
                            "borders": BORDER_ALL,
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.verticalAlignment,userEnteredFormat.borders",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid_an, "startRowIndex": e0, "endRowIndex": e1, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}, "horizontalAlignment": "CENTER"}},
                    "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid_an, "startRowIndex": e0, "endRowIndex": e1, "startColumnIndex": 1, "endColumnIndex": 3},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}, "horizontalAlignment": "RIGHT"}},
                    "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid_an, "startRowIndex": e0, "endRowIndex": e1, "startColumnIndex": 3, "endColumnIndex": 4},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "+#,##0;-#,##0;0"}, "horizontalAlignment": "RIGHT"}},
                    "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid_an, "startRowIndex": e0, "endRowIndex": e1, "startColumnIndex": 4, "endColumnIndex": 5},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.00%"}, "horizontalAlignment": "RIGHT"}},
                    "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid_an, "startRowIndex": e0, "endRowIndex": e1, "startColumnIndex": 5, "endColumnIndex": 6},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "+#,##0;-#,##0;0"}, "horizontalAlignment": "RIGHT"}},
                    "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid_an, "startRowIndex": e0, "endRowIndex": e1, "startColumnIndex": 6, "endColumnIndex": 7},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}, "horizontalAlignment": "RIGHT"}},
                    "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment",
                }
            },
        ])

    return reqs


def verify_all_tabs(new_tl_row, new_ssl_start, new_ssl_count):
    """Run concurrent verification across all 7 tabs + newly written rows."""
    error_tokens = ("#REF!", "#VALUE!", "#N/A", "#DIV/0!", "#NAME?", "#ERROR!")
    checks = {
        "Analytics_top": "Analytics!B4:D15",
        "Analytics_tail": "Analytics!A175:G",
        "Trading_Log_new": f"'Trading Log'!A{new_tl_row}:J{new_tl_row}",
        "Stand_Sell_new": f"'Stand Sell Log'!A{new_ssl_start}:G{new_ssl_start + new_ssl_count - 1}",
        "Buy_Orders": "'Buy Orders & Inv'!A1:J60",
        "Slots": "Slots!A1:J40",
        "Item_Totals": "'Item Totals'!A1:F60",
        "ChartData": "_ChartData!A1:G60",
    }
    out = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        fut_map = {
            ex.submit(gsheets_read_json, rng, "FORMATTED_VALUE"): key
            for key, rng in checks.items()
        }
        for fut in concurrent.futures.as_completed(fut_map):
            key = fut_map[fut]
            out[key] = fut.result()

    errors_found = []
    for key, rows in out.items():
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                s = str(val)
                if any(tok in s for tok in error_tokens):
                    errors_found.append(f"{key}[{r_idx},{c_idx}]={s}")

    return out, errors_found


def main():
    parser = argparse.ArgumentParser(description="Atomic delta sync for Trading Log and Analytics")
    parser.add_argument("--liquid", type=int, required=True, help="Liquid mushroom balance")
    parser.add_argument(
        "--item",
        action="append",
        default=[],
        help="Stand item as 'Name=Qty@Price' (repeat per item)",
    )
    parser.add_argument("--items-json", type=str, help="JSON list of [name, qty, price] or objects")
    parser.add_argument("--timestamp", type=str, help="Override timestamp 'YYYY-MM-DD HH:MM:SS'")
    parser.add_argument("--stock-num", type=int, help="Override Stock number (default: auto next)")
    parser.add_argument("--sheet-id", type=str, help="Override target Google Spreadsheet ID")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Preview operations without writing")
    group.add_argument("--apply", action="store_true", help="Write changes, format, and verify")
    args = parser.parse_args()

    global SHEET_ID
    if args.sheet_id:
        SHEET_ID = args.sheet_id

    items = [parse_item_arg(spec) for spec in args.item]
    if args.items_json:
        raw = json.loads(args.items_json)
        for entry in raw:
            if isinstance(entry, dict):
                items.append((normalize_item_name(entry["name"]), int(entry["qty"]), int(entry["price"])))
            else:
                items.append((normalize_item_name(entry[0]), int(entry[1]), int(entry[2])))

    if not items:
        raise ValueError("Provide at least one stand item via --item or --items-json.")

    if args.timestamp:
        dt = datetime.strptime(args.timestamp, "%Y-%m-%d %H:%M:%S")
    else:
        dt = datetime.now()
    date_s = dt.strftime("%Y-%m-%d")
    time_s = dt.strftime("%H:%M:%S")

    state = fetch_preflight_state()
    next_stock = args.stock_num if args.stock_num is not None else state["last_stock_num"] + 1
    stock_label = f"Stock {next_stock}"

    stand_total = sum(q * p for _, q, p in items)
    expected_nw = args.liquid + stand_total + state["slots_val"] + state["buy_orders_val"] + state["held_inv_val"]
    profit_delta = expected_nw - state["prev_nw"]
    profit_pct = (profit_delta / state["prev_nw"] * 100.0) if state["prev_nw"] else 0.0

    new_tl_row = state["last_tl_row"] + 1
    new_ssl_start = state["last_ssl_row"] + 1
    new_ssl_end = new_ssl_start + len(items) - 1

    date_rolled = date_s > state["last_eod_date"]
    eod_new_row = (state["last_eod_row"] + 1) if date_rolled else None

    ops = [
        {"op": "write", "range": "Analytics!C5", "data": [[args.liquid]]},
    ]

    if date_rolled:
        if state["last_eod_is_formula"]:
            ops.append({
                "op": "write",
                "range": f"Analytics!B{state['last_eod_row']}:C{state['last_eod_row']}",
                "data": [[state["last_eod_nw"], state["last_eod_ex_slots"]]],
            })
        ops.append({
            "op": "write",
            "range": f"Analytics!A{eod_new_row}:C{eod_new_row}",
            "data": [[date_s, "=C13", "=C13-Slots!F3"]],
        })

    if state["prev_tl_h_is_formula"]:
        ops.append({
            "op": "write",
            "range": f"'Trading Log'!H{state['last_tl_row']}",
            "data": [[state["prev_nw"]]],
        })

    tl_row_data = build_trading_log_row(date_s, time_s, stock_label, items, state["slots_val"], args.liquid)
    ops.append({
        "op": "write",
        "range": f"'Trading Log'!A{new_tl_row}:H{new_tl_row}",
        "data": [tl_row_data],
    })

    ssl_rows_data = [[date_s, time_s, stock_label, name, qty, price] for name, qty, price in items]
    ops.append({
        "op": "write",
        "range": f"'Stand Sell Log'!A{new_ssl_start}:F{new_ssl_end}",
        "data": ssl_rows_data,
    })

    fmt_reqs = build_format_requests(new_ssl_start, len(items), new_tl_row, eod_new_row)

    summary = {
        "mode": "DRY_RUN" if args.dry_run else "APPLY",
        "stock": stock_label,
        "timestamp": f"{date_s} {time_s}",
        "date_rollover": date_rolled,
        "target_rows": {
            "Trading Log": new_tl_row,
            "Stand Sell Log": f"{new_ssl_start}-{new_ssl_end}",
            "Analytics EOD": eod_new_row if date_rolled else f"{state['last_eod_row']} (active)",
        },
        "metrics": {
            "liquid": args.liquid,
            "liquid_delta": args.liquid - state["prev_liquid"],
            "stand_total": stand_total,
            "slots": state["slots_val"],
            "expected_net_worth": expected_nw,
            "prev_net_worth": state["prev_nw"],
            "profit_delta": profit_delta,
            "profit_pct": round(profit_pct, 2),
        },
        "items": [
            {
                "name": name,
                "qty": qty,
                "price": price,
                "subtotal": qty * price,
                "prev_qty": state["prev_items"].get(name, (0, 0))[0],
                "prev_price": state["prev_items"].get(name, (0, 0))[1],
                "qty_delta": qty - state["prev_items"].get(name, (0, 0))[0],
            }
            for name, qty, price in items
        ],
    }

    if args.dry_run:
        summary["planned_write_ops"] = ops
        summary["planned_format_req_count"] = len(fmt_reqs)
        print(json.dumps(summary, indent=2))
        return

    # Execute batch value writes
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(ops, tf)
        ops_path = tf.name
    try:
        run_gsheets(["gsheets", "mutate", "batch", SHEET_ID, "--file", ops_path])
    finally:
        os.remove(ops_path)

    # Execute batch formatting
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump({"requests": fmt_reqs}, tf)
        fmt_path = tf.name
    try:
        run_gsheets(["gsheets", "mutate", "raw-batch", SHEET_ID, "--file", fmt_path])
    finally:
        os.remove(fmt_path)

    # Verify live values & zero errors across all 7 tabs
    verified, errors_found = verify_all_tabs(new_tl_row, new_ssl_start, len(items))
    summary["verified_analytics_top"] = verified.get("Analytics_top", [])
    summary["verified_trading_log_row"] = verified.get("Trading_Log_new", [])
    summary["verified_stand_sell_rows"] = verified.get("Stand_Sell_new", [])
    summary["formula_errors"] = errors_found
    print(json.dumps(summary, indent=2))
    if errors_found:
        sys.exit(1)


if __name__ == "__main__":
    main()
