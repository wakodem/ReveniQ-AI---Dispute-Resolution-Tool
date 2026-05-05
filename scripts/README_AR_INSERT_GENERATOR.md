# AR Data: Generate INSERTs for Customer (PROD → UT)

**Creator:** Digital COE Gen AI Team

This script generates `INSERT` statements for all AR (AR1% and AR9%) data for a given customer so you can copy the data from **PROD** and run it on **UT** in Oracle SQL Developer.

## What it does

- **Input:** Customer ID (e.g. `282406484`) and schema (e.g. `ABPAPPO1`).
- **Output:** One `INSERT` per row for AR tables, in **dependency order** (parents before children) so you can run them on UT without foreign key errors.

### Table order (parent → child)

1. **AR1_ACCOUNT** (root; filter: `CUSTOMER_NO = &customer_id`)
2. **AR1_BILLING_ARRANGEMENT**, **AR1_ADDRESS_NAME**, **AR1_INVOICE**, **AR1_PAYMENT**
3. **AR1_CHARGES**, **AR1_CHARGE_GROUP**
4. **AR1_TAX_ITEM** (by CHARGE_ID / CREDIT_ID)
5. **AR1_PAYMENT_DETAILS**, **AR1_AGED_TRIAL_BALANCE**, **AR1_CL_STATUS**, **AR1_CREDIT_DEBIT_LINK**, **AR1_CUSTOMER_CREDIT**, **AR1_DEPOSIT_REQUEST**, **AR1_DIRECT_DEBIT_REQUEST**, **AR1_DISPUTE**, **AR1_DISPUTE_ACTIVITY**, **AR1_EXTERNAL_REFERENCES**, **AR1_MEMO**, **AR1_PAYMENT_ACTIVITY**, **AR1_PAY_CHANNEL**, **AR1_PAY_SLIP**, **AR1_PROOF_AND_BALANCE**, **AR1_REFUND_REQUEST**, **AR1_TRANSACTION_LOG**, **AR1_UNAPPLIED_CREDIT**, **AR1_WRITE_OFF**
6. **AR1_GL_DATA**, **AR1_GL_DETAILED_DATA**, **AR1_COLL_EXTRACT_TEMP**, **AR1_LATEST_INVOICE_TEMP**
7. **AR9_*** tables: **AR9_BALANCE_TRANSFER**, **AR9_NOTIFICATIONS**, **AR9_PAYMENT_REQUEST**, **AR9_PAYMENT_REQUEST_LINK**, **AR9_UNCONFIRMED_PYM**, **AR9_LPF_PAST_DUE_LOG**, **AR9_GL_DET_DATA**, **AR9_GL_DET_DATA_TMP**, **AR9_GL_EXTRACT_DATA**, **AR9_PERIOD_KEY**

Relationships were derived from the schema (e.g. `AR1_ACCOUNT.CUSTOMER_NO`, child tables with `ACCOUNT_ID`, **AR1_TAX_ITEM** by **CHARGE_ID**/**CREDIT_ID**, **AR1_DISPUTE_ACTIVITY** by **DISPUTE_ID**). No FKs are defined in the connected schema; order is based on these logical links.

## How to use

### 1. Configure (top of script)

Edit in the script:

- `DEFINE V_SCHEMA     = ABPAPPO1`  → PROD schema that owns AR1/AR9 tables.
- `DEFINE V_CUSTOMER_ID = 282406484` → Customer to copy.

### 2. Run on PROD (Oracle SQL Developer)

- Connect to **PROD**.
- Open `ar_generate_inserts_for_customer.sql`.
- (Optional) Uncomment and set **SPOOL** to write output to a file, e.g.  
  `SPOOL C:\temp\ar_inserts_customer_282406484.sql`
- Run the script (F5 or Run Script).
- Output is in the **Script Output** (or the spool file). Each line is one full `INSERT` statement.

### 3. Run on UT

- Connect to **UT** in SQL Developer.
- If UT uses a **different schema**, do a find/replace on the generated file (e.g. replace `ABPAPPO1` with the UT schema).
- Run the generated `INSERT` statements in the same order (e.g. paste into a worksheet and Run Script). Order is already correct for dependencies.

## Notes

- **SET DEFINE OFF** is used so date format strings (e.g. `HH24:MI:SS`) are not treated as substitution variables.
- **Spool:** For large result sets, spooling to a file is more reliable than copying from the grid.
- **Long strings / CLOB:** The generator uses `TO_CHAR(...)` for string columns. Very long or CLOB values may need manual handling if they are truncated or cause issues.
- **Schema:** The script uses the schema you defined (`V_SCHEMA`) in both the generated `INSERT` table name and the `WHERE` subqueries. Change the schema in the generated file if PROD and UT use different schema names.

## Files

| File | Purpose |
|------|--------|
| `ar_generate_inserts_for_customer.sql` | Run on PROD; prints INSERT statements in dependency order. |
| `README_AR_INSERT_GENERATOR.md` | This file. |
