"""
Credential management for LOOVE AI Agent Infrastructure.

This module provides environment-aware credential management and GitHub App
authentication for all AI assistants in the LOOVE ecosystem.

Simple Usage (recommended for Manus):
    from loove_credentials import get_asana_token, get_github_token
    
    # Tokens auto-bootstrap from GitHub on first access
    asana_token = get_asana_token()
    github_token = get_github_token()

Advanced Usage:
    from loove_credentials import get_agent_provider
    
    provider = get_agent_provider("manus")
    github_token = provider.get_github_token()
    github_headers = provider.get_github_headers()

CLI Usage:
    python -m loove_credentials status
    python -m loove_credentials verify
    python -m loove_credentials setup
"""

import os
import subprocess
import base64

__version__ = "1.2.0"

from .env_credential_manager import EnvCredentialManager
from .github_app_auth import (
    GitHubAppAuth,
    get_github_app_auth,
    get_installation_token,
)
from .agent_provider import (
    AgentCredentialProvider,
    get_agent_provider,
    get_manus_provider,
    get_devin_provider,
    get_claude_provider,
)
from .shopify_provider import (
    ShopifyCredentialProvider,
    get_shopify_provider,
)

__all__ = [
    # Simple API
    'bootstrap',
    'get_asana_token',
    'get_github_token',
    'get_coda_token',
    'get_coda_financial_modeling_token',
    'get_coda_expense_projections_token',
    'get_coda_studio_booking_token',
    'get_coda_loove_brain_token',
    'get_coda_josh_trombonistry_token',
    'get_shopify_token',
    'get_shopify_client',
    'get_token',
    # Advanced API
    'EnvCredentialManager',
    'GitHubAppAuth',
    'get_github_app_auth',
    'get_installation_token',
    'AgentCredentialProvider',
    'get_agent_provider',
    'get_manus_provider',
    'get_devin_provider',
    'get_claude_provider',
    'ShopifyCredentialProvider',
    'get_shopify_provider',
]

_bootstrapped = False


def bootstrap(repo: str = "joshroseman/loove_os_integrations", env_path: str = ".env"):
    """
    Bootstrap credentials from GitHub repository.
    
    Fetches the .env file from the private repo using gh CLI authentication.
    Call this once at the start of a session before accessing tokens,
    or let the get_*_token() functions call it automatically.
    
    Args:
        repo: GitHub repository containing credentials
        env_path: Path to .env file within the repo
    
    Returns:
        True if successful
    
    Raises:
        RuntimeError: If credentials cannot be fetched
    """
    global _bootstrapped
    
    if _bootstrapped:
        return True
    
    try:
        # Fetch .env content via GitHub API using gh CLI
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{env_path}", "--jq", ".content"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Decode base64 content
        env_content = base64.b64decode(result.stdout.strip()).decode("utf-8")
        
        # Parse and set environment variables
        for line in env_content.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value
        
        _bootstrapped = True
        return True
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to fetch credentials from GitHub. "
            f"Ensure gh CLI is authenticated: {e.stderr}"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to bootstrap credentials: {e}")


def get_asana_token() -> str:
    """
    Get Asana access token.
    
    Automatically calls bootstrap() on first use to fetch credentials
    from the GitHub repository.
    
    Returns:
        Asana API token string
    
    Raises:
        ValueError: If token not found after bootstrap
    """
    if not _bootstrapped:
        bootstrap()
    
    token = os.environ.get("ASANA_ACCESS_TOKEN")
    if not token:
        raise ValueError("ASANA_ACCESS_TOKEN not found after bootstrap")
    return token


def get_github_token() -> str:
    """
    Get GitHub token via GitHub App or fallback to PAT.
    
    Tries GitHub App authentication first (preferred), then falls back
    to a personal access token if available.
    
    Returns:
        GitHub API token string
    
    Raises:
        ValueError: If no GitHub token available
    """
    if not _bootstrapped:
        bootstrap()
    
    # Try GitHub App first
    try:
        auth = get_github_app_auth("manus")
        token = auth.get_installation_token()
        if token:
            return token
    except Exception:
        pass
    
    # Fallback to PAT
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    
    raise ValueError("No GitHub token available")


def get_coda_token(doc_name: str = None) -> str:
    """
    Get Coda API token.
    
    Args:
        doc_name: Optional doc name to get specific token.
                  Valid values: 'financial_modeling', 'expense_projections',
                  'studio_booking', 'loove_brain', 'josh_trombonistry'
                  If None, returns the default CODA_API_KEY.
    
    Returns:
        Coda API token string
    
    Raises:
        ValueError: If token not found after bootstrap
    """
    if not _bootstrapped:
        bootstrap()
    
    if doc_name:
        env_var = f"CODA_{doc_name.upper()}_TOKEN"
        token = os.environ.get(env_var)
        if not token:
            raise ValueError(f"{env_var} not found after bootstrap")
        return token
    
    token = os.environ.get("CODA_API_KEY")
    if not token:
        raise ValueError("CODA_API_KEY not found after bootstrap")
    return token


def get_coda_financial_modeling_token() -> str:
    """
    Get Coda token for Financial Modeling doc.
    
    Returns:
        Coda API token string for Financial Modeling doc
    """
    return get_coda_token("financial_modeling")


def get_coda_expense_projections_token() -> str:
    """
    Get Coda token for Expense Projections doc.
    
    Returns:
        Coda API token string for Expense Projections doc
    """
    return get_coda_token("expense_projections")


def get_coda_studio_booking_token() -> str:
    """
    Get Coda token for Studio Booking doc.
    
    Returns:
        Coda API token string for Studio Booking doc
    """
    return get_coda_token("studio_booking")


def get_coda_loove_brain_token() -> str:
    """
    Get Coda token for LOOVE BRAIN doc.
    
    Returns:
        Coda API token string for LOOVE BRAIN doc
    """
    return get_coda_token("loove_brain")


def get_coda_josh_trombonistry_token() -> str:
    """
    Get Coda token for Josh Trombonistry doc.
    
    Returns:
        Coda API token string for Josh Trombonistry doc
    """
    return get_coda_token("josh_trombonistry")


def get_shopify_token() -> str:
    """
    Get Shopify access token.
    
    Returns:
        Shopify API token string
    
    Raises:
        ValueError: If token not found after bootstrap
    """
    if not _bootstrapped:
        bootstrap()
    
    token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    if not token:
        raise ValueError("SHOPIFY_ACCESS_TOKEN not found after bootstrap")
    return token


def get_token(name: str) -> str:
    """
    Get any token by environment variable name.
    
    Args:
        name: Environment variable name (e.g., "ASANA_ACCESS_TOKEN")
    
    Returns:
        Token value string
    
    Raises:
        ValueError: If token not found after bootstrap
    """
    if not _bootstrapped:
        bootstrap()
    
    token = os.environ.get(name)
    if not token:
        raise ValueError(f"{name} not found after bootstrap")
    return token


def get_shopify_client(shop_domain: str = "boops-nyc.myshopify.com"):
    """
    Get a ready-to-use Shopify API client.
    
    This function handles OAuth authentication automatically using the Client
    Credentials Grant flow. Access tokens are cached and auto-refreshed.
    
    Args:
        shop_domain: Shopify store domain (default: boops-nyc.myshopify.com)
    
    Returns:
        ShopifyAPIClient instance ready for API calls
    
    Example:
        from loove_credentials import get_shopify_client
        
        client = get_shopify_client()
        products = client.list_products()
        orders = client.list_orders()
    """
    if not _bootstrapped:
        bootstrap()
    
    # Import here to avoid circular dependencies
    from ..shopify_client import ShopifyAPIClient
    
    return ShopifyAPIClient(agent_name="manus", shop_domain=shop_domain)
