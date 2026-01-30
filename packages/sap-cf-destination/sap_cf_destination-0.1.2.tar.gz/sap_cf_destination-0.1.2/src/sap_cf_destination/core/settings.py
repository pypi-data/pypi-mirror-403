from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from .models import EnvDestination


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    vcap_services: dict | None = None

    destinations: list[EnvDestination] | None = None

    @model_validator(mode="after")
    def validate_vcap_variables(self):
        vcap = self.vcap_services.get("destination") if self.vcap_services else None
        if not self.destinations and not vcap:
            raise ValueError("Destination service not bound to the application")

        return self
