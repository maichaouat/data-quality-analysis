import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo
from normalization import DataNormalizer
from typing import List, Any

from USDAmountConverter import USDAmountConverter


def align_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aligns rows where there is a value in an unnamed column (empty header).
    For such rows, shift cells starting from column C (index 2) one position to the left.
    """
    df_aligned = df.copy()
    # Identify unnamed columns
    unnamed_cols = [col for col in df.columns if str(col).startswith("Unnamed")]
    for col in unnamed_cols:
        # Find rows where unnamed column has a value
        mask = df_aligned[col].notna() & (df_aligned[col] != "")
        for idx in df_aligned[mask].index:
            # Shift values from col C (index 2) left by 1
            row_vals = df_aligned.loc[idx].values.tolist()
            start_idx = 2  # column C index
            shifted_part = row_vals[start_idx:]
            shifted_part = shifted_part[1:] + [np.nan]  # shift left
            new_row = row_vals[:start_idx] + shifted_part
            df_aligned.loc[idx] = new_row
    return df_aligned



def missing_user_trans_ids(
    trans_df: pd.DataFrame,
    id_col: str,
    usr_col: str,
    users_list: List[Any]
) -> List[Any]:
    """
    Return a list of transaction IDs (from `id_col`) whose user (in `usr_col`) is NOT in `users_list`.

    Notes:
    - Rows with NaN in `usr_col` are treated as "not found".
    - `id_col` must exist in trans_df (e.g., 'transaction_id').
    """
    if id_col not in trans_df.columns:
        raise ValueError(f"trans_df must contain the '{id_col}' column.")

    valid_users = set(users_list)
    mask = trans_df[usr_col].isna() | ~trans_df[usr_col].isin(valid_users)
    return trans_df.loc[mask, id_col].dropna().unique().tolist()


# --- Load and align
df_tx = pd.read_excel("data/Test_TRX_USR.xlsx", sheet_name="Transactions")
df_tx_aligned = align_table(df_tx)

# --- Normalize timestamp / currency / payment_method (same logic, wrapped in a class)
normalizer = DataNormalizer(default_tz="UTC", dayfirst=True)
df_tx_aligned_fixed = normalizer.fix_timestamp_currency_payment(
    df_tx_aligned, ts_col="timestamp", curr_col="currency", pay_col="payment_method"
)

# --- Convert amounts to USD (unchanged)
conv = USDAmountConverter()
df_tx_usd = conv.add_amount_usd(
    df_tx_aligned_fixed,
    amount_col="amount",
    currency_col="currency",
    save_path="data/transactions_with_amount_usd.xlsx",
    strict=False,
    refresh_rates=True,
)

# --- Save aligned transactions (unchanged)
pd.DataFrame(df_tx_aligned_fixed).to_excel("data/transactions_aligned_simple.xlsx", index=False)

# --- Users sheet (unchanged)
df_usr = pd.read_excel("data/Test_TRX_USR.xlsx", sheet_name="Users")
df_usr_aligned = align_table(df_usr)
df_usr_aligned.to_excel("data/users_aligned_simple.xlsx", index=False)

# --- Orphaned users (unchanged)
bad_ids = missing_user_trans_ids(
    df_tx_aligned_fixed,
    id_col="transaction_id",
    usr_col="user_id",
    users_list=df_usr_aligned["user_id"],
)
pd.DataFrame({"transaction_id": bad_ids}).to_excel("data/trans_id_with_unmatched_userid.xlsx", index=False)