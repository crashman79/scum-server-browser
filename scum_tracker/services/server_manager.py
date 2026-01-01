"""
Server management and API integration

Data Sources:
- BattleMetrics API (https://battlemetrics.com) - Aggregates servers from multiple sources

Game Architecture:
- SCUM uses Unreal Engine with Steam's MatchMaking system (App ID 513650)
- Official in-game browser queries Valve's master servers: hl2master.steampowered.com:27011-27015
- BattleMetrics aggregates servers from Steam and provides comprehensive API access
  
BattleMetrics Data:
- Country: Determined via GeoIP lookup of server IP address
- Coordinates: Approximate physical server location (lat/long) derived from GeoIP
- Note: Country/location may be inaccurate for:
  * IPs registered in different countries than physical location
  * Multi-region datacenters (G-Portal, etc.)
  * IP blocks that originated in one country but are hosted elsewhere
  * If you know a server is in the wrong location, you can verify via ping latency or add it manually

Notes:
- BattleMetrics provides complete coverage of public SCUM servers
- BattleMetrics API is easier to query than binary Steam master server protocol
- Private/unlisted servers may not appear in either Steam or BattleMetrics
- To find servers missing from the lists:
  1. Check the in-game server browser for IP addresses
  2. Look for server names in Discord communities
  3. Visit SCUM community forums and Reddit (/r/SCUMgame)
- You can add missing servers manually via the MANUAL_SERVERS list
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List
from scum_tracker.models.server import GameServer
import uuid
import a2s


class ServerManager:
    """Handles fetching and managing game servers"""

    BATTLEMETRICS_API = "https://api.battlemetrics.com/servers"
    GAME_ID = "scum"
    
    # Shared session with connection pooling for better performance on Windows
    _session = None
    
    @classmethod
    def _get_session(cls):
        """Get or create a shared requests session with connection pooling and retry logic"""
        if cls._session is None:
            cls._session = requests.Session()
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=3,  # Total number of retries
                backoff_factor=0.5,  # Wait 0.5s, 1s, 2s between retries
                status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
                allowed_methods=["GET"]  # Only retry GET requests
            )
            
            # Mount adapter with connection pooling
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,  # Number of connection pools to cache
                pool_maxsize=20  # Max number of connections in the pool
            )
            
            cls._session.mount("http://", adapter)
            cls._session.mount("https://", adapter)
            
            # Set default headers
            cls._session.headers.update({
                'User-Agent': 'SCUM-Server-Browser/1.0',
                'Accept': 'application/json'
            })
        
        return cls._session
    
    # Version mapping from BattleMetrics internal version to in-game display version
    # Based on official SCUM servers:
    # - Stable: "Official" = 1.1.0.5.101995
    # - PTE: "Official PTE" = 1.1.0.4.101925
    # - Alpha: "Official Public Alpha" = 1.2.0.0.103469+103478
    VERSION_MAPPING = {
        "0.256.1304": "1.1.0.5.101995",  # Current stable
        "0.256.1048": "1.1.0.4.101925",  # PTE (Public Test Environment)
        "0.512.25": "1.2.0.0.103469+103478",  # Alpha
        "0.256.536": "1.1.0 (Older)",  # Legacy
    }
    
    # Manual servers list - add servers not found in BattleMetrics here
    MANUAL_SERVERS = [
        # Format: {"name": "...", "ip": "...", "port": ...}
        # Example: {"name": "My Private Server", "ip": "192.168.1.1", "port": 7777}
    ]

    @staticmethod
    def convert_battlemetrics_version(bm_version: str) -> str:
        """
        Convert BattleMetrics internal version to in-game display version.
        
        BattleMetrics format: 0.X.Y.Z where:
        - 0: Engine indicator (always 0)
        - X: Version identifier (256=1.1.0, 512=1.2.0, etc)
        - Y: Build iteration
        - Z: Timestamp/hash
        
        Returns in-game version like "1.1.0.5.101995" or falls back to BM version if unmapped
        """
        if not bm_version or bm_version == "Unknown":
            return "Unknown"
        
        # Try to match the first 3 segments (0.X.Y)
        parts = bm_version.split('.')
        if len(parts) >= 3:
            version_key = f"{parts[0]}.{parts[1]}.{parts[2]}"
            if version_key in ServerManager.VERSION_MAPPING:
                return ServerManager.VERSION_MAPPING[version_key]
        
        # Fall back to the full BattleMetrics version if no mapping found
        return bm_version

    @staticmethod
    def fetch_servers() -> List[GameServer]:
        """Fetch servers from BattleMetrics API and add manual servers"""
        servers = ServerManager._fetch_battlemetrics_servers()
        servers.extend(ServerManager._get_manual_servers())
        return servers

    @staticmethod
    def _fetch_battlemetrics_servers() -> List[GameServer]:
        """Fetch servers from BattleMetrics API with pagination using cursor-based pagination"""
        try:
            servers = []
            session = ServerManager._get_session()
            url = f"{ServerManager.BATTLEMETRICS_API}?filter[game]={ServerManager.GAME_ID}&page[size]=100"
            page_count = 0
            max_pages = 10  # Limit to ~1000 servers to keep load times reasonable
            
            while url and page_count < max_pages:
                response = session.get(
                    url,
                    timeout=15  # Increased timeout for better reliability on Windows
                )
                response.raise_for_status()
                
                data = response.json()
                server_list = data.get("data", [])
                
                # Process servers from this page
                for server_data in server_list:
                    attrs = server_data.get("attributes", {})
                    details = attrs.get("details", {})
                    
                    server = GameServer(
                        id=server_data.get("id", str(uuid.uuid4())),
                        name=attrs.get("name", "Unknown"),
                        ip=attrs.get("ip", "0.0.0.0"),
                        port=attrs.get("port", 0),
                        players=attrs.get("players", 0),
                        max_players=attrs.get("maxPlayers", 0),
                        map=details.get("map", "Unknown"),
                        region=attrs.get("country", "Unknown"),
                        version=details.get("version", "Unknown"),
                    )
                    servers.append(server)
                
                # Get next page URL from links
                links = data.get("links", {})
                url = links.get("next")
                page_count += 1
            
            return servers
        
        except requests.RequestException as e:
            print(f"Error fetching servers from BattleMetrics: {e}")
            return []
    
    @staticmethod
    def _get_manual_servers() -> List[GameServer]:
        """Get manually added servers"""
        servers = []
        for manual_server in ServerManager.MANUAL_SERVERS:
            server = GameServer(
                id=f"manual_{manual_server.get('ip')}_{manual_server.get('port')}",
                name=manual_server.get("name", "Unknown"),
                ip=manual_server.get("ip", "0.0.0.0"),
                port=manual_server.get("port", 0),
                players=manual_server.get("players", 0),
                max_players=manual_server.get("max_players", 128),
                map="Unknown",
                region=manual_server.get("country", "??"),
                version=manual_server.get("version", "Unknown"),
            )
            servers.append(server)
        return servers
    
    @staticmethod
    def query_server_realtime(ip: str, port: int) -> dict:
        """
        Query a server directly using A2S protocol for real-time info.
        This bypasses BattleMetrics and gets data straight from the game server.
        
        Args:
            ip: Server IP address
            port: Server port
            
        Returns:
            dict with server info or None if query fails
        """
        try:
            info = a2s.info((ip, port), timeout=3.0)
            return {
                'name': info.server_name,
                'players': info.player_count,
                'max_players': info.max_players,
                'map': info.map_name,
                'version': info.version,
                'game': info.game,
            }
        except Exception as e:
            print(f"A2S query failed for {ip}:{port}: {e}")
            return None
