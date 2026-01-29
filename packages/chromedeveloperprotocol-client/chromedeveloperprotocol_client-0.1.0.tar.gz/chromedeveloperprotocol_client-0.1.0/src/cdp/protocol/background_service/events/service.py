"""CDP BackgroundService Domain Events"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class BackgroundServiceEvents:
    """
    Events for the BackgroundService domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the BackgroundService events.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    def on_recording_state_changed(self, callback: Callable[[recordingStateChangedEvent,Optional[str]], None]=None) -> None:
        """
    Called when the recording state for the service has been updated.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: recordingStateChangedEvent, session_id: Optional[str]).
        """
        self.client.on('BackgroundService.recordingStateChanged', callback)
    def on_background_service_event_received(self, callback: Callable[[backgroundServiceEventReceivedEvent,Optional[str]], None]=None) -> None:
        """
    Called with all existing backgroundServiceEvents when enabled, and all new events afterwards if enabled and recording.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: backgroundServiceEventReceivedEvent, session_id: Optional[str]).
        """
        self.client.on('BackgroundService.backgroundServiceEventReceived', callback)