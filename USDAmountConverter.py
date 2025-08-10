import os
from typing import Dict, Iterable, Optional
import pandas as pd
import requests


class USDAmountConverter:
    """
    Convert amounts to USD by adding `amount_usd` (and `fx_to_usd`) to a DataFrame.
    Assumes `currency` values are already normalized ISO-4217 codes (e.g., USD, EUR, GBP).
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        # Stored convention: 1 USD = rate units of CURRENCY (e.g., {'EUR': 0.92})
        self._rates: Dict[str, float] = {"USD": 1.0}

    def _fetch_rates(self, symbols: Iterable[str]) -> Dict[str, float]:
        url = "https://v6.exchangerate-api.com/v6/6a58224f99e9f5641c0df7b2/latest/USD"
        r = requests.get(url, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()

        if data.get("result") != "success":
            raise RuntimeError(f"API error: {data}")

        rates = data.get("conversion_rates", {}) or {}
        rates["USD"] = 1.0

        # Filter only to requested symbols if provided
        syms = {str(s).upper().strip() for s in symbols if pd.notna(s)}
        if len(syms) > 0:
            rates = {k: v for k, v in rates.items() if k in syms}

        return rates

    def set_rates(self, rates: Dict[str, float]) -> None:
        """
        Manually set rates. Same convention: 1 USD = rate units of currency.
        """
        cleaned = {str(k).upper().strip(): float(v) for k, v in rates.items()}
        cleaned["USD"] = 1.0
        self._rates.update(cleaned)

    def add_amount_usd(
        self,
        df: pd.DataFrame,
        amount_col: str = "amount",
        currency_col: str = "currency",
        save_path: Optional[str] = None,
        inplace: bool = False,
        strict: bool = False,
        refresh_rates: bool = True,
    ) -> pd.DataFrame:
        """
        Add `amount_usd` for every row using latest FX (or manually provided rates).

        Parameters
        ----------
        df : DataFrame with `amount_col` and `currency_col`.
        amount_col : numeric column to convert (coerced with `pd.to_numeric`).
        currency_col : ISO-4217 codes (already normalized).
        save_path : optional .xlsx path to save the result.
        inplace : if True, modify `df` in place and return it.
        strict : if True, raise on missing/zero FX for any currency.
        refresh_rates : if True, fetch rates for the currencies present in `df`.
        """
        out = df if inplace else df.copy()

        cur = out[currency_col].astype(str).str.upper().str.strip()
        amt = pd.to_numeric(out[amount_col], errors="coerce")

        if refresh_rates:
            self._rates.update(self._fetch_rates(cur.unique()))

        # Build USD-per-currency factor (invert because stored rates are currency per 1 USD)
        inv = {}
        for c in cur.unique():
            rate = self._rates.get(c)
            try:
                rate = float(rate)
                if rate == 0.0 or rate is None:
                    if strict:
                        raise ValueError(f"Missing/zero FX rate for currency '{c}'")
                    inv[c] = float("nan")
                else:
                    inv[c] = 1.0 / rate  # 1 CURRENCY -> ? USD
            except (TypeError, ValueError):
                if strict:
                    raise ValueError(f"Invalid FX rate for currency '{c}': {rate!r}")
                inv[c] = float("nan")

        out["fx_to_usd"] = cur.map(inv)
        out["amount_usd"] = amt * out["fx_to_usd"]

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            out.to_excel(save_path, index=False)

        return out
