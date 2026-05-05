-- =============================================================================
-- AR Data: Generate INSERT statements for a customer (PROD -> UT)
-- Run this script in Oracle SQL Developer connected to PROD.
-- Output: INSERT statements appear as a RESULT SET (grid / Script Output).
-- Creator: Digital COE Gen AI Team
-- =============================================================================
--
-- IMPORTANT: Use "Run Script" (Ctrl+Shift+E or Run Script button), not "Run Statement".
-- Results will show in the grid below the script, or in Script Output tab.
-- Edit v_schema and v_customer_id in the DECLARE block. Generated INSERTs use table name only (no schema).
-- PILOT: Set v_table_count := 3 to test with 3 tables only; change to 41 for full run.
--
SET LONG 1000000
SET LINESIZE 32767
SET PAGESIZE 0
SET TRIMSPOOL ON
SET FEEDBACK ON
SET HEADING ON
SET ECHO OFF

-- *** CONFIGURATION: edit the two literals in the DECLARE block below (no & variables) ***
-- Schema that owns AR tables (e.g. ABPAPPO1), and customer ID to copy (e.g. 282406484)

-- Drop temp table if left from a previous run (ignore error if not exists)
BEGIN EXECUTE IMMEDIATE 'DROP TABLE AR_INSERT_OUTPUT_TEMP'; EXCEPTION WHEN OTHERS THEN NULL; END;
/

CREATE TABLE AR_INSERT_OUTPUT_TEMP (line_no NUMBER, insert_stmt CLOB)
/

DECLARE
  v_schema       VARCHAR2(128) := 'ABPAPPO1';      /* PROD schema to read from; change if different */
  v_customer_id  NUMBER        := 282406484;       /* customer ID to copy */

  TYPE t_table_rec IS RECORD (tname VARCHAR2(128), where_clause VARCHAR2(4000));
  TYPE t_table_tab IS TABLE OF t_table_rec INDEX BY PLS_INTEGER;
  v_tables      t_table_tab;

  v_sql         CLOB;
  v_col_list    CLOB;
  v_val_exprs   CLOB;
  v_val_one     VARCHAR2(4000);
  v_ins         CLOB;
  v_cur         SYS_REFCURSOR;
  v_line_no     NUMBER := 0;
  v_q           VARCHAR2(1);
  v_concat      VARCHAR2(10);   /* holds space-pipe-pipe-space to avoid parser issues */
  v_table_count PLS_INTEGER := 3;   /* 3 = pilot (AR1_ACCOUNT, AR1_BILLING_ARRANGEMENT, AR1_ADDRESS_NAME); 41 = all tables */
BEGIN
  v_q      := CHR(39);
  v_concat := CHR(32) || CHR(124) || CHR(124) || CHR(32);   /* ' || ' */
  INSERT INTO AR_INSERT_OUTPUT_TEMP (line_no, insert_stmt) VALUES (v_line_no, '-- AR INSERT statements for CUSTOMER_NO = ' || v_customer_id || ', schema ' || v_schema);
  v_line_no := v_line_no + 1;
  INSERT INTO AR_INSERT_OUTPUT_TEMP (line_no, insert_stmt) VALUES (v_line_no, '-- Run these on UT. INSERTs use table name only (no schema prefix).');
  v_line_no := v_line_no + 1;
  INSERT INTO AR_INSERT_OUTPUT_TEMP (line_no, insert_stmt) VALUES (v_line_no, '');
  v_line_no := v_line_no + 1;
  COMMIT;
  -- Table order: parent -> child (by ACCOUNT_ID / CUSTOMER_NO / child keys)
  v_tables(1).tname := 'AR1_ACCOUNT'; v_tables(1).where_clause := 'CUSTOMER_NO = ' || v_customer_id;
  v_tables(2).tname := 'AR1_BILLING_ARRANGEMENT'; v_tables(2).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(3).tname := 'AR1_ADDRESS_NAME'; v_tables(3).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(4).tname := 'AR1_INVOICE'; v_tables(4).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(5).tname := 'AR1_PAYMENT'; v_tables(5).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(6).tname := 'AR1_CHARGES'; v_tables(6).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(7).tname := 'AR1_CHARGE_GROUP'; v_tables(7).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(8).tname := 'AR1_TAX_ITEM'; v_tables(8).where_clause := 'CHARGE_ID IN (SELECT CHARGE_ID FROM ' || v_schema || '.AR1_CHARGES WHERE ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')) OR CREDIT_ID IN (SELECT CREDIT_ID FROM ' || v_schema || '.AR1_CUSTOMER_CREDIT WHERE ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || '))';
  v_tables(9).tname := 'AR1_PAYMENT_DETAILS'; v_tables(9).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(10).tname := 'AR1_AGED_TRIAL_BALANCE'; v_tables(10).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(11).tname := 'AR1_CL_STATUS'; v_tables(11).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(12).tname := 'AR1_CREDIT_DEBIT_LINK'; v_tables(12).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(13).tname := 'AR1_CUSTOMER_CREDIT'; v_tables(13).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(14).tname := 'AR1_DEPOSIT_REQUEST'; v_tables(14).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(15).tname := 'AR1_DIRECT_DEBIT_REQUEST'; v_tables(15).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(16).tname := 'AR1_DISPUTE'; v_tables(16).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(17).tname := 'AR1_DISPUTE_ACTIVITY'; v_tables(17).where_clause := 'DISPUTE_ID IN (SELECT DISPUTE_ID FROM ' || v_schema || '.AR1_DISPUTE WHERE ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || '))';
  v_tables(18).tname := 'AR1_EXTERNAL_REFERENCES'; v_tables(18).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(19).tname := 'AR1_MEMO'; v_tables(19).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(20).tname := 'AR1_PAYMENT_ACTIVITY'; v_tables(20).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(21).tname := 'AR1_PAY_CHANNEL'; v_tables(21).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(22).tname := 'AR1_PAY_SLIP'; v_tables(22).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(23).tname := 'AR1_PROOF_AND_BALANCE'; v_tables(23).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(24).tname := 'AR1_REFUND_REQUEST'; v_tables(24).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(25).tname := 'AR1_TRANSACTION_LOG'; v_tables(25).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(26).tname := 'AR1_UNAPPLIED_CREDIT'; v_tables(26).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(27).tname := 'AR1_WRITE_OFF'; v_tables(27).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(28).tname := 'AR1_GL_DATA'; v_tables(28).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(29).tname := 'AR1_GL_DETAILED_DATA'; v_tables(29).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(30).tname := 'AR1_COLL_EXTRACT_TEMP'; v_tables(30).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(31).tname := 'AR1_LATEST_INVOICE_TEMP'; v_tables(31).where_clause := 'CUSTOMER_NO = ' || v_customer_id;
  v_tables(32).tname := 'AR9_BALANCE_TRANSFER'; v_tables(32).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(33).tname := 'AR9_NOTIFICATIONS'; v_tables(33).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(34).tname := 'AR9_PAYMENT_REQUEST'; v_tables(34).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(35).tname := 'AR9_PAYMENT_REQUEST_LINK'; v_tables(35).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(36).tname := 'AR9_UNCONFIRMED_PYM'; v_tables(36).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(37).tname := 'AR9_LPF_PAST_DUE_LOG'; v_tables(37).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(38).tname := 'AR9_GL_DET_DATA'; v_tables(38).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(39).tname := 'AR9_GL_DET_DATA_TMP'; v_tables(39).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(40).tname := 'AR9_GL_EXTRACT_DATA'; v_tables(40).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';
  v_tables(41).tname := 'AR9_PERIOD_KEY'; v_tables(41).where_clause := 'ACCOUNT_ID IN (SELECT ACCOUNT_ID FROM ' || v_schema || '.AR1_ACCOUNT WHERE CUSTOMER_NO = ' || v_customer_id || ')';

  FOR t IN 1..v_table_count LOOP
    BEGIN
      v_col_list := NULL;
      v_val_exprs := NULL;
      FOR rec IN (
        SELECT column_name, data_type
        FROM all_tab_columns
        WHERE owner = v_schema AND table_name = v_tables(t).tname
        ORDER BY column_id
      ) LOOP
        v_col_list := v_col_list || CASE WHEN v_col_list IS NOT NULL THEN ',' END || rec.column_name;
        IF rec.data_type IN ('NUMBER','FLOAT','BINARY_FLOAT','BINARY_DOUBLE') THEN
          v_val_one := 'CASE WHEN ' || rec.column_name || ' IS NULL THEN ''NULL'' ELSE TO_CHAR(' || rec.column_name || ') END';
        ELSIF rec.data_type IN ('DATE','TIMESTAMP','TIMESTAMP WITH TIME ZONE','TIMESTAMP WITH LOCAL TIME ZONE') THEN
          v_val_one := 'CASE WHEN ' || rec.column_name || ' IS NULL THEN ''NULL'' ELSE ''TO_DATE(''''||TO_CHAR(' || rec.column_name || ',''''SYYYY-MM-DD HH24:MI:SS'''')||'''',''''SYYYY-MM-DD HH24:MI:SS'''')'' END';
        ELSE
          v_val_one := 'CASE WHEN ' || rec.column_name || ' IS NULL THEN ''NULL'' ELSE ''''||REPLACE(REPLACE(NVL(TO_CHAR(' || rec.column_name || '),''''''''),'''''''','''''''''''''''''),CHR(0),'''')||'''' END';
        END IF;
        v_val_exprs := v_val_exprs || CASE WHEN v_val_exprs IS NOT NULL THEN '||'',''||' END || v_val_one;
      END LOOP;
      IF v_col_list IS NULL THEN RAISE NO_DATA_FOUND; END IF;

      v_sql := 'SELECT ' || v_q || 'INSERT INTO ' || v_tables(t).tname || ' (' || v_col_list || CHR(41) || ' VALUES (' || v_q;
      v_sql := v_sql || v_concat || v_val_exprs || v_concat || v_q || CHR(41) || CHR(59) || v_q || ' FROM ' || v_schema || '.' || v_tables(t).tname || ' WHERE ' || v_tables(t).where_clause;

      OPEN v_cur FOR v_sql;
      LOOP
        FETCH v_cur INTO v_ins;
        EXIT WHEN v_cur%NOTFOUND;
        v_line_no := v_line_no + 1;
        INSERT INTO AR_INSERT_OUTPUT_TEMP (line_no, insert_stmt) VALUES (v_line_no, v_ins);
      END LOOP;
      CLOSE v_cur;
    EXCEPTION WHEN OTHERS THEN
      IF v_cur%ISOPEN THEN CLOSE v_cur; END IF;
      v_line_no := v_line_no + 1;
      INSERT INTO AR_INSERT_OUTPUT_TEMP (line_no, insert_stmt) VALUES (v_line_no, '-- Error ' || v_tables(t).tname || ': ' || SQLERRM);
    END;
  END LOOP;

  v_line_no := v_line_no + 1;
  INSERT INTO AR_INSERT_OUTPUT_TEMP (line_no, insert_stmt) VALUES (v_line_no, '');
  v_line_no := v_line_no + 1;
  INSERT INTO AR_INSERT_OUTPUT_TEMP (line_no, insert_stmt) VALUES (v_line_no, '-- End of INSERTs for customer ' || v_customer_id);
  COMMIT;
END;
/

-- Show all generated INSERT statements (this result appears in the grid / Script Output)
SELECT insert_stmt FROM AR_INSERT_OUTPUT_TEMP ORDER BY line_no
/

-- Optional: drop the temp table when done (uncomment to clean up)
-- DROP TABLE AR_INSERT_OUTPUT_TEMP;
