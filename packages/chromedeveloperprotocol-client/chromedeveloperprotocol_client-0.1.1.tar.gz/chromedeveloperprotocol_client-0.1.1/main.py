import asyncio
import logging
import sys
import httpx
import subprocess
import os
import time

from cdp import Client

async def launch_browser(port=9222):
    """
    Launch MS Edge or Google Chrome with remote debugging enabled.
    """
    # Common paths for Edge and Chrome on Windows
    paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    
    exe_path = next((p for p in paths if os.path.exists(p)), None)
    if not exe_path:
        # Try finding it in PATH if not in standard locations
        try:
            exe_path = subprocess.check_output(["where", "msedge"]).decode().splitlines()[0]
        except:
            try:
                exe_path = subprocess.check_output(["where", "chrome"]).decode().splitlines()[0]
            except:
                raise Exception("Compatible browser (Edge or Chrome) not found in standard paths or PATH.")

    print(f"Launching browser: {exe_path}")
    
    # Launch the process
    # Using a detached process so it keeps running even if our script restarts
    process = subprocess.Popen([
        exe_path,
        f"--remote-debugging-port={port}",
        "--headless",
        "--disable-gpu",
        "--remote-allow-origins=*",
        "--user-data-dir=" + os.path.join(os.getcwd(), "cdp_user_data")
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Poll for the debugger endpoint to become available
    print(f"Waiting for debugger on port {port}...")
    async with httpx.AsyncClient() as http:
        for _ in range(20): # Try for up to 10 seconds
            try:
                resp = await http.get(f"http://localhost:{port}/json/version")
                if resp.status_code == 200:
                    data = resp.json()
                    print("Browser launched and debugger ready.")
                    return process, data['webSocketDebuggerUrl']
            except (httpx.ConnectError, httpx.HTTPError):
                await asyncio.sleep(0.5)
                
    raise Exception("Timed out waiting for browser to start.")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    port = 9222
    ws_url = None
    browser_process = None

    print("Checking for existing browser session...")
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(f"http://localhost:{port}/json/version")
            data = resp.json()
            ws_url = data['webSocketDebuggerUrl']
            print(f"Found existing session at: {ws_url}")
    except Exception:
        print("No existing session found. Launching new browser...")
        try:
            browser_process, ws_url = await launch_browser(port)
        except Exception as e:
            print(f"FAILED to launch browser: {e}")
            return

    try:
        async with Client(ws_url) as client:
            print("Connected! Getting target list...")
            targets = await client.target.get_targets({})
            print(f"Found {len(targets['targetInfos'])} targets")
            
            # Create a new page
            print("Creating new target...")
            target = await client.target.create_target({"url": "https://www.google.com"})
            target_id = target['targetId']
            print(f"Created new target: {target_id}")
            
            # Get browser info
            version = await client.browser.get_version({})
            print(f"Browser Version: {version['product']}")
            
            print("\nSUCCESS! CDP interaction verified.")
    finally:
        if browser_process:
            print("Closing the browser process...")
            # Optional: You can keep it running by NOT calling terminate()
            # browser_process.terminate()
            # print("Browser process terminated.")

if __name__ == "__main__":
    asyncio.run(main())
