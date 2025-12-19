# SCUM Server Browser

A lightweight desktop application for tracking and pinging SCUM game servers with real-time latency monitoring.

## Features

✨ **Core Features**
- 🌐 Browse SCUM servers from BattleMetrics API
- ⏱️ Real-time ping latency measurement
- ⭐ Mark and filter favorite servers
- 📊 View ping history with timestamps
- 🔄 Auto-refresh server list at configurable intervals
- 🔍 Search servers by name
- 📈 Color-coded latency indicators (green <100ms, orange 100-200ms, red >200ms)
- 🎨 Light/Dark/System theme support
- 💾 Filter preferences automatically saved

## Installation & Usage

### Option 1: Standalone Executable (Recommended)

**No Python installation required!**

Download the pre-built executable for your platform:
- **Linux**: `SCUM_Server_Browser` (146 MB)
- **Windows**: `SCUM_Server_Browser.exe` (146 MB)

Just download and run - everything is included! See [DISTRIBUTION.md](DISTRIBUTION.md) for details.

### Option 2: From Source (Requires Python)

**Prerequisites:**
- Python 3.8+

**Installation:**
```bash
pip install -r requirements.txt
python -m scum_tracker
```

## Building Standalone Executables

To create your own standalone executables for distribution:

**Linux:**
```bash
chmod +x build_linux.sh
./build_linux.sh
```

**Windows:**
```cmd
build_windows.bat
```

See [BUILD.md](BUILD.md) for detailed build instructions.

## Project Structure

```
scum-browser/
├── scum_tracker/
│   ├── __init__.py           # Application entry point
│   ├── models/
│   │   ├── server.py         # GameServer and PingRecord data models
│   │   └── database.py       # SQLite database management
│   ├── services/
│   │   ├── server_manager.py # BattleMetrics API integration
│   │   └── ping_service.py   # Ping functionality
│   └── ui/
│       └── main_window.py    # Main PyQt6 application window
├── requirements.txt
└── README.md
```

## Data Storage

- Favorites and ping history are stored in `~/.scum_tracker/data.db`
- SQLite database with two tables: `favorites` and `ping_history`

## Features in Detail

### Server Monitoring
- Fetch server list from BattleMetrics API
- Display player count, map, region information
- Real-time ping with visual color indicators

### Favorites Management
- Click ★ to mark/unmark favorite servers
- Filter to show only favorite servers
- Favorites persist across sessions

### Ping History
- Automatic recording of all pings
- View detailed history for any server
- Timestamps for trend analysis

### Auto-Refresh
- Configurable refresh interval (5-300 seconds)
- Background refresh with server updates
- Manual refresh button available

## Troubleshooting

**ImportError: No module named 'PyQt6'**
```bash
pip install PyQt6
```

**Ping not working**
- On Linux, ping may require elevated permissions
- On Windows, ensure ICMP is enabled in firewall

**Database issues**
- Database file is stored in `~/.scum_tracker/data.db`
- Safe to delete to reset favorites and history

## Future Enhancements

- [ ] Filter by region/map
- [ ] Ping statistics (average, min, max)
- [ ] Export server data to CSV
- [ ] Server status notifications
- [ ] Custom server list import

## License

MIT
