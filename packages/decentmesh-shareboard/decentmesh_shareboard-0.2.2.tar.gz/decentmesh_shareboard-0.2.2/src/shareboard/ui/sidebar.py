"""
Sidebar panel for ShareBoard.

Contains the user's identity card, add contact button, and contact list.
"""

from typing import List, Optional, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QInputDialog, QMessageBox, QApplication
)

from shareboard.models import Identity, MyIdentity
from shareboard.ui.styles import COLORS, get_sidebar_style
from shareboard.ui.widgets import IdentityCard, StatusBadge


class SidebarPanel(QFrame):
    """
    Left sidebar panel containing identity management.
    
    Sections:
    - My Identity card (with copy key button)
    - Add Contact button
    - Scrollable contact list
    - Connection status badge
    
    Signals:
        contact_added(Identity): Emitted when a new contact is added
        contact_removed(str): Emitted when a contact is deleted (public_key)
        contact_toggled(str, bool): Emitted when active state changes
    """
    
    contact_added = Signal(object)  # Identity
    contact_removed = Signal(str)  # public_key
    contact_toggled = Signal(str, bool)  # public_key, is_active
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._my_identity: Optional[MyIdentity] = None
        self._contacts: List[Identity] = []
        
        self.setFixedWidth(280)
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Build the sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # ============ Header ============
        header = QLabel("ShareBoard")
        header.setProperty("class", "title")
        header.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 22px;
            font-weight: 700;
        """)
        layout.addWidget(header)
        
        # Status badge
        self._status_badge = StatusBadge()
        layout.addWidget(self._status_badge)
        
        # ============ My Identity Section ============
        section_label = QLabel("MY IDENTITY")
        section_label.setProperty("class", "muted")
        section_label.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1px;
        """)
        layout.addWidget(section_label)
        
        # Placeholder for my identity card
        self._my_identity_container = QVBoxLayout()
        self._my_identity_container.setSpacing(0)
        layout.addLayout(self._my_identity_container)
        
        # ============ Add Contact Section ============
        add_section = QHBoxLayout()
        add_section.setSpacing(8)
        
        contacts_label = QLabel("CONTACTS")
        contacts_label.setProperty("class", "muted")
        contacts_label.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1px;
        """)
        add_section.addWidget(contacts_label)
        
        add_section.addStretch()
        
        # Active count badge
        self._active_badge = QLabel("0 active")
        self._active_badge.setStyleSheet(f"""
            color: {COLORS["accent_cyan"]};
            font-size: 10px;
            background: {COLORS["bg_tertiary"]};
            padding: 2px 8px;
            border-radius: 8px;
        """)
        add_section.addWidget(self._active_badge)
        
        layout.addLayout(add_section)
        
        # Add from clipboard button
        self._add_btn = QPushButton("📋 Add from Clipboard")
        self._add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._add_btn.setFixedHeight(42)
        self._add_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS["accent_cyan"]},
                    stop:1 {COLORS["accent_magenta"]}
                );
                color: #0d0d1a;
                font-weight: 700;
                font-size: 13px;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #33e0ff,
                    stop:1 #ff33ff
                );
            }}
            QPushButton:pressed {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00b3d9,
                    stop:1 #cc00cc
                );
            }}
        """)
        self._add_btn.clicked.connect(self._on_add_from_clipboard)
        layout.addWidget(self._add_btn)
        
        # ============ Contacts List ============
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self._contacts_container = QWidget()
        self._contacts_layout = QVBoxLayout(self._contacts_container)
        self._contacts_layout.setContentsMargins(0, 0, 0, 0)
        self._contacts_layout.setSpacing(8)
        self._contacts_layout.addStretch()
        
        scroll.setWidget(self._contacts_container)
        layout.addWidget(scroll, 1)  # Take remaining space
        
        # Empty state
        self._empty_label = QLabel("No contacts yet.\nAdd someone to get started!")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 12px;
            padding: 20px;
        """)
        self._contacts_layout.insertWidget(0, self._empty_label)
    
    def _apply_style(self) -> None:
        """Apply visual styling."""
        self.setStyleSheet(get_sidebar_style())
    
    def set_my_identity(self, identity: MyIdentity) -> None:
        """Set and display the user's own identity."""
        self._my_identity = identity
        
        # Clear existing
        while self._my_identity_container.count():
            item = self._my_identity_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add identity card
        card = IdentityCard(
            name=identity.name,
            public_key=identity.public_key,
            is_own=True
        )
        self._my_identity_container.addWidget(card)
    
    def set_contacts(self, contacts: List[Identity]) -> None:
        """Set and display the contact list."""
        self._contacts = contacts
        self._refresh_contacts()
    
    def _refresh_contacts(self) -> None:
        """Rebuild the contacts list UI."""
        # Clear existing cards (keep stretch at end)
        while self._contacts_layout.count() > 1:
            item = self._contacts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Update empty state
        if not self._contacts:
            self._empty_label.show()
        else:
            self._empty_label.hide()
            
            # Add contact cards
            for contact in self._contacts:
                card = IdentityCard(
                    name=contact.name,
                    public_key=contact.public_key,
                    is_active=contact.is_active,
                    is_own=False
                )
                card.active_toggled.connect(self._on_contact_toggled)
                card.delete_clicked.connect(self._on_contact_delete)
                self._contacts_layout.insertWidget(self._contacts_layout.count() - 1, card)
        
        # Update active count
        active_count = sum(1 for c in self._contacts if c.is_active)
        self._active_badge.setText(f"{active_count} active")
    
    def set_status(self, status: str, details: str = "") -> None:
        """Update connection status badge."""
        self._status_badge.set_status(status, details)
    
    def _on_add_from_clipboard(self) -> None:
        """Handle add from clipboard button click."""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        
        # Validate as public key
        if not self._validate_public_key(text):
            QMessageBox.warning(
                self,
                "Invalid Key",
                "Clipboard doesn't contain a valid 64-character hex public key.\n\n"
                "Ask your contact to copy their key and try again."
            )
            return
        
        # Check if already exists
        if any(c.public_key == text for c in self._contacts):
            QMessageBox.information(
                self,
                "Already Added",
                "This contact is already in your list."
            )
            return
        
        # Ask for name
        name, ok = QInputDialog.getText(
            self,
            "Add Contact",
            "Enter a name for this contact:",
            text=f"Contact {len(self._contacts) + 1}"
        )
        
        if ok and name:
            identity = Identity(name=name, public_key=text)
            self._contacts.append(identity)
            self._refresh_contacts()
            self.contact_added.emit(identity)
    
    def _on_contact_toggled(self, public_key: str, is_active: bool) -> None:
        """Handle contact active toggle."""
        for contact in self._contacts:
            if contact.public_key == public_key:
                contact.is_active = is_active
                break
        
        # Update badge
        active_count = sum(1 for c in self._contacts if c.is_active)
        self._active_badge.setText(f"{active_count} active")
        
        self.contact_toggled.emit(public_key, is_active)
    
    def _on_contact_delete(self, public_key: str) -> None:
        """Handle contact delete button."""
        # Find contact name
        contact = next((c for c in self._contacts if c.public_key == public_key), None)
        if not contact:
            return
        
        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Remove Contact",
            f"Remove '{contact.name}' from your contacts?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            self._contacts = [c for c in self._contacts if c.public_key != public_key]
            self._refresh_contacts()
            self.contact_removed.emit(public_key)
    
    @staticmethod
    def _validate_public_key(key: str) -> bool:
        """Validate a potential public key string."""
        if not isinstance(key, str) or len(key) != 64:
            return False
        try:
            int(key, 16)
            return True
        except ValueError:
            return False
