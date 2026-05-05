# Oracle DB connection for ReveniQ AI

**Digital COE Gen AI Team**

Required for running **Required Action** rules (e.g. Rejection Fee Dispute) against the database.

## 1. Configure credentials (.env)

Copy from `.env.example` and set in `.env` (do not commit `.env`):

```env
REVENIQ_DB_USER=ABPAPPO1
REVENIQ_DB_PASSWORD=your_password
REVENIQ_DB_HOST=illnqw1347
REVENIQ_DB_PORT=1521
REVENIQ_DB_SID=TSADB1408
```

## 2. Password verifier (DPY-3015)

If you see:

**`DPY-3015: password verifier type 0x939 is not supported by python-oracledb in thin mode`**

then the server uses an auth method that needs **thick mode** (Oracle Instant Client).

- In `.env` set: `REVENIQ_DB_USE_THICK=1`
- Install **Oracle Instant Client** (64-bit) and either:
  - Add its directory to `PATH`, or
  - Set in `.env`: `REVENIQ_DB_ORACLE_HOME=C:\path\to\instantclient_21_xx`

Download: https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html  
Use the “Basic” or “Basic Light” package; unzip to e.g. `C:\oracle\instantclient_21_12`.

## 3. Test connection

From project root:

```powershell
python scripts/test_db_connection.py
```

With a dispute ID (runs Rejection Fee Dispute rule):

```powershell
python scripts/test_db_connection.py 1234567
```

## 4. If you see DPI-1047

**`DPI-1047: Cannot locate a 64-bit Oracle Client library`**

- Install Oracle Instant Client 64-bit (see link above).
- Add the folder containing `oci.dll` to your `PATH`, or set `REVENIQ_DB_ORACLE_HOME` in `.env` to that folder.
