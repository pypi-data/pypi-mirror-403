"""
Main Client class for Cisco Security Cloud Control SDK
"""

import requests
from typing import Optional
from .resources.organizations import OrganizationsResource
from .resources.subscriptions import SubscriptionsResource
from .resources.groups import GroupsResource
from .resources.users import UsersResource
from .resources.roles import RolesResource
from .resources.tokens import TokensResource
from .exceptions import SCCError, AuthenticationError


class Client:
    """
    Main client for interacting with Cisco Security Cloud Control API.
    
    Args:
        access_token (str): The bearer token for authentication
        base_path (str, optional): API base path version. Defaults to "v1".
        base_url (str, optional): Override the default base URL. Defaults to "http://localhost:8080".
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
    
    Example:
        >>> client = Client(access_token="your_bearer_token")
        >>> orgs = client.organizations.list()
        >>> subscriptions = client.subscriptions.list(org_id="org-uuid")
    """
    
    def __init__(
        self,
        access_token: str,
        base_path: str = "v1",
        base_url: str = "https://api.security.cisco.com",
        timeout: int = 30
    ):
        """
        Initialize the SCC API client.
        
        Args:
            access_token: The bearer token for authentication
            base_path: API base path version (default: "v1")
            base_url: Base server URL (default: "https://api.security.cisco.com")
            timeout: Request timeout in seconds (default: 30)
        """
        if not access_token:
            raise ValueError("access_token is required")
        
        self.access_token = access_token
        self.base_url = f"{base_url.rstrip('/')}/{base_path}"
        self.timeout = timeout
        self._session = self._create_session()
        
        # Initialize resource handlers
        self.organizations = OrganizationsResource(self)
        self.subscriptions = SubscriptionsResource(self)
        self.groups = GroupsResource(self)
        self.users = UsersResource(self)
        self.roles = RolesResource(self)
        self.tokens = TokensResource(self)
    
    def _create_session(self) -> requests.Session:
        """Create and configure a requests session."""
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        return session
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> dict:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (will be appended to base_url)
            params: Query parameters
            json: JSON body data
            data: Form data
            headers: Additional headers
        
        Returns:
            Response data as dictionary
        
        Raises:
            AuthenticationError: If authentication fails (401)
            SCCError: For other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        request_headers = self._session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                headers=request_headers,
                timeout=self.timeout,
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed. Please check your access token.")
            
            # Handle 204 No Content
            if response.status_code == 204:
                return {}
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Return JSON response if available
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', str(e))
                except Exception:
                    error_msg = str(e)
                
                raise SCCError(f"API request failed ({status_code}): {error_msg}") from e
            raise SCCError(f"API request failed: {str(e)}") from e
    
    def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params)
    
    def post(
        self,
        endpoint: str,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None
    ) -> dict:
        """Make a POST request."""
        return self._request("POST", endpoint, json=json, data=data, headers=headers)
    
    def put(self, endpoint: str, json: Optional[dict] = None) -> dict:
        """Make a PUT request."""
        return self._request("PUT", endpoint, json=json)
    
    def patch(self, endpoint: str, json: Optional[dict] = None) -> dict:
        """Make a PATCH request."""
        return self._request("PATCH", endpoint, json=json)
    
    def delete(self, endpoint: str) -> dict:
        """Make a DELETE request."""
        return self._request("DELETE", endpoint)
    
    def close(self):
        """Close the session."""
        self._session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
