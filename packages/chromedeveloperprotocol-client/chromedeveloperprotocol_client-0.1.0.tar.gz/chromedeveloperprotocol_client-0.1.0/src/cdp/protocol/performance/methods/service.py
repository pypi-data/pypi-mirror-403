"""CDP Performance Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class PerformanceMethods:
    """
    Methods for the Performance domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Performance methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def disable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Disable collecting and reporting metrics.    
        Args:
            params (None, optional): Parameters for the disable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the disable call.
        """
        return await self.client.send(method="Performance.disable", params=params,session_id=session_id)
    async def enable(self, params: Optional[enableParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Enable collecting and reporting metrics.    
        Args:
            params (enableParameters, optional): Parameters for the enable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the enable call.
        """
        return await self.client.send(method="Performance.enable", params=params,session_id=session_id)
    async def get_metrics(self, params: None=None,session_id: Optional[str] = None) -> getMetricsReturns:
        """
    Retrieve current values of run-time metrics.    
        Args:
            params (None, optional): Parameters for the getMetrics method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    getMetricsReturns: The result of the getMetrics call.
        """
        return await self.client.send(method="Performance.getMetrics", params=params,session_id=session_id)