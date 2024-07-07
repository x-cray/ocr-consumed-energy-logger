"""
Defines routines to preserve the last run timestamp in GCS bucket
"""

import io
import os
import logging
from datetime import datetime, timezone
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCRIPT_PATH = os.path.realpath(os.path.dirname(__file__))
KEY_PATH = os.path.join(SCRIPT_PATH, "credentials.json")
BUCKET = "heat-meter-logger"
BLOB = "last-success"


def update_last_run():
    """Updates last run timestamp in GCS bucket"""
    last_run_timestamp = datetime.now(timezone.utc).isoformat()
    creds = Credentials.from_service_account_file(KEY_PATH)
    service = build("storage", "v1", credentials=creds)

    contents = MediaIoBaseUpload(
        io.StringIO(last_run_timestamp),
        mimetype="application/text",
        chunksize=-1,
        resumable=False,
    )

    service.objects().insert(
        bucket=BUCKET,
        name=BLOB,
        media_body=contents,
        predefinedAcl="publicRead",
        body={"cacheControl": "no-cache"},
    ).execute()
    logging.info("Updated last run timestamp to %s", last_run_timestamp)
