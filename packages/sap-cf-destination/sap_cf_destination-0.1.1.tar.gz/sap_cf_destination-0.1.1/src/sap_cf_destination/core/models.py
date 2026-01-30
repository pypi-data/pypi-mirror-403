from enum import Enum
from typing import Optional
import base64

from pydantic import BaseModel, model_validator


class Singelton:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super(Singelton, cls).__new__(cls)
            cls._instances[cls] = instance
        return cls._instances[cls]


class DestinationType(str, Enum):
    HTTP = "HTTP"


class ProxyType(str, Enum):
    INTERNET = "Internet"
    ONPREMISE = "OnPremise"


class AuthType(str, Enum):
    NO_AUTH = "NoAuthentication"
    BASIC = "BasicAuthentication"
    OAUTH2_CLIENT_CREDENTIALS = "OAuth2ClientCredentials"
    PRINCIPAL_PROPAGATION = "PrincipalPropagation"


class EnvProxyType(str, Enum):
    INTERNET = "Internet"
    ONPREMISE = "OnPremise"


class EnvAuthType(str, Enum):
    NO_AUTH = "NoAuthentication"
    BASIC = "BasicAuthentication"


class EnvDestination(BaseModel):
    name: str
    url: str
    type: DestinationType
    proxy_type: EnvProxyType
    auntentication: EnvAuthType
    username: Optional[str] = None
    password: Optional[str] = None
    forwardAuthToken: Optional[bool] = None
    proxyHost: Optional[str] = None
    proxyPort: Optional[int] = None
    timeout: Optional[int] = None

    @model_validator(mode="after")
    def validate_auth_fields(self):
        if self.auntentication == EnvAuthType.BASIC:
            if not self.username or not self.password:
                raise ValueError(
                    "Username and password are required for Basic Authentication."
                )
        return self

    @model_validator(mode="after")
    def validate_proxy(self):
        if self.proxy_type == EnvProxyType.ONPREMISE:
            if not self.proxyHost and not self.proxyPort:
                raise ValueError(
                    "Proxy Host and Port are required for OnPremise proxy type."
                )
        return self

    def get_configuration(self) -> dict:
        config = {
            "destinationConfiguration": {
                "Name": self.name,
                "Type": self.type.value,
                "URL": self.url,
                "ProxyType": self.proxy_type.value,
                "Authentication": self.auntentication.value,
                "ForwardAuthToken": self.forwardAuthToken,
                "Timeout": self.timeout,
            },
        }

        if self.auntentication == EnvAuthType.BASIC:
            config["authToken"] = [self._get_auth_token()]

        if self.proxy_type == EnvProxyType.ONPREMISE:
            config["proxyConfiguration"] = (
                {"proxy": f"{self.proxyHost}:{self.proxyPort}"}
                if self.proxyHost and self.proxyPort
                else {}
            )

    def _get_auth_token(self) -> dict:
        token_str = f"{self.username}:{self.password}"
        token_bytes = token_str.encode("utf-8")
        base64_bytes = base64.b64encode(token_bytes)
        base64_token = base64_bytes.decode("utf-8")
        return {
            "type": "Basic",
            "value": base64_token,
            "http_header": {"key": "Authorization", "value": f"Basic {base64_token}"},
        }
