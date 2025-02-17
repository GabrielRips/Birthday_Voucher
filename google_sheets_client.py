# google_sheets_client.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsClient:
    def __init__(self, credentials_json, spreadsheet_id, worksheet_name):
        self.credentials_json = credentials_json
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.client = self._init_client()
        self.sheet = self._open_sheet()

    def _init_client(self):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_json, scope)
        return gspread.authorize(creds)

    def _open_sheet(self):
        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            return spreadsheet.worksheet(self.worksheet_name)
        except Exception as e:
            logger.error(f"Failed to open the worksheet: {e}")
            raise

    def append_row(self, row_data):
        """
        Appends a row of data to the Google Sheet.
        :param row_data: A list of values corresponding to each column.
        :return: True if successful, False otherwise.
        """
        try:
            self.sheet.append_row(row_data)
            return True
        except Exception as e:
            logger.error(f"Failed to append row to Google Sheets: {e}")
            return False
