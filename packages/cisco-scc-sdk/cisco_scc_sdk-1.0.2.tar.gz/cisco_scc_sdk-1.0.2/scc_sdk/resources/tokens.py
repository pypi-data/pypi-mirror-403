"""
Token refresh resource handler
"""

from typing import Dict, Any
from .base import BaseResource


class TokensResource(BaseResource):
    """
    Handler for token refresh API endpoints.
    
    Example:
        >>> client = Client(access_token="refresh_token")
        >>> new_tokens = client.tokens.refresh(
        ...     org_id="org-uuid",
        ...     api_key_id="key-uuid",
        ...     refresh_token="refresh_token_value"
        ... )
    """
    
    def refresh(
        self,
        org_id: str,
        api_key_id: str,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh access token using a refresh token.
        
        Args:
            org_id: The organization UUID
            api_key_id: The API key UUID
            refresh_token: The refresh token value
        
        Returns:
            Dictionary containing new access token and refresh token
        """
        # Update authorization header with refresh token
        headers = {
            "Authorization": f"Bearer {refresh_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Form data
        data = {"grant_type": "refresh_token"}
        
        return self.client.post(
            f"organizations/{org_id}/apiKeys/{api_key_id}/token",
            data=data,
            headers=headers
        )
