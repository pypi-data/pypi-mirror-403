import logging
import re
import shutil
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from google.auth import default
from google.auth.transport.urllib3 import Request
from urllib3 import PoolManager

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
logger = logging.getLogger(__name__)


def fetch_sheet_json(spreadsheet_url: str, sheet_name: str) -> Path:
    logger.info(f"Fetching raw data for {sheet_name}")
    spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
    creds, _ = default(scopes=SCOPES)
    http = PoolManager()
    auth_req = Request(http)
    creds.refresh(auth_req)

    sheet_name_encoded = urllib.parse.quote(sheet_name)
    query = urllib.parse.urlencode(
        {
            "majorDimension": "ROWS",
            "valueRenderOption": "UNFORMATTED_VALUE",
        }
    )
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/"
        f"{sheet_name_encoded}?{query}"
    )

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {creds.token}")
    req.add_header("User-Agent", "Tiller-Parquet/1.0 (urllib)")

    if hasattr(creds, "quota_project_id") and creds.quota_project_id:
        req.add_header("X-Goog-User-Project", creds.quota_project_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp_path = Path(tmp.name)
    with urllib.request.urlopen(req) as response, open(tmp_path, "wb") as f:
        shutil.copyfileobj(response, f)
    return tmp_path


def extract_spreadsheet_id(url: str) -> str:
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError(f"Could not extract spreadsheet ID from URL: {url}")
    return match.group(1)
