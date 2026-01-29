"""
Base resource class
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client


class BaseResource:
    """
    Base class for all resource handlers.
    
    Args:
        client: The API client instance
    """
    
    def __init__(self, client: "Client"):
        self.client = client
