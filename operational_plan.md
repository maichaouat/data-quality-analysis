# Operational Plan 
## Goals & Core Setup
- Keep data **accurate and fresh** at all times.
- Define a clear **data format** with payment methods (fields, valid values, timezone, delivery cadence, retries).
- Centralize **standardization** in one shared library:
  - Timestamps → **UTC**.
  - Currency → **ISO‑4217**, with up‑to‑date FX.
  - `payment_method` → map **card/credit/debit → CARD** (one canonical name).
- Ingestion guards:
  - **Deduplicate** by `transaction_id` (exactly‑once writes).
  - Enforce **required fields**: `status`, `amount`, `currency`, `timestamp`, `user_id`.
  - **Referential integrity**: each `user_id` must exist in **users**.
  - Quarantine bad rows with a **reason code** (don’t block the whole batch).


## Monitoring (hourly + daily)
- **Transaction volume** vs baseline (same weekday last week) + **last load time**.
- **Failure rate by payment method** and **by merchant category** (today vs same weekday last week).
- **Orphaned `user_id` rate** (transactions that don’t join to users).
- **FX freshness** (latest update within 24 hours).
- **Risk model health @ 0.65**: precision, recall, accuracy, and big mix shifts.

## Alerts (Slack / on‑call)
- **Low volume**: attempts ↓ **>30%** vs baseline for **2 consecutive hours** → **Severity‑1**.
- **Failure spike**: method/category failure rate and attempts spikes. **Severity‑1**
- **Data violations**: orphaned `user_id` **>0.5%**, **FX stale >24h**, or **schema changes** → **Severity‑2** (open ticket + Slack).
- **Model drift**: precision or recall **drops >5%** → **Severity‑2** (attach confusion‑matrix snapshot).

## Runbooks
- One **1‑page checklist per alert**: what to check, who owns it, and the first action (e.g., temporarily **route more traffic to wallets** until recovery).

## Week‑1 Deliverables
- **Data contract signed** with the partner.
- **Standardization library** plugged into ETL.
- **Quality tests live** (freshness, volume, uniqueness, required fields, enums, referential integrity).
- **Dashboard published** (metrics above) and **alerts wired** to Slack.
- **Fix orphaned `user_id`** in ingestion (key normalization + log audit).
