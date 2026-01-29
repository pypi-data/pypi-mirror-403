"""CDP Debugger Domain Events"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class DebuggerEvents:
    """
    Events for the Debugger domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Debugger events.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    def on_paused(self, callback: Callable[[pausedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when the virtual machine stopped on breakpoint or exception or any other stop criteria.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: pausedEvent, session_id: Optional[str]).
        """
        self.client.on('Debugger.paused', callback)
    def on_resumed(self, callback: Callable[[resumedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when the virtual machine resumed execution.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: resumedEvent, session_id: Optional[str]).
        """
        self.client.on('Debugger.resumed', callback)
    def on_script_failed_to_parse(self, callback: Callable[[scriptFailedToParseEvent,Optional[str]], None]=None) -> None:
        """
    Fired when virtual machine fails to parse the script.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: scriptFailedToParseEvent, session_id: Optional[str]).
        """
        self.client.on('Debugger.scriptFailedToParse', callback)
    def on_script_parsed(self, callback: Callable[[scriptParsedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when virtual machine parses script. This event is also fired for all known and uncollected scripts upon enabling debugger.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: scriptParsedEvent, session_id: Optional[str]).
        """
        self.client.on('Debugger.scriptParsed', callback)