import asyncio
import logging
import sys
import httpx

from cdp import Client

async def main():
    logging.basicConfig(level=logging.INFO)
    
    print("Fetching debugger URL...")
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get("http://localhost:9222/json/version")
            data = resp.json()
            ws_url = data['webSocketDebuggerUrl']
            print(f"Connecting to: {ws_url}")
    except Exception as e:
        print(f"Browser not found at localhost:9222. Error: {e}")
        return

    async with Client(ws_url) as client:
        print("Connected! Getting target list...")
        # Since we connected to the browser, we might need to attach to a page target
        targets = await client.target.get_targets({})
        print(f"Found {len(targets['targetInfos'])} targets")
        
        # Create a new page
        target = await client.target.create_target({"url": "about:blank"})
        target_id = target['targetId']
        print(f"Created new target: {target_id}")
        
        # In a real app, you'd attach to the target. 
        # But our high-level Page domain is usually for the main session.
        # If we are connected to the browser endpoint, we use 'target' domain to manage pages.
        
        print("Navigating main page to google.com...")
        # Note: navigating a browser session directly might not work, 
        # usually you navigate a page session. 
        # But let's try a simple command.
        version = await client.browser.get_version({})
        print(f"Browser Version: {version['product']}")
        
        print("\nSUCCESS! CDP interaction verified.")

if __name__ == "__main__":
    asyncio.run(main())
