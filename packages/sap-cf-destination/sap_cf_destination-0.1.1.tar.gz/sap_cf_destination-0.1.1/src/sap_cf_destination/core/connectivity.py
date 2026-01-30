import httpx
from datetime import datetime, timedelta

from .models import Singelton
from .settings import Settings


class Connectivity(Singelton):
    settings = Settings()
    auth: dict = {"token": None, "expires_at": None}

    def __init__(self) -> None:
        self._init_instance_credentials()

    def _init_instance_credentials(self) -> None:
        """
        Initialize instance credentials from settings.
        """
        if self.settings.vcap_services and self.settings.vcap_services.get(
            "connectivity"
        ):
            vcap = self.settings.vcap_services.get("connectivity")  # type: ignore
            credentials = vcap[0].get("credentials")  # type: ignore

            self.token_url = credentials.get("url")
            self.client_id = credentials.get("clientid")
            self.client_secret = credentials.get("clientsecret")
            self.onpremise_proxy_host = credentials.get("onpremise_proxy_host")
            self.onpremise_proxy_port = credentials.get("onpremise_proxy_port")
        else:
            raise ValueError("Connectivity service not bound to the application")

    async def _get_auth_token(self) -> None:
        """
        Generate an authentication token using client credentials.

        Returns:
            None
        """

        # Return cached token if valid
        if self.auth["token"] is not None and self.auth["expires_at"] > datetime.now():
            return self.auth["token"]
        # Generate new token
        else:
            try:
                async with httpx.AsyncClient(
                    base_url=self.token_url,
                    auth=httpx.BasicAuth(self.client_id, self.client_secret),
                ) as client:
                    response = await client.post(
                        "/oauth/token",
                        params={"grant_type": "client_credentials"},
                    )
                    response.raise_for_status()
                    token_data = response.json()

                    # Cache the token with its expiry time
                    self.auth["token"] = token_data.get("access_token")
                    self.auth["expires_at"] = datetime.now() + timedelta(
                        seconds=token_data.get("expires_in", 3600)
                    )

            except httpx.HTTPError as e:
                raise ConnectionError(f"Failed to obtain auth token: {e}") from e

    async def get_proxy_config(self) -> dict:
        """
        Get the OnPremise proxy configuration.

        Returns:
            dict: Proxy configuration with host and port.
        """
        await self._get_auth_token()

        return {
            "proxy": f"http://{self.onpremise_proxy_host}:{self.onpremise_proxy_port}",
            "headers": {"Proxy-Authorization": f"Bearer {self.auth['token']}"},
        }
