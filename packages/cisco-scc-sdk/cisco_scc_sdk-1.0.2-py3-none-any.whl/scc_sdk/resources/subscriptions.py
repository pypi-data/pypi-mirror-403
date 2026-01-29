"""
Subscriptions resource handler
"""

from typing import List, Dict, Any, Optional
from .base import BaseResource


class SubscriptionsResource(BaseResource):
    """
    Handler for subscription-related API endpoints.
    
    Example:
        >>> client = Client(access_token="token")
        >>> subs = client.subscriptions.list(org_id="org-uuid")
        >>> sub = client.subscriptions.get(org_id="org-uuid", subscription_id="sub-uuid")
        >>> new_sub = client.subscriptions.create(org_id="org-uuid", claim_code="XXXX-XXXX")
    """
    
    def list(
        self,
        org_id: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all subscriptions for an organization.
        
        Args:
            org_id: The organization UUID
            name: Optional subscription name filter
        
        Returns:
            Dictionary containing list of subscriptions
        """
        params = {}
        if name:
            params["name"] = name
        
        return self.client.get(f"organizations/{org_id}/subscriptions", params=params)
    
    def get(self, org_id: str, subscription_id: str) -> Dict[str, Any]:
        """
        Get a specific subscription by ID.
        
        Args:
            org_id: The organization UUID
            subscription_id: The subscription UUID
        
        Returns:
            Subscription dictionary
        """
        return self.client.get(f"organizations/{org_id}/subscriptions/{subscription_id}")
    
    def create(
        self,
        org_id: str,
        claim_code: str,
        type: str = "STANDALONE",
        products: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a new subscription using a claim code.
        
        Args:
            org_id: The organization UUID
            claim_code: Claim code for subscription creation
            type: Organization type (STANDALONE, MANAGER, MANAGED)
            products: Optional list of products to provision with configuration
        
        Returns:
            Created subscription dictionary
        """
        data = {
            "claimCode": claim_code,
            "type": type
        }
        
        if products:
            data["products"] = products
        
        return self.client.post(f"organizations/{org_id}/subscriptions", json=data)
    
    def update(
        self,
        org_id: str,
        subscription_id: str,
        product_id: str,
        status: bool,
        source_instance_id: Optional[str] = None,
        region_code: Optional[str] = None,
        initial_admin: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a subscription (activate/deactivate product).
        
        Args:
            org_id: The organization UUID
            subscription_id: The subscription UUID
            product_id: The product UUID
            status: True to activate, False to deactivate
            source_instance_id: Source instance ID for using existing tenant
            region_code: Product region code (NAM, EMEA, APAC, US, GLOBAL)
            initial_admin: Initial admin email for new tenant provisioning
        
        Returns:
            Updated subscription dictionary
        """
        data = {
            "productId": product_id,
            "status": status
        }
        
        if source_instance_id:
            data["sourceInstanceId"] = source_instance_id
        if region_code:
            data["regionCode"] = region_code
        if initial_admin:
            data["initialAdmin"] = initial_admin
        
        return self.client.put(
            f"organizations/{org_id}/subscriptions/{subscription_id}",
            json=data
        )
    
    def patch(
        self,
        org_id: str,
        subscription_id: str,
        entitlements: List[Dict[str, Any]],
        use_existing_tenants: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Patch a subscription (update entitlement quantities for managed orgs).
        
        Args:
            org_id: The managed organization UUID
            subscription_id: The subscription UUID
            entitlements: List of entitlements with id and quantity
            use_existing_tenants: Optional list of existing tenant UUIDs
        
        Returns:
            Updated subscription dictionary
        
        Example:
            >>> client.subscriptions.patch(
            ...     org_id="org-uuid",
            ...     subscription_id="sub-uuid",
            ...     entitlements=[{"id": "E3S-AIDEF-ADV", "quantity": 10}],
            ...     use_existing_tenants=["8a9f43fa-f8f5-4aac-8d0b-380cf6656255"]
            ... )
        """
        data = {"entitlements": entitlements}
        
        if use_existing_tenants:
            data["useExistingTenants"] = use_existing_tenants
        
        return self.client.patch(
            f"organizations/{org_id}/subscriptions/{subscription_id}",
            json=data
        )
    
    def read_claim_code(self, org_id: str, claim_code: str) -> Dict[str, Any]:
        """
        Read and validate claim code details.
        
        Args:
            org_id: The organization UUID
            claim_code: Claim code to validate
        
        Returns:
            Claim code information dictionary
        """
        data = {"claimCode": claim_code}
        return self.client.post(
            f"organizations/{org_id}/subscriptions/claimInfo",
            json=data
        )
