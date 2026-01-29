"""CDP Tethering Domain Events"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class TetheringEvents:
    """
    Events for the Tethering domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Tethering events.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    def on_accepted(self, callback: Callable[[acceptedEvent,Optional[str]], None]=None) -> None:
        """
    Informs that port was successfully bound and got a specified connection id.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: acceptedEvent, session_id: Optional[str]).
        """
        self.client.on('Tethering.accepted', callback)