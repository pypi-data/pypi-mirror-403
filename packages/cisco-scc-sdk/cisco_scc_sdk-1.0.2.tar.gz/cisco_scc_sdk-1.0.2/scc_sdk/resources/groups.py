"""
Admin Groups resource handler
"""

from typing import List, Dict, Any, Optional
from .base import BaseResource


class GroupsResource(BaseResource):
    """
    Handler for admin group-related API endpoints.
    
    Example:
        >>> client = Client(access_token="token")
        >>> groups = client.groups.list(org_id="org-uuid")
        >>> group = client.groups.get(org_id="org-uuid", group_id="group-uuid")
        >>> new_group = client.groups.create(org_id="org-uuid", name="Team", description="Desc")
    """
    
    def list(self, org_id: str) -> Dict[str, Any]:
        """
        List all admin groups for an organization.
        
        Args:
            org_id: The organization UUID
        
        Returns:
            Dictionary containing list of groups
        """
        return self.client.get(f"organizations/{org_id}/adminGroups")
    
    def get(self, org_id: str, group_id: str) -> Dict[str, Any]:
        """
        Get a specific admin group by ID.
        
        Args:
            org_id: The organization UUID
            group_id: The group UUID
        
        Returns:
            Group dictionary
        """
        return self.client.get(f"organizations/{org_id}/adminGroups/{group_id}")
    
    def create(
        self,
        org_id: str,
        name: str,
        description: Optional[str] = None,
        applies_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new admin group.
        
        Args:
            org_id: The organization UUID
            name: Group name
            description: Group description
            applies_to: Specifies to whom the group applies (all, manager, selected_managed)
        
        Returns:
            Created group dictionary
        """
        data = {"name": name}
        
        if description:
            data["description"] = description
        if applies_to:
            data["appliesTo"] = applies_to
        
        return self.client.post(f"organizations/{org_id}/adminGroups", json=data)
    
    def update(
        self,
        org_id: str,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing admin group.
        
        Args:
            org_id: The organization UUID
            group_id: The group UUID
            name: New group name
            description: New group description
        
        Returns:
            Updated group dictionary
        """
        data = {}
        
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        
        return self.client.put(f"organizations/{org_id}/adminGroups/{group_id}", json=data)
    
    def delete(self, org_id: str, group_id: str) -> bool:
        """
        Delete an admin group.
        
        Args:
            org_id: The organization UUID
            group_id: The group UUID
        
        Returns:
            True if deletion was successful
        """
        self.client.delete(f"organizations/{org_id}/adminGroups/{group_id}")
        return True
    
    def patch(
        self,
        org_id: str,
        group_id: str,
        users: Optional[List[Dict[str, str]]] = None,
        managed_orgs: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Patch admin group membership (add/remove users and managed organizations).
        
        Args:
            org_id: The organization UUID
            group_id: The group UUID
            users: List of user operations with 'operation' (add/remove) and 'id' (email)
            managed_orgs: List of managed org operations with 'operation' (add/remove) and 'id'
        
        Returns:
            Patch operation results
        
        Example:
            >>> client.groups.patch(
            ...     org_id="org-uuid",
            ...     group_id="group-uuid",
            ...     users=[{"operation": "add", "id": "user@example.com"}],
            ...     managed_orgs=[{"operation": "remove", "id": "managed-org-id"}]
            ... )
        """
        data = {}
        
        if users:
            data["users"] = users
        if managed_orgs:
            data["managedOrg"] = managed_orgs
        
        return self.client.patch(f"organizations/{org_id}/adminGroups/{group_id}", json=data)
    
    def get_managed_organizations(self, org_id: str, group_id: str) -> Dict[str, Any]:
        """
        Get managed organizations for a shared admin group.
        
        Args:
            org_id: The organization UUID
            group_id: The group UUID
        
        Returns:
            Dictionary containing list of managed organizations
        """
        return self.client.get(f"organizations/{org_id}/adminGroups/{group_id}/managedOrgs")
    
    def get_assigned_roles(self, org_id: str, group_id: str) -> Dict[str, Any]:
        """
        Get assigned roles for a specific admin group.
        
        Args:
            org_id: The organization UUID
            group_id: The group UUID
        
        Returns:
            Dictionary containing list of roles
        """
        return self.client.get(f"organizations/{org_id}/adminGroups/{group_id}/roles")
    
    def get_users(self, org_id: str, group_id: str) -> Dict[str, Any]:
        """
        Get all users that belong to a specific admin group.
        
        Args:
            org_id: The organization UUID
            group_id: The group UUID
        
        Returns:
            Dictionary containing list of users
        """
        return self.client.get(f"organizations/{org_id}/adminGroups/{group_id}/users")
