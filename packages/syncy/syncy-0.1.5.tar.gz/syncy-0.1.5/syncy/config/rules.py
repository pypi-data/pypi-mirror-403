RULE_PACK = [
    {
        "id": "R01",
        "desc": "TOP vs LIMIT",
        "hint": "Replace SQL Server TOP with PostgreSQL LIMIT (or use FETCH FIRST)."
    },
    {
        "id": "R02",
        "desc": "ISNULL() vs COALESCE()",
        "hint": "Use COALESCE for cross-engine null handling (ISNULL is SQL Server-only)."
    },
    {
        "id": "R03",
        "desc": "IDENTITY vs SEQUENCE",
        "hint": "Use GENERATED {ALWAYS|BY DEFAULT} AS IDENTITY or a SEQUENCE + DEFAULT nextval()."
    },
    {
        "id": "R04",
        "desc": "BIT vs BOOLEAN",
        "hint": "Map SQL Server BIT to PostgreSQL BOOLEAN (0/1 -> FALSE/TRUE)."
    },
    {
        "id": "R05",
        "desc": "DATETIME vs TIMESTAMP",
        "hint": "Map DATETIME to TIMESTAMP [WITHOUT TIME ZONE]; review precision and timezone usage."
    },
    {
        "id": "R06",
        "desc": "NVARCHAR length mismatch",
        "hint": "Align VARCHAR/NVARCHAR lengths across engines; ensure target length >= source."
    },
    {
        "id": "R07",
        "desc": "UUID vs UNIQUEIDENTIFIER",
        "hint": "Use PostgreSQL UUID (enable uuid-ossp if generating) for SQL Server UNIQUEIDENTIFIER."
    },
    {
        "id": "R08",
        "desc": "Collation differences",
        "hint": "Remove/adjust COLLATE clauses; pick equivalent collation semantics on the target."
    },
    {
        "id": "R09",
        "desc": "Trigger timing mismatch",
        "hint": "Rewrite INSTEAD OF triggers to BEFORE/AFTER with equivalent logic on the target."
    },
    {
        "id": "R10",
        "desc": "Function name mismatch",
        "hint": "Translate common functions (e.g., LEN -> length/char_length) to target equivalents."
    },
]
