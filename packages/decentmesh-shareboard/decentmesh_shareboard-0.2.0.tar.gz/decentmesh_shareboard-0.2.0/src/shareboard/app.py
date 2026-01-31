"""
Main application window for ShareBoard.

Combines the sidebar and board panels, manages network connection,
and handles all application logic.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QInputDialog, QMessageBox
)

from shareboard.models import Identity, MyIdentity, SharedText
from shareboard.storage import ShareBoardStorage
from shareboard.network import NetworkManager, create_identity
from shareboard.ui.styles import get_stylesheet
from shareboard.ui.sidebar import SidebarPanel
from shareboard.ui.board import BoardPanel


class ShareBoardWindow(QMainWindow):
    """
    Main ShareBoard application window.
    
    Manages the overall application lifecycle including:
    - Identity creation/loading
    - Contact management
    - Network connection
    - Message sending/receiving
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Initialize core components
        self._storage = ShareBoardStorage()
        self._network = NetworkManager()
        self._my_identity: Optional[MyIdentity] = None
        
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._load_data()
        self._start_network()
    
    def _setup_window(self) -> None:
        """Configure main window properties."""
        self.setWindowTitle("ShareBoard")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)
        
        # Apply global stylesheet
        self.setStyleSheet(get_stylesheet())
    
    def _setup_ui(self) -> None:
        """Build the main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout: sidebar + board
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        self._sidebar = SidebarPanel()
        layout.addWidget(self._sidebar)
        
        # Board
        self._board = BoardPanel()
        layout.addWidget(self._board, 1)  # Board takes remaining space
    
    def _connect_signals(self) -> None:
        """Connect all signals and slots."""
        # Sidebar signals
        self._sidebar.contact_added.connect(self._on_contact_added)
        self._sidebar.contact_removed.connect(self._on_contact_removed)
        self._sidebar.contact_toggled.connect(self._on_contact_toggled)
        
        # Board signals
        self._board.share_clicked.connect(self._on_share_clicked)
        
        # Network signals
        self._network.signals.message_received.connect(self._on_message_received)
        self._network.signals.status_changed.connect(self._on_status_changed)
        self._network.signals.connection_ready.connect(self._on_connection_ready)
    
    def _load_data(self) -> None:
        """Load all persisted data."""
        # Load or create identity
        self._my_identity = self._storage.load_my_identity()
        
        if not self._my_identity:
            # First run: create new identity
            self._create_new_identity()
        else:
            self._sidebar.set_my_identity(self._my_identity)
        
        # Load contacts
        contacts = self._storage.load_identities()
        self._sidebar.set_contacts(contacts)
        
        # Load history
        history = self._storage.load_history()
        self._board.set_messages(history)
    
    def _create_new_identity(self) -> None:
        """Create a new identity for first-time users."""
        # Ask for name
        name, ok = QInputDialog.getText(
            self,
            "Welcome to ShareBoard",
            "Enter your display name:",
            text="Anonymous"
        )
        
        if not ok or not name:
            name = "Anonymous"
        
        # Generate keypair
        private_key, public_key = create_identity()
        
        # Create and save identity
        self._my_identity = MyIdentity(
            name=name,
            private_key=private_key,
            public_key=public_key
        )
        self._storage.save_my_identity(self._my_identity)
        
        # Update UI
        self._sidebar.set_my_identity(self._my_identity)
        
        # Show welcome message
        QMessageBox.information(
            self,
            "Identity Created",
            f"Welcome, {name}!\n\n"
            "Your identity has been created. Click 'Copy My Key' to share "
            "your public key with others."
        )
    
    def _start_network(self) -> None:
        """Start the network manager."""
        if self._my_identity:
            self._sidebar.set_status("connecting")
            self._network.start(self._my_identity.private_key)
    
    # ============ Sidebar Handlers ============
    
    def _on_contact_added(self, identity: Identity) -> None:
        """Handle new contact added."""
        self._storage.add_identity(identity)
    
    def _on_contact_removed(self, public_key: str) -> None:
        """Handle contact removed."""
        self._storage.remove_identity(public_key)
    
    def _on_contact_toggled(self, public_key: str, is_active: bool) -> None:
        """Handle contact active state changed."""
        self._storage.update_identity_active(public_key, is_active)
    
    # ============ Board Handlers ============
    
    def _on_share_clicked(self, content: str) -> None:
        """Handle share button clicked."""
        if not self._my_identity:
            return
        
        # Create outgoing message
        message = SharedText.new(
            content=content,
            sender_name=self._my_identity.name,
            sender_key=self._my_identity.public_key,
            is_incoming=False
        )
        
        # Add to board and history
        self._board.add_message(message)
        self._storage.add_to_history(message)
        
        # Send to all active contacts
        contacts = self._storage.load_identities()
        self._network.send_to_all(content, contacts)
    
    # ============ Network Handlers ============
    
    def _on_message_received(self, sender_key: str, content: str, timestamp: float) -> None:
        """Handle incoming message from network."""
        # Look up sender name
        contacts = self._storage.load_identities()
        sender = next((c for c in contacts if c.public_key == sender_key), None)
        sender_name = sender.name if sender else f"Unknown ({sender_key[:8]}...)"
        
        # Create incoming message
        message = SharedText.new(
            content=content,
            sender_name=sender_name,
            sender_key=sender_key,
            is_incoming=True
        )
        
        # Add to board and history
        self._board.add_message(message)
        self._storage.add_to_history(message)
    
    def _on_status_changed(self, status: str) -> None:
        """Handle network status change."""
        # Parse status for badge display - simplify verbose SDK messages
        status_lower = status.lower()
        
        # Network is ready
        if "ready" in status_lower:
            self._sidebar.set_status("online")
        # Connected to relays
        elif "connected" in status_lower:
            self._sidebar.set_status("online")
        # Errors
        elif "error" in status_lower or "failed" in status_lower:
            self._sidebar.set_status("offline")
        # Still connecting - don't show verbose details
        elif "connecting" in status_lower or "started" in status_lower:
            self._sidebar.set_status("connecting")
        # Ignore other internal status messages
    
    def _on_connection_ready(self) -> None:
        """Handle network ready signal."""
        self._sidebar.set_status("online")
    
    # ============ Window Events ============
    
    def closeEvent(self, event) -> None:
        """Handle window close: cleanup network."""
        self._network.stop()
        event.accept()
