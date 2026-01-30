import httpx
import asyncio
from datetime import datetime, timedelta

from .core import DestinationInstance, ProxyType, AuthType


class Destination:
    """
    SAP BTP Destination client
    """

    _instance = DestinationInstance()
    _config: dict = {"parameters": None, "expires_in": None}
    auth_type: str = None
    proxy_type: str = None
    forward_auth_token: bool = False
    url: str = None
    timeout: int = 30

    def __init__(self, name: str, cache_duration: int = 3600) -> None:
        if name is None or name.strip() == "":
            raise ValueError("Destination name must be provided and cannot be empty.")
        else:
            self.name = name

        self.cache_duration = cache_duration

    def _validate_configuration(self, config: dict) -> None:
        """
        Validate the retrieved destination configuration.
        """
        proxy_type = config.get("destinationConfiguration").get("ProxyType")
        auth_type = config.get("destinationConfiguration").get(
            "Authentication"
        )

        if proxy_type not in ProxyType:
            raise ValueError(f"Unsupported proxy type: {proxy_type}")

        if auth_type not in AuthType:
            raise ValueError(f"Unsupported authentication type: {auth_type}")

    async def _get_configuration(self) -> dict:
        """
        Retrieve the destination configuration.

        Returns:
            dict: The destination configuration.
        """
        config = await self._instance.get_configuration(self.name)

        destinationConfig = config.get("destinationConfiguration")

        self.auth_type = destinationConfig.get("Authentication")
        self.proxy_type = destinationConfig.get("ProxyType")
        self.forward_auth_token = destinationConfig.get("ForwardAuthToken", False)
        self.url = destinationConfig.get("URL")
        self.timeout = destinationConfig.get("Timeout", 30)

        self._validate_configuration(config)

        return config

    async def _build_parameters(self, jwt: str) -> None:
        """
        Build the parameters dictionary from the configuration.
        """
        if (
            self.auth_type is not None and self.auth_type != AuthType.OAUTH2_CLIENT_CREDENTIALS.value
            and self._config["parameters"] is not None
        ):
            return self._config["parameters"]
        elif (
            self.auth_type is not None and self.auth_type == AuthType.OAUTH2_CLIENT_CREDENTIALS.value
            and self._config["expires_in"] is not None
            and self._config["expires_in"] > datetime.now()
        ):
            return self._config["parameters"]
        else:
            config = await self._get_configuration()

            params = {
                "base_url": self.url,
                "timeout": self.timeout,
            }

            if (
                config.get("authTokens") is not None
                and len(config.get("authTokens")) > 0
            ):
                params["headers"] = {
                    config["authTokens"][0]["http_header"]["key"]: config["authTokens"][
                        0
                    ]["http_header"]["value"]
                }
                self._config["expires_in"] = datetime.now() + timedelta(
                    seconds=int(config["authTokens"][0].get(
                        "expires_in", self.cache_duration
                    ))
                )

            if self.auth_type == AuthType.NO_AUTH.value and self.forward_auth_token:
                if jwt is None:
                    raise ValueError("JWT must be provided for forwarding auth token.")
                else:
                    if "headers" not in params:
                        params["headers"] = {}
                    params["headers"]["Authorization"] = f"Bearer {jwt}"

            if self.proxy_type == ProxyType.ONPREMISE.value:
                proxy_config = config.get("proxyConfiguration", {})
                if proxy_config.get("proxy") is not None:
                    params["proxy"] = proxy_config.get("proxy")
                    params["headers"] = {
                        **params.get("headers", {}),
                        **proxy_config.get("headers", {}),
                    }

                if self.auth_type == AuthType.PRINCIPAL_PROPAGATION.value:
                    if jwt is None:
                        raise ValueError(
                            "JWT must be provided for Principal Propagation."
                        )
                    else:
                        params["headers"]["SAP-Connectivity-Authentication"] = (
                            f"Bearer {jwt}"
                        )

                if (
                    config["destinationConfiguration"].get("CloudConnectorLocationId")
                    is not None
                ):
                    params["headers"]["SAP-Connectivity-SCC-Location_ID"] = config[
                        "destinationConfiguration"
                    ].get("CloudConnectorLocationId")

            self._config["parameters"] = params

    def get_client(self, jwt: str = None) -> httpx.Client:
        """
        Create and return an HTTP client configured for the destination.

        Returns:
            httpx.Client: An HTTP client instance.
        """
        asyncio.run(self._build_parameters(jwt))
        return httpx.Client(**self._config["parameters"])

    async def get_aclient(self, jwt: str = None) -> httpx.AsyncClient:
        """
        Create and return an asynchronous HTTP client configured for the destination.

        Returns:
            httpx.AsyncClient: An asynchronous HTTP client instance.
        """
        await self._build_parameters(jwt)
        return httpx.AsyncClient(**self._config["parameters"])
