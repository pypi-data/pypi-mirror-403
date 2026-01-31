"""
Main message board panel for ShareBoard.

Contains the header, message scroll area, and input field.
"""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTextEdit, QSizePolicy
)

from shareboard.models import SharedText
from shareboard.ui.styles import COLORS
from shareboard.ui.widgets import ChatBubble, StatusBadge


class BoardPanel(QFrame):
    """
    Main message board panel.
    
    Sections:
    - Header with title and status
    - Scrollable message area with chat bubbles
    - Input area with text field and share button
    
    Signals:
        share_clicked(str): Emitted when share button is clicked with content
    """
    
    share_clicked = Signal(str)  # content
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._messages: List[SharedText] = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build the board UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ============ Header ============
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["bg_secondary"]};
                border-bottom: 1px solid {COLORS["border_light"]};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        title = QLabel("📋 Shared Board")
        title.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 18px;
            font-weight: 600;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Header status
        self._header_status = QLabel("Waiting for shares...")
        self._header_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        header_layout.addWidget(self._header_status)
        
        layout.addWidget(header)
        
        # ============ Message Area ============
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS["bg_primary"]};
            }}
        """)
        
        self._messages_container = QWidget()
        self._messages_container.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._messages_layout = QVBoxLayout(self._messages_container)
        self._messages_layout.setContentsMargins(20, 20, 20, 20)
        self._messages_layout.setSpacing(12)
        self._messages_layout.addStretch()
        
        scroll.setWidget(self._messages_container)
        self._scroll_area = scroll
        layout.addWidget(scroll, 1)
        
        # Empty state
        self._empty_state = QWidget()
        empty_layout = QVBoxLayout(self._empty_state)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_icon = QLabel("📋")
        empty_icon.setStyleSheet("font-size: 64px;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)
        
        empty_text = QLabel("Share something to get started!")
        empty_text.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 16px;
        """)
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_text)
        
        empty_hint = QLabel("Type below and click Share to send to all active contacts")
        empty_hint.setStyleSheet(f"""
            color: {COLORS["text_dim"]};
            font-size: 12px;
        """)
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_hint)
        
        self._messages_layout.insertWidget(0, self._empty_state)
        
        # ============ Input Area ============
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["bg_secondary"]};
                border-top: 1px solid {COLORS["border_light"]};
            }}
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 16, 20, 16)
        input_layout.setSpacing(12)
        
        # Text input
        self._input = QTextEdit()
        self._input.setPlaceholderText("Type or paste text to share...")
        self._input.setMaximumHeight(100)
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS["bg_tertiary"]};
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border_light"]};
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }}
            QTextEdit:focus {{
                border-color: {COLORS["accent_cyan"]};
            }}
        """)
        input_layout.addWidget(self._input)
        
        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        
        # Character counter
        self._char_count = QLabel("0 characters")
        self._char_count.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        btn_row.addWidget(self._char_count)
        
        btn_row.addStretch()
        
        # Share button
        self._share_btn = QPushButton("🚀 Share")
        self._share_btn.setProperty("class", "primary")
        self._share_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._share_btn.setFixedSize(120, 40)
        self._share_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS["accent_cyan"]},
                    stop:1 {COLORS["accent_magenta"]}
                );
                color: {COLORS["bg_primary"]};
                font-weight: 700;
                font-size: 14px;
                border: none;
                border-radius: 10px;
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
            QPushButton:disabled {{
                background: {COLORS["bg_tertiary"]};
                color: {COLORS["text_dim"]};
            }}
        """)
        self._share_btn.clicked.connect(self._on_share_clicked)
        btn_row.addWidget(self._share_btn)
        
        input_layout.addLayout(btn_row)
        layout.addWidget(input_frame)
        
        # Connect text change for char counter
        self._input.textChanged.connect(self._update_char_count)
    
    def _update_char_count(self) -> None:
        """Update character counter label."""
        count = len(self._input.toPlainText())
        self._char_count.setText(f"{count} characters")
        
        # Enable/disable share button
        self._share_btn.setEnabled(count > 0)
    
    def _on_share_clicked(self) -> None:
        """Handle share button click."""
        content = self._input.toPlainText().strip()
        if content:
            self.share_clicked.emit(content)
            self._input.clear()
    
    def add_message(self, message: SharedText) -> None:
        """Add a message to the board."""
        self._messages.append(message)
        
        # Hide empty state
        self._empty_state.hide()
        
        # Create bubble
        bubble = ChatBubble(
            content=message.content,
            sender_name=message.sender_name,
            timestamp=message.timestamp,
            is_outgoing=not message.is_incoming
        )
        
        # Wrap in alignment layout for left/right positioning
        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        
        if message.is_incoming:
            wrapper_layout.addWidget(bubble)
            wrapper_layout.addStretch()
        else:
            wrapper_layout.addStretch()
            wrapper_layout.addWidget(bubble)
        
        # Insert before stretch
        self._messages_layout.insertWidget(self._messages_layout.count() - 1, wrapper)
        
        # Scroll to bottom
        self._scroll_to_bottom()
        
        # Update header
        self._header_status.setText(f"{len(self._messages)} shares")
    
    def set_messages(self, messages: List[SharedText]) -> None:
        """Set all messages (used for loading history)."""
        # Clear existing (keep stretch and empty state)
        while self._messages_layout.count() > 2:
            item = self._messages_layout.takeAt(1)  # Skip empty state at 0
            if item.widget():
                item.widget().deleteLater()
        
        self._messages = []
        
        # Show empty state if no messages
        if not messages:
            self._empty_state.show()
            self._header_status.setText("No shares yet")
            return
        
        self._empty_state.hide()
        
        # Add all messages
        for message in messages:
            self.add_message(message)
    
    def _scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the message area."""
        # Use timer to ensure layout is complete
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self._scroll_area.verticalScrollBar().setValue(
            self._scroll_area.verticalScrollBar().maximum()
        ))
    
    def clear_input(self) -> None:
        """Clear the input field."""
        self._input.clear()
    
    def get_input_text(self) -> str:
        """Get current input text."""
        return self._input.toPlainText().strip()
