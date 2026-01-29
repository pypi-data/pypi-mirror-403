"""Vault provider implementations.

This subpackage contains concrete implementations of the vault provider
protocols for different backend systems.

Available Providers:
    - OpenBaoVaultProvider: OpenBao/HashiCorp Vault (KV v2)
    - YAMLVaultProvider: YAML file-based (development only)
    - AzureKeyVaultProvider: Azure Key Vault
    - CyberArkVaultProvider: CyberArk PVWA REST API
    - DelineaVaultProvider: Delinea Secret Server REST API
    - FileVaultProvider: Local filesystem / CSI-mounted secrets

Note:
    DB provider is CRUDService-internal and not included here.
    It uses a non-URI format (db:credentials:uuid) that doesn't fit
    the unified registry pattern.
"""
from __future__ import annotations

from empowernow_common.vault.providers.openbao import OpenBaoVaultProvider
from empowernow_common.vault.providers.yaml import YAMLVaultProvider
from empowernow_common.vault.providers.azure_keyvault import AzureKeyVaultProvider
from empowernow_common.vault.providers.cyberark import CyberArkVaultProvider
from empowernow_common.vault.providers.delinea import DelineaVaultProvider
from empowernow_common.vault.providers.file import FileVaultProvider

# Auto-register providers with the factory
from empowernow_common.vault.config import register_provider_factory

register_provider_factory("openbao", OpenBaoVaultProvider)
register_provider_factory("hashicorp", OpenBaoVaultProvider)  # Alias
register_provider_factory("vault", OpenBaoVaultProvider)  # Alias
register_provider_factory("yaml", YAMLVaultProvider)
register_provider_factory("azure", AzureKeyVaultProvider)
register_provider_factory("azure_keyvault", AzureKeyVaultProvider)  # Alias
register_provider_factory("akv", AzureKeyVaultProvider)  # Alias
register_provider_factory("cyberark", CyberArkVaultProvider)
register_provider_factory("pvwa", CyberArkVaultProvider)  # Alias
register_provider_factory("delinea", DelineaVaultProvider)
register_provider_factory("secretserver", DelineaVaultProvider)  # Alias
register_provider_factory("thycotic", DelineaVaultProvider)  # Legacy alias
register_provider_factory("file", FileVaultProvider)


__all__ = [
    "OpenBaoVaultProvider",
    "YAMLVaultProvider",
    "AzureKeyVaultProvider",
    "CyberArkVaultProvider",
    "DelineaVaultProvider",
    "FileVaultProvider",
]
