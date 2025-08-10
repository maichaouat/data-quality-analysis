
# Requirements: pip install pandas openpyxl duckdb
# Purpose: 1) convert XLSX -> CSV, 2) run SQL file, 3) export one Excel with three sheets.

import os
from pathlib import Path
import pandas as pd
import duckdb

DATA_DIR = Path("data")
OUT_DIR = Path("out")
SQL_FILE = Path("business_queries.sql")

TX_XLSX = DATA_DIR / "transactions_with_amount_usd.xlsx"
USERS_XLSX = DATA_DIR / "users_aligned_simple.xlsx"

TX_CSV = DATA_DIR / "transactions_with_amount_usd.csv"
USERS_CSV = DATA_DIR / "users_aligned_simple.csv"

# Outputs written by the SQL file (must match your SQL!)
OUT_REVENUE_BY_CAT = OUT_DIR / "revenue_by_merchant_category.csv"
OUT_CONF_MATRIX    = OUT_DIR / "confusion_matrix_risk_score.csv"
OUT_PM_SUCCESS     = OUT_DIR / "payment_method_integration_success.csv"

OUT_XLSX = OUT_DIR / "bettercharge_analysis_combined.xlsx"

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) XLSX -> CSV (always refresh so SQL sees latest data)
    pd.read_excel(TX_XLSX, engine="openpyxl").to_csv(TX_CSV, index=False)
    if USERS_XLSX.exists():
        pd.read_excel(USERS_XLSX, engine="openpyxl").to_csv(USERS_CSV, index=False)
    print("OK: wrote CSVs to data/*.csv")

    # 2) Run the SQL (UTF-8)
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_script = f.read()
    duckdb.connect().execute(sql_script)
    print("Done running SQL.")

    # 3) Build a single Excel workbook with three sheets
    df1 = pd.read_csv(OUT_REVENUE_BY_CAT)
    df2 = pd.read_csv(OUT_CONF_MATRIX)
    df3 = pd.read_csv(OUT_PM_SUCCESS)

    with pd.ExcelWriter(OUT_XLSX) as w:
        df1.to_excel(w, sheet_name="Revenue by Category", index=False)
        df2.to_excel(w, sheet_name="Risk Confusion Matrix", index=False)
        df3.to_excel(w, sheet_name="Payment Method Success", index=False)

    print(f"Wrote {OUT_XLSX}")

if __name__ == "__main__":
    main()
