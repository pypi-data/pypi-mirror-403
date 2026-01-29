"""CDP Inspector Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class InspectorMethods:
    """
    Methods for the Inspector domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Inspector methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def disable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Disables inspector domain notifications.    
        Args:
            params (None, optional): Parameters for the disable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the disable call.
        """
        return await self.client.send(method="Inspector.disable", params=params,session_id=session_id)
    async def enable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Enables inspector domain notifications.    
        Args:
            params (None, optional): Parameters for the enable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the enable call.
        """
        return await self.client.send(method="Inspector.enable", params=params,session_id=session_id)