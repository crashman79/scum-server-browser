#!/usr/bin/env python3
"""
Query SCUM servers directly from Steam Community to correlate build versions.
Uses Steam's public server list to get authoritative version info.
"""

import urllib.request
import json
import re
from typing import Dict, List

class SteamServerQuery:
    """Query Steam's server browser for SCUM servers"""
    
    # Steam app ID for SCUM
    SCUM_APP_ID = 513710
    
    # Steam Community API endpoint for server browser
    STEAM_API_BASE = "https://api.steampowered.com/ISteamApps/GetServersAtAddress/v1"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
        }
    
    def query_steam_community(self) -> Dict:
        """
        Query Steam Community server browser for SCUM.
        Note: This may be rate-limited or require authentication.
        """
        try:
            # Try the public Steam server list
            url = f"https://api.steampowered.com/IGameServersService/GetAccountPublicServers/v1?key=STEAMMASTERSERVERUPDATERKEY&appid={self.SCUM_APP_ID}&limit=200"
            
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data
        except Exception as e:
            print(f"Error querying Steam API: {e}")
            return None
    
    def parse_version_strings(self, version_str: str) -> Dict:
        """Parse version string to extract components"""
        parts = version_str.split('.')
        return {
            'raw': version_str,
            'major': parts[0] if len(parts) > 0 else '?',
            'minor': parts[1] if len(parts) > 1 else '?',
            'patch': parts[2] if len(parts) > 2 else '?',
            'build': parts[3] if len(parts) > 3 else '?',
        }


def query_battlemetrics_comparison() -> List[Dict]:
    """
    Get current BattleMetrics servers and their versions for comparison.
    """
    import urllib.request
    import json
    
    try:
        url = "https://api.battlemetrics.com/servers?filter[game]=scum&limit=50"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        servers = []
        for server in data.get('data', [])[:20]:
            attrs = server.get('attributes', {})
            servers.append({
                'name': attrs.get('name', 'Unknown'),
                'bm_version': attrs.get('details', {}).get('version', 'Unknown'),
                'players': attrs.get('players', 0),
                'maxPlayers': attrs.get('maxPlayers', 0),
            })
        
        return servers
    except Exception as e:
        print(f"Error querying BattleMetrics: {e}")
        return []


def main():
    print("=" * 80)
    print("SCUM Version Correlation Analysis")
    print("=" * 80)
    
    print("\n[1] Querying Steam servers...")
    steam_query = SteamServerQuery()
    steam_data = steam_query.query_steam_community()
    
    if steam_data:
        print(f"✓ Got Steam data: {len(steam_data)} results")
        print(json.dumps(steam_data, indent=2)[:500])
    else:
        print("✗ Could not query Steam API directly")
    
    print("\n[2] Querying BattleMetrics for comparison...")
    bm_servers = query_battlemetrics_comparison()
    
    if bm_servers:
        print(f"✓ Got {len(bm_servers)} BattleMetrics servers\n")
        
        # Group by BattleMetrics version
        bm_by_version = {}
        for server in bm_servers:
            version = server['bm_version']
            if version not in bm_by_version:
                bm_by_version[version] = []
            bm_by_version[version].append(server['name'])
        
        print("BattleMetrics Versions Found:")
        print("-" * 80)
        for version in sorted(bm_by_version.keys()):
            servers = bm_by_version[version]
            print(f"  {version:30} -> {len(servers):3} servers")
            if len(servers) <= 3:
                for name in servers:
                    print(f"      - {name}")
        
        print("\n" + "=" * 80)
        print("Version Analysis")
        print("=" * 80)
        
        print("\nFrom your screenshots:")
        print("  In-Game Build: 1.1.0.5.101995")
        print("  Alpha Version: 1.2.0.0.103469+103478")
        print("  PTE Version:   1.1.0.4.101925")
        
        print("\nFrom BattleMetrics:")
        for version in sorted(bm_by_version.keys()):
            print(f"  {version}")
        
        print("\nNext Step: Cross-reference these to find exact mapping")
        
    else:
        print("✗ Could not query BattleMetrics")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
