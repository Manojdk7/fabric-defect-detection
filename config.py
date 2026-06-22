import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent


def path_from_env(name: str, default: str) -> Path:
    value = os.getenv(name, default)
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


class Config:
    """Runtime settings for the inspection API."""

    SERVICE_NAME = os.getenv("QIS_SERVICE_NAME", "Quality Inspection System")
    VERSION = os.getenv("QIS_VERSION", "1.1.0")

    UPLOAD_FOLDER = path_from_env("QIS_UPLOAD_FOLDER", "uploads")
    RESULTS_FOLDER = path_from_env("QIS_RESULTS_FOLDER", "inspection_results")
    DATABASE_PATH = path_from_env("QIS_DATABASE_PATH", "inspection_history.db")
    LOG_FILE = path_from_env("QIS_LOG_FILE", "logs/app.log")
    MODELS_DIR = path_from_env("QIS_MODELS_DIR", "models")
    MVTEC_DATA_DIR = path_from_env("QIS_MVTEC_DATA_DIR", "mvtec_data")
    SOURCE_DATA_DIR = path_from_env("QIS_SOURCE_DATA_DIR", str(Path.home() / "Downloads"))
    VALIDATION_REPORTS_DIR = path_from_env("QIS_VALIDATION_REPORTS_DIR", "validation_reports")

    MAX_CONTENT_LENGTH = int(os.getenv("QIS_MAX_UPLOAD_MB", "16")) * 1024 * 1024
    ALLOWED_EXTENSIONS = {
        ext.strip().lower()
        for ext in os.getenv("QIS_ALLOWED_EXTENSIONS", "png,jpg,jpeg,gif,bmp").split(",")
        if ext.strip()
    }

    ADMIN_USER = os.getenv("QIS_ADMIN_USER", "admin")
    ADMIN_PASSWORD = os.getenv("QIS_ADMIN_PASSWORD", "admin123")
