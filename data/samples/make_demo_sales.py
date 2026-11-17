"""Write demo_sales.csv: 16 weeks of daily sales ending yesterday, for a demo with live forecasts.

The fixed-date sample files are fine for testing the import, but their dates age, so the dashboard
shows no recent demand. Run this on demo day, create the products below, then import the file.

    python data/samples/make_demo_sales.py
"""
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

DAYS = 16 * 7

# sku -> (average units per day, change per day, weekly swing): steady, growing and seasonal demand.
PRODUCTS = {
    "SKU-100": (12, 0.0, 3),
    "SKU-200": (20, 0.15, 2),
    "SKU-300": (8, 0.0, 6),
}


def main() -> None:
    rng = random.Random(42)
    out = Path(__file__).with_name("demo_sales.csv")
    today = date.today()
    with out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sku", "date", "quantity_sold"])
        for days_ago in range(DAYS, 0, -1):
            day = today - timedelta(days=days_ago)
            t = DAYS - days_ago
            for sku, (base, trend, swing) in PRODUCTS.items():
                qty = base + trend * t + swing * math.sin(2 * math.pi * t / 7) + rng.uniform(-2, 2)
                writer.writerow([sku, day.isoformat(), max(0, round(qty))])
    print(f"Wrote {DAYS * len(PRODUCTS)} rows to {out}")


if __name__ == "__main__":
    main()
