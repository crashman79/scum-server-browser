#!/usr/bin/env python3
"""Check what data BattleMetrics API actually provides for SCUM"""
import requests
import json

BATTLEMETRICS_API = "https://api.battlemetrics.com/servers"
GAME_ID = "scum"  # Correct game ID for SCUM

try:
    url = f"{BATTLEMETRICS_API}?filter[game]={GAME_ID}&page[size]=2"
    print(f"Fetching from: {url}")
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    server_count = len(data.get("data", []))
    print(f"Response status: {response.status_code}")
    print(f"Servers found: {server_count}")
    
    if server_count > 0:
        print("✓ Found servers! Analyzing structure...")
        server = data["data"][0]
        attrs = server.get("attributes", {})
        details = attrs.get("details", {})
        
        print(f"\nServer ID: {server.get('id')}")
        print(f"Server name: {attrs.get('name', 'Unknown')}")
        print(f"\nAll attributes keys: {list(attrs.keys())}")
        print(f"Details keys: {list(details.keys())}")
        
        print(f"\n=== FULL DETAILS ===")
        print(json.dumps(details, indent=2))
        
        print(f"\n=== FULL ATTRIBUTES (truncated) ===")
        attrs_copy = {k: v for k, v in attrs.items() if k != 'details'}
        print(json.dumps(attrs_copy, indent=2)[:1500])
    else:
        print("No servers found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()



