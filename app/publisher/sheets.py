"""Functions to publish meter readings to Google Sheets"""

import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCRIPT_PATH = os.path.realpath(os.path.dirname(__file__))
KEY_PATH = os.path.join(SCRIPT_PATH, "../credentials.json")


def publish_readings(spreadsheet_id, sheet_range, timestamp, readings):
    """Publishes timestamp and readings to a Google Sheets table"""
    creds = Credentials.from_service_account_file(KEY_PATH)
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    body = {"values": [[timestamp, readings]]}
    result = (
        sheet.values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=sheet_range,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )
    logging.info("%d cells appended", result.get("updates").get("updatedCells"))
    return result
