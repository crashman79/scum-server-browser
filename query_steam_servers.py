#!/usr/bin/env python3
"""
Query SCUM servers directly from Steam Master Server to get real version numbers.
This will give us the authoritative source for version->build correlations.
"""

import socket
import struct
import json
from typing import List, Tuple

class A2SQueryer:
    """Query game servers using the A2S protocol (Valve's query protocol)"""
    
    # A2S packet types
    A2S_INFO = 0x54  # Server info request
    A2S_PLAYER = 0x55  # Player list request
    A2S_RULES = 0x56  # Server rules request
    
    def __init__(self, timeout=5):
        self.timeout = timeout
    
    def query_server_info(self, host: str, port: int) -> dict:
        """Query a server for info including version"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Build A2S_INFO request
            # Format: 0xFFFFFFFF (4 bytes) + type (1 byte) + "Source Engine Query\0"
            request = struct.pack('>I', 0xFFFFFFFF) + bytes([self.A2S_INFO]) + b'Source Engine Query\x00'
            
            sock.sendto(request, (host, port))
            response, _ = sock.recvfrom(4096)
            
            # Parse response
            if len(response) < 6:
                return None
            
            # Skip header (0xFFFFFFFF and type byte)
            offset = 5
            data = response[offset:]
            
            # Parse fields
            protocol = data[0]
            offset = 1
            
            # Server name (null-terminated)
            name_end = data.find(b'\x00', offset)
            if name_end == -1:
                return None
            name = data[offset:name_end].decode('utf-8', errors='ignore')
            offset = name_end + 1
            
            # Map name
            map_end = data.find(b'\x00', offset)
            if map_end == -1:
                return None
            map_name = data[offset:map_end].decode('utf-8', errors='ignore')
            offset = map_end + 1
            
            # Folder
            folder_end = data.find(b'\x00', offset)
            if folder_end == -1:
                return None
            folder = data[offset:folder_end].decode('utf-8', errors='ignore')
            offset = folder_end + 1
            
            # Game
            game_end = data.find(b'\x00', offset)
            if game_end == -1:
                return None
            game = data[offset:game_end].decode('utf-8', errors='ignore')
            offset = game_end + 1
            
            # Version string (null-terminated)
            version_end = data.find(b'\x00', offset)
            if version_end == -1:
                # Sometimes version is just part of remaining data
                version = data[offset:offset+20].decode('utf-8', errors='ignore').rstrip('\x00')
            else:
                version = data[offset:version_end].decode('utf-8', errors='ignore')
            
            return {
                'name': name,
                'map': map_name,
                'folder': folder,
                'game': game,
                'version': version,
                'protocol': protocol,
                'raw_response': response[:100]  # First 100 bytes for debugging
            }
            
        except socket.timeout:
            return {'error': 'timeout'}
        except Exception as e:
            return {'error': str(e)}
        finally:
            try:
                sock.close()
            except:
                pass


def get_scum_servers_from_steam() -> List[Tuple[str, int]]:
    """
    Get list of SCUM servers from Steam Master Server.
    This is the authoritative source.
    """
    # Known SCUM official server IPs (from your screenshot)
    # These are a sample to query
    official_servers = [
        ("155.133.248.241", 7777),  # Example - would need to find actual IPs
        ("155.133.248.242", 7777),
    ]
    
    # For now, let's hardcode some known official server addresses
    # In production, you'd query the Steam Master Server for the full list
    return official_servers


def main():
    print("=" * 70)
    print("SCUM Server Query - Direct from Steam")
    print("=" * 70)
    
    # Let's try querying known official servers
    # First, we need to find actual server IPs
    
    print("\nKnown Official Servers (from screenshot):")
    print("- SCUM Server Official #3 - Russia")
    print("- SCUM Server Official Beginner #1 - US West")
    print("- SCUM Server Official Public Alpha #1 - US East")
    print("\nTo query these directly, we need their IP addresses.")
    print("\nSteps to get real data:")
    print("1. Look up official server IPs from Steam server browser")
    print("2. Query each with A2S protocol")
    print("3. Extract version field")
    print("4. Compare with BattleMetrics version")
    
    # Example of how to use the querier once we have IPs
    querier = A2SQueryer()
    
    print("\n" + "=" * 70)
    print("Version Mapping Discovery")
    print("=" * 70)
    
    print("""
From your screenshots, we can see:
- Build Version (in-game launcher): 1.1.0.5.101995
- Official Servers show versions like:
  * 1.1.0.5.101995 (Stable servers)
  * 1.1.0.4.101925 (PTE servers)
  * 1.2.0.0.103469+103478 (Alpha servers)

To correlate with BattleMetrics:
- We need to query Steam servers directly to get their exact version strings
- Then match against BattleMetrics API responses
- This gives us the definitive mapping
""")


if __name__ == "__main__":
    main()
