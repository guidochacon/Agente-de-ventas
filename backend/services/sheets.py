"""
Google Sheets integration service.

Requires GOOGLE_SERVICE_ACCOUNT_JSON (JSON string) and GOOGLE_SHEETS_ID in env.
Uses google-auth to obtain a Bearer token and calls the Sheets REST API via httpx.
"""
import json
import time
from typing import Any

import httpx

SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"


async def _get_access_token(service_account_json: str) -> str:
    """Exchange service account credentials for a short-lived OAuth2 Bearer token."""
    try:
        import google.auth.transport.requests
        import google.oauth2.service_account

        info = json.loads(service_account_json)
        creds = google.oauth2.service_account.Credentials.from_service_account_info(
            info, scopes=[SCOPE]
        )
        import google.auth.transport.requests as req_transport

        request = req_transport.Request()
        creds.refresh(request)
        return creds.token
    except ImportError:
        # Fallback: manual JWT if google-auth not installed
        raise RuntimeError(
            "google-auth package is required. Install with: pip install google-auth"
        )


async def read_range(spreadsheet_id: str, range_: str, token: str) -> list[list[Any]]:
    """Read a range from a Google Sheet and return as list of rows."""
    url = f"{SHEETS_BASE}/{spreadsheet_id}/values/{range_}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        data = r.json()
        return data.get("values", [])


async def sync_from_sheet(service_account_json: str, spreadsheet_id: str, range_: str = "Sheet1!A1:Z1000") -> dict:
    """
    Read data from Google Sheets and return parsed rows.
    Expected sheet format:
      Row 1: headers (date, agent_email, new_leads, total_calls, conversations,
                       demos_booked, demos_showed, offers_made, closed_deals,
                       revenue, cash_collected)
      Row 2+: data
    """
    if not service_account_json or not spreadsheet_id:
        return {"error": "GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEETS_ID must be configured"}

    token = await _get_access_token(service_account_json)
    rows = await read_range(spreadsheet_id, range_, token)

    if not rows:
        return {"rows": [], "count": 0}

    headers = [h.lower().strip() for h in rows[0]]
    parsed = []
    for row in rows[1:]:
        if not row:
            continue
        record = {}
        for i, h in enumerate(headers):
            record[h] = row[i] if i < len(row) else None
        parsed.append(record)

    return {"rows": parsed, "count": len(parsed)}
