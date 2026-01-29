"""CDP Memory Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class MemoryMethods:
    """
    Methods for the Memory domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Memory methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def get_dom_counters(self, params: None=None,session_id: Optional[str] = None) -> getDOMCountersReturns:
        """
    Retruns current DOM object counters.    
        Args:
            params (None, optional): Parameters for the getDOMCounters method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    getDOMCountersReturns: The result of the getDOMCounters call.
        """
        return await self.client.send(method="Memory.getDOMCounters", params=params,session_id=session_id)
    async def get_dom_counters_for_leak_detection(self, params: None=None,session_id: Optional[str] = None) -> getDOMCountersForLeakDetectionReturns:
        """
    Retruns DOM object counters after preparing renderer for leak detection.    
        Args:
            params (None, optional): Parameters for the getDOMCountersForLeakDetection method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    getDOMCountersForLeakDetectionReturns: The result of the getDOMCountersForLeakDetection call.
        """
        return await self.client.send(method="Memory.getDOMCountersForLeakDetection", params=params,session_id=session_id)
    async def prepare_for_leak_detection(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Prepares for leak detection by terminating workers, stopping spellcheckers, dropping non-essential internal caches, running garbage collections, etc.    
        Args:
            params (None, optional): Parameters for the prepareForLeakDetection method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the prepareForLeakDetection call.
        """
        return await self.client.send(method="Memory.prepareForLeakDetection", params=params,session_id=session_id)
    async def forcibly_purge_java_script_memory(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Simulate OomIntervention by purging V8 memory.    
        Args:
            params (None, optional): Parameters for the forciblyPurgeJavaScriptMemory method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the forciblyPurgeJavaScriptMemory call.
        """
        return await self.client.send(method="Memory.forciblyPurgeJavaScriptMemory", params=params,session_id=session_id)
    async def set_pressure_notifications_suppressed(self, params: Optional[setPressureNotificationsSuppressedParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Enable/disable suppressing memory pressure notifications in all processes.    
        Args:
            params (setPressureNotificationsSuppressedParameters, optional): Parameters for the setPressureNotificationsSuppressed method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the setPressureNotificationsSuppressed call.
        """
        return await self.client.send(method="Memory.setPressureNotificationsSuppressed", params=params,session_id=session_id)
    async def simulate_pressure_notification(self, params: Optional[simulatePressureNotificationParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Simulate a memory pressure notification in all processes.    
        Args:
            params (simulatePressureNotificationParameters, optional): Parameters for the simulatePressureNotification method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the simulatePressureNotification call.
        """
        return await self.client.send(method="Memory.simulatePressureNotification", params=params,session_id=session_id)
    async def start_sampling(self, params: Optional[startSamplingParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Start collecting native memory profile.    
        Args:
            params (startSamplingParameters, optional): Parameters for the startSampling method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the startSampling call.
        """
        return await self.client.send(method="Memory.startSampling", params=params,session_id=session_id)
    async def stop_sampling(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Stop collecting native memory profile.    
        Args:
            params (None, optional): Parameters for the stopSampling method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the stopSampling call.
        """
        return await self.client.send(method="Memory.stopSampling", params=params,session_id=session_id)
    async def get_all_time_sampling_profile(self, params: None=None,session_id: Optional[str] = None) -> getAllTimeSamplingProfileReturns:
        """
    Retrieve native memory allocations profile collected since renderer process startup.    
        Args:
            params (None, optional): Parameters for the getAllTimeSamplingProfile method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    getAllTimeSamplingProfileReturns: The result of the getAllTimeSamplingProfile call.
        """
        return await self.client.send(method="Memory.getAllTimeSamplingProfile", params=params,session_id=session_id)
    async def get_browser_sampling_profile(self, params: None=None,session_id: Optional[str] = None) -> getBrowserSamplingProfileReturns:
        """
    Retrieve native memory allocations profile collected since browser process startup.    
        Args:
            params (None, optional): Parameters for the getBrowserSamplingProfile method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    getBrowserSamplingProfileReturns: The result of the getBrowserSamplingProfile call.
        """
        return await self.client.send(method="Memory.getBrowserSamplingProfile", params=params,session_id=session_id)
    async def get_sampling_profile(self, params: None=None,session_id: Optional[str] = None) -> getSamplingProfileReturns:
        """
    Retrieve native memory allocations profile collected since last `startSampling` call.    
        Args:
            params (None, optional): Parameters for the getSamplingProfile method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    getSamplingProfileReturns: The result of the getSamplingProfile call.
        """
        return await self.client.send(method="Memory.getSamplingProfile", params=params,session_id=session_id)