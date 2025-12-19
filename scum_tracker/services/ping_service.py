"""
Ping service for measuring server latency
"""
import socket
from datetime import datetime
from typing import Optional
from scum_tracker.models.server import PingRecord


class PingService:
    """Handles ping operations for servers"""

    @staticmethod
    def ping_server(ip: str, port: int) -> PingRecord:
        """Ping a server by attempting TCP connection to the game port"""
        try:
            start_time = datetime.now()
            
            # Create socket and attempt connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            
            try:
                # Attempt to connect to the server's game port
                sock.connect((ip, port))
                latency = int((datetime.now() - start_time).total_seconds() * 1000)
                sock.close()
                
                return PingRecord(
                    server_id="",  # Will be set by caller
                    latency=latency,
                    success=True
                )
            except (socket.timeout, socket.error) as e:
                latency = int((datetime.now() - start_time).total_seconds() * 1000)
                return PingRecord(
                    server_id="",
                    latency=latency if latency < 2000 else -1,
                    success=False,
                    error_message=f"Connection failed: {str(e)}"
                )
            finally:
                sock.close()
        
        except Exception as e:
            return PingRecord(
                server_id="",
                latency=-1,
                success=False,
                error_message=str(e)
            )
