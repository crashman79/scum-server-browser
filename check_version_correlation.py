#!/usr/bin/env python3
"""
Use the app's own ServerManager to fetch servers, then correlate versions.
"""

import sys
import socket
import time
from typing import Optional, Dict

# Add app to path
sys.path.insert(0, '/home/crashman79/development/scum-browser')

from scum_tracker.services.server_manager import ServerManager

class A2SQuery:
    """Query game servers using A2S protocol"""
    
    def __init__(self, timeout=3):
        self.timeout = timeout
    
    def query_server_info(self, host: str, port: int) -> Optional[Dict]:
        """Query a game server for info using A2S_INFO"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # A2S_INFO request
            request = b'\xFF\xFF\xFF\xFFT' + b'Source Engine Query\x00'
            sock.sendto(request, (host, port))
            
            response, _ = sock.recvfrom(4096)
            sock.close()
            
            if len(response) < 6 or response[:4] != b'\xFF\xFF\xFF\xFF':
                return None
            
            # Parse response
            offset = 5
            
            def read_cstring(data, offset):
                end = data.find(b'\x00', offset)
                if end == -1:
                    return None, offset
                return data[offset:end].decode('utf-8', errors='ignore'), end + 1
            
            protocol_str, offset = read_cstring(response, offset - 1)
            server_name, offset = read_cstring(response, offset)
            map_name, offset = read_cstring(response, offset)
            game_dir, offset = read_cstring(response, offset)
            game_desc, offset = read_cstring(response, offset)
            
            # Version string
            if offset < len(response):
                version_raw = response[offset:offset+32]
                version = version_raw.decode('utf-8', errors='ignore').split('\x00')[0].strip()
            else:
                version = "Unknown"
            
            return {
                'name': server_name,
                'version': version,
            }
            
        except:
            return None


def main():
    print("=" * 90)
    print("SCUM Version Correlation: BattleMetrics ↔ A2S Direct Query")
    print("(Using app's ServerManager)")
    print("=" * 90)
    
    print("\n[1] Fetching SCUM servers from ServerManager...")
    try:
        servers = ServerManager.fetch_servers()
        print(f"✓ Got {len(servers)} servers\n")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    print("[2] Querying servers directly with A2S protocol...")
    print("-" * 90)
    
    querier = A2SQuery()
    correlations = []
    successful = 0
    
    # Get unique BattleMetrics versions
    unique_versions = {}
    for server in servers:
        bm_v = server.version
        if bm_v not in unique_versions:
            unique_versions[bm_v] = []
        unique_versions[bm_v].append(server)
    
    print(f"\nFound {len(unique_versions)} unique BattleMetrics versions\n")
    
    # Query a few servers from each version
    for bm_version, servers_with_version in sorted(unique_versions.items()):
        print(f"\nBattleMetrics Version: {bm_version}")
        print(f"  Servers with this version: {len(servers_with_version)}")
        
        a2s_versions = {}
        
        # Test up to 3 servers per BM version
        for server in servers_with_version[:3]:
            # Parse IP:port from server address
            if not hasattr(server, 'ip') or not server.ip:
                print(f"    ✗ {server.name[:40]}: No IP address")
                continue
            
            addr = f"{server.ip}:{server.port}"
            print(f"    Querying {addr}...")
            
            info = querier.query_server_info(server.ip, server.port)
            
            if info:
                a2s_version = info['version']
                if a2s_version not in a2s_versions:
                    a2s_versions[a2s_version] = 0
                a2s_versions[a2s_version] += 1
                
                print(f"      ✓ A2S Version: {a2s_version}")
                successful += 1
            else:
                print(f"      ✗ No response")
            
            time.sleep(0.3)  # Rate limit
        
        # Show summary for this BM version
        if a2s_versions:
            print(f"  A2S Versions found:")
            for a2s_v, count in sorted(a2s_versions.items(), key=lambda x: x[1], reverse=True):
                print(f"    → {a2s_v:30} ({count} servers)")
    
    print("\n" + "=" * 90)
    print(f"Queried {successful} servers successfully")
    print("=" * 90)
    print("""
If each BattleMetrics version maps to exactly ONE A2S version,
the correlation is confirmed!

Update VERSION_MAPPING in server_manager.py with the pattern you see.
""")


if __name__ == "__main__":
    main()
