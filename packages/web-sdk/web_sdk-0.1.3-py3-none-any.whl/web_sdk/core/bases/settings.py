"""Base SDK settings."""

import logging

from pydantic import ImportString, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from web_sdk.enums import TokenType
from web_sdk.utils.url import join_path


class BaseSDKSettings(BaseSettings):
    """Base SDK settings."""

    # URL settings
    protocol: str = "https"
    """API protocol"""
    host: str = "0.0.0.0"
    """API host"""
    port: int | None = None
    """API port"""
    api_path: str = ""
    """API path (WSDL path for SOAP)"""

    # Auth settings
    username: str | None = None
    """Login for authentication"""
    password: str | None = None
    """Password for authentication"""
    token: str | None = None
    """Token for authentication"""
    token_type: TokenType | None = None
    """Token type for authentication"""
    custom_token_type: str | None = None
    """Custom token type for authentication"""
    api_key: str | None = None
    """API key for authentication"""
    api_key_header: str = "x-api-key"
    """API key for authentication header"""

    # Client settings
    max_retry_count: int = 0
    """Max retry count"""
    max_retry_count_after_disconnect: int = 1
    """Max retry after disconnect count"""
    need_authentication: bool = False
    """Need authentication"""
    timeout: int | tuple[int, int] = 15
    """Timeout"""

    # Tests settings
    test_mode: bool = False
    """Is test mode"""
    # Next 2 settings are sorted in order of priority
    skip_for_test: bool = False
    """Skip make_request execution for test"""
    fake_for_test: bool = False
    """Fake result for make_request execution for test"""

    # Logger settings (settings are sorted in order of priority)
    default_logger: ImportString[logging.Logger] | None = None
    """Default logger for SDK clients"""
    default_logger_name: str | None = None
    """Default logger name for SDK clients"""
    use_logging_as_default_logger: bool = True
    """Use logging module as default logger in SDK clients"""

    # Other settings (settings are sorted in order of priority)
    raise_exceptions: bool = True
    """Raise exceptions during sdk method execution"""

    model_config = SettingsConfigDict(frozen=True)

    @computed_field
    @property
    def url(self) -> str:
        """Full API url (wsdl url for SOAP)."""
        url = f"{self.protocol}://{self.host}"

        if self.port:
            url = f"{url}:{self.port}"
        if self.api_path:
            url = join_path(url, self.api_path)

        return url
