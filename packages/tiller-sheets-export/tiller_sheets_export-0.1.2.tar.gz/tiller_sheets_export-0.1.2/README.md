# tiller-sheets-export

[![PyPI](https://img.shields.io/pypi/v/tiller-sheets-export.svg)](https://pypi.org/project/tiller-sheets-export/)

Unofficial tool to fetch Tiller financial data from Google Sheets as Arrow, DuckDB, or Parquet.

> **Note:** This is an unofficial project and is not affiliated with, endorsed by, or connected to Tiller HQ.

## Auth

This tool uses [Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc). You will need a Google Cloud project with the Sheets API enabled.

```bash
# 1. Login to Google Cloud
gcloud auth login

# 2. Setup credentials with Sheets scope
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/spreadsheets.readonly

# 3. Set your project (replace <PROJECT_ID> with your actual GCP project ID)
gcloud auth application-default set-quota-project <PROJECT_ID>
gcloud services enable sheets.googleapis.com --project=<PROJECT_ID>
```

Alternatively, set `GOOGLE_APPLICATION_CREDENTIALS` to the path of a service account JSON key.

## Installation

### CLI Installation

**Linux/macOS permanent install with `uvx.sh` (installs [uv](https://github.com/astral-sh/uv) + `tiller-sheets-export`):**
```bash
curl -LsSf uvx.sh/tiller-sheets-export/install.sh | sh
tiller-sheets-export "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"
```

**Or, if you have [uv](https://github.com/astral-sh/uv) already installed:**
```bash
uvx tiller-sheets-export "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"
```

### Library Installation

```bash
uv add tiller-sheets-export
```

## CLI Usage

```bash
tiller-sheets-export "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"
```

This generates `data/processed/transactions.parquet` and `data/processed/categories.parquet`.

## Library Usage

```python
from tiller_sheets_export import TillerData

data = TillerData.fetch(spreadsheet_url="https://docs.google.com/spreadsheets/d/YOUR_ID/edit")

# To Arrow
data.transactions.to_arrow()
data.categories.to_arrow()

# To DuckDB
data.transactions.to_duckdb()
data.categories.to_duckdb()

# To pandas
data.transactions.to_arrow().to_pandas()
```

### Query with DuckDB

```python
import duckdb

con = duckdb.connect()
transactions = data.transactions.to_duckdb(con=con)
categories = data.categories.to_duckdb(con=con)

con.sql("""
    SELECT t.date, t.description, t.amount, c.group, c.type
    FROM transactions t
    LEFT JOIN categories c ON t.category = c.category
    ORDER BY t.date DESC
""").show()
```

## Google Colab

```python
from google.colab import auth
auth.authenticate_user()

!pip install tiller-sheets-export

from tiller_sheets_export import TillerData

data = TillerData.fetch(spreadsheet_url="https://docs.google.com/spreadsheets/d/YOUR_ID/edit")
data.transactions.to_arrow().to_pandas()
```

## Schema

### Transactions

See [Tiller's documentation](https://help.tiller.com/en/articles/432681-transactions-sheet-columns) for column descriptions.

| Column | Type |
|--------|------|
| date | date |
| description | string |
| category | string |
| amount | decimal(19,2) |
| account | string |
| account_number | string |
| institution | string |
| month | date |
| week | date |
| transaction_id | string |
| account_id | string |
| check_number | string |
| full_description | string |
| date_added | timestamp |
| import_tag | string |
| merchant_name | string |
| category_hint | string |
| note | string |
| tags | list&lt;string&gt; |
| categorized_date | timestamp |
| statement | string |
| metadata | string |

### Categories

| Column | Type |
|--------|------|
| category | string |
| group | string |
| type | string |
| hide_from_reports | bool |
| tags | list&lt;string&gt; |

## Data Quality

Automatic validation logs warnings for type mismatches, missing categories, and empty critical fields. Invalid values are coerced to `NULL`.

## Other Tiller Projects

- https://github.com/peterkeen/ledger_tiller_export - Tool to export transactions from Tiller into Ledger.
- https://github.com/basnijholt/tiller-streamlit - Streamlit dashboard for Tiller data.
- https://github.com/jackstein21/tiller-mcp-server/tree/main - MCP server exposing Tiller data.
- https://github.com/clomok/finance-visualizer/ - Browser-based visual data explorer.
