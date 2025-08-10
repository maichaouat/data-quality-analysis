# BetterCharge — Quick Start

A minimal pipeline to clean the data, convert amounts to USD, and produce board-ready metrics.

## How to Run
1) **Process data** - read the file name _"Test_TRX_USR.xlsx"_
```bash
python data_processing.py
```
2) **Run SQL reports**
```bash
python sql-run.py
```
Results are written to the **out/** folder. Inputs live under **data/**.

## Project Layout
```
data/                       # input & intermediate files
out/                        # results (CSV/Excel)
business_queries.sql        # DuckDB queries (3 core reports)
data_processing.py          # cleans/normalizes, adds amount_usd
sql-run.py                  # converts to CSV (if needed) + runs SQL + writes reports
initial_assessment.md       # Part A analysis 
data_processing.py          # Part B code 
business_queries.sql        # Part C SQL queries 
executive_summary.pdf       # Part D findings 
operational_plan.md         # Part E recommendations 
README.md                   # Instructions and overview 

```

---



# Important Notes

## Decision-Making & Documentation
- **Prioritization rationale.**  focused first on: 
1. Reliable USD conversion and fields normalization
2. Sum of amount by merchant category 
3. Failure rates by payment method
4. Risk threshold analysis (0.60–0.65). 
These directly affect revenue, approval rate, and the board discussion.
- **Assumptions are explicit.** I assume `status ∈ {success, failed}`, `amount_usd` is the revenue basis for successful transactions, currencies are convertible via the latest FX, and payment methods are normalized (card/credit/debit → `CARD`).

## Business Focus
- **Practical & actionable.** Outputs are simple tables and a PDF summary, with a clear recommendation to set the risk threshold to **0.65** and prefer wallets where applicable.
- **Stakeholder impact.**
  - **Finance:** clean sum of amount in USD; view of categories dragging conversion.
  - **Product/Risk:** threshold choice (0.65), failure patterns, and top decline areas to fix.
  - **Engineering:** pipeline checks, normalization, and data contracts.
  - **Compliance:** visibility into categories like gambling and user join integrity.
- **Revenue & risk.** prioritized items that move approval rate and revenue, and reduce fraud/chargeback exposure.

## Production Mindset
- **Ongoing operations.** Design assumes daily/hourly refresh: automatic conversions, checks, and exports.
- **Scale.** Pipelines deduplicate by `transaction_id`, normalize with a shared library, and can be scheduled. 
- **Monitoring.** Track failure rate by payment method and category (today vs same weekday last week), data freshness, FX age, and orphaned users. Alert on volume drops and failure spikes.

## Comprehensive Documentation
- **This README** summarizes assumptions, reasoning, and steps to run.
- **What I didn’t fix yet (by design):**
  - **User approvals (KYC).** Each transaction with `status = success` should belong to an **approved** user. We did not enforce this join in code because some `user_id` values were missing in the users file. Without logs, I can’t confirm if the users table is complete. **Next:** fix the ingestion join and add a KYC status check.
  - **Revenue model.**  calculated revenue as the **sum of successful `amount_usd`**. If BetterCharge earns a commission, replace with `commission_rate * amount_usd` or fee tables as applicable.
- **Business recommendations (summary):**
  - Set risk threshold to **0.65** now; A/B test against **0.60** for confirmation.
  - Prefer **wallets** (Google/Apple Pay) over `CARD` where possible.
  - Review **Gambling** (0% approvals) and **Food Delivery** routes/declines.
  - Repair **user_id ↔ users** joins (keys/logs), then add KYC gating for revenue.

## Resources
Use any tools needed (Pandas, DuckDB, Great Expectations/dbt for checks). The goal is a practical, real-world approach.

## Questions?
If anything is unclear, please reach out. We’re happy to help ensure the best outcome.

---

# Assumptions (Explicit)
- `status = success` indicates an approved transaction that contributes to revenue.
- FX rates are available and recent; `amount_usd` is computed as `amount * fx_to_usd`.
- Payment methods are normalized to a small set (CARD, GOOGLE_PAY, APPLE_PAY, DIGITAL_WALLET, PAYPAL, BANK_TRANSFER, WIRE_TRANSFER, ACH, CRYPTO).
- Timestamps are standardized to UTC epoch seconds.
- Number of nullified values was minor, so no strategy was taken to handle nullified rows in this stage of project.

# Known Gaps / Deferred Items
- **KYC/Approval gate not enforced** in this version. I will add a join to user KYC status so only KYC-approved users count toward revenue.
- **Users table completeness.** Some transactions reference `user_id` not present in `users`. We exported these to Excel for log investigation.
- **Commission model.** If revenue depends on fees, replace the simple sum with a commission calculation (flat/percent/tiered).


