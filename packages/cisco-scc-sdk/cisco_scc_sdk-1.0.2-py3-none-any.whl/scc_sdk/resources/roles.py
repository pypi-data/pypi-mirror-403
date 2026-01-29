"""
Roles resource handler
"""

from typing import List, Dict, Any, Optional
from .base import BaseResource


class RolesResource(BaseResource):
    """
    Handler for role-related API endpoints.
    
    Example:
        >>> client = Client(access_token="token")
        >>> roles = client.roles.list(org_id="org-uuid")
        >>> role = client.roles.get(org_id="org-uuid", role_id="role-uuid")
        >>> result = client.roles.patch(org_id="org-uuid", role_id="role-uuid", users=[...])
    """
    
    def list(
        self,
        org_id: str,
        type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all roles for an organization.
        
        Args:
            org_id: The organization UUID
            type: Optional filter by role type (CUSTOM, BUNDLED, STATIC)
        
        Returns:
            Dictionary containing list of roles
        """
        params = {}
        
        if type:
            params["type"] = type
        
        return self.client.get(f"organizations/{org_id}/roles", params=params)
    
    def get(self, org_id: str, role_id: str) -> Dict[str, Any]:
        """
        Get a specific role by ID.
        
        Args:
            org_id: The organization UUID
            role_id: The role UUID
        
        Returns:
            Role dictionary
        """
        return self.client.get(f"organizations/{org_id}/roles/{role_id}")
    
    def patch(
        self,
        org_id: str,
        role_id: str,
        users: Optional[List[Dict[str, str]]] = None,
        groups: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Update role assignments by adding or removing users and groups.
        
        Args:
            org_id: The organization UUID
            role_id: The role UUID
            users: List of user operations with 'operation' (add/remove) and 'id' (user UUID)
            groups: List of group operations with 'operation' (add/remove) and 'id' (group UUID)
        
        Returns:
            Operation results dictionary
        
        Example:
            >>> client.roles.patch(
            ...     org_id="org-uuid",
            ...     role_id="role-uuid",
            ...     users=[{"operation": "add", "id": "user-uuid"}],
            ...     groups=[{"operation": "remove", "id": "group-uuid"}]
            ... )
        """
        data = {}
        
        if users:
            data["users"] = users
        if groups:
            data["groups"] = groups
        
        return self.client.patch(f"organizations/{org_id}/roles/{role_id}", json=data)
