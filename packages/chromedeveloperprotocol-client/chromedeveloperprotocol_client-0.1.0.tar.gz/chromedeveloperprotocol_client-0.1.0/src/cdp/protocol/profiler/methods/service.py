"""CDP Profiler Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class ProfilerMethods:
    """
    Methods for the Profiler domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Profiler methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def disable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    No description available for disable.    
        Args:
            params (None, optional): Parameters for the disable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the disable call.
        """
        return await self.client.send(method="Profiler.disable", params=params,session_id=session_id)
    async def enable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    No description available for enable.    
        Args:
            params (None, optional): Parameters for the enable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the enable call.
        """
        return await self.client.send(method="Profiler.enable", params=params,session_id=session_id)
    async def get_best_effort_coverage(self, params: None=None,session_id: Optional[str] = None) -> getBestEffortCoverageReturns:
        """
    Collect coverage data for the current isolate. The coverage data may be incomplete due to garbage collection.    
        Args:
            params (None, optional): Parameters for the getBestEffortCoverage method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    getBestEffortCoverageReturns: The result of the getBestEffortCoverage call.
        """
        return await self.client.send(method="Profiler.getBestEffortCoverage", params=params,session_id=session_id)
    async def set_sampling_interval(self, params: Optional[setSamplingIntervalParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Changes CPU profiler sampling interval. Must be called before CPU profiles recording started.    
        Args:
            params (setSamplingIntervalParameters, optional): Parameters for the setSamplingInterval method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the setSamplingInterval call.
        """
        return await self.client.send(method="Profiler.setSamplingInterval", params=params,session_id=session_id)
    async def start(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    No description available for start.    
        Args:
            params (None, optional): Parameters for the start method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the start call.
        """
        return await self.client.send(method="Profiler.start", params=params,session_id=session_id)
    async def start_precise_coverage(self, params: Optional[startPreciseCoverageParameters]=None,session_id: Optional[str] = None) -> startPreciseCoverageReturns:
        """
    Enable precise code coverage. Coverage data for JavaScript executed before enabling precise code coverage may be incomplete. Enabling prevents running optimized code and resets execution counters.    
        Args:
            params (startPreciseCoverageParameters, optional): Parameters for the startPreciseCoverage method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    startPreciseCoverageReturns: The result of the startPreciseCoverage call.
        """
        return await self.client.send(method="Profiler.startPreciseCoverage", params=params,session_id=session_id)
    async def stop(self, params: None=None,session_id: Optional[str] = None) -> stopReturns:
        """
    No description available for stop.    
        Args:
            params (None, optional): Parameters for the stop method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    stopReturns: The result of the stop call.
        """
        return await self.client.send(method="Profiler.stop", params=params,session_id=session_id)
    async def stop_precise_coverage(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Disable precise code coverage. Disabling releases unnecessary execution count records and allows executing optimized code.    
        Args:
            params (None, optional): Parameters for the stopPreciseCoverage method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the stopPreciseCoverage call.
        """
        return await self.client.send(method="Profiler.stopPreciseCoverage", params=params,session_id=session_id)
    async def take_precise_coverage(self, params: None=None,session_id: Optional[str] = None) -> takePreciseCoverageReturns:
        """
    Collect coverage data for the current isolate, and resets execution counters. Precise code coverage needs to have started.    
        Args:
            params (None, optional): Parameters for the takePreciseCoverage method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    takePreciseCoverageReturns: The result of the takePreciseCoverage call.
        """
        return await self.client.send(method="Profiler.takePreciseCoverage", params=params,session_id=session_id)