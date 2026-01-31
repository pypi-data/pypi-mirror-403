import os
import logging
from logging.handlers import RotatingFileHandler
from azure.storage.blob import BlobServiceClient
from datetime import datetime
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

    def setup_azure_logger(self):
        """
        Setup Azure Blob Storage logger using environment variables.
        
        Required environment variables:
        - AZURE_STORAGE_CONNECTION_STRING
        - AZURE_STORAGE_ACCOUNT_NAME
        - AZURE_STORAGE_ACCOUNT_KEY
        - AZURE_CONTAINER_NAME
        """
        try:
            connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
            account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
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

            self.logger.info("Azure logger initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Azure logger: {e}")
            return False

    def setup_local_logger(self, log_folder: str = "logs"):
        """
        Setup local file logger that logs to a local folder.
        
        Args:
            log_folder (str): Path to the folder where logs will be stored.
                            Defaults to "logs" in the current directory.
        """
        try:
            os.makedirs(log_folder, exist_ok=True)

            log_file = os.path.join(
                log_folder,
                f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            )

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
