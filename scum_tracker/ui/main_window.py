"""
Main application window
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QCheckBox, QSpinBox, QLabel, QDialog, QTextEdit, QScrollArea, QGroupBox, QMenu, QAbstractItemDelegate, QFrame,
    QApplication, QMessageBox, QComboBox, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QPoint
from PyQt6.QtGui import QFont, QColor, QAction, QPixmap, QPainter, QPen, QBrush, QStandardItemModel, QStandardItem
from functools import cmp_to_key
from datetime import datetime
from typing import List
import matplotlib
matplotlib.use('Qt5Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.interpolate import make_interp_spline
import numpy as np
import subprocess
import platform
import os

from scum_tracker.models.server import GameServer, PingRecord
from scum_tracker.models.database import Database
from scum_tracker.services.server_manager import ServerManager
from scum_tracker.services.ping_service import PingService
from scum_tracker.services.theme_service import ThemeService, Theme

# Country to continent mapping
COUNTRY_TO_CONTINENT = {
    # North America
    "US": "North America", "CA": "North America", "MX": "North America",
    # South America
    "BR": "South America", "CO": "South America", "CL": "South America", "AR": "South America", "PE": "South America",
    # Europe
    "GB": "Europe", "DE": "Europe", "FR": "Europe", "NL": "Europe", "PL": "Europe", "RU": "Europe",
    "IT": "Europe", "ES": "Europe", "PT": "Europe", "BE": "Europe", "CH": "Europe", "AT": "Europe",
    "SE": "Europe", "NO": "Europe", "DK": "Europe", "FI": "Europe", "CZ": "Europe", "HU": "Europe",
    "RO": "Europe", "GR": "Europe", "UA": "Europe",
    # Middle East
    "AE": "Middle East", "SA": "Middle East", "IL": "Middle East", "TR": "Middle East", "IQ": "Middle East", "IR": "Middle East",
    # Asia
    "CN": "Asia", "JP": "Asia", "SG": "Asia", "IN": "Asia", "KR": "Asia", "TH": "Asia",
    "MY": "Asia", "PH": "Asia", "VN": "Asia", "ID": "Asia", "PK": "Asia", "BD": "Asia",
    # Oceania
    "AU": "Oceania", "NZ": "Oceania",
    # Africa
    "ZA": "Africa", "EG": "Africa", "NG": "Africa",
}


class CustomCheckBox(QCheckBox):
    """Custom checkbox with visible painted checkmark"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(24)
        # Set smaller font size to fit text in narrower width
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)
        # Set minimum width based on checkbox + text
        if text:
            self.setMinimumWidth(70)
    
    def paintEvent(self, event):
        """Paint checkbox with custom checkmark"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Checkbox box dimensions
        box_size = 18
        box_x = 2
        box_y = (self.height() - box_size) // 2
        
        # Determine colors based on theme
        if self.palette().color(self.foregroundRole()).red() > 128:
            # Light theme
            border_color = QColor("#cccccc")
            check_color = QColor("#4CAF50")
        else:
            # Dark theme
            border_color = QColor("#555555")
            check_color = QColor("#4CCA50")
        
        # Draw checkbox box
        painter.setPen(QPen(border_color, 1))
        painter.drawRect(box_x, box_y, box_size, box_size)
        
        # Draw checkmark if checked
        if self.isChecked():
            painter.setPen(QPen(check_color, 2.5))
            painter.drawLine(box_x + 4, box_y + 10, box_x + 8, box_y + 14)
            painter.drawLine(box_x + 8, box_y + 14, box_x + 15, box_y + 6)
        
        # Draw text label
        text_x = box_x + box_size + 8
        text_y = self.height() // 2
        
        painter.setPen(QPen(self.palette().color(self.foregroundRole())))
        painter.setFont(self.font())
        
        # Draw text aligned to the middle
        text_rect = self.fontMetrics().boundingRect(self.text())
        painter.drawText(text_x, text_y + text_rect.height() // 2, self.text())


class ServerFetchWorker(QThread):
    """Worker thread for fetching servers"""
    servers_fetched = pyqtSignal(list)  # List[GameServer]
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
    
    def run(self):
        try:
            servers = ServerManager.fetch_servers()
            favorites = self.db.get_favorites()
            
            for server in servers:
                server.is_favorite = server.id in favorites
            
            self.servers_fetched.emit(servers)
        except Exception as e:
            print(f"Error fetching servers: {e}")
            self.servers_fetched.emit([])


class PingWorker(QThread):
    """Worker thread for pinging servers"""
    ping_completed = pyqtSignal(str, int, bool)  # server_id, latency, success
    
    def __init__(self, server: GameServer):
        super().__init__()
        self.server = server
    
    def run(self):
        result = PingService.ping_server(self.server.ip, self.server.port)
        self.ping_completed.emit(
            self.server.id,
            result.latency if result.latency > 0 else 0,
            result.success
        )


class NumericTableItem(QTableWidgetItem):
    """Table item that sorts numerically"""
    def __init__(self, display_text: str, numeric_value: int):
        super().__init__(display_text)
        self.numeric_value = numeric_value
    
    def __lt__(self, other):
        """Override less-than for numeric sorting"""
        if isinstance(other, NumericTableItem):
            return self.numeric_value < other.numeric_value
        return super().__lt__(other)


class PingItemDelegate(QAbstractItemDelegate):
    """Custom delegate for rendering ping values with color coding"""
    def paint(self, painter, option, index):
        """Paint the ping item with color coding"""
        text = index.data()
        
        # Extract latency value from text (e.g., "19ms" -> 19)
        try:
            latency = int(str(text).rstrip('ms'))
        except (ValueError, AttributeError, TypeError):
            # Fall back to default rendering for non-numeric items
            return
        
        # Determine color based on latency
        if latency < 100:
            color = QColor("#00AA00")  # Green
        elif latency < 200:
            color = QColor("#FF9900")  # Orange
        else:
            color = QColor("#FF0000")  # Red
        
        # Draw background
        painter.fillRect(option.rect, QColor(color.red(), color.green(), color.blue(), 30))
        
        # Draw text
        painter.setPen(color)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(option.rect, int(Qt.AlignmentFlag.AlignCenter), str(text))
    
    def sizeHint(self, option, index):
        """Return size hint for the item"""
        return option.rect.size()


class NumericSortTableWidget(QTableWidget):
    """Custom table widget with proper numeric sorting"""
    pass


class SpinningCheckBox(CustomCheckBox):
    """Checkbox with visible checkmark (animation removed)"""
    
    stateChanged = pyqtSignal(int)
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.stateChanged.connect(self._on_state_changed)
    
    def _on_state_changed(self):
        """Emit state change signal"""
        self.stateChanged.emit(2 if self.isChecked() else 0)
    
    def start_spin(self):
        """Placeholder for animation (no longer used)"""
        pass
    
    def stop_spin(self):
        """Placeholder for animation (no longer used)"""
        pass


class AnimatedIndicator(QLabel):
    
    def __init__(self, parent=None):
        super().__init__("●", parent)
        self.setStyleSheet("color: #4CAF50; font-size: 12px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(20)
        self.setVisible(False)
        
        # Create pulsing animation
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(0.3)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Create looping animation
        self.anim_group = QSequentialAnimationGroup()
        self.anim_group.addAnimation(self.animation)
        
        # Create reverse animation
        self.animation_reverse = QPropertyAnimation(self, b"opacity")
        self.animation_reverse.setDuration(800)
        self.animation_reverse.setStartValue(1.0)
        self.animation_reverse.setEndValue(0.3)
        self.animation_reverse.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim_group.addAnimation(self.animation_reverse)
        self.anim_group.setLoopCount(-1)  # Loop forever
        
        self._opacity = 1.0
    
    def setOpacity(self, value):
        """Set opacity for animation"""
        self._opacity = value
        self.setStyleSheet(f"color: #4CAF50; font-size: 12px; opacity: {value};")
    
    def start_animation(self):
        """Start pulsing animation"""
        self.setVisible(True)
        self.anim_group.start()
    
    def stop_animation(self):
        """Stop pulsing animation"""
        self.anim_group.stop()
        self.setVisible(False)


class DisplayWorker(QThread):
    """Worker thread for filtering and sorting servers asynchronously"""
    display_ready = pyqtSignal(list)  # Emits filtered and sorted servers
    
    def __init__(self, servers, search_text, favorites_only, region_name, max_ping,
                 hide_empty, hide_full, sort_column, sort_order, db):
        super().__init__()
        self.servers = servers
        self.search_text = search_text
        self.favorites_only = favorites_only
        self.region_name = region_name
        self.max_ping = max_ping
        self.hide_empty = hide_empty
        self.hide_full = hide_full
        self.sort_column = sort_column
        self.sort_order = sort_order
        self.db = db
    
    def run(self):
        """Filter, sort, and prepare servers for display"""
        # Build list of countries from selected region
        selected_countries = []
        if self.region_name != "All Regions":
            for country, region in COUNTRY_TO_CONTINENT.items():
                if region == self.region_name:
                    selected_countries.append(country)
        
        # Filter servers
        filtered = []
        for server in self.servers:
            # Favorites filter
            if self.favorites_only and not server.is_favorite:
                continue
            
            # Search filter
            if self.search_text and self.search_text not in server.name.lower():
                continue
            
            # Region filter
            if selected_countries and server.region not in selected_countries:
                continue
            
            # Ping filter - max ping only
            if server.latency is not None and server.latency > 0:
                if server.latency > self.max_ping:
                    continue
            
            # Player count filter
            if self.hide_empty and server.players == 0:
                continue
            if self.hide_full and server.players >= server.max_players:
                continue
            
            filtered.append(server)
        
        # Sort servers
        sort_reverse = self.sort_order == Qt.SortOrder.DescendingOrder
        
        if self.sort_column == 0:  # Star (favorites)
            pass
        elif self.sort_column == 1:  # Server Name
            filtered = sorted(filtered, key=lambda s: s.name.lower(), reverse=sort_reverse)
        elif self.sort_column == 2:  # Players
            filtered = sorted(filtered, key=lambda s: s.players, reverse=sort_reverse)
        elif self.sort_column == 3:  # Ping
            filtered = sorted(filtered, key=lambda s: s.latency if s.latency else 999999, reverse=sort_reverse)
        elif self.sort_column == 4:  # Region
            pass
        elif self.sort_column == 5:  # IP:Port
            pass
        elif self.sort_column == 6:  # History
            pass
        
        # Keep favorites on top
        favorites = [s for s in filtered if s.is_favorite]
        non_favorites = [s for s in filtered if not s.is_favorite]
        filtered = favorites + non_favorites
        
        # Emit result
        self.display_ready.emit(filtered)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCUM Server Browser")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set application icon
        self._set_window_icon()
        
        self.db = Database()
        self.theme_service = ThemeService()
        self.servers: List[GameServer] = []
        self.displayed_servers: List[GameServer] = []  # Filtered/displayed servers for table
        self.ping_workers = []
        self.fetch_worker = None
        self.display_worker = None  # Worker thread for filtering/sorting
        self.pings_completed = 0
        self.local_scum_version = self._get_local_scum_version()
        self.total_pings = 0
        
        # Timer for periodic display updates during pinging (updates in place without rebuilding)
        self.display_update_timer = QTimer()
        self.display_update_timer.timeout.connect(self._update_displayed_pings)
        
        self.init_ui()
        self.load_servers()

    def closeEvent(self, event):
        """Clean up threads before closing"""
        # Save filter settings before closing
        self._save_filter_settings()
        
        # Stop display update timer
        if hasattr(self, 'display_update_timer'):
            self.display_update_timer.stop()
        
        # Stop and wait for display worker thread to finish
        if self.display_worker and self.display_worker.isRunning():
            self.display_worker.terminate()  # Force terminate if needed
            if not self.display_worker.wait(timeout=1000):  # Wait 1 second
                print("Warning: Display worker did not terminate cleanly")
        
        # Stop and wait for ping workers with proper cleanup
        active_workers = [w for w in self.ping_workers if w and w.isRunning()]
        for worker in active_workers:
            worker.terminate()
        
        # Wait for all workers to finish
        for worker in active_workers:
            worker.wait(timeout=500)  # Shorter timeout per worker
        
        # Clear worker lists
        self.ping_workers.clear()
        
        # Stop fetch worker if running
        if self.fetch_worker and self.fetch_worker.isRunning():
            self.fetch_worker.terminate()
            self.fetch_worker.wait(timeout=1000)
        
        super().closeEvent(event)

    def _set_theme(self, theme: Theme):
        """Change the application theme."""
        self.theme_service.save_theme(theme)
        # Update button states
        self.theme_light_btn.setStyleSheet("background-color: #0078d4; color: white;" if theme == Theme.LIGHT else "")
        self.theme_dark_btn.setStyleSheet("background-color: #0078d4; color: white;" if theme == Theme.DARK else "")
        self.theme_system_btn.setStyleSheet("background-color: #0078d4; color: white;" if theme == Theme.SYSTEM else "")
        # Apply theme to app
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.theme_service.get_stylesheet())
        # Reapply to this window
        self.setStyleSheet(self.theme_service.get_stylesheet())

    def _set_window_icon(self):
        """Set the application window icon"""
        from PyQt6.QtGui import QIcon
        icon_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "assets", 
            "app_icon.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _save_filter_settings(self):
        """Save current filter settings to database"""
        settings = {
            'search_text': self.search_box.text(),
            'favorites_only': self.favorites_checkbox.isChecked(),
            'max_ping': self.max_ping.value(),
            'hide_empty': self.hide_empty_checkbox.isChecked(),
            'hide_full': self.hide_full_checkbox.isChecked(),
            'region': self.region_filter.currentText(),
        }
        self.db.save_filter_settings(settings)

    def _load_filter_settings(self):
        """Load and apply saved filter settings from database"""
        settings = self.db.load_filter_settings()
        if settings:
            # Apply saved values to UI controls
            self.search_box.setText(settings.get('search_text', ''))
            self.favorites_checkbox.setChecked(settings.get('favorites_only', False))
            self.max_ping.setValue(settings.get('max_ping', 300))
            self.hide_empty_checkbox.setChecked(settings.get('hide_empty', False))
            self.hide_full_checkbox.setChecked(settings.get('hide_full', False))
            
            region = settings.get('region', 'All Regions')
            index = self.region_filter.findText(region)
            if index >= 0:
                self.region_filter.setCurrentIndex(index)

    def _on_filter_changed(self):
        """Called when any filter changes - saves settings and filters servers"""
        self._save_filter_settings()
        self.filter_servers()

    def init_ui(self):
        """Initialize UI components"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        
        # Apply initial theme
        self.setStyleSheet(self.theme_service.get_stylesheet())
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Search box
        header_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search servers by name...")
        self.search_box.textChanged.connect(self._on_filter_changed)
        self.search_box.setMaximumWidth(200)
        # Add built-in clear button (X)
        self.search_box.setClearButtonEnabled(True)
        header_layout.addWidget(self.search_box)
        
        header_layout.addStretch()
        
        # Theme selector (right side)
        header_layout.addWidget(QLabel("Theme:"))
        self.theme_light_btn = QPushButton("Light")
        self.theme_light_btn.setMaximumWidth(70)
        self.theme_light_btn.clicked.connect(lambda: self._set_theme(Theme.LIGHT))
        header_layout.addWidget(self.theme_light_btn)
        
        self.theme_dark_btn = QPushButton("Dark")
        self.theme_dark_btn.setMaximumWidth(70)
        self.theme_dark_btn.clicked.connect(lambda: self._set_theme(Theme.DARK))
        header_layout.addWidget(self.theme_dark_btn)
        
        self.theme_system_btn = QPushButton("System")
        self.theme_system_btn.setMaximumWidth(70)
        self.theme_system_btn.clicked.connect(lambda: self._set_theme(Theme.SYSTEM))
        header_layout.addWidget(self.theme_system_btn)
        
        # Update button state to show current theme
        current = self.theme_service.current_theme
        self.theme_light_btn.setStyleSheet("background-color: #0078d4; color: white;" if current == Theme.LIGHT else "")
        self.theme_dark_btn.setStyleSheet("background-color: #0078d4; color: white;" if current == Theme.DARK else "")
        self.theme_system_btn.setStyleSheet("background-color: #0078d4; color: white;" if current == Theme.SYSTEM else "")
        

        layout.addLayout(header_layout)
        
        # Filters section - Top row with favorites, ping, players, and auto-refresh
        filter_layout = QHBoxLayout()
        
        # "Filters:" label on the left
        filter_layout.addWidget(QLabel("Filters:"))
        filter_layout.addSpacing(10)
        
        self.favorites_checkbox = CustomCheckBox("Favorites Only")
        self.favorites_checkbox.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.favorites_checkbox)
        
        filter_layout.addSpacing(15)
        
        # Max ping filter
        filter_layout.addWidget(QLabel("Max Ping (ms):"))
        self.max_ping = QSpinBox()
        self.max_ping.setMinimum(0)
        self.max_ping.setMaximum(10000)
        self.max_ping.setValue(300)
        self.max_ping.setMaximumWidth(60)
        self.max_ping.valueChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.max_ping)
        
        filter_layout.addSpacing(15)
        
        # Players filter - checkboxes instead of range
        self.hide_empty_checkbox = CustomCheckBox("Hide Empty")
        self.hide_empty_checkbox.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.hide_empty_checkbox)
        
        self.hide_full_checkbox = CustomCheckBox("Hide Full")
        self.hide_full_checkbox.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.hide_full_checkbox)
        
        filter_layout.addSpacing(15)
        
        # Region filter
        filter_layout.addWidget(QLabel("Region:"))
        self.region_filter = QComboBox()
        self.region_filter.addItem("All Regions")
        self.region_filter.addItem("North America")
        self.region_filter.addItem("South America")
        self.region_filter.addItem("Europe")
        self.region_filter.addItem("Middle East")
        self.region_filter.addItem("Asia")
        self.region_filter.addItem("Oceania")
        self.region_filter.addItem("Africa")
        self.region_filter.setToolTip("Country and region data is provided by BattleMetrics using GeoIP. Accuracy is not guaranteed.")
        self.region_filter.setMaximumWidth(140)
        self.region_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.region_filter)
        
        # Add stretch to push refresh controls to the right
        filter_layout.addStretch()
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        filter_layout.addWidget(separator)
        
        filter_layout.addSpacing(10)
        
        # Refresh button on the right
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_servers)
        self.refresh_btn.setMaximumWidth(90)
        filter_layout.addWidget(self.refresh_btn)
        
        filter_layout.addSpacing(10)
        
        # Auto-refresh controls - grouped together with minimal spacing
        self.auto_refresh_checkbox = SpinningCheckBox("Auto")
        self.auto_refresh_checkbox.stateChanged.connect(self.toggle_auto_refresh)
        filter_layout.addWidget(self.auto_refresh_checkbox)
        
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setMinimum(5)
        self.refresh_interval.setMaximum(300)
        self.refresh_interval.setValue(30)
        self.refresh_interval.setMaximumWidth(60)
        filter_layout.addWidget(self.refresh_interval, 0)
        
        filter_layout.addWidget(QLabel("s"), 0)
        
        layout.addLayout(filter_layout)
        
        # Server table
        self.table = NumericSortTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "★", "Server Name", "Players", "Ping (ms)", "Region", "IP:Port", "History"
        ])
        
        # Set column widths
        # Column 0 (★): Fixed width just for the star
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(0, self.table.horizontalHeader().ResizeMode.Fixed)
        
        # Column 1 (Server Name): Resizable, stretch to fill available space
        self.table.setColumnWidth(1, 350)
        self.table.horizontalHeader().setSectionResizeMode(1, self.table.horizontalHeader().ResizeMode.Stretch)
        
        # Column 2 (Players): Fixed width for "XXX/XXX" format
        self.table.setColumnWidth(2, 80)
        self.table.horizontalHeader().setSectionResizeMode(2, self.table.horizontalHeader().ResizeMode.Fixed)
        
        # Column 3 (Ping): Fixed width for "XXXX ms" format
        self.table.setColumnWidth(3, 85)
        self.table.horizontalHeader().setSectionResizeMode(3, self.table.horizontalHeader().ResizeMode.Fixed)
        # Set custom delegate for ping column to preserve colors during selection
        self.ping_delegate = PingItemDelegate()
        self.table.setItemDelegateForColumn(3, self.ping_delegate)
        
        # Column 4 (Region): Fixed width for region display
        self.table.setColumnWidth(4, 140)
        self.table.horizontalHeader().setSectionResizeMode(4, self.table.horizontalHeader().ResizeMode.Fixed)
        # Add tooltip to Region column header
        region_header = self.table.horizontalHeaderItem(4)
        if region_header:
            region_header.setToolTip("Country and region data is provided by BattleMetrics using GeoIP. Accuracy is not guaranteed.")
        
        # Column 5 (IP:Port): Resizable to fit IP addresses properly
        self.table.setColumnWidth(5, 140)
        self.table.horizontalHeader().setSectionResizeMode(5, self.table.horizontalHeader().ResizeMode.ResizeToContents)
        
        # Column 6 (History): Resizable for ping history stats
        self.table.setColumnWidth(6, 350)
        self.table.horizontalHeader().setSectionResizeMode(6, self.table.horizontalHeader().ResizeMode.ResizeToContents)
        
        # Connect header resize signal to save column widths
        self.table.horizontalHeader().sectionResized.connect(self._save_column_widths)
        
        # Hide vertical header (row numbers) to prevent size changes from scrollbar
        self.table.verticalHeader().setVisible(False)
        
        # Disable Qt's built-in sorting - we handle sorting manually
        self.table.setSortingEnabled(False)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)  # Disable cell editing
        self.table.horizontalHeader().sectionClicked.connect(self._on_table_sort)
        self.table.doubleClicked.connect(self._on_table_double_click)
        self.table_sort_column = 1  # Default sort by server name
        self.table_sort_order = Qt.SortOrder.AscendingOrder
        layout.addWidget(self.table)
        
        # Load saved column widths
        self._load_column_widths()
        
        # Update header styling to bold the default sort column
        self._update_header_styling()
        
        main_widget.setLayout(layout)
        
        # Status bar with proper layout for message, credit, and counters
        # Left: Temporary status messages
        self.status_message = QLabel("")
        self.status_message.setStyleSheet("font-size: 9px;")
        self.statusBar().addWidget(self.status_message, 1)
        
        # Center: BattleMetrics credit - bold and prominent
        credit_label = QLabel("Data Source: BattleMetrics ©")
        credit_label.setStyleSheet("font-weight: bold; font-size: 10px; color: #0078d4;")
        self.statusBar().addWidget(credit_label)
        
        # Right: Server/player counters
        self.servers_counter = QLabel("Servers: 0")
        self.servers_counter.setStyleSheet("font-weight: bold; font-size: 10px; margin-right: 5px;")
        self.statusBar().addPermanentWidget(self.servers_counter)
        
        self.players_counter = QLabel("Players: 0")
        self.players_counter.setStyleSheet("font-weight: bold; font-size: 10px; margin-right: 10px;")
        self.statusBar().addPermanentWidget(self.players_counter)

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_servers)
        
        # Load saved filter settings
        self._load_filter_settings()

    def _load_column_widths(self):
        """Load saved column widths from database"""
        import json
        try:
            # Try to load from a simple config - for now, just use defaults
            # In future could store in database
            pass
        except Exception:
            pass

    def _save_column_widths(self):
        """Save column widths to database for next session"""
        import json
        try:
            # Get current column widths
            widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]
            # Save to a simple JSON file for now
            import os
            config_dir = os.path.expanduser("~/.scum_tracker")
            os.makedirs(config_dir, exist_ok=True)
            with open(os.path.join(config_dir, "column_widths.json"), "w") as f:
                json.dump({"widths": widths}, f)
        except Exception as e:
            print(f"Error saving column widths: {e}")

    def _get_local_scum_version(self) -> str:
        """Get the local SCUM version installed on Steam"""
        try:
            if platform.system() == "Windows":
                # Common Steam library paths on Windows
                steam_paths = [
                    os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steamapps\common\SCUM"),
                    os.path.expandvars(r"%ProgramFiles%\Steam\steamapps\common\SCUM"),
                    os.path.expandvars(r"%UserProfile%\Desktop\steamcmd\steamapps\common\SCUM"),
                    "/mnt/ct2000/SteamLibrary/steamapps/common/SCUM",  # Custom mount
                ]
            else:
                # Common Steam library paths on Linux/Mac
                steam_paths = [
                    os.path.expanduser("~/.steam/steamapps/common/SCUM"),
                    os.path.expanduser("~/Steam/steamapps/common/SCUM"),
                    os.path.expanduser("~/.var/app/com.valvesoftware.Steam/data/Steam/steamapps/common/SCUM"),
                    "/mnt/ct2000/SteamLibrary/steamapps/common/SCUM",  # Custom mount
                ]
            
            # Also try to get Steam build ID from manifest to correlate with known versions
            steam_build_id = self._get_steam_build_id()
            
            for steam_path in steam_paths:
                if not os.path.exists(steam_path):
                    continue
                    
                # Try reading version.txt first (most reliable)
                version_file = os.path.join(steam_path, "version.txt")
                if os.path.exists(version_file):
                    try:
                        with open(version_file, "r") as f:
                            version = f.read().strip()
                            if version:
                                return version
                    except:
                        pass
                
                # Try checking SCUM subdirectory
                scum_subdir = os.path.join(steam_path, "SCUM")
                if os.path.exists(scum_subdir):
                    version_file = os.path.join(scum_subdir, "version.txt")
                    if os.path.exists(version_file):
                        try:
                            with open(version_file, "r") as f:
                                version = f.read().strip()
                                if version:
                                    return version
                        except:
                            pass
                
                # Windows: Try reading from game exe properties
                if platform.system() == "Windows":
                    exe_path = os.path.join(steam_path, "SCUM-Win64-Shipping.exe")
                    if os.path.exists(exe_path):
                        try:
                            output = subprocess.check_output(
                                ['powershell', '-Command', f'(Get-Item "{exe_path}").VersionInfo.ProductVersion'],
                                stderr=subprocess.DEVNULL
                            ).decode().strip()
                            if output:
                                return output
                        except:
                            pass
                    
                    # Also try the default UE4 game exe path
                    exe_path = os.path.join(steam_path, "SCUM", "Binaries", "Win64", "SCUM.exe")
                    if os.path.exists(exe_path):
                        try:
                            output = subprocess.check_output(
                                ['powershell', '-Command', f'(Get-Item "{exe_path}").VersionInfo.ProductVersion'],
                                stderr=subprocess.DEVNULL
                            ).decode().strip()
                            if output:
                                return output
                        except:
                            pass
                
                # Linux: Try reading from executable or version metadata
                elif platform.system() == "Linux":
                    # Try to find Linux executable
                    possible_exes = [
                        os.path.join(steam_path, "SCUM-Linux-Shipping"),
                        os.path.join(steam_path, "SCUM-Linux-Shipping.exe"),
                        os.path.join(scum_subdir, "Binaries", "Linux", "SCUM-Linux-Shipping"),
                        os.path.join(steam_path, "run"),
                        os.path.join(steam_path, "start.sh"),
                    ]
                    
                    for exe_path in possible_exes:
                        if os.path.exists(exe_path):
                            try:
                                # Try to extract version from file metadata or strings
                                result = subprocess.check_output(
                                    ['strings', exe_path],
                                    stderr=subprocess.DEVNULL
                                ).decode()
                                # Look for version patterns like "0.12.345" or "1.2.3.4"
                                import re
                                versions = re.findall(r'\b\d+\.\d+(?:\.\d+)*\b', result)
                                # Filter for reasonable version numbers
                                if versions:
                                    # Return the first reasonable looking version
                                    return versions[0]
                            except:
                                pass
                    
                    # Try checking Proton/Wine config for version info
                    drive_c = os.path.join(steam_path, "..", "..", "drive_c", "Program Files (x86)", "SCUM")
                    if os.path.exists(drive_c):
                        version_file = os.path.join(drive_c, "version.txt")
                        if os.path.exists(version_file):
                            try:
                                with open(version_file, "r") as f:
                                    version = f.read().strip()
                                    if version:
                                        return version
                            except:
                                pass
            
            # Fall back to correlating Steam build ID if found
            if steam_build_id:
                version = self._correlate_steam_build_to_version(steam_build_id)
                if version:
                    return version
            
            return "Unknown"
        except Exception as e:
            print(f"Error detecting local SCUM version: {e}")
            return "Unknown"
    
    def _get_steam_build_id(self) -> str:
        """Get the Steam build ID from app manifest"""
        try:
            import re
            # Check common Steam library locations
            manifest_paths = [
                os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steamapps\appmanifest_513710.acf"),
                os.path.expandvars(r"%ProgramFiles%\Steam\steamapps\appmanifest_513710.acf"),
                "/mnt/ct2000/SteamLibrary/steamapps/appmanifest_513710.acf",
                os.path.expanduser("~/.steam/steamapps/appmanifest_513710.acf"),
                os.path.expanduser("~/Steam/steamapps/appmanifest_513710.acf"),
            ]
            
            for manifest_path in manifest_paths:
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r') as f:
                        content = f.read()
                        match = re.search(r'"buildid"\s*"(\d+)"', content)
                        if match:
                            return match.group(1)
        except:
            pass
        return None
    
    def _correlate_steam_build_to_version(self, build_id: str) -> str:
        """Correlate Steam build ID to known SCUM versions"""
        # Known correlations (can be expanded as we discover more)
        # Build ID 21005454 = Stable 1.1.0.5.101995 (as of Dec 2025)
        build_correlations = {
            "21005454": "1.1.0.5.101995",  # Current stable
        }
        
        if build_id in build_correlations:
            return build_correlations[build_id]
        
        # If we don't have an exact match, return the build ID for reference
        return f"Build {build_id}"

    def load_servers(self):
        """Load servers from BattleMetrics"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Loading...")
        self.status_message.setText("Fetching servers from BattleMetrics...")
        
        self.fetch_worker = ServerFetchWorker(self.db)
        self.fetch_worker.servers_fetched.connect(self._update_servers, Qt.ConnectionType.QueuedConnection)
        self.fetch_worker.start()

    def _update_servers(self, servers: List[GameServer]):
        """Update servers list and ping them"""
        self.servers = servers
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh")
        self.status_message.setText(f"Loaded {len(servers)} servers | Pinging...")
        
        self.filter_servers()
        self._start_pinging()

    def _populate_country_filters(self):
        """Populate region filter checkboxes - disabled since region selector removed"""
        pass
    
    def _start_pinging(self):
        """Start pinging all servers in batches"""
        # Adjust batch size based on OS - Windows benefits from smaller batches
        import platform
        batch_size = 8 if platform.system() == 'Windows' else 10
        
        # Ping servers in batches to avoid overwhelming the system
        self.total_pings = len(self.servers)
        self.pings_completed = 0
        self._ping_batch(0, batch_size)
        
        # Don't use periodic updates - just wait for all pings to complete then rebuild table once

    def _ping_batch(self, start_idx: int, batch_size: int):
        """Ping a batch of servers"""
        end_idx = min(start_idx + batch_size, len(self.servers))
        
        # Clean up completed workers before starting new batch (helps on Windows)
        self.ping_workers = [w for w in self.ping_workers if w.isRunning()]
        
        for i in range(start_idx, end_idx):
            server = self.servers[i]
            worker = PingWorker(server)
            worker.ping_completed.connect(self._on_ping_completed, Qt.ConnectionType.QueuedConnection)
            worker.start()
            self.ping_workers.append(worker)
        
        # Schedule next batch after a short delay if there are more servers
        # Longer delay on Windows for better stability
        import platform
        delay = 150 if platform.system() == 'Windows' else 100
        
        if end_idx < len(self.servers):
            QTimer.singleShot(delay, lambda: self._ping_batch(end_idx, batch_size))

    def _on_ping_completed(self, server_id: str, latency: int, success: bool):
        """Handle ping completion"""
        for server in self.servers:
            if server.id == server_id:
                server.latency = latency
                server.last_ping_time = datetime.now()
                
                # Store in database
                record = PingRecord(
                    server_id=server_id,
                    latency=latency,
                    success=success
                )
                self.db.add_ping_record(record)
                break
        
        self.pings_completed += 1
        
        # Re-enable refresh button and stop periodic updates when all pings are done
        if self.pings_completed >= self.total_pings:
            self.display_update_timer.stop()
            self.filter_servers()  # Final update
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("Refresh")
            self.status_message.setText(f"Loaded {len(self.servers)} servers")

    def _update_displayed_pings(self):
        """Update ping values in the table without rebuilding it (for periodic updates during pinging)"""
        # This updates ping cells in place without changing the table structure or selection
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            if not name_item:
                continue
            
            # Find the corresponding server by name
            server_name = name_item.text()
            server = None
            for s in self.servers:
                if s.name == server_name:
                    server = s
                    break
            
            if not server:
                continue
            
            # Update ping column (column 3)
            if server.latency is not None and server.latency > 0:
                ping_text = f"{server.latency}ms"
                ping_color = QColor("green") if server.latency < 100 else QColor("orange") if server.latency < 200 else QColor("red")
            else:
                ping_text = "N/A"
                ping_color = QColor("black")
            
            ping_item = self.table.item(row, 3)
            if ping_item:
                ping_item.setText(ping_text)
                ping_item.setForeground(ping_color)

    def _on_display_ready(self, servers: List[GameServer]):
        """Handle filtered/sorted servers from worker thread"""
        self.display_worker = None
        self.display_servers(servers)

    def _on_table_sort(self, column: int):
        """Handle table column sorting"""
        if self.table_sort_column == column:
            # Toggle sort order if clicking same column
            self.table_sort_order = Qt.SortOrder.DescendingOrder if self.table_sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            # New column, sort ascending
            self.table_sort_column = column
            self.table_sort_order = Qt.SortOrder.AscendingOrder
        
        # Update header styling to show current sort column
        self._update_header_styling()
        
        # Re-display with new sort order
        self.filter_servers()
    
    def _update_header_styling(self):
        """Bold the header of the current sort column"""
        for col in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(col)
            if item:
                font = item.font()
                font.setBold(col == self.table_sort_column)
                item.setFont(font)

    def filter_servers(self):
        """Filter servers asynchronously"""
        # Start display worker thread
        if self.display_worker:
            return  # Already running
        
        self.display_worker = DisplayWorker(
            self.servers,
            self.search_box.text().lower(),
            self.favorites_checkbox.isChecked(),
            self.region_filter.currentText(),
            self.max_ping.value(),
            self.hide_empty_checkbox.isChecked(),
            self.hide_full_checkbox.isChecked(),
            self.table_sort_column,
            self.table_sort_order,
            self.db
        )
        self.display_worker.display_ready.connect(self._on_display_ready, Qt.ConnectionType.QueuedConnection)
        self.display_worker.start()

    def display_servers(self, servers: List[GameServer]):
        """Display servers in table"""
        # Load all ping history stats at once (much faster than per-server queries)
        history_stats = self.db.get_all_ping_history_stats()
        
        # Sort servers based on current sort column and order
        sort_reverse = self.table_sort_order == Qt.SortOrder.DescendingOrder
        
        if self.table_sort_column == 0:  # Star (favorites) - not sortable, keep current order
            pass
        elif self.table_sort_column == 1:  # Server Name
            servers = sorted(servers, key=lambda s: s.name.lower(), reverse=sort_reverse)
        elif self.table_sort_column == 2:  # Players
            servers = sorted(servers, key=lambda s: s.players, reverse=sort_reverse)
        elif self.table_sort_column == 3:  # Ping
            servers = sorted(servers, key=lambda s: s.latency if s.latency else 999999, reverse=sort_reverse)
        elif self.table_sort_column == 4:  # IP:Port - not sortable
            pass
        elif self.table_sort_column == 5:  # Actions - not sortable
            pass
        
        # Keep favorites on top - separate and recombine
        favorites = [s for s in servers if s.is_favorite]
        non_favorites = [s for s in servers if not s.is_favorite]
        servers = favorites + non_favorites
        
        # Store SORTED servers for later reference (e.g., double-click handler)
        self.displayed_servers = servers
        
        # Clear all existing rows first
        self.table.setRowCount(0)
        
        # Show empty state message if no servers match filters
        if not servers:
            self.table.setRowCount(1)
            empty_cell = QTableWidgetItem("No servers found. Try adjusting your search terms or filter settings.")
            empty_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_font = empty_cell.font()
            empty_font.setItalic(True)
            empty_cell.setFont(empty_font)
            self.table.setItem(0, 0, empty_cell)
            self.table.setSpan(0, 0, 1, 9)  # Span across all columns
            self.servers_counter.setText("Servers: 0")
            self.players_counter.setText("Players: 0")
            return
        
        self.table.setRowCount(len(servers))
        
        for row, server in enumerate(servers):
            try:
                # Star button
                star_btn = QPushButton("★" if server.is_favorite else "☆")
                star_btn.clicked.connect(self._make_favorite_callback(server.id))
                if server.is_favorite:
                    # Use darker color for light theme, gold for dark theme
                    bg_color = self.palette().color(self.backgroundRole())
                    if bg_color.lightness() > 128:  # Light theme
                        star_btn.setStyleSheet("color: #CC8800; font-weight: bold;")
                    else:  # Dark theme
                        star_btn.setStyleSheet("color: gold;")
                self.table.setCellWidget(row, 0, star_btn)
                
                # Server name
                name_item = QTableWidgetItem(server.name)
                self.table.setItem(row, 1, name_item)
                
                # Players - use custom numeric item for proper sorting
                players_item = NumericTableItem(f"{server.players}/{server.max_players}", server.players)
                self.table.setItem(row, 2, players_item)
                
                # Ping - use custom numeric item for proper sorting
                if server.latency is not None and server.latency > 0:
                    ping_item = NumericTableItem(f"{server.latency}ms", server.latency)
                    font = ping_item.font()
                    font.setBold(True)
                    ping_item.setFont(font)
                    if server.latency < 100:
                        ping_item.setForeground(QColor("#00AA00"))  # Bright green
                        ping_item.setBackground(QColor(0, 170, 0, 30))  # Light green background
                    elif server.latency < 200:
                        ping_item.setForeground(QColor("#FF9900"))  # Orange
                        ping_item.setBackground(QColor(255, 153, 0, 30))  # Light orange background
                    else:
                        ping_item.setForeground(QColor("#FF0000"))  # Red
                        ping_item.setBackground(QColor(255, 0, 0, 30))  # Light red background
                else:
                    ping_item = NumericTableItem("N/A", 999999)
                self.table.setItem(row, 3, ping_item)
                
                # Region - Show region continent and country code together
                region_text = f"{server.region}"
                if server.region in COUNTRY_TO_CONTINENT:
                    continent = COUNTRY_TO_CONTINENT[server.region]
                    region_text = f"{continent}: {server.region}"
                region_item = QTableWidgetItem(region_text)
                self.table.setItem(row, 4, region_item)
                
                # IP:Port
                ip_item = QTableWidgetItem(f"{server.ip}:{server.port}")
                self.table.setItem(row, 5, ip_item)
                
                # History - Show ping history stats (clickable to see full graph)
                history_widget = self._create_history_widget_from_stats(server.id, server.name, history_stats.get(server.id))
                self.table.setCellWidget(row, 6, history_widget)
            except Exception as e:
                print(f"Error populating row {row}: {e}")
                import traceback
                traceback.print_exc()
        
        # Update counters in bottom right
        total_servers = self.table.rowCount()
        total_players = sum(server.players for server in servers)
        self.servers_counter.setText(f"Servers: {total_servers}")
        self.players_counter.setText(f"Players: {total_players}")

    def toggle_favorite(self, server_id: str):
        """Toggle favorite status for a server"""
        for server in self.servers:
            if server.id == server_id:
                if server.is_favorite:
                    self.db.remove_favorite(server_id)
                    server.is_favorite = False
                else:
                    self.db.add_favorite(server_id, server.name)
                    server.is_favorite = True
                break
        
        self.filter_servers()

    def _make_ping_callback(self, server: GameServer):
        """Create a callback for the ping button that captures the correct server"""
        def callback():
            self.ping_single_server(server)
        return callback

    def _create_history_widget(self, server_id: str, server_name: str) -> QWidget:
        """Create a clickable history preview widget for a server (uses database query)"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        history = self.db.get_ping_history(server_id)
        
        if history:
            # Extract latency values (filter out failed pings)
            latencies = [record.latency for record in history if record.latency > 0]
            
            if latencies:
                # Create simple text preview with color coding
                min_lat = min(latencies)
                max_lat = max(latencies)
                avg_lat = sum(latencies) / len(latencies)
                
                # Helper function to get color based on latency
                def get_color_hex(lat):
                    if lat < 100:
                        return "#00AA00"  # Green
                    elif lat < 200:
                        return "#FF9900"  # Orange
                    else:
                        return "#FF0000"  # Red
                
                # Create HTML with color-coded values (only on the numbers)
                preview_html = f'Min: <span style="color: {get_color_hex(min_lat)}; font-weight: bold;">{min_lat}ms</span>  ' \
                              f'Max: <span style="color: {get_color_hex(max_lat)}; font-weight: bold;">{max_lat}ms</span>  ' \
                              f'Avg: <span style="color: {get_color_hex(avg_lat)}; font-weight: bold;">{avg_lat:.0f}ms</span>'
                
                label = QLabel(preview_html)
                label.setStyleSheet("font-size: 8px; padding: 1px;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setCursor(Qt.CursorShape.PointingHandCursor)
                label.mousePressEvent = lambda e: self.show_history(server_id, server_name)
                layout.addWidget(label)
            else:
                label = QLabel("No data")
                label.setStyleSheet("font-size: 8px; padding: 1px;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
        else:
            label = QLabel("No history")
            label.setStyleSheet("font-size: 8px; padding: 1px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        
        widget.setLayout(layout)
        return widget

    def _create_history_widget_from_stats(self, server_id: str, server_name: str, stats: dict) -> QWidget:
        """Create a clickable history preview widget using cached stats (fast)"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        if stats:
            min_lat = stats['min']
            max_lat = stats['max']
            avg_lat = stats['avg']
            
            # Helper function to get color based on latency
            def get_color_hex(lat):
                if lat < 100:
                    return "#00AA00"  # Green
                elif lat < 200:
                    return "#FF9900"  # Orange
                else:
                    return "#FF0000"  # Red
            
            # Create HTML with color-coded values (only on the numbers)
            preview_html = f'Min: <span style="color: {get_color_hex(min_lat)}; font-weight: bold;">{min_lat}ms</span>  ' \
                          f'Max: <span style="color: {get_color_hex(max_lat)}; font-weight: bold;">{max_lat}ms</span>  ' \
                          f'Avg: <span style="color: {get_color_hex(avg_lat)}; font-weight: bold;">{avg_lat:.0f}ms</span>'
            
            label = QLabel(preview_html)
            label.setStyleSheet("font-size: 8px; padding: 1px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.mousePressEvent = lambda e: self.show_history(server_id, server_name)
            layout.addWidget(label)
        else:
            label = QLabel("No data")
            label.setStyleSheet("font-size: 8px; padding: 1px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        
        widget.setLayout(layout)
        return widget

    def _make_history_callback(self, server: GameServer):
        """Create a callback for the history button that captures the correct server"""
        def callback():
            self.show_history(server.id, server.name)
        return callback

    def _make_favorite_callback(self, server_id: str):
        """Create a callback for the favorite button that captures the correct server ID"""
        def callback():
            self.toggle_favorite(server_id)
        return callback

    def ping_single_server(self, server: GameServer):
        """Ping a single server"""
        result = PingService.ping_server(server.ip, server.port)
        server.latency = result.latency if result.latency > 0 else 0
        
        record = PingRecord(
            server_id=server.id,
            latency=server.latency,
            success=result.success
        )
        self.db.add_ping_record(record)
        self.filter_servers()

    def show_history(self, server_id: str, server_name: str):
        """Show ping history for a server as a line graph"""
        history = self.db.get_ping_history(server_id)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ping History - {server_name}")
        dialog.setGeometry(200, 200, 700, 500)
        
        layout = QVBoxLayout()
        
        try:
            if history:
                # Extract latency values and timestamps (filter out failed pings)
                timestamps = []
                latencies = []
                for record in history:
                    if record.latency > 0:
                        timestamps.append(record.timestamp)
                        latencies.append(record.latency)
                
                if latencies:
                    # Create figure and plot line graph
                    fig = Figure(figsize=(8, 5), dpi=100)
                    ax = fig.add_subplot(111)
                    
                    # Get theme colors based on current theme
                    if self.theme_service.current_theme == Theme.LIGHT:
                        is_dark = False
                    elif self.theme_service.current_theme == Theme.DARK:
                        is_dark = True
                    else:  # SYSTEM
                        try:
                            import darkdetect
                            is_dark = darkdetect.isDark()
                        except Exception:
                            is_dark = False
                    
                    # Set figure and axes background colors based on theme
                    if is_dark:
                        fig_bg_color = '#1e1e1e'
                        ax_bg_color = '#2d2d2d'
                        text_color = '#e0e0e0'
                        line_color = '#4ab8f0'  # Light blue for dark theme
                    else:
                        fig_bg_color = 'white'
                        ax_bg_color = '#f9f9f9'
                        text_color = '#000000'
                        line_color = '#0078d4'  # Dark blue for light theme
                    
                    fig.patch.set_facecolor(fig_bg_color)
                    ax.set_facecolor(ax_bg_color)
                    
                    # Apply moving average to smooth the data
                    window_size = max(5, len(latencies) // 20)  # Adaptive window size
                    averaged_latencies = []
                    for i in range(len(latencies)):
                        start = max(0, i - window_size // 2)
                        end = min(len(latencies), i + window_size // 2 + 1)
                        avg = sum(latencies[start:end]) / (end - start)
                        averaged_latencies.append(avg)
                    
                    x = np.arange(len(averaged_latencies))
                    y = np.array(averaged_latencies)
                    
                    # Create spline with smoothing on the averaged data (requires at least k+1 points)
                    if len(averaged_latencies) >= 4:
                        # Use cubic spline for smooth curve (k=3)
                        spl = make_interp_spline(x, y, k=3)
                        x_smooth = np.linspace(x.min(), x.max(), 300)
                        y_smooth = spl(x_smooth)
                        ax.plot(x_smooth, y_smooth, linestyle='-', linewidth=2, color=line_color)
                    elif len(averaged_latencies) >= 3:
                        # Use quadratic spline for fewer points (k=2)
                        spl = make_interp_spline(x, y, k=2)
                        x_smooth = np.linspace(x.min(), x.max(), 100)
                        y_smooth = spl(x_smooth)
                        ax.plot(x_smooth, y_smooth, linestyle='-', linewidth=2, color=line_color)
                    else:
                        # For 1-2 points, just plot raw data with markers
                        ax.plot(x, y, marker='o', linestyle='-', linewidth=2, markersize=8, color=line_color)
                    
                    # Normalize y-axis so small variations don't create drastic jumps
                    min_latency = min(latencies)
                    max_latency = max(latencies)
                    latency_range = max_latency - min_latency
                    # Add 20% padding on both sides for better visualization
                    padding = max(latency_range * 0.2, 5)  # At least 5ms padding
                    ax.set_ylim(min_latency - padding, max_latency + padding)
                    
                    # Add labels and title with theme colors
                    ax.set_xlabel('Time (samples)', fontsize=11, color=text_color)
                    ax.set_ylabel('Latency (ms)', fontsize=11, color=text_color)
                    ax.set_title('Ping Latency Over Time', fontsize=12, fontweight='bold', color=text_color)
                    ax.grid(True, alpha=0.3, color=text_color)
                    
                    # Style axis ticks and spines
                    ax.tick_params(colors=text_color)
                    for spine in ax.spines.values():
                        spine.set_edgecolor(text_color)
                    
                    fig.tight_layout()
                    
                    # Embed matplotlib figure in PyQt6
                    canvas = FigureCanvas(fig)
                    layout.addWidget(canvas)
                else:
                    text_edit = QTextEdit()
                    text_edit.setReadOnly(True)
                    text_edit.setText("No successful ping records available")
                    layout.addWidget(text_edit)
            else:
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                text_edit.setText("No ping history available")
                layout.addWidget(text_edit)
        
        except Exception as e:
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setText(f"Error displaying graph: {str(e)}\n\nPlease check if matplotlib is properly installed.")
            layout.addWidget(text_edit)
        
        dialog.setLayout(layout)
        dialog.exec()

    def toggle_auto_refresh(self, state):
        """Toggle auto-refresh based on checkbox state"""
        if state == 2:  # Checked state from SpinningCheckBox
            interval = self.refresh_interval.value() * 1000  # Convert to ms
            self.refresh_timer.start(interval)
            self.auto_refresh_checkbox.start_spin()
        else:  # Unchecked
            self.refresh_timer.stop()
            self.auto_refresh_checkbox.stop_spin()

    def _on_table_double_click(self):
        """Handle double-click on table row - show instructions and offer to launch SCUM"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        
        # Get server from displayed servers (filtered list)
        if current_row < len(self.displayed_servers):
            server = self.displayed_servers[current_row]
            server_info = f"{server.ip}:{server.port}"
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(server_info)
            
            # Create custom dialog with screenshot
            dialog = QDialog(self)
            dialog.setWindowTitle("Connect to Server")
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(6)
            
            # Header: Server name
            title_label = QLabel(f"<b>{server.name}</b>")
            title_font = QFont()
            title_font.setPointSize(12)
            title_font.setWeight(700)
            title_label.setFont(title_font)
            title_label.setStyleSheet("margin: 0px; padding: 0px; line-height: 1.2;")
            main_layout.addWidget(title_label)
            
            # Sub-header: Address
            address_label = QLabel(f"<b>Address:</b> <span style='color: #2196F3; font-family: monospace;'>{server_info}</span> (copied to clipboard)")
            address_font = QFont()
            address_font.setPointSize(10)
            address_label.setFont(address_font)
            address_label.setStyleSheet("margin: 0px; padding: 0px; line-height: 1.2;")
            main_layout.addWidget(address_label)
            
            # Content row: Instructions on left, image on right
            content_layout = QHBoxLayout()
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(10)
            
            # Instructions (left side)
            instructions_label = QLabel(
                "<b>STEPS TO JOIN:</b><br>"
                "1. <b>Click 'Launch SCUM'</b> button below<br>"
                "2. <b>Wait</b> for SCUM to load to main menu<br>"
                "3. <b>Click 'MULTI PLAY'</b><br>"
                "4. <b><span style='color: #4CAF50;'>Paste</span></b> the server address (Ctrl+V)<br>"
                "5. <b>Click '<span style='color: #F44336;'>CONNECT</span>'</b>"
            )
            instructions_font = QFont()
            instructions_font.setPointSize(10)
            instructions_label.setFont(instructions_font)
            instructions_label.setStyleSheet("margin: 0px; padding: 0px; line-height: 1.2;")
            instructions_label.setAlignment(Qt.AlignmentFlag.AlignTop)
            content_layout.addWidget(instructions_label, 1)
            
            # Screenshot (right side)
            ui_dir = os.path.dirname(__file__)  # scum_tracker/ui
            assets_path = os.path.join(ui_dir, "..", "assets", "connection_guide.png")
            assets_path = os.path.normpath(assets_path)
            if os.path.exists(assets_path):
                screenshot_label = QLabel()
                screenshot_label.setStyleSheet("margin: 0px; padding: 0px;")
                pixmap = QPixmap(assets_path)
                # Scale to fit nicely in dialog (max 300px width)
                if pixmap.width() > 300:
                    pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
                screenshot_label.setPixmap(pixmap)
                screenshot_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
                content_layout.addWidget(screenshot_label, 0)
            
            main_layout.addLayout(content_layout)
            
            # Buttons (bottom)
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(0, 0, 0, 0)
            launch_btn = QPushButton("Launch SCUM")
            close_btn = QPushButton("Close")
            button_layout.addStretch()
            button_layout.addWidget(launch_btn)
            button_layout.addWidget(close_btn)
            main_layout.addLayout(button_layout)
            
            dialog.setLayout(main_layout)
            dialog.resize(800, 400)
            
            # Connect buttons
            def on_launch():
                self._launch_scum()
                dialog.accept()
                self.statusBar().showMessage(f"✓ SCUM launching... Paste {server_info} in MULTIPLAYER > CONNECT")
            
            launch_btn.clicked.connect(on_launch)
            close_btn.clicked.connect(dialog.reject)
            
            dialog.exec()
    
    def _launch_scum(self):
        """Launch SCUM game via Steam"""
        try:
            if platform.system() == "Linux":
                # Try steam command first
                try:
                    subprocess.Popen(["steam", "steam://run/513710"],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                except FileNotFoundError:
                    # Fallback to xdg-open
                    subprocess.Popen(["xdg-open", "steam://run/513710"],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
            elif platform.system() == "Windows":
                subprocess.Popen("steam://run/513710")
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", "steam://run/513710"])
        except Exception as e:
            self.statusBar().showMessage(f"Error launching SCUM: {e}")

