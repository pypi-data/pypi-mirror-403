"""CDP DOM Domain Events"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class DOMEvents:
    """
    Events for the DOM domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the DOM events.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    def on_attribute_modified(self, callback: Callable[[attributeModifiedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when `Element`'s attribute is modified.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: attributeModifiedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.attributeModified', callback)
    def on_adopted_style_sheets_modified(self, callback: Callable[[adoptedStyleSheetsModifiedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when `Element`'s adoptedStyleSheets are modified.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: adoptedStyleSheetsModifiedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.adoptedStyleSheetsModified', callback)
    def on_attribute_removed(self, callback: Callable[[attributeRemovedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when `Element`'s attribute is removed.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: attributeRemovedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.attributeRemoved', callback)
    def on_character_data_modified(self, callback: Callable[[characterDataModifiedEvent,Optional[str]], None]=None) -> None:
        """
    Mirrors `DOMCharacterDataModified` event.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: characterDataModifiedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.characterDataModified', callback)
    def on_child_node_count_updated(self, callback: Callable[[childNodeCountUpdatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when `Container`'s child node count has changed.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: childNodeCountUpdatedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.childNodeCountUpdated', callback)
    def on_child_node_inserted(self, callback: Callable[[childNodeInsertedEvent,Optional[str]], None]=None) -> None:
        """
    Mirrors `DOMNodeInserted` event.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: childNodeInsertedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.childNodeInserted', callback)
    def on_child_node_removed(self, callback: Callable[[childNodeRemovedEvent,Optional[str]], None]=None) -> None:
        """
    Mirrors `DOMNodeRemoved` event.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: childNodeRemovedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.childNodeRemoved', callback)
    def on_distributed_nodes_updated(self, callback: Callable[[distributedNodesUpdatedEvent,Optional[str]], None]=None) -> None:
        """
    Called when distribution is changed.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: distributedNodesUpdatedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.distributedNodesUpdated', callback)
    def on_document_updated(self, callback: Callable[[documentUpdatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when `Document` has been totally updated. Node ids are no longer valid.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: documentUpdatedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.documentUpdated', callback)
    def on_inline_style_invalidated(self, callback: Callable[[inlineStyleInvalidatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when `Element`'s inline style is modified via a CSS property modification.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: inlineStyleInvalidatedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.inlineStyleInvalidated', callback)
    def on_pseudo_element_added(self, callback: Callable[[pseudoElementAddedEvent,Optional[str]], None]=None) -> None:
        """
    Called when a pseudo element is added to an element.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: pseudoElementAddedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.pseudoElementAdded', callback)
    def on_top_layer_elements_updated(self, callback: Callable[[topLayerElementsUpdatedEvent,Optional[str]], None]=None) -> None:
        """
    Called when top layer elements are changed.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: topLayerElementsUpdatedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.topLayerElementsUpdated', callback)
    def on_scrollable_flag_updated(self, callback: Callable[[scrollableFlagUpdatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when a node's scrollability state changes.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: scrollableFlagUpdatedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.scrollableFlagUpdated', callback)
    def on_affected_by_starting_styles_flag_updated(self, callback: Callable[[affectedByStartingStylesFlagUpdatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when a node's starting styles changes.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: affectedByStartingStylesFlagUpdatedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.affectedByStartingStylesFlagUpdated', callback)
    def on_pseudo_element_removed(self, callback: Callable[[pseudoElementRemovedEvent,Optional[str]], None]=None) -> None:
        """
    Called when a pseudo element is removed from an element.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: pseudoElementRemovedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.pseudoElementRemoved', callback)
    def on_set_child_nodes(self, callback: Callable[[setChildNodesEvent,Optional[str]], None]=None) -> None:
        """
    Fired when backend wants to provide client with the missing DOM structure. This happens upon most of the calls requesting node ids.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: setChildNodesEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.setChildNodes', callback)
    def on_shadow_root_popped(self, callback: Callable[[shadowRootPoppedEvent,Optional[str]], None]=None) -> None:
        """
    Called when shadow root is popped from the element.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: shadowRootPoppedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.shadowRootPopped', callback)
    def on_shadow_root_pushed(self, callback: Callable[[shadowRootPushedEvent,Optional[str]], None]=None) -> None:
        """
    Called when shadow root is pushed into the element.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: shadowRootPushedEvent, session_id: Optional[str]).
        """
        self.client.on('DOM.shadowRootPushed', callback)