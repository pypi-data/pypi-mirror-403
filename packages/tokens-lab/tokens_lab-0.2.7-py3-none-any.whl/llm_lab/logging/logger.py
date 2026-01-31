import os
import logging
from logging.handlers import RotatingFileHandler
from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class Logger:
    """Logger class with Azure and local logging capabilities."""

    def __init__(self, name: str = "llm_lab"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.blob_service_client = None
        self.container_client = None

    def _get_week_start_date(self):
        """
        Get the start date of the current week (Monday).
        
        Returns:
            str: Formatted date string (YYYY-MM-DD)
        """
        today = datetime.now()
        # Monday is 0, Sunday is 6
        week_start = today - timedelta(days=today.weekday())
        return week_start.strftime("%Y-%m-%d")

    def _get_current_date(self):
        """
        Get the current date in YYYY-MM-DD format.
        
        Returns:
            str: Formatted date string (YYYY-MM-DD)
        """
        return datetime.now().strftime("%Y-%m-%d")

    def setup_azure_logger(self):
        """
        Setup Azure Blob Storage logger using environment variables.
        Creates a weekly folder structure with daily log files.
        
        Required environment variables:
        - AZURE_STORAGE_CONNECTION_STRING
        - AZURE_STORAGE_ACCOUNT_NAME
        - AZURE_STORAGE_ACCOUNT_KEY
        - AZURE_CONTAINER_NAME
        """
        try:
            connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            container_name = os.getenv("AZURE_CONTAINER_NAME")

            if not connection_string or not container_name:
                raise ValueError(
                    "Missing required Azure environment variables: "
                    "AZURE_STORAGE_CONNECTION_STRING and AZURE_CONTAINER_NAME"
                )

            self.blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
            self.container_client = self.blob_service_client.get_container_client(
                container_name
            )

            # Create a console handler to display logs
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            # Create weekly folder structure in Azure
            week_start = self._get_week_start_date()
            current_date = self._get_current_date()
            azure_blob_path = f"logs/{week_start}/{current_date}_logs.log"
            
            self.logger.info(
                f"Azure logger initialized successfully. "
                f"Logs will be stored at: {azure_blob_path}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Azure logger: {e}")
            return False

    def setup_local_logger(self, log_folder: str = "logs"):
        """
        Setup local file logger that logs to a local folder with weekly structure.
        Creates a folder structure: logs/{week_start_date}/{date}_logs.log
        
        Args:
            log_folder (str): Path to the base logs folder.
                            Defaults to "logs" in the current directory.
        """
        try:
            # Get week start date and current date
            week_start = self._get_week_start_date()
            current_date = self._get_current_date()
            
            # Create weekly folder structure: logs/YYYY-MM-DD/
            weekly_log_folder = os.path.join(log_folder, week_start)
            os.makedirs(weekly_log_folder, exist_ok=True)

            # Create daily log file: YYYY-MM-DD_logs.log
            log_file = os.path.join(weekly_log_folder, f"{current_date}_logs.log")

            handler = RotatingFileHandler(
                log_file, maxBytes=10485760, backupCount=5  # 10MB max file size
            )
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            self.logger.info(f"Local logger initialized at {log_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup local logger: {e}")
            return False

    def get_logger(self):
        """Return the configured logger instance."""
        return self.logger
