"""CDP Emulation Domain Events"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class EmulationEvents:
    """
    Events for the Emulation domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Emulation events.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    def on_virtual_time_budget_expired(self, callback: Callable[[virtualTimeBudgetExpiredEvent,Optional[str]], None]=None) -> None:
        """
    Notification sent after the virtual time budget for the current VirtualTimePolicy has run out.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: virtualTimeBudgetExpiredEvent, session_id: Optional[str]).
        """
        self.client.on('Emulation.virtualTimeBudgetExpired', callback)