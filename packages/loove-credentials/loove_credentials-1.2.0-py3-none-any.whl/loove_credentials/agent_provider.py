"""
Agent Credential Provider for LOOVE AI Infrastructure.

This module provides a simple interface for AI agents (Manus, Devin, Claude Code, etc.)
to obtain credentials for various services. It abstracts the underlying credential
management and provides a consistent API across all agents.

Usage:
    from integration_validation.credential.agent_provider import AgentCredentialProvider

    # Initialize for your agent
    provider = AgentCredentialProvider("manus")

    # Get GitHub credentials
    github_token = provider.get_github_token()
    github_headers = provider.get_github_headers()

    # Get other service credentials
    slack_token = provider.get_credential("SLACK_BOT_TOKEN")
    asana_token = provider.get_credential("ASANA_ACCESS_TOKEN")
"""

import logging
from typing import Optional, Dict, Any, List

from .env_credential_manager import EnvCredentialManager
from .github_app_auth import GitHubAppAuth, get_github_app_auth

logger = logging.getLogger(__name__)


class AgentCredentialProvider:
    """
    Unified credential provider for LOOVE AI agents.

    Provides a simple, consistent interface for obtaining credentials
    across different services and environments.
    """

    def __init__(self, agent_name: str):
        """
        Initialize the credential provider for an agent.

        Args:
            agent_name: Name of the AI agent (e.g., "manus", "devin", "claude")
        """
        self.agent_name = agent_name
        self._cred_manager = EnvCredentialManager(agent_name)
        self._github_auth: Optional[GitHubAppAuth] = None
        
        logger.info(f"AgentCredentialProvider initialized for '{agent_name}'")

    @property
    def github_auth(self) -> GitHubAppAuth:
        """Get or create the GitHub App auth instance."""
        if self._github_auth is None:
            self._github_auth = get_github_app_auth(self.agent_name)
        return self._github_auth

    def get_credential(
        self,
        name: str,
        required: bool = False,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a credential by name.

        Args:
            name: Name of the credential (e.g., "SLACK_BOT_TOKEN")
            required: If True, raises error when credential is missing in dev
            default: Default value if credential is not found

        Returns:
            Credential value or default/None if not found
        """
        return self._cred_manager.get_credential(name, required=required, default=default)

    def get_github_token(self) -> Optional[str]:
        """
        Get a GitHub token for API access.

        Prefers GitHub App installation token, falls back to GITHUB_TOKEN PAT.

        Returns:
            GitHub token or None if unavailable
        """
        token = self.github_auth.get_installation_token()
        if token:
            return token
        
        return self._cred_manager.get_credential("GITHUB_TOKEN")

    def get_github_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for GitHub API requests.

        Returns:
            Dictionary with Authorization and other required headers
        """
        return self.github_auth.get_auth_headers()

    def get_slack_token(self) -> Optional[str]:
        """Get Slack bot token."""
        return self._cred_manager.get_credential("SLACK_BOT_TOKEN")

    def get_asana_token(self) -> Optional[str]:
        """Get Asana access token."""
        return self._cred_manager.get_credential("ASANA_ACCESS_TOKEN")

    def get_environment(self) -> str:
        """Get current environment (github_actions, ci, or development)."""
        return self._cred_manager.get_environment()

    def validate_required_credentials(
        self,
        credentials: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that required credentials are available.

        Args:
            credentials: List of credential names to validate

        Returns:
            Dictionary with validation results
        """
        success, missing = self._cred_manager.validate_credentials(credentials)
        return {
            "success": success,
            "missing": missing,
            "environment": self.get_environment(),
            "agent_name": self.agent_name
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of credential availability.

        Returns:
            Dictionary with status information
        """
        github_status = self.github_auth.get_status()
        
        return {
            "agent_name": self.agent_name,
            "environment": self.get_environment(),
            "github": {
                "app_configured": github_status["configured"],
                "app_id": github_status["app_id"],
                "has_token": github_status["has_cached_token"],
                "fallback_available": self._cred_manager.get_credential("GITHUB_TOKEN") is not None
            },
            "services": {
                "slack": self.get_slack_token() is not None,
                "asana": self.get_asana_token() is not None
            }
        }


def get_agent_provider(agent_name: str) -> AgentCredentialProvider:
    """
    Factory function to get an AgentCredentialProvider instance.

    Args:
        agent_name: Name of the AI agent

    Returns:
        AgentCredentialProvider instance
    """
    return AgentCredentialProvider(agent_name)


# Pre-configured providers for common agents
def get_manus_provider() -> AgentCredentialProvider:
    """Get credential provider for Manus."""
    return get_agent_provider("manus")


def get_devin_provider() -> AgentCredentialProvider:
    """Get credential provider for Devin."""
    return get_agent_provider("devin")


def get_claude_provider() -> AgentCredentialProvider:
    """Get credential provider for Claude Code."""
    return get_agent_provider("claude")
