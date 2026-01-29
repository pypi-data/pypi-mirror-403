from paapi5_python_sdk.api.default_api import DefaultApi
from pydantic import BaseModel


class AuthenticationConfig(BaseModel):
    """Configuration model for Amazon PA API authentication."""

    access_key: str
    secret_key: str
    partner_tag: str
    host: str
    region: str


class Authentication:
    """Handles authentication for Amazon Product Advertising API."""

    def __init__(self, config: AuthenticationConfig):
        """
        Initialize authentication with configuration.

        Args:
            config: Authentication configuration containing credentials and settings
        """
        self._api_client = None
        self.access_key = config.access_key
        self.secret_key = config.secret_key
        self.partner_tag = config.partner_tag
        self.host = config.host
        self.region = config.region

    def authenticate(self) -> DefaultApi:
        """
        Create and return an authenticated API client.

        Returns:
            DefaultApi: Authenticated API client

        Raises:
            ValueError: If authentication fails
        """
        if not all([self.access_key, self.secret_key, self.host, self.region]):
            raise ValueError("Missing required authentication credentials")
        try:
            self._api_client = DefaultApi(
                access_key=self.access_key,
                secret_key=self.secret_key,
                host=self.host,
                region=self.region,
            )
            print("Authentication successful.")
            return self._api_client
        except Exception as e:
            raise ValueError(f"Authentication failed: {str(e)}") from e

    def __repr__(self):
        return f"Authentication(partner_tag={self.partner_tag}, host={self.host}, region={self.region})"
