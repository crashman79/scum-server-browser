"""
Ping service for measuring server latency
"""
import subprocess
import platform
from datetime import datetime
from typing import Optional
from scum_tracker.models.server import PingRecord


class PingService:
    """Handles ping operations for servers"""

    @staticmethod
    def ping_server(ip: str, port: int) -> PingRecord:
        """Ping a server and return latency"""
        try:
            start_time = datetime.now()
            
            # Use platform-specific ping command
            if platform.system() == "Windows":
                cmd = f"ping -n 1 -w 1000 {ip}"
            else:
                cmd = f"ping -c 1 -W 1000 {ip}"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=3
            )
            
            latency = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if result.returncode == 0:
                return PingRecord(
                    server_id="",  # Will be set by caller
                    latency=latency,
                    success=True
                )
            else:
                return PingRecord(
                    server_id="",
                    latency=latency,
                    success=False,
                    error_message="Server unreachable"
                )
        
        except subprocess.TimeoutExpired:
            return PingRecord(
                server_id="",
                latency=-1,
                success=False,
                error_message="Ping timeout"
            )
        except Exception as e:
            return PingRecord(
                server_id="",
                latency=-1,
                success=False,
                error_message=str(e)
            )
