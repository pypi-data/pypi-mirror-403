Syncy
=====

Syncy is a lightweight database migration validation tool for comparing logic and schema objects between SQL Server and PostgreSQL. It focuses on safe, read-only validation and produces HTML + JSON reports.

Features
- Read-only connectors for MSSQL (pyodbc) and Postgres (psycopg2-binary)
- Extract views, functions, procedures, triggers metadata/definitions
- Built-in rule pack (10 cross-engine mismatch checks)
- Simple behaviour tests on views (sample shape comparison)
- Timestamped HTML + JSON reports

Quick Start
0. (Recommended) Create and activate a virtual environment
   - Windows (PowerShell):
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
   - macOS/Linux:
     python3 -m venv .venv
     source .venv/bin/activate

1. Install dependencies (Python 3.10+):
   pip install -r requirements.txt

2. Provide connection URLs via flags, YAML, or env:
   - Flags: --source, --target
   - YAML: validator.yaml (see example below)
   - Env: SYNCY_SOURCE_URL, SYNCY_TARGET_URL

3. Seed sample schemas into your own SQL Server/Postgres (optional):
   python demo/load_samples.py --source "mssql://sa:Your_password123@localhost:1433/master?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes" --target "postgresql://postgres:postgres@localhost:5432/syncy?sslmode=disable"

4. Run validation:
   syncy validate --source "mssql://sa:Your_password123@localhost:1433/master?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes" \
                  --target "postgresql://postgres:postgres@localhost:5432/syncy?sslmode=disable" \
                  --out ./reports/demo/

Config Resolution Order
1) CLI flags > 2) validator.yaml > 3) environment variables.

validator.yaml example
source:
  url: ${SYNCY_SOURCE_URL}
target:
  url: ${SYNCY_TARGET_URL}
include_schemas: [public]
exclude_schemas: []

Notes
- All queries run in safe mode. Obvious write operations are blocked.
- Reports are written to a timestamped folder under the provided --out or ./reports/.
- For production environments, you may swap psycopg2-binary for psycopg2 in requirements.

License
MIT
