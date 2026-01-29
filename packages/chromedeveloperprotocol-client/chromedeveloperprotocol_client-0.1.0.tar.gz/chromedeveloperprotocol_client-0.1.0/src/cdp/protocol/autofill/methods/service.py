"""CDP Autofill Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class AutofillMethods:
    """
    Methods for the Autofill domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Autofill methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def trigger(self, params: Optional[triggerParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Trigger autofill on a form identified by the fieldId. If the field and related form cannot be autofilled, returns an error.    
        Args:
            params (triggerParameters, optional): Parameters for the trigger method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the trigger call.
        """
        return await self.client.send(method="Autofill.trigger", params=params,session_id=session_id)
    async def set_addresses(self, params: Optional[setAddressesParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Set addresses so that developers can verify their forms implementation.    
        Args:
            params (setAddressesParameters, optional): Parameters for the setAddresses method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the setAddresses call.
        """
        return await self.client.send(method="Autofill.setAddresses", params=params,session_id=session_id)
    async def disable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Disables autofill domain notifications.    
        Args:
            params (None, optional): Parameters for the disable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the disable call.
        """
        return await self.client.send(method="Autofill.disable", params=params,session_id=session_id)
    async def enable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Enables autofill domain notifications.    
        Args:
            params (None, optional): Parameters for the enable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the enable call.
        """
        return await self.client.send(method="Autofill.enable", params=params,session_id=session_id)