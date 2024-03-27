from pydantic import EmailStr
from pydantic_settings import BaseSettings


class SettingsConfig(BaseSettings):
    """Config for NextDNS Invoices."""

    mailgun_from: EmailStr = "tviknarajah@bink.com"
    mailgun_to: EmailStr = "tviknarajah@bink.com"

    keyvault_url: str = "https://uksouth-prod-qj46.vault.azure.net/"


settings = SettingsConfig()
