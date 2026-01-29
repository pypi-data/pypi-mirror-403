"""CDP Input Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class InputMethods:
    """
    Methods for the Input domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Input methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def dispatch_drag_event(self, params: Optional[dispatchDragEventParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Dispatches a drag event into the page.    
        Args:
            params (dispatchDragEventParameters, optional): Parameters for the dispatchDragEvent method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the dispatchDragEvent call.
        """
        return await self.client.send(method="Input.dispatchDragEvent", params=params,session_id=session_id)
    async def dispatch_key_event(self, params: Optional[dispatchKeyEventParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Dispatches a key event to the page.    
        Args:
            params (dispatchKeyEventParameters, optional): Parameters for the dispatchKeyEvent method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the dispatchKeyEvent call.
        """
        return await self.client.send(method="Input.dispatchKeyEvent", params=params,session_id=session_id)
    async def insert_text(self, params: Optional[insertTextParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    This method emulates inserting text that doesn't come from a key press, for example an emoji keyboard or an IME.    
        Args:
            params (insertTextParameters, optional): Parameters for the insertText method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the insertText call.
        """
        return await self.client.send(method="Input.insertText", params=params,session_id=session_id)
    async def ime_set_composition(self, params: Optional[imeSetCompositionParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    This method sets the current candidate text for IME. Use imeCommitComposition to commit the final text. Use imeSetComposition with empty string as text to cancel composition.    
        Args:
            params (imeSetCompositionParameters, optional): Parameters for the imeSetComposition method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the imeSetComposition call.
        """
        return await self.client.send(method="Input.imeSetComposition", params=params,session_id=session_id)
    async def dispatch_mouse_event(self, params: Optional[dispatchMouseEventParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Dispatches a mouse event to the page.    
        Args:
            params (dispatchMouseEventParameters, optional): Parameters for the dispatchMouseEvent method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the dispatchMouseEvent call.
        """
        return await self.client.send(method="Input.dispatchMouseEvent", params=params,session_id=session_id)
    async def dispatch_touch_event(self, params: Optional[dispatchTouchEventParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Dispatches a touch event to the page.    
        Args:
            params (dispatchTouchEventParameters, optional): Parameters for the dispatchTouchEvent method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the dispatchTouchEvent call.
        """
        return await self.client.send(method="Input.dispatchTouchEvent", params=params,session_id=session_id)
    async def cancel_dragging(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Cancels any active dragging in the page.    
        Args:
            params (None, optional): Parameters for the cancelDragging method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the cancelDragging call.
        """
        return await self.client.send(method="Input.cancelDragging", params=params,session_id=session_id)
    async def emulate_touch_from_mouse_event(self, params: Optional[emulateTouchFromMouseEventParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Emulates touch event from the mouse event parameters.    
        Args:
            params (emulateTouchFromMouseEventParameters, optional): Parameters for the emulateTouchFromMouseEvent method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the emulateTouchFromMouseEvent call.
        """
        return await self.client.send(method="Input.emulateTouchFromMouseEvent", params=params,session_id=session_id)
    async def set_ignore_input_events(self, params: Optional[setIgnoreInputEventsParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Ignores input events (useful while auditing page).    
        Args:
            params (setIgnoreInputEventsParameters, optional): Parameters for the setIgnoreInputEvents method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the setIgnoreInputEvents call.
        """
        return await self.client.send(method="Input.setIgnoreInputEvents", params=params,session_id=session_id)
    async def set_intercept_drags(self, params: Optional[setInterceptDragsParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Prevents default drag and drop behavior and instead emits `Input.dragIntercepted` events. Drag and drop behavior can be directly controlled via `Input.dispatchDragEvent`.    
        Args:
            params (setInterceptDragsParameters, optional): Parameters for the setInterceptDrags method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the setInterceptDrags call.
        """
        return await self.client.send(method="Input.setInterceptDrags", params=params,session_id=session_id)
    async def synthesize_pinch_gesture(self, params: Optional[synthesizePinchGestureParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Synthesizes a pinch gesture over a time period by issuing appropriate touch events.    
        Args:
            params (synthesizePinchGestureParameters, optional): Parameters for the synthesizePinchGesture method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the synthesizePinchGesture call.
        """
        return await self.client.send(method="Input.synthesizePinchGesture", params=params,session_id=session_id)
    async def synthesize_scroll_gesture(self, params: Optional[synthesizeScrollGestureParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Synthesizes a scroll gesture over a time period by issuing appropriate touch events.    
        Args:
            params (synthesizeScrollGestureParameters, optional): Parameters for the synthesizeScrollGesture method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the synthesizeScrollGesture call.
        """
        return await self.client.send(method="Input.synthesizeScrollGesture", params=params,session_id=session_id)
    async def synthesize_tap_gesture(self, params: Optional[synthesizeTapGestureParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Synthesizes a tap gesture over a time period by issuing appropriate touch events.    
        Args:
            params (synthesizeTapGestureParameters, optional): Parameters for the synthesizeTapGesture method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the synthesizeTapGesture call.
        """
        return await self.client.send(method="Input.synthesizeTapGesture", params=params,session_id=session_id)