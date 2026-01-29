"""CDP Log Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class LogMethods:
    """
    Methods for the Log domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Log methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def clear(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Clears the log.    
        Args:
            params (None, optional): Parameters for the clear method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the clear call.
        """
        return await self.client.send(method="Log.clear", params=params,session_id=session_id)
    async def disable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Disables log domain, prevents further log entries from being reported to the client.    
        Args:
            params (None, optional): Parameters for the disable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the disable call.
        """
        return await self.client.send(method="Log.disable", params=params,session_id=session_id)
    async def enable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Enables log domain, sends the entries collected so far to the client by means of the `entryAdded` notification.    
        Args:
            params (None, optional): Parameters for the enable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the enable call.
        """
        return await self.client.send(method="Log.enable", params=params,session_id=session_id)
    async def start_violations_report(self, params: Optional[startViolationsReportParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    start violation reporting.    
        Args:
            params (startViolationsReportParameters, optional): Parameters for the startViolationsReport method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the startViolationsReport call.
        """
        return await self.client.send(method="Log.startViolationsReport", params=params,session_id=session_id)
    async def stop_violations_report(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Stop violation reporting.    
        Args:
            params (None, optional): Parameters for the stopViolationsReport method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the stopViolationsReport call.
        """
        return await self.client.send(method="Log.stopViolationsReport", params=params,session_id=session_id)