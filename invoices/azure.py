"""Functions for interacting with Azure services."""

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from invoices.settings import settings

identity = DefaultAzureCredential()

keyvault_client = SecretClient(
    vault_url=str(settings.keyvault_url), credential=identity
)
