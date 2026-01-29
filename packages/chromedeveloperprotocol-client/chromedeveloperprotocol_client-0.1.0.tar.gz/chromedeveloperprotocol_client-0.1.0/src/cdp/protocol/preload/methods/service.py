"""CDP Preload Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class PreloadMethods:
    """
    Methods for the Preload domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Preload methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def enable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    No description available for enable.    
        Args:
            params (None, optional): Parameters for the enable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the enable call.
        """
        return await self.client.send(method="Preload.enable", params=params,session_id=session_id)
    async def disable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    No description available for disable.    
        Args:
            params (None, optional): Parameters for the disable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the disable call.
        """
        return await self.client.send(method="Preload.disable", params=params,session_id=session_id)