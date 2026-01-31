from enum import Enum
from importlib.machinery import PathFinder
from pathlib import Path
from typing import Optional

from pydantic import SecretStr
from pydantic_extra_types.color import Color
from pydantic_settings import BaseSettings


class StorageType(str, Enum):
    MINIO = "MINIO"
    MINIO_AWS = "MINIO_AWS"
    NONE = "NONE"


class StreamlitBaseSettings(BaseSettings):
    SIGNOUT_URL: Optional[str] = None
    CURRENT_PACKAGE: str = __name__.split(".")[0]
    BASE_PATH: str = str(Path(PathFinder().find_spec(CURRENT_PACKAGE).origin).parent)  # type: ignore
    DATA_DIR: str = str(Path.cwd() / "appdata")
    DOCS_DIR: str = str(Path.cwd() / "docs")
    """Root directory for storing app data."""

    ###############
    # Storage Vars
    ###############
    STORAGE_TYPE: StorageType = StorageType.NONE
    BUCKET_NAME: Optional[str] = None
    BUCKET_PREFIX: Optional[str] = None
    MINIO_SECRET_KEY: Optional[SecretStr] = None
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_HTTPS: bool = True

    XT_HOME_URL: str = "https://apps.exploration.tools"
    """URL of where the privacy policy button should link to."""
    XT_PRIVACY_URL: str = "https://www.csiro.au/en/About/Access-to-information/Privacy"
    """URL of where the xt logo should link to."""
    APP_NAME: str = "my_app"
    """Name of the app that be tagged in the DB."""
    APP_TAG_TEXT: str = "Dev"
    """Text that will appear next the application logo."""
    APP_TAG_BACKGROUND: Color = Color("#00a9ce")
    """Background colour of the APP_TAG_TEXT."""
    APP_GET_HELP: Optional[str] = None
    """Link to "Get Help" in streamlit hamburger menu (menu item is hidden if set to None)."""
    APP_REPORT_BUG: Optional[str] = None
    """Link to "Report a Bug" in streamlit hamburger menu (menu item is hidden if set to None)."""
    APP_ABOUT: Optional[str] = None
    """Markdown Text to show in streamlit hamburger menu (shows streamlit default if set to None)."""
    DEBUG: bool = False
    """Enable debug information in the app."""
    DEBUG_MOCK_SESSION: bool = False
    """Mock the session headers returned when deployed to AWS."""
    USE_COGNITO: bool = False
    """Use AWS Cognito for Auth."""
    ACCESS_TOKEN_KEY: str = "X-Forwarded-Access-Token"
    """Key used to retrieve the access token from the headers."""
    USER_KEY: str = "X-Forwarded-User"
    """Key used to retrieve the user from the headers."""
    EMAIL_KEY: str = "X-Forwarded-Email"
    """Key used to retrieve the email from the headers."""
    OIDC_TOKEN: str | None = None  # "X-Amzn-Oidc-Data"

    COGNITO_COOKIE: str = "AWSELBAuthSessionCookie"
    """If set cookies with this prefix will be deleted on signout."""
    COGNITO_GROUPS: str = "ap-southeast-2_lC6GUKOej_CSIRO-EASI"
    """One of these comma separated groups must be present in the user's `cognito:groups`."""
    NO_ACCESS_MSG: str = "Error: You do not have permission to use this app."
    """Error message displayed when a user doesn't have permission to use the app."""
    STREAMLIT_SERVER_BASE_URL_PATH: str = ""
    """The base path for the URL where Streamlit should be served from."""
    MONGO_CONNECTION_STRING: str = ""
    """Mongo DB connection string."""
    DATABASE_NAME: str = ""
    """Mongo DB Database Name."""
    TIMEZONE: str = "Australia/Perth"
    """Default timezone used within the app."""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"
