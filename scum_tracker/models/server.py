"""
Data models for SCUM servers
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class GameServer:
    """Represents a SCUM game server"""
    id: str
    name: str
    ip: str
    port: int
    players: int
    max_players: int
    map: str
    region: str
    version: str = "Unknown"
    latency: Optional[int] = None
    is_favorite: bool = False
    last_ping_time: Optional[datetime] = None

    def __str__(self) -> str:
        return f"{self.name} ({self.players}/{self.max_players})"


@dataclass
class PingRecord:
    """Represents a ping measurement"""
    server_id: str
    latency: int
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None
