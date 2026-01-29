"""CDP Security Domain Events"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class SecurityEvents:
    """
    Events for the Security domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Security events.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    def on_visible_security_state_changed(self, callback: Callable[[visibleSecurityStateChangedEvent,Optional[str]], None]=None) -> None:
        """
    The security state of the page changed.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: visibleSecurityStateChangedEvent, session_id: Optional[str]).
        """
        self.client.on('Security.visibleSecurityStateChanged', callback)