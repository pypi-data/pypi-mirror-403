"""
Environment-aware credential management for LOOVE AI Agent Infrastructure.

This module provides consistent credential access across different environments
(development, CI, GitHub Actions) for any AI assistant in the LOOVE ecosystem.

Usage:
    from integration_validation.credential import EnvCredentialManager

    cred_manager = EnvCredentialManager("my_service")
    token = cred_manager.get_credential("API_TOKEN", required=True)
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Tuple


class EnvCredentialManager:
    """
    Environment-aware credential management with minimal overhead.

    Provides consistent credential access across:
    - GitHub Actions (uses environment variables from secrets)
    - CI environments (uses environment variables)
    - Development (uses central .env file or local credential stores)

    The central credential store location can be configured via the LOOVE_CREDENTIAL_STORE_PATH
    environment variable. Default: ~/repos/Devin_integrations/.env
    """

    def __init__(self, service_name: str):
        """
        Initialize credential manager for a service.

        Args:
            service_name: Name of the service/agent using credentials
        """
        self.service_name = service_name
        self.environment = self._detect_environment()
        self._credential_cache = {}
        self.logger = logging.getLogger(f"{__name__}.{service_name}")

    def _detect_environment(self) -> str:
        """Detect current environment with minimal overhead."""
        if os.environ.get("GITHUB_ACTIONS"):
            return "github_actions"
        elif os.environ.get("CI"):
            return "ci"
        else:
            return "development"

    def get_credential(
        self,
        name: str,
        required: bool = False,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get credential from appropriate source based on environment.

        Args:
            name: Name of the credential (e.g., "GITHUB_TOKEN")
            required: If True, raises error when credential is missing in dev
            default: Default value if credential is not found

        Returns:
            Credential value or default/None if not found
        """
        cache_key = f"{self.environment}:{name}"
        if cache_key in self._credential_cache:
            return self._credential_cache[cache_key]

        value = None
        if self.environment in ["github_actions", "ci"]:
            value = os.environ.get(name)
        else:
            value = self._get_from_local_store(name) or os.environ.get(name)

        if value:
            self._credential_cache[cache_key] = value
        elif required:
            if self.environment in ["github_actions", "ci"]:
                self.logger.warning(
                    f"Required credential {name} missing in {self.environment} environment"
                )
                return default or f"ci-mock-{name.lower()}"
            else:
                raise ValueError(f"Required credential {name} is not configured")

        return value or default

    def _get_from_local_store(self, name: str) -> Optional[str]:
        """Get credential from local store with minimal file operations."""
        env_path = os.environ.get("LOOVE_CREDENTIAL_STORE_PATH")
        if env_path:
            central_env = Path(os.path.expanduser(env_path))
        else:
            central_env = Path.home() / "repos" / "loove_os_integrations" / ".env"
        if central_env.exists():
            try:
                with open(central_env, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() == name:
                                return value.strip().strip('"').strip("'")
            except Exception as e:
                self.logger.warning(f"Failed to load from central .env: {e}")

        store_path = Path.home() / f".{self.service_name}_credentials.json"
        if not store_path.exists():
            return None

        try:
            with open(store_path, "r") as f:
                credentials = json.load(f)
                return credentials.get(name)
        except Exception as e:
            self.logger.warning(f"Failed to load credentials from {store_path}: {e}")
            return None

    def validate_credentials(
        self,
        required_credentials: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that required credentials are available.

        Args:
            required_credentials: List of credential names to validate

        Returns:
            Tuple of (success, list of missing credentials)
        """
        missing = []
        for cred in required_credentials:
            if not self.get_credential(cred):
                missing.append(cred)

        if missing:
            self.logger.error(f"Missing required credentials: {missing}")
            return False, missing
        return True, []

    def get_environment(self) -> str:
        """Get current environment."""
        return self.environment

    def clear_cache(self) -> None:
        """Clear credential cache."""
        self._credential_cache.clear()
        self.logger.info("Credential cache cleared")
