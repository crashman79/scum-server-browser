"""
Ping service for measuring server latency
"""
import socket
import platform
from datetime import datetime
from typing import Optional
from scum_tracker.models.server import PingRecord


class PingService:
    """Handles ping operations for servers"""
    
    # Windows-specific socket options for better performance
    _is_windows = platform.system() == 'Windows'
    
    @staticmethod
    def ping_server(ip: str, port: int) -> PingRecord:
        """Ping a server by attempting TCP connection to the game port"""
        sock = None
        try:
            start_time = datetime.now()
            
            # Create socket with optimizations
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Windows-specific optimizations
            if PingService._is_windows:
                try:
                    # Disable Nagle's algorithm for faster small packet sends
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    # Enable quick socket reuse (helps with rapid successive pings)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                except (OSError, AttributeError):
                    pass  # Some options may not be available
            
            # Set connection timeout (shorter for better responsiveness)
            sock.settimeout(1.5)
            
            try:
                # Attempt to connect to the server's game port
                sock.connect((ip, port))
                latency = int((datetime.now() - start_time).total_seconds() * 1000)
                
                return PingRecord(
                    server_id="",  # Will be set by caller
                    latency=latency,
                    success=True
                )
            except socket.timeout:
                latency = int((datetime.now() - start_time).total_seconds() * 1000)
                return PingRecord(
                    server_id="",
                    latency=-1,
                    success=False,
                    error_message="Connection timeout"
                )
            except socket.error as e:
                latency = int((datetime.now() - start_time).total_seconds() * 1000)
                return PingRecord(
                    server_id="",
                    latency=-1,
                    success=False,
                    error_message=f"Connection failed: {str(e)}"
                )
        
        except Exception as e:
            return PingRecord(
                server_id="",
                latency=-1,
                success=False,
                error_message=str(e)
            )
        finally:
            # Ensure socket is properly closed
            if sock is not None:
                try:
                    sock.close()
                except:
                    pass
