from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import asyncio
import qasync
from datetime import datetime

class BotStatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        
        # Status indicator
        self.status_led = QLabel()
        self.status_led.setFixedSize(16, 16)
        self.set_status_offline()
        layout.addWidget(self.status_led)
        
        # Status text
        self.status_text = QLabel("Offline")
        layout.addWidget(self.status_text)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def set_status_online(self):
        self.status_led.setStyleSheet("""
            QLabel {
                background-color: #2ecc71;
                border-radius: 8px;
                border: 1px solid #27ae60;
            }
        """)
        self.status_text.setText("Online")
        
    def set_status_offline(self):
        self.status_led.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                border-radius: 8px;
                border: 1px solid #c0392b;
            }
        """)
        self.status_text.setText("Offline")

class BotStatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout()
        
        # Stats labels
        layout.addWidget(QLabel("Uptime:"), 0, 0)
        self.uptime_label = QLabel("00:00:00")
        layout.addWidget(self.uptime_label, 0, 1)
        
        layout.addWidget(QLabel("Messages:"), 1, 0)
        self.message_count = QLabel("0")
        layout.addWidget(self.message_count, 1, 1)
        
        layout.addWidget(QLabel("Last Message:"), 2, 0)
        self.last_message_time = QLabel("Never")
        layout.addWidget(self.last_message_time, 2, 1)
        
        self.setLayout(layout)

class BotControlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.restart_button = QPushButton("Restart")
        
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.restart_button)
        
        self.setLayout(layout)

class BotTab(QWidget):
    def __init__(self, bot, parent=None):
        super().__init__(parent)
        self.bot = bot
        self.setup_ui()
        self.setup_timer()
        self.setup_message_handler()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Top section with status and controls
        top_section = QHBoxLayout()
        
        # Status widget
        self.status_widget = BotStatusWidget()
        top_section.addWidget(self.status_widget)
        
        # Stats widget
        self.stats_widget = BotStatsWidget()
        top_section.addWidget(self.stats_widget)
        
        # Control widget
        self.control_widget = BotControlWidget()
        top_section.addWidget(self.control_widget)
        
        layout.addLayout(top_section)
        
        # Splitter for chat and debug
        splitter = QSplitter(Qt.Vertical)
        
        # Chat output
        chat_group = QGroupBox("Chat")
        chat_layout = QVBoxLayout()
        self.chat_output = QTextEdit()
        self.chat_output.setReadOnly(True)
        chat_layout.addWidget(self.chat_output)
        chat_group.setLayout(chat_layout)
        splitter.addWidget(chat_group)
        
        # Debug output
        debug_group = QGroupBox("Debug")
        debug_layout = QVBoxLayout()
        self.debug_output = QTextEdit()
        self.debug_output.setReadOnly(True)
        debug_layout.addWidget(self.debug_output)
        debug_group.setLayout(debug_layout)
        splitter.addWidget(debug_group)
        
        layout.addWidget(splitter)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter command (cmd:, move:, say:)")
        self.send_button = QPushButton("Send")
        input_layout.addWidget(self.input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.send_button.clicked.connect(self.send_message)
        self.input.returnPressed.connect(self.send_message)
        self.control_widget.start_button.clicked.connect(self.start_bot)
        self.control_widget.stop_button.clicked.connect(self.stop_bot)
        self.control_widget.restart_button.clicked.connect(self.restart_bot)
        
    def setup_timer(self):
        """Setup timer for updating UI elements"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # Update every second
        
    def update_stats(self):
        """Update statistics display"""
        if self.bot.connected:
            self.status_widget.set_status_online()
            
            # Update uptime
            if self.bot.start_time:
                uptime = datetime.now() - self.bot.start_time
                hours = int(uptime.total_seconds() // 3600)
                minutes = int((uptime.total_seconds() % 3600) // 60)
                seconds = int(uptime.total_seconds() % 60)
                self.stats_widget.uptime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update message count
            self.stats_widget.message_count.setText(str(self.bot.message_count))
            
            # Update last message time
            if self.bot.last_message_time:
                self.stats_widget.last_message_time.setText(
                    self.bot.last_message_time.strftime("%H:%M:%S")
                )
        else:
            self.status_widget.set_status_offline()
    
    @qasync.asyncSlot()
    async def send_message(self):
        msg = self.input.text().strip()
        if msg:
            if not msg.startswith(('cmd:', 'move:', 'say:')):
                msg = f'say:{msg}'  # Default to say command
            await self.bot.send_message(msg)
            self.input.clear()
            
    @qasync.asyncSlot()
    async def start_bot(self):
        if not self.bot.connected:
            await self.bot.connect()
            
    @qasync.asyncSlot()
    async def stop_bot(self):
        if self.bot.connected:
            self.bot.disconnect()
            
    @qasync.asyncSlot()
    async def restart_bot(self):
        await self.stop_bot()
        await asyncio.sleep(1)
        await self.start_bot()

    def setup_message_handler(self):
        """Setup message handling for the bot"""
        self.bot.message_handlers = {
            'chat': self.handle_chat_message,
            'debug': self.handle_debug_message
        }
    
    def handle_chat_message(self, message: str):
        """Handle chat messages"""
        self.chat_output.append(message)
        # Auto-scroll to bottom
        scrollbar = self.chat_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def handle_debug_message(self, message: str):
        """Handle debug messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_output.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.debug_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class MainWindow(QMainWindow):
    def __init__(self, bot_manager):
        super().__init__()
        self.bot_manager = bot_manager
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("KiwiBot Manager")
        self.setMinimumSize(800, 600)
        
        # Create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        # Add actions
        reload_action = QAction("Reload Configs", self)
        reload_action.setShortcut("Ctrl+R")
        reload_action.triggered.connect(self.reload_configs)
        file_menu.addAction(reload_action)
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Add tab for each bot
        for bot_name, bot in self.bot_manager.bots.items():
            self.tabs.addTab(BotTab(bot), bot_name)
            
    @qasync.asyncSlot()
    async def reload_configs(self):
        await self.bot_manager.stop_all()
        await self.bot_manager.load_configs()
        # Recreate tabs
        self.tabs.clear()
        for bot_name, bot in self.bot_manager.bots.items():
            self.tabs.addTab(BotTab(bot), bot_name)
        await self.bot_manager.start_all() 