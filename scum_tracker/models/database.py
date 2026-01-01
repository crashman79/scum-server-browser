"""
Database layer for storing favorites and ping history
"""
import sqlite3
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from scum_tracker.models.server import PingRecord


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(Path.home() / ".scum_tracker" / "data.db")
        
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Get a database connection with optimizations for Windows"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        
        # Apply performance optimizations
        if platform.system() == 'Windows':
            # Windows-specific optimizations
            conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging for better concurrency
            conn.execute('PRAGMA synchronous=NORMAL')  # Faster writes, still safe
            conn.execute('PRAGMA temp_store=MEMORY')  # Use memory for temp tables
            conn.execute('PRAGMA cache_size=10000')  # Larger cache (10MB)
        else:
            # Linux optimizations
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=FULL')
        
        return conn

    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Favorites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    server_id TEXT PRIMARY KEY,
                    server_name TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ping history table with indexes for better query performance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ping_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT,
                    latency INTEGER,
                    timestamp TIMESTAMP,
                    success BOOLEAN,
                    error_message TEXT,
                    FOREIGN KEY (server_id) REFERENCES favorites(server_id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ping_server_timestamp 
                ON ping_history(server_id, timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ping_timestamp 
                ON ping_history(timestamp)
            """)
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            conn.commit()
        
        # Clean up old records on startup (keep last 24 hours)
        self.cleanup_old_records(days=1)

    def add_favorite(self, server_id: str, server_name: str) -> bool:
        """Add a server to favorites"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO favorites (server_id, server_name) VALUES (?, ?)",
                    (server_id, server_name)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding favorite: {e}")
            return False

    def remove_favorite(self, server_id: str) -> bool:
        """Remove a server from favorites"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM favorites WHERE server_id = ?", (server_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error removing favorite: {e}")
            return False

    def get_favorites(self) -> List[str]:
        """Get list of favorite server IDs"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT server_id FROM favorites")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching favorites: {e}")
            return []

    def is_favorite(self, server_id: str) -> bool:
        """Check if a server is in favorites"""
        return server_id in self.get_favorites()

    def add_ping_record(self, record: PingRecord) -> bool:
        """Add a ping record to history"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO ping_history 
                       (server_id, latency, timestamp, success, error_message) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (record.server_id, record.latency, record.timestamp, 
                     record.success, record.error_message)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding ping record: {e}")
            return False

    def get_ping_history(self, server_id: str, limit: int = 100) -> List[PingRecord]:
        """Get ping history for a server (last N records)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT server_id, latency, timestamp, success, error_message 
                       FROM ping_history 
                       WHERE server_id = ? 
                       ORDER BY timestamp DESC 
                       LIMIT ?""",
                    (server_id, limit)
                )
                records = []
                for row in cursor.fetchall():
                    records.append(PingRecord(
                        server_id=row[0],
                        latency=row[1],
                        timestamp=datetime.fromisoformat(row[2]),
                        success=bool(row[3]),
                        error_message=row[4]
                    ))
                return records
        except Exception as e:
            print(f"Error getting ping history: {e}")
            return []

    def get_all_ping_history_stats(self, limit: int = 100) -> dict:
        """Get ping stats (min/max/avg) for all servers efficiently"""
        try:
            stats = {}
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Optimized query using indexes
                cursor.execute(f"""
                    SELECT server_id, latency, timestamp FROM ping_history 
                    WHERE latency > 0
                    ORDER BY server_id, timestamp DESC
                """)
                
                current_server = None
                latencies = []
                last_timestamp = None
                
                for row in cursor.fetchall():
                    server_id, latency, timestamp = row
                    
                    if server_id != current_server:
                        # Store stats for previous server
                        if current_server and latencies:
                            stats[current_server] = {
                                'min': min(latencies),
                                'max': max(latencies),
                                'avg': sum(latencies) / len(latencies),
                                'count': len(latencies),
                                'last_timestamp': last_timestamp
                            }
                        
                        current_server = server_id
                        latencies = []
                        last_timestamp = datetime.fromisoformat(timestamp) if timestamp else None
                    
                    if len(latencies) < limit:
                        latencies.append(latency)
                
                # Don't forget the last server
                if current_server and latencies:
                    stats[current_server] = {
                        'min': min(latencies),
                        'max': max(latencies),
                        'avg': sum(latencies) / len(latencies),
                        'count': len(latencies),
                        'last_timestamp': last_timestamp
                    }
            
            return stats
        except Exception as e:
            print(f"Error getting ping history stats: {e}")
            return {}

    def cleanup_old_records(self, days: int = 1) -> int:
        """Delete ping records older than N days. Returns number of deleted records."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM ping_history WHERE timestamp < ?",
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                if deleted_count > 0:
                    day_str = "day" if days == 1 else "days"
                    print(f"Cleaned up {deleted_count} ping records older than {days} {day_str}")
                return deleted_count
        except Exception as e:
            print(f"Error cleaning up old records: {e}")
            return 0
    def save_filter_settings(self, settings: Dict) -> bool:
        """Save filter settings as JSON"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                settings_json = json.dumps(settings)
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ('filter_settings', settings_json)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error saving filter settings: {e}")
            return False

    def load_filter_settings(self) -> Dict:
        """Load filter settings from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key = ?", ('filter_settings',))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return {}
        except Exception as e:
            print(f"Error loading filter settings: {e}")
            return {}