"""Lark API Bot for managing sheets and folders."""

from datetime import datetime
import time
from typing import Any, Dict, List, Optional

import requests

from owlab.core.logger import get_logger
from owlab.lark.sheet_manager import LarkSheetManager
from owlab.utils.formatter import ExperimentDataFormatter
from owlab.utils.retry import retry_on_http_error

logger = get_logger("owlab.lark.api_bot")


class LarkAPIBot:
    """Lark API Bot for managing sheets and folders."""

    def __init__(self, app_id: str, app_secret: str, root_folder_token: str):
        """Initialize Lark API Bot.

        Args:
            app_id: Lark app ID
            app_secret: Lark app secret
            root_folder_token: Root folder token in Lark
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.root_folder_token = root_folder_token
        self._token: Optional[str] = None
        self._token_expire_time: float = 0.0
        self._type_folders: Dict[str, str] = {}  # Cache for type folder tokens
        self._sheet_manager = LarkSheetManager(self._get_tenant_access_token)
        logger.info("Lark API Bot initialized")

    @retry_on_http_error(max_attempts=3, delay=1.0)
    def _get_tenant_access_token(self) -> Optional[str]:
        """Get tenant access token with caching.

        Returns:
            Access token or None if failed
        """
        # Return cached token if still valid
        if self._token and time.time() < self._token_expire_time:
            return self._token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                self._token = data.get("tenant_access_token")
                # Expire time is usually 7200 seconds, set buffer
                self._token_expire_time = time.time() + data.get("expire", 7200) - 60
                logger.debug("Tenant access token obtained")
                return self._token
            else:
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"Error getting token: {error_msg}")
                return None
        except Exception as e:
            logger.error(f"Exception getting token: {e}")
            return None

    def _list_folders(self, folder_token: str) -> Dict[str, str]:
        """List folders in a parent folder.

        Args:
            folder_token: Parent folder token

        Returns:
            Dictionary mapping folder names to folder tokens
        """
        token = self._get_tenant_access_token()
        if not token:
            return {}

        url = "https://open.feishu.cn/open-apis/drive/v1/files"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        params: Dict[str, Any] = {
            "folder_token": folder_token,
            "page_size": 200,  # Maximum page size
        }

        folder_map = {}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                files = data.get("data", {}).get("files", [])
                for file_info in files:
                    if file_info.get("type") == "folder":
                        folder_name = file_info.get("name", "")
                        folder_token = file_info.get("token", "")
                        if folder_name and folder_token:
                            folder_map[folder_name] = folder_token
        except Exception as e:
            logger.debug(f"Exception listing folders: {e}")

        return folder_map

    def get_or_create_type_folder(self, experiment_type: str) -> Optional[str]:
        """Get or create type folder in root folder.

        If a folder with the same name exists, use it. Otherwise, create a new one.

        Args:
            experiment_type: Type of experiment (e.g., "baseline", "debug", "ablation")

        Returns:
            Type folder token or None if failed
        """
        # Check cache first
        if experiment_type in self._type_folders:
            return self._type_folders[experiment_type]

        token = self._get_tenant_access_token()
        if not token:
            return None

        # First, try to list existing folders to check if type folder exists
        existing_folders = self._list_folders(self.root_folder_token)
        if experiment_type in existing_folders:
            folder_token = existing_folders[experiment_type]
            # Cache the folder token
            self._type_folders[experiment_type] = folder_token
            logger.info(f"Found existing type folder '{experiment_type}' (token: {folder_token})")
            return folder_token

        # Folder doesn't exist, create it
        url = "https://open.feishu.cn/open-apis/drive/v1/files/create_folder"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "name": experiment_type,
            "folder_token": self.root_folder_token,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                folder_token = data.get("data", {}).get("token")
                # Cache the folder token
                self._type_folders[experiment_type] = folder_token
                logger.info(f"Created type folder '{experiment_type}' (token: {folder_token})")
                return folder_token  # type: ignore[no-any-return]
            else:
                error_msg = data.get("msg", "Unknown error")
                error_code = data.get("code", 0)
                logger.error(
                    f"Error creating type folder '{experiment_type}' (code: {error_code}): {error_msg}"
                )
                return None
        except Exception as e:
            logger.error(f"Exception creating type folder '{experiment_type}': {e}")
            return None

    def create_experiment_folder(
        self,
        experiment_name: str,
        description: str = "",
        experiment_type: str = "default",
    ) -> Optional[str]:
        """Create experiment folder in type folder.

        Args:
            experiment_name: Name of the experiment
            description: Description of the experiment
            experiment_type: Type of experiment (for categorization)

        Returns:
            Folder token or None if failed
        """
        # Get or create type folder first
        type_folder_token = self.get_or_create_type_folder(experiment_type)
        if not type_folder_token:
            return None

        token = self._get_tenant_access_token()
        if not token:
            return None

        # Create folder name: use experiment_name or description + timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if experiment_name:
            folder_name = f"{experiment_name}_{timestamp}"
        elif description:
            # Use first 20 chars of description if experiment_name is empty
            desc_short = description[:20].replace(" ", "_")
            folder_name = f"{desc_short}_{timestamp}"
        else:
            folder_name = f"experiment_{timestamp}"

        # Use drive/v1/files API to create folder
        url = "https://open.feishu.cn/open-apis/drive/v1/files/create_folder"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "name": folder_name,
            "folder_token": type_folder_token,  # Create in type folder, not root
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                folder_token = data.get("data", {}).get("token")
                logger.info(f"Created folder: {folder_name} (token: {folder_token})")
                return folder_token  # type: ignore[no-any-return]
            else:
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"Error creating folder: {error_msg}")
                logger.debug(f"Response: {data}")
                return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error creating folder: {e}")
            if hasattr(e.response, 'text'):
                logger.debug(f"Response text: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Exception creating folder: {e}")
            return None

    def write_results_to_sheet(
        self,
        folder_token: str,
        experiment_config: Dict[str, Any],
        experiment_data: List[Dict[str, Any]],
        swanlab_url: str = "",
        sheet_name: Optional[str] = None,
    ) -> Optional[str]:
        """Write experiment results to Lark sheet.

        Args:
            folder_token: Token of the folder to create sheet in
            experiment_config: Experiment configuration dictionary
            experiment_data: List of experiment data dictionaries
            swanlab_url: SwanLab experiment URL
            sheet_name: Name of the sheet (optional)

        Returns:
            Spreadsheet token or None if failed
        """
        if not experiment_data:
            logger.warning("No experiment data provided")
            return None

        # Create spreadsheet with better naming
        experiment_name = experiment_config.get("experiment_name", "Experiment")
        description = experiment_config.get("description", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Use experiment_name or description for spreadsheet title
        if experiment_name:
            spreadsheet_title = f"{experiment_name}_{timestamp}"
        elif description:
            desc_short = description[:20].replace(" ", "_")
            spreadsheet_title = f"{desc_short}_{timestamp}"
        else:
            spreadsheet_title = f"experiment_{timestamp}"

        spreadsheet_token = self._sheet_manager.create_spreadsheet(
            title=spreadsheet_title, folder_token=folder_token
        )
        if not spreadsheet_token:
            logger.error("Failed to create spreadsheet")
            return None

        # Log folder URL
        folder_url = f"https://bytedance.feishu.cn/drive/folder/{folder_token}"
        logger.info(f"Experiment folder URL: {folder_url}")
        logger.info(f"Spreadsheet URL: https://bytedance.feishu.cn/sheets/{spreadsheet_token}")

        # Get first sheet info
        sheet_id, _ = self._sheet_manager.get_first_sheet_info(spreadsheet_token)
        if not sheet_id:
            sheet_id = "Sheet1"  # Fallback
            logger.warning("Could not get sheet ID, using Sheet1")

        # Format configuration text (include SwanLab URL)
        config_text = self._format_config_text(experiment_config, swanlab_url=swanlab_url)

        # Initialize formatter
        formatter = ExperimentDataFormatter(experiment_config)

        # Group data by measure
        grouped_by_measure = formatter.format_experiment_data(experiment_data)

        # Write each measure to a separate sheet
        measure_sheets = {}
        for measure_idx, (measure_name, measure_data) in enumerate(grouped_by_measure.items()):
            # Get measure display name
            measure_display = next(
                (
                    m.get("display_name", m["name"])
                    for m in experiment_config.get("measures", [])
                    if m["name"] == measure_name
                ),
                measure_name,
            )

            current_sheet_id: Optional[str]
            if measure_idx == 0:
                # Rename first sheet to measure name
                current_sheet_id = sheet_id
                # Rename the first sheet to measure name
                self._sheet_manager.update_sheet_title(
                    spreadsheet_token, sheet_id, measure_display
                )
                logger.info(f"Renamed first sheet to '{measure_display}' (ID: {sheet_id})")
            else:
                # Create new sheet for other measures
                current_sheet_id = self._sheet_manager.add_sheet(
                    spreadsheet_token, measure_display
                )
                if not current_sheet_id:
                    logger.warning(f"Failed to create sheet for measure {measure_name}")
                    continue

            measure_sheets[measure_name] = current_sheet_id

            # Filter experiment data for this specific measure
            # Only include methods that have data for this measure
            measure_data_list = []
            for d in experiment_data:
                # Check if this method has data for this measure in any dataset
                has_measure_data = any(
                    d.get(k, {}).get("measure") == measure_name
                    for k in d
                    if k not in ["method", "Average"]
                )
                # Also check Average if it exists
                has_average = (
                    "Average" in d
                    and d.get("Average", {}).get("measure") == measure_name
                )
                if has_measure_data or has_average:
                    measure_data_list.append(d)

            # Format data rows for this measure (filter by measure_name)
            data_rows = formatter.format_to_sheet_rows(
                measure_data_list,
                include_average=True,
                target_measure=measure_name,
            )

            # Write sheet
            self._write_experiment_sheet(
                spreadsheet_token=spreadsheet_token,
                sheet_id=current_sheet_id,
                config_text=config_text,
                data_rows=data_rows,
                formatter=formatter,
            )

        logger.info(f"Results written to spreadsheet: {spreadsheet_token}")
        return spreadsheet_token

    def _format_config_text(
        self, experiment_config: Dict[str, Any], swanlab_url: str = ""
    ) -> str:
        """Format experiment configuration as text.

        Args:
            experiment_config: Experiment configuration dictionary
            swanlab_url: SwanLab experiment URL

        Returns:
            Formatted configuration text
        """
        lines = []
        # Add project name (if available)
        if experiment_config.get("project"):
            lines.append(f"Project: {experiment_config['project']}")
        lines.append(f"Experiment: {experiment_config.get('experiment_name', 'Unknown')}")
        if experiment_config.get("version"):
            lines.append(f"Version: {experiment_config['version']}")
        if experiment_config.get("description"):
            lines.append(f"Description: {experiment_config['description']}")

        # Add seed (check both top-level and experiment_params)
        seed = experiment_config.get("seed")
        if seed is None:
            params = experiment_config.get("experiment_params", {})
            seed = params.get("seed")
        if seed is not None:
            lines.append(f"Seed: {seed}")

        if swanlab_url:
            lines.append(f"SwanLab URL: {swanlab_url}")

        params = experiment_config.get("experiment_params", {})
        if params:
            lines.append("\nParameters:")
            for key, value in params.items():
                # Skip seed if already shown above
                if key != "seed":
                    lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def _write_experiment_sheet(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        config_text: str,
        data_rows: List[List[Any]],
        formatter: ExperimentDataFormatter,
    ) -> None:
        """Write experiment data to a sheet with formatting.

        Args:
            spreadsheet_token: Spreadsheet token
            sheet_id: Sheet ID
            config_text: Configuration text
            data_rows: Data rows to write
            formatter: Data formatter instance
        """
        # Use sheet_id directly as range prefix (e.g., "a4baa4!A1")
        start_row = 3  # Start from row 3 (row 1 for config, row 2 empty)

        # 1. Write config text
        # Range format: sheet_id!A1:A1 (飞书 API 需要完整的范围格式)
        config_range = f"{sheet_id}!A1:A1"
        self._sheet_manager.update_data(
            spreadsheet_token, config_range, [[config_text]]
        )

        # 2. Get and write headers
        header_rows = formatter.get_header_rows(include_average=True)
        num_cols = len(header_rows[0]) if header_rows else 0
        end_col_letter = formatter._col_letter(num_cols)

        # Range format: sheet_id!A3:Q4
        header_range = f"{sheet_id}!A{start_row}:{end_col_letter}{start_row + 1}"
        self._sheet_manager.update_data(spreadsheet_token, header_range, header_rows)

        # 3. Merge header cells
        merge_ranges = formatter.get_merge_ranges(sheet_id, start_row, include_average=True)
        for merge_range in merge_ranges:
            self._sheet_manager.merge_cells(spreadsheet_token, merge_range)

        # 4. Style headers
        header_style = {
            "hAlign": 1,  # Center
            "vAlign": 1,  # Center
            "font": {"bold": True},
        }
        header_style_range = f"{sheet_id}!A{start_row}:{end_col_letter}{start_row + 1}"
        self._sheet_manager.set_style(
            spreadsheet_token,
            header_style_range,
            header_style,
        )

        # 5. Write data rows
        if data_rows:
            # Format numeric values
            formatted_rows = []
            for row in data_rows:
                formatted_row = []
                for val in row:
                    if isinstance(val, float):
                        formatted_row.append(round(val, 3))
                    else:
                        formatted_row.append(val)
                formatted_rows.append(formatted_row)

            data_start_row = start_row + 2
            data_end_row = data_start_row + len(formatted_rows) - 1
            data_range = f"{sheet_id}!A{data_start_row}:{end_col_letter}{data_end_row}"
            self._sheet_manager.update_data(spreadsheet_token, data_range, formatted_rows)

            # Style data cells (center align)
            data_style = {"hAlign": 1, "vAlign": 1}
            data_style_range = f"{sheet_id}!A{data_start_row}:{end_col_letter}{data_end_row}"
            self._sheet_manager.set_style(
                spreadsheet_token,
                data_style_range,
                data_style,
            )

            # 6. Bold best values
            best_ranges = formatter.get_best_value_ranges(
                sheet_id, formatted_rows, data_start_row, include_average=True
            )
            if best_ranges:
                bold_style = {"font": {"bold": True}}
                self._sheet_manager.batch_set_style(
                    spreadsheet_token,
                    [{"ranges": best_ranges, "style": bold_style}],
                )

        logger.info(f"Sheet {sheet_id} written successfully")
