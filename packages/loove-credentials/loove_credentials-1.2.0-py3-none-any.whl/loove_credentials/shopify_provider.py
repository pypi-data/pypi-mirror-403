"""
Shopify Credential Provider for LOOVE AI Infrastructure.

This module provides automatic token management for Shopify API access,
including token caching and automatic refresh.
"""

import logging
import time
from typing import Optional, Dict, Any
import requests

from .env_credential_manager import EnvCredentialManager

logger = logging.getLogger(__name__)


class ShopifyCredentialProvider:
    """
    Manages Shopify API authentication with automatic token refresh.
    
    Handles the client credentials grant flow and caches tokens until expiry.
    """
    
    def __init__(self, agent_name: str, shop_domain: str):
        """
        Initialize Shopify credential provider.
        
        Args:
            agent_name: Name of the AI agent (e.g., "manus")
            shop_domain: Shopify store domain (e.g., "boops-nyc.myshopify.com")
        """
        self.agent_name = agent_name
        self.shop_domain = shop_domain
        self._cred_manager = EnvCredentialManager(agent_name)
        
        # Token cache
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        self._token_scopes: Optional[str] = None
        
        logger.info(f"ShopifyCredentialProvider initialized for '{agent_name}' on '{shop_domain}'")
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get a valid Shopify access token.
        
        Automatically refreshes the token if expired or if force_refresh is True.
        
        Args:
            force_refresh: Force token refresh even if current token is valid
            
        Returns:
            Valid Shopify access token
            
        Raises:
            RuntimeError: If token acquisition fails
        """
        # Check if we have a valid cached token
        if not force_refresh and self._is_token_valid():
            logger.debug("Using cached Shopify access token")
            return self._access_token
        
        # Request new token
        logger.info("Requesting new Shopify access token")
        return self._request_new_token()
    
    def _is_token_valid(self) -> bool:
        """Check if the cached token is still valid."""
        if not self._access_token or not self._token_expires_at:
            return False
        
        # Consider token invalid 5 minutes before actual expiry
        buffer_seconds = 300
        return time.time() < (self._token_expires_at - buffer_seconds)
    
    def _request_new_token(self) -> str:
        """
        Request a new access token from Shopify.
        
        Returns:
            New access token
            
        Raises:
            RuntimeError: If token request fails
        """
        # Get credentials
        client_id = self._cred_manager.get_credential('SHOPIFY_CLIENT_ID', required=True)
        client_secret = self._cred_manager.get_credential('SHOPIFY_API_SECRET', required=True)
        
        # Build request
        token_url = f"https://{self.shop_domain}/admin/oauth/access_token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            response = requests.post(token_url, data=payload, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data['access_token']
            self._token_scopes = token_data['scope']
            expires_in = token_data['expires_in']
            
            # Calculate expiry time
            self._token_expires_at = time.time() + expires_in
            
            logger.info(f"Successfully obtained Shopify access token (expires in {expires_in}s)")
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to obtain Shopify access token: {e}")
            raise RuntimeError(f"Shopify token request failed: {e}")
    
    def get_api_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for Shopify API requests.
        
        Returns:
            Dictionary with required headers including access token
        """
        token = self.get_access_token()
        return {
            'X-Shopify-Access-Token': token,
            'Content-Type': 'application/json'
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information about the Shopify connection.
        
        Returns:
            Dictionary with status information
        """
        return {
            'agent_name': self.agent_name,
            'shop_domain': self.shop_domain,
            'has_token': self._access_token is not None,
            'token_valid': self._is_token_valid(),
            'token_scopes': self._token_scopes,
            'expires_at': self._token_expires_at
        }
    
    def clear_cache(self) -> None:
        """Clear cached token, forcing refresh on next request."""
        self._access_token = None
        self._token_expires_at = None
        self._token_scopes = None
        logger.info("Shopify token cache cleared")


def get_shopify_provider(agent_name: str, shop_domain: str = "boops-nyc.myshopify.com") -> ShopifyCredentialProvider:
    """
    Factory function to get a ShopifyCredentialProvider instance.
    
    Args:
        agent_name: Name of the AI agent
        shop_domain: Shopify store domain (defaults to boops-nyc.myshopify.com)
        
    Returns:
        ShopifyCredentialProvider instance
    """
    return ShopifyCredentialProvider(agent_name, shop_domain)
