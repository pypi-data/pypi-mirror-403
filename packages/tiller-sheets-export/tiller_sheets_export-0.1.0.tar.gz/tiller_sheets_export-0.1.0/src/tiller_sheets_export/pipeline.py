from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb

from .dataset import TillerData, TillerDataset
from .sheets import fetch_sheet_json

if TYPE_CHECKING:
    from duckdb import DuckDBPyConnection, DuckDBPyRelation

logger = logging.getLogger(__name__)

TRANSACTIONS_SHEET_NAME = "Transactions"
CATEGORIES_SHEET_NAME = "Categories"

TRANSACTIONS_EXTRACT_SQL = """
    SELECT
        rn,
        clean_str(row[list_position(header_row, 'Date')]) AS date,
        clean_str(row[list_position(header_row, 'Description')]) AS description,
        clean_str(row[list_position(header_row, 'Category')]) AS category,
        clean_str(row[list_position(header_row, 'Amount')]) AS amount,
        clean_str(row[list_position(header_row, 'Account')]) AS account,
        clean_str(row[list_position(header_row, 'Account #')]) AS account_number,
        clean_str(row[list_position(header_row, 'Institution')]) AS institution,
        clean_str(row[list_position(header_row, 'Month')]) AS month,
        clean_str(row[list_position(header_row, 'Week')]) AS week,
        clean_str(row[COALESCE(list_position(header_row, 'Transaction ID'), list_position(header_row, 'Transaction Id'))]) AS transaction_id,
        clean_str(row[COALESCE(list_position(header_row, 'Account ID'), list_position(header_row, 'Account Id'))]) AS account_id,
        clean_str(row[list_position(header_row, 'Check Number')]) AS check_number,
        clean_str(row[list_position(header_row, 'Full Description')]) AS full_description,
        clean_str(row[list_position(header_row, 'Date Added')]) AS date_added,
        clean_str(row[list_position(header_row, 'Import Tag')]) AS import_tag,
        clean_str(row[list_position(header_row, 'Merchant Name')]) AS merchant_name,
        clean_str(row[list_position(header_row, 'Category Hint')]) AS category_hint,
        clean_str(row[list_position(header_row, 'Note')]) AS note,
        list_transform(string_split(clean_str(row[list_position(header_row, 'Tags')]), ','), tag -> trim(tag))::VARCHAR[] AS tags,
        clean_str(row[list_position(header_row, 'Categorized Date')]) AS categorized_date,
        clean_str(row[list_position(header_row, 'Statement')]) AS statement,
        clean_str(row[list_position(header_row, 'Metadata')]) AS metadata
    FROM rows, header
"""

TRANSACTIONS_TRANSFORM_SQL = """
    SELECT * REPLACE (
        excel_date(date)::DATE AS date,
        clean_decimal(amount) AS amount,
        excel_date(month)::DATE AS month,
        excel_date(week)::DATE AS week,
        excel_timestamp(date_added)::TIMESTAMP AS date_added,
        excel_timestamp(categorized_date)::TIMESTAMP AS categorized_date
    )
    FROM tiller_transactions_raw
"""

CATEGORIES_EXTRACT_SQL = """
    SELECT
        rn,
        clean_str(row[list_position(header_row, 'Category')]) AS category,
        clean_str(row[list_position(header_row, 'Group')]) AS group,
        clean_str(row[list_position(header_row, 'Type')]) AS type,
        clean_str(row[list_position(header_row, 'Hide From Reports')]) AS hide_from_reports,
        list_transform(string_split(clean_str(row[list_position(header_row, 'Tags')]), ','), tag -> trim(tag))::VARCHAR[] AS tags,
    FROM rows, header
"""

CATEGORIES_TRANSFORM_SQL = """
    SELECT * REPLACE (
        clean_bool(hide_from_reports, 'Hide') AS hide_from_reports
    )
    FROM tiller_categories_raw
"""

TRANSACTIONS_AUDIT_SQL = """
    SELECT column_name, 'cast_loss' as issue_type, len(bad_values) as count, bad_values[1:20] as sample
    FROM (
        SELECT
            list(format('{} (Row {})', raw.date, raw.rn)) FILTER(WHERE raw.date != '' AND final.date IS NULL) AS date,
            list(format('{} (Row {})', raw.amount, raw.rn)) FILTER(WHERE raw.amount != '' AND final.amount IS NULL) AS amount,
            list(format('{} (Row {})', raw.month, raw.rn)) FILTER(WHERE raw.month != '' AND final.month IS NULL) AS month,
            list(format('{} (Row {})', raw.week, raw.rn)) FILTER(WHERE raw.week != '' AND final.week IS NULL) AS week,
            list(format('{} (Row {})', raw.date_added, raw.rn)) FILTER(WHERE raw.date_added != '' AND final.date_added IS NULL) AS date_added,
            list(format('{} (Row {})', raw.categorized_date, raw.rn)) FILTER(WHERE raw.categorized_date != '' AND final.categorized_date IS NULL) AS categorized_date
        FROM tiller_transactions_raw raw
        JOIN tiller_transactions final ON raw.rn = final.rn
    ) UNPIVOT (bad_values FOR column_name IN (date, amount, month, week, date_added, categorized_date))
    WHERE len(bad_values) > 0

    UNION ALL

    SELECT column_name, 'empty_value' as issue_type, len(bad_values) as count, bad_values[1:20] as sample
    FROM (
        SELECT
            list(rn::VARCHAR) FILTER(WHERE date IS NULL OR date = '') as date,
            list(rn::VARCHAR) FILTER(WHERE amount IS NULL OR amount = '') as amount,
            list(rn::VARCHAR) FILTER(WHERE description IS NULL OR description = '') as description,
            list(rn::VARCHAR) FILTER(WHERE category IS NULL OR category = '') as category,
            list(rn::VARCHAR) FILTER(WHERE account IS NULL OR account = '') as account
        FROM tiller_transactions_raw
    ) UNPIVOT (bad_values FOR column_name IN (date, amount, description, category, account))
    WHERE len(bad_values) > 0
"""

CATEGORIES_AUDIT_SQL = """
    SELECT column_name, 'empty_value' as issue_type, len(bad_values) as count, bad_values[1:20] as sample
    FROM (
        SELECT
            list(rn::VARCHAR) FILTER(WHERE category IS NULL OR category = '') as category,
            list(rn::VARCHAR) FILTER(WHERE "group" IS NULL OR "group" = '') as "group",
            list(rn::VARCHAR) FILTER(WHERE type IS NULL OR type = '') as type
        FROM tiller_categories_raw
    ) UNPIVOT (bad_values FOR column_name IN (category, "group", type))
    WHERE len(bad_values) > 0
"""

INTEGRITY_AUDIT_SQL = """
    SELECT 
        'category_mismatch' as issue_type,
        len(mismatches) as count,
        mismatches[1:20] as sample
    FROM (
        SELECT list(DISTINCT category) as mismatches
        FROM tiller_transactions trans
        WHERE category NOT IN (SELECT category FROM tiller_categories)
          AND category IS NOT NULL 
          AND category != ''
    )
    WHERE len(mismatches) > 0
"""

PIPELINE_CONFIG = {
    "transactions": {
        "extract": TRANSACTIONS_EXTRACT_SQL,
        "transform": TRANSACTIONS_TRANSFORM_SQL,
        "audit": TRANSACTIONS_AUDIT_SQL,
    },
    "categories": {
        "extract": CATEGORIES_EXTRACT_SQL,
        "transform": CATEGORIES_TRANSFORM_SQL,
        "audit": CATEGORIES_AUDIT_SQL,
    },
}


def _fetch_and_transform(spreadsheet_url: str) -> TillerData:
    logger.info(f"Fetching data from spreadsheet: {spreadsheet_url}")

    def fetch(sheet_name: str) -> Path:
        return fetch_sheet_json(spreadsheet_url=spreadsheet_url, sheet_name=sheet_name)

    with ThreadPoolExecutor(max_workers=2) as executor:
        transactions_json, categories_json = executor.map(
            fetch, [TRANSACTIONS_SHEET_NAME, CATEGORIES_SHEET_NAME]
        )

    con = duckdb.connect()
    _setup_macros(con=con)

    transactions_rel = _transform_sheet(
        con=con, json_path=transactions_json, sheet_key="transactions"
    )
    categories_rel = _transform_sheet(
        con=con, json_path=categories_json, sheet_key="categories"
    )

    _validate_integrity(con=con)

    return TillerData(
        _con=con,
        transactions=TillerDataset(_relation=transactions_rel),
        categories=TillerDataset(_relation=categories_rel),
    )


def _transform_sheet(
    con: DuckDBPyConnection,
    json_path: Path,
    sheet_key: str,
) -> DuckDBPyRelation:
    config = PIPELINE_CONFIG[sheet_key]
    table_name = f"tiller_{sheet_key}"

    json_literal = _sql_literal(str(json_path))

    # 1. Extract to Raw Table
    extract_sql = f"""
    CREATE OR REPLACE TEMP TABLE {table_name}_raw AS
    WITH data AS (
        SELECT values
        FROM read_json({json_literal}, columns={{'values': 'VARCHAR[][]'}})
    ),
    all_rows AS (
        SELECT row, rn
        FROM data, unnest(values) WITH ORDINALITY AS t(row, rn)
    ),
    header AS (
        SELECT row AS header_row FROM all_rows WHERE rn = 1
    ),
    rows AS (
        SELECT row, rn FROM all_rows WHERE rn > 1
    )
    {config["extract"]}
    """
    con.execute(query=extract_sql)
    json_path.unlink(missing_ok=True)

    # 2. Transform to Final Table
    transform_sql = f"""
    CREATE OR REPLACE TABLE {table_name} AS
    {config["transform"]}
    """
    con.execute(query=transform_sql)

    # 3. Audit Data Loss
    _audit_sheet(con=con, config=config)

    # 4. Cleanup
    con.execute(f"ALTER TABLE {table_name} DROP rn")
    con.execute(f"DROP TABLE {table_name}_raw")

    relation = con.table(table_name=table_name)

    return relation


def _validate_integrity(con: DuckDBPyConnection) -> None:
    results = con.sql(INTEGRITY_AUDIT_SQL).fetchall()
    for issue, count, sample in results:
        if issue == "category_mismatch":
            logger.warning(
                f"Validation Warning: Found {count} categories in Transactions "
                f"that are missing from the Categories sheet. Sample: {sample}"
            )


def _setup_macros(con: DuckDBPyConnection) -> None:
    con.sql("""
        CREATE OR REPLACE MACRO excel_date(col) AS
            CAST('1899-12-30' AS DATE) + TRY_CAST(col AS DOUBLE)::INT;
        CREATE OR REPLACE MACRO excel_timestamp(col) AS
            CAST('1899-12-30' AS TIMESTAMP) + (TRY_CAST(col AS DOUBLE) * INTERVAL 1 DAY);
        CREATE OR REPLACE MACRO clean_str(col) AS
            NULLIF(col::VARCHAR, '');
        CREATE OR REPLACE MACRO clean_decimal(col) AS
            TRY_CAST(NULLIF(col::VARCHAR, '') AS DECIMAL(19,2));
        CREATE OR REPLACE MACRO clean_bool(col, true_val) AS
            COALESCE(NULLIF(col::VARCHAR, '') = true_val, FALSE);
    """)


def _audit_sheet(
    con: DuckDBPyConnection,
    config: dict,
) -> None:
    sql = config["audit"]
    results = con.sql(sql).fetchall()

    for col, issue, count, sample in results:
        if issue == "cast_loss":
            logger.warning(
                f"Validation Warning: Found {count} values in '{col}' "
                f"that could not be cast (will be set to NULL). Sample: {sample}"
            )
        elif issue == "empty_value":
            logger.warning(
                f"Validation Warning: Found {count} empty values in '{col}'. "
                f"Sample Rows: {sample}"
            )


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
