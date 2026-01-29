"""
GitHub App Authentication for LOOVE AI Agent Infrastructure.

This module provides GitHub App-based authentication that can be used by any AI assistant
(Devin, Manus, Claude Code, etc.) to securely access GitHub Actions and repository resources.

GitHub Apps provide:
- Automatic token rotation (installation tokens expire in 1 hour)
- Fine-grained permissions per repository
- Better audit trail than personal access tokens
- Scalable access for multiple AI assistants

Usage:
    from integration_validation.credential.github_app_auth import GitHubAppAuth, get_github_app_auth

    # Get the singleton instance (auto-configured from environment)
    auth = get_github_app_auth()

    # Get installation token for API calls
    token = auth.get_installation_token()

    # Get auth headers for requests
    headers = auth.get_auth_headers()
"""

import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .env_credential_manager import EnvCredentialManager

logger = logging.getLogger(__name__)


class GitHubAppAuth:
    """
    GitHub App authentication handler for AI assistants.

    Manages JWT generation and installation token retrieval for GitHub App authentication.
    Designed to be agent-agnostic - works with Devin, Manus, Claude Code, or any other AI assistant.

    Required credentials (via environment or central .env):
        - GITHUB_APP_ID: The GitHub App's ID
        - GITHUB_APP_PRIVATE_KEY: The App's private key (PEM format)
        - GITHUB_APP_INSTALLATION_ID: The installation ID for your org/repos

    Optional:
        - GITHUB_APP_PRIVATE_KEY_PATH: Path to private key file (alternative to inline key)
    """

    GITHUB_API_BASE = "https://api.github.com"
    JWT_EXPIRATION_SECONDS = 600  # 10 minutes (GitHub max)
    TOKEN_REFRESH_BUFFER_SECONDS = 300  # Refresh 5 minutes before expiry

    def __init__(
        self,
        app_id: Optional[str] = None,
        private_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        installation_id: Optional[str] = None,
        agent_name: str = "loove_agent"
    ):
        """
        Initialize GitHub App authentication.

        Args:
            app_id: GitHub App ID (or set GITHUB_APP_ID env var)
            private_key: Private key content in PEM format (or set GITHUB_APP_PRIVATE_KEY)
            private_key_path: Path to private key file (or set GITHUB_APP_PRIVATE_KEY_PATH)
            installation_id: Installation ID (or set GITHUB_APP_INSTALLATION_ID)
            agent_name: Name of the AI agent using this auth (for logging/audit)
        """
        self.agent_name = agent_name
        self._cred_manager = EnvCredentialManager(f"github_app_{agent_name}")

        self._app_id = app_id or self._cred_manager.get_credential("GITHUB_APP_ID")
        self._installation_id = installation_id or self._cred_manager.get_credential("GITHUB_APP_INSTALLATION_ID")

        self._private_key = self._load_private_key(private_key, private_key_path)

        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0

        if self.is_configured():
            logger.info(f"GitHubAppAuth initialized for agent '{agent_name}'")
            logger.debug(f"GitHubAppAuth app_id for agent '{agent_name}' is {self._app_id}")
        else:
            logger.warning(f"GitHubAppAuth for agent '{agent_name}' is not fully configured")

    def _load_private_key(
        self,
        private_key: Optional[str],
        private_key_path: Optional[str]
    ) -> Optional[str]:
        """Load private key from provided value, path, or environment."""
        if private_key:
            return private_key

        key_path = private_key_path or self._cred_manager.get_credential("GITHUB_APP_PRIVATE_KEY_PATH")
        if key_path:
            path = Path(key_path).expanduser()
            if path.exists():
                try:
                    return path.read_text()
                except Exception as e:
                    logger.error(f"Failed to read private key from {path}: {e}")

        env_key = self._cred_manager.get_credential("GITHUB_APP_PRIVATE_KEY")
        if env_key:
            return env_key.replace("\\n", "\n")

        return None

    def is_configured(self) -> bool:
        """Check if all required credentials are available."""
        return all([
            self._app_id,
            self._private_key,
            self._installation_id
        ])

    def get_jwt(self) -> Optional[str]:
        """
        Generate a JWT for GitHub App authentication.

        Returns:
            JWT string or None if not configured or JWT library unavailable
        """
        if not self.is_configured():
            logger.warning("Cannot generate JWT: GitHub App not fully configured")
            return None

        if not HAS_JWT:
            logger.error("PyJWT library not installed. Install with: pip install PyJWT")
            return None

        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued 60 seconds ago (clock skew buffer)
            "exp": now + self.JWT_EXPIRATION_SECONDS,
            "iss": self._app_id
        }

        try:
            token = jwt.encode(payload, self._private_key, algorithm="RS256")
            logger.debug(f"Generated JWT for app_id={self._app_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to generate JWT: {e}")
            return None

    def get_installation_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get an installation access token for GitHub API calls.

        Tokens are cached and automatically refreshed before expiry.

        Args:
            force_refresh: Force token refresh even if cached token is valid

        Returns:
            Installation token string or None if unavailable
        """
        if not force_refresh and self._cached_token:
            if time.time() < (self._token_expires_at - self.TOKEN_REFRESH_BUFFER_SECONDS):
                return self._cached_token

        if not HAS_REQUESTS:
            logger.error("requests library not installed. Install with: pip install requests")
            return None

        jwt_token = self.get_jwt()
        if not jwt_token:
            return None

        url = f"{self.GITHUB_API_BASE}/app/installations/{self._installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        try:
            response = requests.post(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            self._cached_token = data.get("token")
            expires_at = data.get("expires_at")

            if expires_at:
                exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                self._token_expires_at = exp_dt.timestamp()
            else:
                self._token_expires_at = time.time() + 3600

            logger.info(f"Obtained installation token for agent '{self.agent_name}'")
            return self._cached_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get installation token: {e}")
            return None

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for GitHub API requests.

        Returns:
            Dictionary with Authorization and other required headers
        """
        token = self.get_installation_token()
        if not token:
            fallback_token = self._cred_manager.get_credential("GITHUB_TOKEN")
            if fallback_token:
                logger.info("Using fallback GITHUB_TOKEN (PAT) for authentication")
                token = fallback_token
            else:
                logger.warning("No GitHub authentication available")
                return {}

        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def verify_installation(self) -> Dict[str, Any]:
        """
        Verify the GitHub App installation is working.

        Returns:
            Dictionary with verification status and details
        """
        result = {
            "configured": self.is_configured(),
            "agent_name": self.agent_name,
            "app_id": self._app_id,
            "installation_id": self._installation_id,
            "jwt_available": False,
            "token_available": False,
            "environment": self._cred_manager.get_environment(),
            "error": None
        }

        if not result["configured"]:
            result["error"] = "GitHub App not fully configured"
            return result

        jwt_token = self.get_jwt()
        result["jwt_available"] = jwt_token is not None

        if jwt_token:
            token = self.get_installation_token()
            result["token_available"] = token is not None

        return result

    def get_status(self) -> Dict[str, Any]:
        """Get current authentication status."""
        return {
            "configured": self.is_configured(),
            "agent_name": self.agent_name,
            "app_id": self._app_id,
            "installation_id": self._installation_id,
            "has_cached_token": self._cached_token is not None,
            "token_expires_at": self._token_expires_at if self._cached_token else None,
            "environment": self._cred_manager.get_environment(),
            "dependencies": {
                "pyjwt": HAS_JWT,
                "requests": HAS_REQUESTS
            }
        }


_github_app_auth_instances: Dict[str, GitHubAppAuth] = {}


def get_github_app_auth(agent_name: str = "default") -> GitHubAppAuth:
    """
    Get a GitHubAppAuth instance for the specified agent.

    Args:
        agent_name: Name of the AI agent (e.g., "devin", "manus", "claude")

    Returns:
        GitHubAppAuth instance (cached per agent name)
    """
    if agent_name not in _github_app_auth_instances:
        _github_app_auth_instances[agent_name] = GitHubAppAuth(agent_name=agent_name)
    return _github_app_auth_instances[agent_name]


def get_installation_token(agent_name: str = "default") -> Optional[str]:
    """
    Convenience function to get an installation token.

    Args:
        agent_name: Name of the AI agent

    Returns:
        Installation token or None
    """
    auth = get_github_app_auth(agent_name)
    return auth.get_installation_token()
