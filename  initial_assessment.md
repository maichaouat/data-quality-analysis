# Executive Communication – Initial Findings & Plan

## Key Findings
- Multiple records in both `transactions` and `users` tables are misaligned, causing corrupted values in critical fields.
- Inconsistent formatting in `currency` and `timestamp` fields is impacting aggregation, revenue calculations, and time-based analysis.
- A subset of approved transactions have `user_id` values not present in the `users` table, creating reconciliation gaps and potential compliance risks.

## Planned Approach
- Systematically profile both datasets to quantify the scope of each issue.
- Apply targeted data cleaning: realign misaligned rows, standardize currency formats and timestamps, and investigate missing user references using alternate matching logic.

## Immediate Concerns
- Revenue reporting may be inaccurate if currency inconsistencies and unlinked approved transactions are not addressed before the upcoming board meeting.
- Potential compliance and audit risks if transactions remain unassociated with valid user records.
