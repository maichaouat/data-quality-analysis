# normalization.py
# Normalization utilities for transactions.

from __future__ import annotations
import re
from typing import Any
import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

# Common timezone abbreviations → IANA names
TZ_ABBREV_MAP = {
    "UTC": "UTC",
    "GMT": "UTC",
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "BST": "Europe/London",
    "CET": "Europe/Berlin",
    "CEST": "Europe/Berlin",
    # Note: "IST" is ambiguous (India/Israel/Ireland). Don’t guess here.
}


def _numeric_timestamp_to_epoch(s: str) -> int | None:
    """
    Detect a numeric timestamp and return epoch seconds (int) if possible.
    Supports seconds, milliseconds, and Excel serial dates.
    """
    try:
        val = float(s)
    except Exception:
        return None

    # Milliseconds (1e12+) or seconds (1e9+)
    if val > 1e12:
        return int(val / 1000)
    if val > 1e9:
        return int(val)

    # Excel serial date
    try:
        return int(pd.to_datetime(val, origin="1899-12-30", unit="D").timestamp())
    except Exception:
        return None


def standardize_timestamp(ts: Any, *, default_tz: str = "UTC", dayfirst: bool = True) -> int | float:
    """
    Convert any timestamp to Unix epoch seconds (UTC).

    Handles:
    - "YYYY-MM-DD HH:MM:SS UTC"
    - "DD/MM/YYYY HH:MM"
    - "2024-07-25 06:42:51 EST"
    - seconds / milliseconds since epoch
    - Excel serial date

    If parsing fails, returns NaN.
    """
    if pd.isna(ts) or str(ts).strip() == "":
        return np.nan

    s = str(ts).strip()

    # Numeric paths
    epoch_num = _numeric_timestamp_to_epoch(s)
    if epoch_num is not None:
        return epoch_num

    # Pull trailing timezone abbrev or explicit " UTC"
    tz_name = None
    s_wo_tz = s

    if s.endswith(" UTC"):
        tz_name = "UTC"
        s_wo_tz = s[:-4].strip()
    else:
        m = re.search(r"\b([A-Za-z]{2,4})$", s)
        if m:
            abbr = m.group(1).upper()
            if abbr in TZ_ABBREV_MAP:
                tz_name = TZ_ABBREV_MAP[abbr]
                s_wo_tz = s[:m.start()].strip()

    # Parse naive datetime and localize
    dt = pd.to_datetime(s_wo_tz, errors="coerce", dayfirst=dayfirst)
    if pd.isna(dt):
        return np.nan

    tz_to_use = tz_name or default_tz
    try:
        dt = dt.tz_localize(ZoneInfo(tz_to_use))
    except Exception:
        dt = dt.tz_localize(ZoneInfo("UTC"))

    return int(dt.timestamp())


def standardize_currency(curr: Any) -> str | float:
    """
    Convert currency to ISO-4217 (3-letter uppercase). Returns NaN if blank.
    """
    if pd.isna(curr) or str(curr).strip() == "":
        return np.nan

    s = str(curr).strip().lower()
    mapping = {
        "$": "USD", "us$": "USD", "usd": "USD", "us dollar": "USD", "u.s. dollar": "USD",
        "€": "EUR", "eur": "EUR", "euro": "EUR",
        "£": "GBP", "gbp": "GBP", "pounds": "GBP",
        "cad": "CAD", "canadian dollar": "CAD",
        "ils": "ILS", "₪": "ILS", "nis": "ILS",
    }
    if s in mapping:
        return mapping[s]

    # Fuzzy match (symbol within string)
    for key, code in mapping.items():
        if key in s:
            return code

    if len(s) == 3 and s.isalpha():
        return s.upper()
    return s.upper()


def standardize_payment_method(value: Any) -> str:
    """
    Normalize payment_method to a small, canonical set.
    - Merge: 'card' / 'credit_card' / 'debit_card' → 'CARD'
    - Keep common wallets/transfers/crypto/ACH
    - Fallback to 'OTHER'
    """
    if value is None:
        return "OTHER"

    s = str(value).strip()
    if not s:
        return "OTHER"
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).upper().strip("_")

    aliases = {
        # cards → one bucket
        "CARD": "CARD",
        "CREDIT_CARD": "CARD",
        "DEBIT_CARD": "CARD",

        # wallets
        "GOOGLE_PAY": "GOOGLE_PAY",
        "APPLE_PAY": "APPLE_PAY",
        "DIGITAL_WALLET": "DIGITAL_WALLET",
        "PAYPAL": "PAYPAL",

        # transfers
        "BANK_TRANSFER": "BANK_TRANSFER",
        "WIRE_TRANSFER": "WIRE_TRANSFER",
        "ACH": "ACH",

        # crypto
        "BITCOIN": "CRYPTO",
        "CRYPTO": "CRYPTO",
    }
    return aliases.get(s, "OTHER")


class DataNormalizer:
    """
    Thin wrapper that applies the existing standardization functions to a DataFrame.
    This does not change logic—just packages the flow for reuse.
    """

    def __init__(self, *, default_tz: str = "UTC", dayfirst: bool = True) -> None:
        self.default_tz = default_tz
        self.dayfirst = dayfirst

    def fix_timestamp_currency_payment(
        self,
        df: pd.DataFrame,
        *,
        ts_col: str,
        curr_col: str,
        pay_col: str,
    ) -> pd.DataFrame:
        """
        Apply timestamp, currency, and payment_method standardization.
        Returns a copy—input is not mutated.
        """
        out = df.copy()
        out[ts_col] = out[ts_col].apply(
            lambda x: standardize_timestamp(x, default_tz=self.default_tz, dayfirst=self.dayfirst)
        )
        out[curr_col] = out[curr_col].apply(standardize_currency)
        out[pay_col] = out[pay_col].apply(standardize_payment_method)
        return out
