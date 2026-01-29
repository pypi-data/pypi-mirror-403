"""
Users resource handler
"""

from typing import Dict, Any, Optional
from .base import BaseResource


class UsersResource(BaseResource):
    """
    Handler for user-related API endpoints.
    
    Example:
        >>> client = Client(access_token="token")
        >>> users = client.users.list(org_id="org-uuid")
        >>> user = client.users.get(org_id="org-uuid", user_id="user-uuid")
        >>> updated_user = client.users.update(org_id="org-uuid", user_id="user-uuid", first_name="John")
    """
    
    def list(
        self,
        org_id: str,
        group_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all users for an organization.
        
        Args:
            org_id: The organization UUID
            group_id: Optional group ID to filter users by group membership
            status: Optional status filter (ACTIVE, DISABLE, PENDING, SHARED)
        
        Returns:
            Dictionary containing list of users
        """
        params = {}
        
        if group_id:
            params["groupId"] = group_id
        if status:
            params["status"] = status
        
        return self.client.get(f"organizations/{org_id}/users", params=params)
    
    def get(self, org_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get a specific user by ID.
        
        Args:
            org_id: The organization UUID
            user_id: The user UUID
        
        Returns:
            User dictionary
        """
        return self.client.get(f"organizations/{org_id}/users/{user_id}")
    
    def invite(
        self,
        org_id: str,
        email: str,
        first_name: str,
        last_name: str
    ) -> Dict[str, Any]:
        """
        Invite a new user to the organization.
        
        Args:
            org_id: The organization UUID
            email: User's email address
            first_name: User's first name
            last_name: User's last name
        
        Returns:
            User operation response dictionary
        
        Example:
            >>> client.users.invite(
            ...     org_id="org-uuid",
            ...     email="user@example.com",
            ...     first_name="John",
            ...     last_name="Doe"
            ... )
        """
        return self.patch(
            org_id=org_id,
            email=email,
            operation="invite",
            first_name=first_name,
            last_name=last_name
        )
    
    def update(
        self,
        org_id: str,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a user's first and last name.
        
        Args:
            org_id: The organization UUID
            user_id: The user UUID
            first_name: User's first name
            last_name: User's last name
        
        Returns:
            Updated user dictionary
        """
        data = {}
        
        if first_name:
            data["firstName"] = first_name
        if last_name:
            data["lastName"] = last_name
        
        return self.client.put(f"organizations/{org_id}/users/{user_id}", json=data)
    
    def patch(
        self,
        org_id: str,
        email: str,
        operation: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform operations on a user (invite, disable, enable, remove, resend_email_invite, reset_password, reset_mfa).
        
        Args:
            org_id: The organization UUID
            email: User's email address
            operation: Operation to perform (invite, disable, enable, remove, resend_email_invite, reset_password, reset_mfa)
            first_name: User's first name (required for 'invite' operation)
            last_name: User's last name (required for 'invite' operation)
        
        Returns:
            Operation result dictionary
        
        Example:
            >>> # Invite a user
            >>> client.users.patch(
            ...     org_id="org-uuid",
            ...     email="user@example.com",
            ...     operation="invite",
            ...     first_name="John",
            ...     last_name="Doe"
            ... )
            >>> # Disable a user
            >>> client.users.patch(org_id="org-uuid", email="user@example.com", operation="disable")
        """
        data = {
            "operation": operation,
            "email": email
        }
        
        # For invite operation, firstName and lastName are required
        if operation == "invite":
            if not first_name or not last_name:
                raise ValueError("first_name and last_name are required for invite operation")
            data["firstName"] = first_name
            data["lastName"] = last_name
        
        return self.client.patch(f"organizations/{org_id}/users", json=data)
    
    def get_groups(self, org_id: str, user_id: str) -> Dict[str, Any]:
        """
        List all groups to which a user is assigned.
        
        Args:
            org_id: The organization UUID
            user_id: The user UUID
        
        Returns:
            Dictionary containing list of groups
        """
        return self.client.get(f"organizations/{org_id}/users/{user_id}/groups")
