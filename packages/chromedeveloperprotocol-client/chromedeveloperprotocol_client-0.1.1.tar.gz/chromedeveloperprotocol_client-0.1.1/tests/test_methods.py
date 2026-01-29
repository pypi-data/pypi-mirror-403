"""Integration Tests for CDP Methods"""

import pytest
import asyncio
from src.cdp import Client

# We don't need mocks anymore, we use the cdp_client fixture from conftest.py

class TestCDPMethodsIntegration:
    """Integration tests using real Chrome browser"""

    async def test_page_navigate(self, cdp_client: Client):
        """Test Page.navigate method"""
        # Navigate to a blank page
        result = await cdp_client.page.navigate({"url": "about:blank"})
        assert "frameId" in result
        
        # Verify we are on the correct page (using Runtime to check location)
        eval_result = await cdp_client.runtime.evaluate({"expression": "window.location.href"})
        assert eval_result["result"]["value"] == "about:blank"

    async def test_runtime_evaluate(self, cdp_client: Client):
        """Test Runtime.evaluate method"""
        result = await cdp_client.runtime.evaluate({
            "expression": "1 + 1"
        })
        assert result["result"]["type"] == "number"
        assert result["result"]["value"] == 2

    async def test_network_enable(self, cdp_client: Client):
        """Test Network.enable method"""
        # Just ensure it doesn't raise an error
        await cdp_client.network.enable()

    async def test_dom_get_document(self, cdp_client: Client):
        """Test DOM.getDocument method"""
        doc = await cdp_client.dom.get_document()
        assert "root" in doc
        assert doc["root"]["nodeName"] == "#document"

    async def test_domain_access(self, cdp_client: Client):
        """Test accessing various domains"""
        assert cdp_client.page is not None
        assert cdp_client.network is not None
        assert cdp_client.runtime is not None
        assert cdp_client.dom is not None
        # Check a few others
        assert cdp_client.target is not None
        assert cdp_client.browser is not None

    async def test_method_error_handling(self, cdp_client: Client):
        """Test that method errors are propagated correctly"""
        # Try a Runtime evaluation that throws
        
        eval_result = await cdp_client.runtime.evaluate({"expression": "throw new Error('oops')"})
        assert "exceptionDetails" in eval_result
        
        # Let's try to send a raw command that doesn't exist to test the client's error handling
        with pytest.raises(Exception):
             await cdp_client.send("Invalid.Method", {})


