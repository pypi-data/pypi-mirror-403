"""Lark sheet manager for creating and formatting experiment reports."""

from typing import List, Optional, Tuple

import requests

from owlab.core.logger import get_logger

logger = get_logger("owlab.lark.sheet_manager")


class LarkSheetManager:
    """Manager for Lark spreadsheet operations."""

    def __init__(self, access_token_getter):
        """Initialize sheet manager.

        Args:
            access_token_getter: Function that returns access token
        """
        self._get_token = access_token_getter

    def create_spreadsheet(
        self, title: str, folder_token: Optional[str] = None
    ) -> Optional[str]:
        """Create a new spreadsheet.

        Args:
            title: Title of the spreadsheet
            folder_token: Token of the folder to create the spreadsheet in (optional)

        Returns:
            Spreadsheet token or None if failed
        """
        token = self._get_token()
        if not token:
            return None

        url = "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        # Use title as-is (caller should include timestamp if needed)
        payload = {"title": title}
        if folder_token:
            payload["folder_token"] = folder_token

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                spreadsheet_token = (
                    data.get("data", {}).get("spreadsheet", {}).get("spreadsheet_token")
                )
                logger.info(f"Created spreadsheet: {title}")
                return spreadsheet_token  # type: ignore[no-any-return]
            else:
                logger.error(f"Error creating spreadsheet: {data.get('msg')}")
                return None
        except Exception as e:
            logger.error(f"Exception creating spreadsheet: {e}")
            return None

    def get_first_sheet_info(self, spreadsheet_token: str) -> Tuple[Optional[str], Optional[str]]:
        """Get first sheet info from spreadsheet.

        Args:
            spreadsheet_token: Spreadsheet token

        Returns:
            Tuple of (sheet_id, sheet_title) or (None, None) if failed
        """
        token = self._get_token()
        if not token:
            return None, None

        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                sheets = data.get("data", {}).get("sheets", [])
                if sheets:
                    sheet = sheets[0]
                    return sheet.get("sheet_id"), sheet.get("title")
        except Exception as e:
            logger.error(f"Exception querying sheets: {e}")
        return None, None

    def add_sheet(self, spreadsheet_token: str, title: str) -> Optional[str]:
        """Add a new sheet to spreadsheet.

        Args:
            spreadsheet_token: Spreadsheet token
            title: Sheet title

        Returns:
            Sheet ID or None if failed
        """
        token = self._get_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        payload = {"requests": [{"addSheet": {"properties": {"title": title}}}]}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                sheet_id = (
                    data.get("data", {})
                    .get("replies", [])[0]
                    .get("addSheet", {})
                    .get("properties", {})
                    .get("sheetId")
                )
                logger.info(f"Added sheet: {title}")
                return sheet_id  # type: ignore[no-any-return]
            else:
                logger.error(f"Error adding sheet: {data.get('msg')}")
                return None
        except Exception as e:
            logger.error(f"Exception adding sheet: {e}")
            return None

    def update_sheet_title(
        self, spreadsheet_token: str, sheet_id: str, title: str
    ) -> bool:
        """Update sheet title.

        Args:
            spreadsheet_token: Spreadsheet token
            sheet_id: Sheet ID
            title: New sheet title

        Returns:
            True if successful, False otherwise
        """
        token = self._get_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        payload = {
            "requests": [
                {
                    "updateSheet": {
                        "properties": {"sheetId": sheet_id, "title": title}
                    }
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                logger.info(f"Updated sheet title: {sheet_id} -> {title}")
                return True
            else:
                logger.error(f"Error updating sheet title: {data.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"Exception updating sheet title: {e}")
            return False

    def update_data(
        self, spreadsheet_token: str, range_name: str, values: List[List]
    ) -> bool:
        """Update data in a spreadsheet (overwrite).

        Args:
            spreadsheet_token: Spreadsheet token
            range_name: Range to update, e.g., "Sheet1!A1:C3"
            values: List of lists representing rows

        Returns:
            True if successful, False otherwise
        """
        token = self._get_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        payload = {"valueRange": {"range": range_name, "values": values}}

        try:
            response = requests.put(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                logger.debug(f"Data updated: Range={range_name}, Rows={len(values)}")
                return True
            else:
                logger.error(f"Error updating data: {data.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"Exception updating data: {e}")
            return False

    def merge_cells(
        self,
        spreadsheet_token: str,
        range_name: str,
        merge_type: str = "MERGE_ALL",
    ) -> bool:
        """Merge cells in spreadsheet.

        Args:
            spreadsheet_token: Spreadsheet token
            range_name: Range to merge, e.g., "Sheet1!A1:C1"
            merge_type: Merge type (MERGE_ALL, MERGE_ROWS, MERGE_COLUMNS)

        Returns:
            True if successful, False otherwise
        """
        token = self._get_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/merge_cells"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        payload = {"range": range_name, "mergeType": merge_type}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                logger.debug(f"Merged cells: Range={range_name}")
                return True
            else:
                logger.error(f"Error merging cells: {data.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"Exception merging cells: {e}")
            return False

    def set_style(
        self, spreadsheet_token: str, range_name: str, style: dict
    ) -> bool:
        """Set style for cells.

        Args:
            spreadsheet_token: Spreadsheet token
            range_name: Range to style, e.g., "Sheet1!A1:C3"
            style: Style dictionary

        Returns:
            True if successful, False otherwise
        """
        token = self._get_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/style"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        payload = {"appendStyle": {"range": range_name, "style": style}}

        try:
            response = requests.put(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                logger.debug(f"Style set: Range={range_name}")
                return True
            else:
                logger.error(f"Error setting style: {data.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"Exception setting style: {e}")
            return False

    def batch_set_style(
        self, spreadsheet_token: str, style_data: List[dict]
    ) -> bool:
        """Batch set styles.

        Args:
            spreadsheet_token: Spreadsheet token
            style_data: List of style rules, e.g.
                [{"ranges": ["range1", "range2"], "style": {...}}]

        Returns:
            True if successful, False otherwise
        """
        token = self._get_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/styles_batch_update"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        payload = {"data": style_data}

        try:
            response = requests.put(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                logger.debug(f"Batch style set: {len(style_data)} rules")
                return True
            else:
                logger.error(f"Error batch setting style: {data.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"Exception batch setting style: {e}")
            return False

    @staticmethod
    def _get_column_letter(col_idx: int) -> str:
        """Convert 1-based column index to letter (e.g., 1->A, 27->AA).

        Args:
            col_idx: 1-based column index

        Returns:
            Column letter(s)
        """
        string = ""
        while col_idx > 0:
            col_idx, remainder = divmod(col_idx - 1, 26)
            string = chr(65 + remainder) + string
        return string
