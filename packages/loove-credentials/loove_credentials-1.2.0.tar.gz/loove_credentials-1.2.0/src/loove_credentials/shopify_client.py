"""
Shopify API Client for LOOVE AI Infrastructure.

Provides high-level methods for common Shopify operations including
content management and reporting.
"""

import logging
from typing import Optional, Dict, Any, List
import requests

from .credential.shopify_provider import get_shopify_provider

logger = logging.getLogger(__name__)


class ShopifyAPIClient:
    """
    High-level Shopify API client for content management and reporting.
    
    Handles authentication automatically and provides convenient methods
    for common operations.
    """
    
    # Shopify API version
    API_VERSION = "2024-01"
    
    def __init__(self, agent_name: str = "manus", shop_domain: str = "boops-nyc.myshopify.com"):
        """
        Initialize Shopify API client.
        
        Args:
            agent_name: Name of the AI agent (default: "manus")
            shop_domain: Shopify store domain
        """
        self.agent_name = agent_name
        self.shop_domain = shop_domain
        self.provider = get_shopify_provider(agent_name, shop_domain)
        self.base_url = f"https://{shop_domain}/admin/api/{self.API_VERSION}"
        
        logger.info(f"ShopifyAPIClient initialized for {shop_domain}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an authenticated request to the Shopify API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/products.json")
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            JSON response as dictionary
            
        Raises:
            RuntimeError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = self.provider.get_api_headers()
        
        # Merge with any additional headers
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        try:
            response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Shopify API request failed: {e}")
            raise RuntimeError(f"Shopify API error: {e}")
    
    # ===== SHOP INFORMATION =====
    
    def get_shop_info(self) -> Dict[str, Any]:
        """
        Get basic information about the shop.
        
        Returns:
            Dictionary with shop information
        """
        response = self._request('GET', '/shop.json')
        return response.get('shop', {})
    
    # ===== PRODUCTS =====
    
    def list_products(self, limit: int = 50, **params) -> List[Dict[str, Any]]:
        """
        List products in the store.
        
        Args:
            limit: Maximum number of products to return (default: 50, max: 250)
            **params: Additional query parameters (e.g., status, vendor, product_type)
            
        Returns:
            List of product dictionaries
        """
        params['limit'] = min(limit, 250)
        response = self._request('GET', '/products.json', params=params)
        return response.get('products', [])
    
    def get_product(self, product_id: int) -> Dict[str, Any]:
        """
        Get a specific product by ID.
        
        Args:
            product_id: Shopify product ID
            
        Returns:
            Product dictionary
        """
        response = self._request('GET', f'/products/{product_id}.json')
        return response.get('product', {})
    
    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a product.
        
        Args:
            product_id: Shopify product ID
            product_data: Dictionary with product fields to update
            
        Returns:
            Updated product dictionary
        """
        payload = {'product': product_data}
        response = self._request('PUT', f'/products/{product_id}.json', json=payload)
        return response.get('product', {})
    
    # ===== ORDERS =====
    
    def list_orders(self, limit: int = 50, **params) -> List[Dict[str, Any]]:
        """
        List orders in the store.
        
        Args:
            limit: Maximum number of orders to return (default: 50, max: 250)
            **params: Additional query parameters (e.g., status, created_at_min, financial_status)
            
        Returns:
            List of order dictionaries
        """
        params['limit'] = min(limit, 250)
        response = self._request('GET', '/orders.json', params=params)
        return response.get('orders', [])
    
    def get_order(self, order_id: int) -> Dict[str, Any]:
        """
        Get a specific order by ID.
        
        Args:
            order_id: Shopify order ID
            
        Returns:
            Order dictionary
        """
        response = self._request('GET', f'/orders/{order_id}.json')
        return response.get('order', {})
    
    def count_orders(self, **params) -> int:
        """
        Get count of orders matching criteria.
        
        Args:
            **params: Query parameters (e.g., status, created_at_min)
            
        Returns:
            Number of orders
        """
        response = self._request('GET', '/orders/count.json', params=params)
        return response.get('count', 0)
    
    # ===== CUSTOMERS =====
    
    def list_customers(self, limit: int = 50, **params) -> List[Dict[str, Any]]:
        """
        List customers in the store.
        
        Args:
            limit: Maximum number of customers to return (default: 50, max: 250)
            **params: Additional query parameters
            
        Returns:
            List of customer dictionaries
        """
        params['limit'] = min(limit, 250)
        response = self._request('GET', '/customers.json', params=params)
        return response.get('customers', [])
    
    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """
        Get a specific customer by ID.
        
        Args:
            customer_id: Shopify customer ID
            
        Returns:
            Customer dictionary
        """
        response = self._request('GET', f'/customers/{customer_id}.json')
        return response.get('customer', {})
    
    # ===== INVENTORY =====
    
    def get_inventory_levels(self, location_ids: Optional[List[int]] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get inventory levels across locations.
        
        Args:
            location_ids: List of location IDs to filter by (optional)
            limit: Maximum number of results (default: 50, max: 250)
            
        Returns:
            List of inventory level dictionaries
        """
        params = {'limit': min(limit, 250)}
        if location_ids:
            params['location_ids'] = ','.join(map(str, location_ids))
        
        response = self._request('GET', '/inventory_levels.json', params=params)
        return response.get('inventory_levels', [])
    
    # ===== ANALYTICS / REPORTS =====
    
    def get_order_summary(self, created_at_min: Optional[str] = None, created_at_max: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of orders for reporting.
        
        Args:
            created_at_min: Minimum creation date (ISO 8601 format)
            created_at_max: Maximum creation date (ISO 8601 format)
            
        Returns:
            Dictionary with order summary statistics
        """
        params = {}
        if created_at_min:
            params['created_at_min'] = created_at_min
        if created_at_max:
            params['created_at_max'] = created_at_max
        
        orders = self.list_orders(limit=250, **params)
        
        total_revenue = sum(float(order.get('total_price', 0)) for order in orders)
        total_orders = len(orders)
        
        return {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'average_order_value': total_revenue / total_orders if total_orders > 0 else 0,
            'orders': orders
        }
    
    # ===== PAGES (CONTENT MANAGEMENT) =====
    
    def list_pages(self, limit: int = 50, **params) -> List[Dict[str, Any]]:
        """
        List pages in the online store.
        
        Args:
            limit: Maximum number of pages to return (default: 50, max: 250)
            **params: Additional query parameters
            
        Returns:
            List of page dictionaries
        """
        params['limit'] = min(limit, 250)
        response = self._request('GET', '/pages.json', params=params)
        return response.get('pages', [])
    
    def get_page(self, page_id: int) -> Dict[str, Any]:
        """
        Get a specific page by ID.
        
        Args:
            page_id: Shopify page ID
            
        Returns:
            Page dictionary
        """
        response = self._request('GET', f'/pages/{page_id}.json')
        return response.get('page', {})
    
    def update_page(self, page_id: int, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a page.
        
        Args:
            page_id: Shopify page ID
            page_data: Dictionary with page fields to update
            
        Returns:
            Updated page dictionary
        """
        payload = {'page': page_data}
        response = self._request('PUT', f'/pages/{page_id}.json', json=payload)
        return response.get('page', {})
    
    def create_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new page.
        
        Args:
            page_data: Dictionary with page fields (title, body_html, etc.)
            
        Returns:
            Created page dictionary
        """
        payload = {'page': page_data}
        response = self._request('POST', '/pages.json', json=payload)
        return response.get('page', {})


def get_shopify_client(agent_name: str = "manus", shop_domain: str = "boops-nyc.myshopify.com") -> ShopifyAPIClient:
    """
    Factory function to get a ShopifyAPIClient instance.
    
    Args:
        agent_name: Name of the AI agent (default: "manus")
        shop_domain: Shopify store domain
        
    Returns:
        ShopifyAPIClient instance
    """
    return ShopifyAPIClient(agent_name, shop_domain)
