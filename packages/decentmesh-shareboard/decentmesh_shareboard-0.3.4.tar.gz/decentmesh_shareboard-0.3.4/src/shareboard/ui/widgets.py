"""
Reusable UI widgets for ShareBoard.

Contains ChatBubble, CopyButton, IdentityCard, and StatusBadge components.
"""

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QFont, QCursor
from PySide6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QWidget, QCheckBox, QSizePolicy, QApplication, QGraphicsDropShadowEffect
)

from shareboard.ui.styles import COLORS, get_bubble_style, get_identity_card_style


class CopyButton(QPushButton):
    """
    A button that copies text to clipboard with visual feedback.
    
    Shows "Copy" normally, changes to "✓ Copied!" for 1.5s after click.
    """
    
    def __init__(self, text_to_copy: str = "", parent: Optional[QWidget] = None):
        super().__init__("📋 Copy", parent)
        self._text_to_copy = text_to_copy
        self._original_text = "📋 Copy"
        
        self.setFixedHeight(28)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clicked.connect(self._on_click)
    
    def set_text_to_copy(self, text: str) -> None:
        """Set the text that will be copied on click."""
        self._text_to_copy = text
    
    def _on_click(self) -> None:
        """Handle click: copy to clipboard and show feedback."""
        if self._text_to_copy:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._text_to_copy)
            
            self.setText("✓ Copied!")
            self.setStyleSheet(f"color: {COLORS['status_online']};")
            
            # Reset after 1.5 seconds
            QTimer.singleShot(1500, self._reset)
    
    def _reset(self) -> None:
        """Reset button to original state."""
        self.setText(self._original_text)
        self.setStyleSheet("")


class StatusBadge(QLabel):
    """
    Connection status indicator badge.
    
    Shows colored dot + status text (e.g., "● Connected (3 relays)").
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._status = "offline"
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status("connecting")
    
    def set_status(self, status: str, details: str = "") -> None:
        """
        Update the status display.
        
        Args:
            status: One of "online", "offline", "connecting"
            details: Optional additional text
        """
        self._status = status
        
        colors = {
            "online": COLORS["status_online"],
            "offline": COLORS["status_offline"],
            "connecting": COLORS["status_connecting"],
        }
        color = colors.get(status, COLORS["text_muted"])
        
        text = status.title()
        if details:
            text += f" ({details})"
        
        self.setText(f"● {text}")
        self.setStyleSheet(f"color: {color}; font-size: 11px;")


class ChatBubble(QFrame):
    """
    A styled message bubble for displaying shared text.
    
    Features:
    - Auto-alignment based on incoming/outgoing
    - Sender name + timestamp header
    - Copy button on hover
    - Drop shadow effect
    """
    
    copy_clicked = Signal(str)  # Emits the content when copy is clicked
    
    def __init__(
        self,
        content: str,
        sender_name: str,
        timestamp: float,
        is_outgoing: bool,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._content = content
        self._is_outgoing = is_outgoing
        
        self._setup_ui(content, sender_name, timestamp, is_outgoing)
        self._apply_style()
    
    def _setup_ui(
        self,
        content: str,
        sender_name: str,
        timestamp: float,
        is_outgoing: bool
    ) -> None:
        """Build the bubble UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # Header row: sender + time + copy button
        header = QHBoxLayout()
        header.setSpacing(8)
        
        # Sender name
        sender_label = QLabel(sender_name)
        sender_label.setProperty("class", "subtitle")
        sender_label.setStyleSheet(f"""
            color: {COLORS["accent_cyan"] if is_outgoing else COLORS["accent_magenta"]};
            font-weight: 600;
            font-size: 12px;
        """)
        header.addWidget(sender_label)
        
        # Timestamp
        dt = datetime.fromtimestamp(timestamp)
        time_str = dt.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setProperty("class", "muted")
        time_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        header.addWidget(time_label)
        
        header.addStretch()
        
        # Copy button
        self._copy_btn = CopyButton(content)
        self._copy_btn.setFixedSize(70, 24)
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS["bg_tertiary"]};
                border: 1px solid {COLORS["border_light"]};
                border-radius: 4px;
                color: {COLORS["text_muted"]};
                font-size: 10px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                border-color: {COLORS["accent_cyan"]};
                color: {COLORS["text_primary"]};
            }}
        """)
        header.addWidget(self._copy_btn)
        
        layout.addLayout(header)
        
        # Content
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
        layout.addWidget(content_label)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setMaximumWidth(500)
    
    def _apply_style(self) -> None:
        """Apply visual styling."""
        self.setStyleSheet(get_bubble_style(self._is_outgoing))
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.GlobalColor.black)
        self.setGraphicsEffect(shadow)


class IdentityCard(QFrame):
    """
    A compact card displaying a contact's identity.
    
    Features:
    - Avatar circle with initial
    - Name + truncated key
    - Active toggle switch
    - Delete button
    """
    
    active_toggled = Signal(str, bool)  # public_key, is_active
    delete_clicked = Signal(str)  # public_key
    
    def __init__(
        self,
        name: str,
        public_key: str,
        is_active: bool = True,
        is_own: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._public_key = public_key
        self._is_own = is_own
        
        self._setup_ui(name, public_key, is_active, is_own)
    
    def _setup_ui(
        self,
        name: str,
        public_key: str,
        is_active: bool,
        is_own: bool
    ) -> None:
        """Build the card UI."""
        # Apply frame style directly without affecting children
        if is_own:
            self.setStyleSheet(f"""
                IdentityCard {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(0, 217, 255, 0.15),
                        stop:1 rgba(255, 0, 255, 0.15)
                    );
                    border: 1px solid {COLORS["accent_cyan"]};
                    border-radius: 12px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                IdentityCard {{
                    background-color: {COLORS["bg_tertiary"]};
                    border: 1px solid {COLORS["border_light"]};
                    border-radius: 10px;
                }}
            """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        
        # Top row: avatar + name + key
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        # Avatar circle
        avatar = QLabel(name[0].upper() if name else "?")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS["accent_cyan"]},
                    stop:1 {COLORS["accent_magenta"]}
                );
                color: {COLORS["bg_primary"]};
                font-weight: 700;
                font-size: 18px;
                border-radius: 20px;
            }}
        """)
        top_row.addWidget(avatar)
        
        # Name + key column
        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-weight: 600;
                font-size: 14px;
                background: transparent;
            }}
        """)
        info_layout.addWidget(name_label)
        
        # Truncated key
        short_key = f"{public_key[:8]}...{public_key[-4:]}" if len(public_key) >= 12 else public_key
        key_label = QLabel(short_key)
        key_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                background: transparent;
            }}
        """)
        info_layout.addWidget(key_label)
        
        top_row.addWidget(info_widget)
        top_row.addStretch()
        
        layout.addLayout(top_row)
        
        # Bottom row: actions
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        
        if is_own:
            # Own identity: show copy button
            copy_btn = QPushButton("📋 Copy My Key")
            copy_btn.setFixedHeight(32)
            copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            copy_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS["accent_cyan"]},
                        stop:1 {COLORS["accent_magenta"]}
                    );
                    color: {COLORS["bg_primary"]};
                    font-weight: 600;
                    font-size: 12px;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #33e0ff,
                        stop:1 #ff33ff
                    );
                }}
            """)
            copy_btn.clicked.connect(lambda: self._copy_key(public_key, copy_btn))
            action_row.addWidget(copy_btn)
            action_row.addStretch()
        else:
            # Contact: show toggle + delete
            toggle = QCheckBox("Active")
            toggle.setChecked(is_active)
            toggle.setStyleSheet(f"""
                QCheckBox {{
                    color: {COLORS["text_primary"]};
                    font-size: 12px;
                    spacing: 6px;
                    background: transparent;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 1px solid {COLORS["border_medium"]};
                    background-color: {COLORS["bg_secondary"]};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {COLORS["accent_cyan"]};
                    border-color: {COLORS["accent_cyan"]};
                }}
            """)
            toggle.toggled.connect(lambda checked: self.active_toggled.emit(self._public_key, checked))
            action_row.addWidget(toggle)
            
            action_row.addStretch()
            
            delete_btn = QPushButton("✕")
            delete_btn.setFixedSize(28, 28)
            delete_btn.setToolTip("Remove contact")
            delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS["text_muted"]};
                    border: 1px solid {COLORS["border_light"]};
                    border-radius: 14px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: {COLORS["status_offline"]};
                    color: {COLORS["text_primary"]};
                    border-color: {COLORS["status_offline"]};
                }}
            """)
            delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._public_key))
            action_row.addWidget(delete_btn)
        
        layout.addLayout(action_row)
    
    def _copy_key(self, key: str, btn: QPushButton) -> None:
        """Copy key to clipboard and show feedback."""
        clipboard = QApplication.clipboard()
        clipboard.setText(key)
        btn.setText("✓ Copied!")
        QTimer.singleShot(1500, lambda: btn.setText("📋 Copy My Key"))

