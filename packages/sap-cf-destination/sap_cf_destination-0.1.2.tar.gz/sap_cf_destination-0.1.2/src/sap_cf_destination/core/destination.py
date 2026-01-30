from datetime import datetime, timedelta

import httpx

from .settings import Settings
from .connectivity import Connectivity
from .models import Singelton, ProxyType


class DestinationInstance(Singelton):
    settings = Settings()
    auth: dict = {"token": None, "expires_at": None}

    def __init__(self):
        self._init_instance_credentials()
        self.local_destination = self.settings.destinations

    def _init_instance_credentials(self):
        """
        Initialize instance credentials from settings.
        """
        if self.settings.vcap_services and self.settings.vcap_services.get(
            "destination"
        ):
            vcap = self.settings.vcap_services.get("destination")  # type: ignore
            credentials = vcap[0].get("credentials")  # type: ignore

            self.base_url = credentials.get("uri")
            self.client_id = credentials.get("clientid")
            self.client_secret = credentials.get("clientsecret")
            self.token_service_url = credentials.get("url")

    async def _generate_auth_token(self) -> str:
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
                    base_url=self.token_service_url,
                    auth=httpx.BasicAuth(self.client_id, self.client_secret),
                ) as client:
                    response = await client.post(
                        "/oauth/token",
                        params={
                            "grant_type": "client_credentials",
                        },
                    )
                    response.raise_for_status()
                    token_data = response.json()
                    self.auth["token"] = token_data.get("access_token")
                    self.auth["expires_at"] = datetime.now() + timedelta(
                        seconds=token_data.get("expires_in", 3600)
                    )
            except httpx.HTTPError as e:
                raise ConnectionError(
                    f"Error generating auth token for destination instance: {e}"
                ) from e

    async def get_configuration(self, name: str) -> dict:
        """
        Retrieve the configuration for a specific destination.

        Args:
            name (str): The name of the destination.
        Returns:
            dict: The destination configuration.
        """
        # Check if destination exists in environment variables
        if self.local_destination is not None:
            for dest in self.local_destination:
                if dest.name == name:
                    return dest.get_configuration()
        # Fetch destination configuration from the service
        else:
            await self._generate_auth_token()
            headers = {
                "Authorization": f"Bearer {self.auth['token']}",
                "Content-Type": "application/json",
            }

            try:
                async with httpx.AsyncClient(
                    base_url=self.base_url, headers=headers
                ) as client:
                    response = await client.get(
                        f"/destination-configuration/v1/destinations/{name}"
                    )
                    response.raise_for_status()
                    result = response.json()

                    proxy_type = result["destinationConfiguration"].get("ProxyType")

                    # Add proxy configuration if proxy type is OnPremise
                    if proxy_type == ProxyType.ONPREMISE.value:
                        connectivity = Connectivity()

                        result["proxyConfiguration"] = {
                            "proxy": await connectivity.get_proxy_config()
                        }
                    return result
            except httpx.HTTPError as e:
                raise ConnectionError(
                    f"Error fetching destination configuration for '{name}': {e}"
                ) from e
