#!/usr/bin/env python3
"""
Utility script to fetch Jupiter prediction market metadata and OG image.
Usage:
    python3 fetch_market_odds.py POLY-1197460
    python3 fetch_market_odds.py https://jup.ag/prediction/POLY-1197460
"""

import sys
import re
import subprocess
import os

def extract_event_id(input_str: str) -> str:
    match = re.search(r'(POLY-\d+)', input_str)
    if match:
        return match.group(1)
    return input_str.strip()

def download_og_image(event_id: str, dest_dir: str = "/tmp") -> str:
    url = f"https://jup.ag/api/prediction/{event_id}/og.png"
    out_path = os.path.join(dest_dir, f"{event_id}_og.png")
    cmd = ["curl", "-s", "-L", url, "-o", out_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        return out_path
    return ""

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_market_odds.py <event_id_or_url>")
        sys.exit(1)
    
    event_id = extract_event_id(sys.argv[1])
    print(f"Target Event ID: {event_id}")
    img_path = download_og_image(event_id)
    if img_path:
        print(f"OG Image downloaded to: {img_path}")
        print(f"View this image with view_file to confirm current odds and prices.")
    else:
        print(f"Failed to download valid OG image for {event_id}")
        sys.exit(1)

if __name__ == "__main__":
    main()
