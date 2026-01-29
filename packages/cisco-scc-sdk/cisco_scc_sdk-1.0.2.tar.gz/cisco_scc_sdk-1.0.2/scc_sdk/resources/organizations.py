"""
Organizations resource handler
"""

from typing import List, Dict, Any, Optional
from .base import BaseResource


class OrganizationsResource(BaseResource):
    """
    Handler for organization-related API endpoints.
    
    Example:
        >>> client = Client(access_token="token")
        >>> orgs = client.organizations.list()
        >>> org = client.organizations.get(org_id="550e8400-e29b-41d4-a716-446655440000")
        >>> updated_org = client.organizations.update(org_id="...", name="New Name")
    """
    
    def list(
        self,
        name: Optional[str] = None,
        type: Optional[str] = None,
        region_code: Optional[str] = None,
        country_code: Optional[str] = None,
        manager_org_id: Optional[str] = None,
        max: int = 100,
        cursor: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List organizations with optional filtering and pagination.
        
        Args:
            name: Filter by organization name (partial match)
            type: Filter by organization type (STANDALONE, MANAGER, MANAGED)
            region_code: Filter by region code (NAM, EMEA, APJC, GLOBAL)
            country_code: Filter by country code
            manager_org_id: Filter by manager organization ID
            max: Maximum number of items to return (default: 100, max: 500)
            cursor: Cursor for pagination
            sort_by: Field to sort by (e.g., "name")
            order: Sort order (ASC or DESC)
        
        Returns:
            Dictionary containing list of organizations and pagination info
        """
        params = {}
        
        # Query filters
        if name:
            params["name"] = name
        if type:
            params["type"] = type
        if region_code:
            params["regionCode"] = region_code
        if country_code:
            params["countryCode"] = country_code
        if manager_org_id:
            params["managerOrgId"] = manager_org_id
        
        # Pagination
        params["max"] = max
        if cursor:
            params["cursor"] = cursor
        
        # Sorting
        if sort_by:
            params["sortBy"] = sort_by
        if order:
            params["order"] = order
        
        return self.client.get("organizations", params=params)
    
    def get(self, org_id: str) -> Dict[str, Any]:
        """
        Get a specific organization by ID.
        
        Args:
            org_id: The organization UUID
        
        Returns:
            Organization dictionary
        """
        return self.client.get(f"organizations/{org_id}")
    
    def create(
        self,
        name: str,
        region_code: str,
        type: str = "STANDALONE"
    ) -> Dict[str, Any]:
        """
        Create a new organization.
        
        Args:
            name: Organization name
            region_code: Region code (NAM, EMEA, APJC)
            type: Organization type (STANDALONE, MANAGER, MANAGED)
        
        Returns:
            Created organization dictionary
        """
        data = {
            "name": name,
            "regionCode": region_code,
            "type": type
        }
        
        return self.client.post("organizations", json=data)
    
    def update(self, org_id: str, name: str) -> Dict[str, Any]:
        """
        Update an organization's name.
        
        Args:
            org_id: The organization UUID
            name: New organization name
        
        Returns:
            Updated organization dictionary
        """
        data = {"name": name}
        return self.client.put(f"organizations/{org_id}", json=data)
