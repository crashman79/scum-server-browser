"""
Steam Master Server and A2S query implementation

This module provides direct communication with Steam's infrastructure to:
1. Query the master server list for SCUM servers
2. Use A2S protocol to get real-time server information including player counts

This bypasses BattleMetrics and gets data directly from the source.
"""
import socket
import struct
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ServerInfo:
    """Information about a game server from A2S query"""
    name: str
    map: str
    game: str
    players: int
    max_players: int
    bots: int
    server_type: str
    environment: str
    visibility: int
    vac: int
    version: str
    port: Optional[int] = None
    steam_id: Optional[int] = None


class SteamMasterServerQuerier:
    """Query Steam's master server list for game servers"""
    
    # Steam master server addresses (using IPs to avoid DNS issues)
    MASTER_SERVERS = [
        '208.64.200.52:27011',  # Valve master server
        '208.64.200.65:27011',  # Valve master server  
        '208.78.164.10:27011',  # Alternative
    ]
    
    # SCUM App ID
    SCUM_APP_ID = 513650
    
    @staticmethod
    def get_server_list(timeout: float = 5.0) -> List[Tuple[str, int]]:
        """
        Query Steam master server for list of SCUM servers
        
        Returns:
            List of (ip, port) tuples
        """
        for master_addr_str in SteamMasterServerQuerier.MASTER_SERVERS:
            try:
                # Parse master server address
                host, port = master_addr_str.rsplit(':', 1)
                port = int(port)
                master_addr = (host, port)
                
                servers = SteamMasterServerQuerier._query_master(
                    master_addr, 
                    SteamMasterServerQuerier.SCUM_APP_ID,
                    timeout
                )
                
                if servers:
                    return servers
                    
            except Exception as e:
                print(f"Error querying {master_addr_str}: {e}")
                continue
        
        return []
    
    @staticmethod
    def _query_master(master_addr: Tuple[str, int], appid: int, timeout: float) -> List[Tuple[str, int]]:
        """
        Query a specific master server
        
        Protocol:
        - Send: 0x31 (query type) + region (0xFF = all) + seed IP:port + filter string
        - Receive: 0xFF 0xFF 0xFF 0xFF 0x66 0x0A + list of 6-byte IP:port entries
        - Seed with last received IP:port to get next batch
        - Stop when receive 0.0.0.0:0
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        servers = []
        seed = b'0.0.0.0:0\x00'  # Start with null seed
        region = b'\xFF'  # All regions
        filter_str = f'\\appid\\{appid}'.encode() + b'\x00'
        
        try:
            max_iterations = 100  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                # Build query packet
                query = b'1' + region + seed + filter_str
                
                sock.sendto(query, master_addr)
                
                try:
                    data, _ = sock.recvfrom(4096)
                except socket.timeout:
                    # No more data
                    break
                
                # Validate response header (should be 0xFF 0xFF 0xFF 0xFF 0x66 0x0A)
                if len(data) < 6:
                    break
                
                # Parse IP:port pairs starting at byte 6
                i = 6
                batch_servers = []
                
                while i + 6 <= len(data):
                    # Read 4 bytes for IP, 2 bytes for port (big-endian)
                    ip_bytes = data[i:i+4]
                    port_bytes = data[i+4:i+6]
                    
                    ip = '.'.join(str(b) for b in ip_bytes)
                    port = struct.unpack('>H', port_bytes)[0]
                    
                    # Check for end marker
                    if ip == '0.0.0.0' and port == 0:
                        return servers
                    
                    batch_servers.append((ip, port))
                    i += 6
                
                if not batch_servers:
                    # No servers in this batch
                    break
                
                servers.extend(batch_servers)
                
                # Use last server as seed for next query
                last_ip, last_port = batch_servers[-1]
                seed = f'{last_ip}:{last_port}'.encode() + b'\x00'
                
                iteration += 1
            
        except Exception as e:
            print(f"Master server query error: {e}")
        finally:
            sock.close()
        
        return servers


class A2SQuerier:
    """Query individual game servers using Source A2S protocol"""
    
    # A2S_INFO request packet
    A2S_INFO_REQUEST = b'\xFF\xFF\xFF\xFF\x54Source Engine Query\x00'
    
    @staticmethod
    def query_server(address: Tuple[str, int], timeout: float = 3.0) -> Optional[ServerInfo]:
        """
        Query a server for information using A2S_INFO protocol
        
        Args:
            address: (ip, port) tuple
            timeout: Query timeout in seconds
            
        Returns:
            ServerInfo object or None if query fails
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        try:
            # Send A2S_INFO request
            sock.sendto(A2SQuerier.A2S_INFO_REQUEST, address)
            
            # Receive response
            data, _ = sock.recvfrom(4096)
            
            # Parse response
            return A2SQuerier._parse_a2s_info(data)
            
        except socket.timeout:
            return None
        except Exception as e:
            print(f"A2S query error for {address}: {e}")
            return None
        finally:
            sock.close()
    
    @staticmethod
    def _parse_a2s_info(data: bytes) -> Optional[ServerInfo]:
        """
        Parse A2S_INFO response
        
        Response format:
        - Header: 0xFF 0xFF 0xFF 0xFF
        - Type: 0x49 (I)
        - Protocol: 1 byte
        - Name: null-terminated string
        - Map: null-terminated string  
        - Folder: null-terminated string
        - Game: null-terminated string
        - App ID: 2 bytes
        - Players: 1 byte
        - Max players: 1 byte
        - Bots: 1 byte
        - Server type: 1 byte ('d'=dedicated, 'l'=listen, 'p'=SourceTV)
        - Environment: 1 byte ('l'=linux, 'w'=windows, 'm'=mac)
        - Visibility: 1 byte (0=public, 1=private)
        - VAC: 1 byte (0=unsecured, 1=secured)
        - Version: null-terminated string
        """
        try:
            # Validate header and type
            if len(data) < 5 or data[0:4] != b'\xFF\xFF\xFF\xFF':
                return None
            
            if data[4] != 0x49:  # 'I'
                return None
            
            # Start parsing at byte 5
            idx = 5
            
            # Skip protocol byte
            idx += 1
            
            # Read null-terminated strings
            def read_string(start_idx):
                end_idx = data.find(b'\x00', start_idx)
                if end_idx == -1:
                    return "", start_idx
                return data[start_idx:end_idx].decode('utf-8', errors='replace'), end_idx + 1
            
            name, idx = read_string(idx)
            map_name, idx = read_string(idx)
            folder, idx = read_string(idx)
            game, idx = read_string(idx)
            
            # Skip app ID (2 bytes)
            idx += 2
            
            # Read numeric values
            if idx + 7 > len(data):
                return None
            
            players = data[idx]
            max_players = data[idx + 1]
            bots = data[idx + 2]
            server_type = chr(data[idx + 3])
            environment = chr(data[idx + 4])
            visibility = data[idx + 5]
            vac = data[idx + 6]
            idx += 7
            
            # Read version string
            version, idx = read_string(idx)
            
            return ServerInfo(
                name=name,
                map=map_name,
                game=game,
                players=players,
                max_players=max_players,
                bots=bots,
                server_type=server_type,
                environment=environment,
                visibility=visibility,
                vac=vac,
                version=version
            )
            
        except Exception as e:
            print(f"Error parsing A2S response: {e}")
            return None


def test_steam_queries():
    """Test function to verify Steam queries work"""
    print("Testing Steam Master Server Query...")
    print("=" * 80)
    
    # Get server list
    servers = SteamMasterServerQuerier.get_server_list()
    print(f"Found {len(servers)} SCUM servers from Steam Master Server")
    
    if servers:
        print("\nTesting A2S queries on first 5 servers:")
        print("=" * 80)
        
        for i, (ip, port) in enumerate(servers[:5]):
            print(f"\n{i+1}. {ip}:{port}")
            
            info = A2SQuerier.query_server((ip, port), timeout=2.0)
            
            if info:
                print(f"   Name: {info.name[:60]}")
                print(f"   Players: {info.players}/{info.max_players}")
                print(f"   Map: {info.map}")
                print(f"   Version: {info.version}")
            else:
                print("   [No response]")


if __name__ == "__main__":
    test_steam_queries()
