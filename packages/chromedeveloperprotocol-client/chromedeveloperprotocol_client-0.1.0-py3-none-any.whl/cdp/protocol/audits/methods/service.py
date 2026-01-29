"""CDP Audits Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class AuditsMethods:
    """
    Methods for the Audits domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Audits methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def get_encoded_response(self, params: Optional[getEncodedResponseParameters]=None,session_id: Optional[str] = None) -> getEncodedResponseReturns:
        """
    Returns the response body and size if it were re-encoded with the specified settings. Only applies to images.    
        Args:
            params (getEncodedResponseParameters, optional): Parameters for the getEncodedResponse method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    getEncodedResponseReturns: The result of the getEncodedResponse call.
        """
        return await self.client.send(method="Audits.getEncodedResponse", params=params,session_id=session_id)
    async def disable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Disables issues domain, prevents further issues from being reported to the client.    
        Args:
            params (None, optional): Parameters for the disable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the disable call.
        """
        return await self.client.send(method="Audits.disable", params=params,session_id=session_id)
    async def enable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Enables issues domain, sends the issues collected so far to the client by means of the `issueAdded` event.    
        Args:
            params (None, optional): Parameters for the enable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the enable call.
        """
        return await self.client.send(method="Audits.enable", params=params,session_id=session_id)
    async def check_contrast(self, params: Optional[checkContrastParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Runs the contrast check for the target page. Found issues are reported using Audits.issueAdded event.    
        Args:
            params (checkContrastParameters, optional): Parameters for the checkContrast method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the checkContrast call.
        """
        return await self.client.send(method="Audits.checkContrast", params=params,session_id=session_id)
    async def check_forms_issues(self, params: None=None,session_id: Optional[str] = None) -> checkFormsIssuesReturns:
        """
    Runs the form issues check for the target page. Found issues are reported using Audits.issueAdded event.    
        Args:
            params (None, optional): Parameters for the checkFormsIssues method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    checkFormsIssuesReturns: The result of the checkFormsIssues call.
        """
        return await self.client.send(method="Audits.checkFormsIssues", params=params,session_id=session_id)