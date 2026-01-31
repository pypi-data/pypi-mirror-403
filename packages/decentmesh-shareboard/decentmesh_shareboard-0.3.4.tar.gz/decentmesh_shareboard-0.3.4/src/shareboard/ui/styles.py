"""
Dark glassmorphism theme and styling for ShareBoard.

Provides color palette, QSS stylesheets, and helper functions
for consistent visual styling throughout the application.
"""

from typing import Dict

# ============ Color Palette ============

COLORS: Dict[str, str] = {
    # Backgrounds
    "bg_primary": "#0d0d1a",
    "bg_secondary": "#1a1a2e",
    "bg_tertiary": "#16213e",
    "bg_glass": "rgba(26, 26, 46, 0.85)",
    "bg_glass_light": "rgba(26, 26, 46, 0.6)",
    
    # Accents
    "accent_cyan": "#00d9ff",
    "accent_magenta": "#ff00ff",
    "accent_purple": "#7b2cbf",
    "accent_gradient_start": "#00d9ff",
    "accent_gradient_end": "#ff00ff",
    
    # Text
    "text_primary": "#ffffff",
    "text_secondary": "#e0e0e0",
    "text_muted": "#8888aa",
    "text_dim": "#666680",
    
    # Borders
    "border_light": "rgba(0, 217, 255, 0.2)",
    "border_medium": "rgba(0, 217, 255, 0.4)",
    "border_accent": "#00d9ff",
    
    # Status
    "status_online": "#00ff88",
    "status_offline": "#ff4444",
    "status_connecting": "#ffaa00",
    
    # Bubbles
    "bubble_incoming": "#1a1a2e",
    "bubble_outgoing": "#16213e",
}


def get_stylesheet() -> str:
    """
    Generate the main application stylesheet.
    
    Returns:
        Complete QSS stylesheet string
    """
    return f"""
        /* ============ Global ============ */
        
        QMainWindow, QWidget {{
            background-color: {COLORS["bg_primary"]};
            color: {COLORS["text_primary"]};
            font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
            font-size: 13px;
        }}
        
        /* ============ Scroll Areas ============ */
        
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}
        
        QScrollBar:vertical {{
            background: {COLORS["bg_secondary"]};
            width: 8px;
            margin: 0;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {COLORS["border_medium"]};
            min-height: 30px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {COLORS["accent_cyan"]};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: none;
        }}
        
        /* ============ Buttons ============ */
        
        QPushButton {{
            background-color: {COLORS["bg_secondary"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["border_light"]};
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background-color: {COLORS["bg_tertiary"]};
            border-color: {COLORS["accent_cyan"]};
        }}
        
        QPushButton:pressed {{
            background-color: {COLORS["bg_primary"]};
        }}
        
        QPushButton:disabled {{
            color: {COLORS["text_dim"]};
            border-color: {COLORS["text_dim"]};
        }}
        
        /* Primary button style */
        QPushButton[class="primary"] {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS["accent_cyan"]},
                stop:1 {COLORS["accent_magenta"]}
            );
            color: {COLORS["bg_primary"]};
            font-weight: 600;
            border: none;
        }}
        
        QPushButton[class="primary"]:hover {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #33e0ff,
                stop:1 #ff33ff
            );
        }}
        
        /* ============ Text Input ============ */
        
        QLineEdit {{
            background-color: {COLORS["bg_secondary"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["border_light"]};
            border-radius: 8px;
            padding: 8px 12px;
            selection-background-color: {COLORS["accent_cyan"]};
        }}
        
        QLineEdit:focus {{
            border-color: {COLORS["accent_cyan"]};
        }}
        
        QLineEdit::placeholder {{
            color: {COLORS["text_muted"]};
        }}
        
        QTextEdit {{
            background-color: {COLORS["bg_secondary"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["border_light"]};
            border-radius: 8px;
            padding: 8px 12px;
            selection-background-color: {COLORS["accent_cyan"]};
        }}
        
        QTextEdit:focus {{
            border-color: {COLORS["accent_cyan"]};
        }}
        
        /* ============ Labels ============ */
        
        QLabel {{
            color: {COLORS["text_primary"]};
            background: transparent;
        }}
        
        QLabel[class="muted"] {{
            color: {COLORS["text_muted"]};
            font-size: 11px;
        }}
        
        QLabel[class="title"] {{
            font-size: 18px;
            font-weight: 600;
        }}
        
        QLabel[class="subtitle"] {{
            font-size: 14px;
            font-weight: 500;
            color: {COLORS["text_secondary"]};
        }}
        
        /* ============ Frames & Panels ============ */
        
        QFrame {{
            background: transparent;
            border: none;
        }}
        
        QFrame[class="panel"] {{
            background-color: {COLORS["bg_glass"]};
            border: 1px solid {COLORS["border_light"]};
            border-radius: 12px;
        }}
        
        QFrame[class="card"] {{
            background-color: {COLORS["bg_secondary"]};
            border: 1px solid {COLORS["border_light"]};
            border-radius: 10px;
            padding: 12px;
        }}
        
        /* ============ Toggle Switch ============ */
        
        QCheckBox {{
            color: {COLORS["text_primary"]};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 40px;
            height: 22px;
            border-radius: 11px;
            background-color: {COLORS["bg_tertiary"]};
            border: 1px solid {COLORS["border_light"]};
        }}
        
        QCheckBox::indicator:checked {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS["accent_cyan"]},
                stop:1 {COLORS["accent_magenta"]}
            );
            border: none;
        }}
        
        /* ============ Dialogs ============ */
        
        QDialog {{
            background-color: {COLORS["bg_primary"]};
        }}
        
        QInputDialog {{
            background-color: {COLORS["bg_primary"]};
        }}
        
        QMessageBox {{
            background-color: {COLORS["bg_primary"]};
        }}
        
        /* ============ Tooltips ============ */
        
        QToolTip {{
            background-color: {COLORS["bg_secondary"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["border_light"]};
            border-radius: 4px;
            padding: 4px 8px;
        }}
    """


def get_sidebar_style() -> str:
    """Get additional styles for the sidebar panel."""
    return f"""
        SidebarPanel {{
            background-color: {COLORS["bg_secondary"]};
            border-right: 1px solid {COLORS["border_light"]};
        }}
    """


def get_identity_card_style(is_own: bool = False) -> str:
    """
    Get style for identity cards.
    
    Args:
        is_own: True if this is the user's own identity card
    """
    if is_own:
        return f"""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(0, 217, 255, 0.15),
                stop:1 rgba(255, 0, 255, 0.15)
            );
            border: 1px solid {COLORS["accent_cyan"]};
            border-radius: 12px;
            padding: 12px;
        """
    return f"""
        background-color: {COLORS["bg_tertiary"]};
        border: 1px solid {COLORS["border_light"]};
        border-radius: 10px;
        padding: 10px;
    """


def get_bubble_style(is_outgoing: bool) -> str:
    """
    Get style for chat bubbles.
    
    Args:
        is_outgoing: True if message is from the user
    """
    bg = COLORS["bubble_outgoing"] if is_outgoing else COLORS["bubble_incoming"]
    border = COLORS["accent_cyan"] if is_outgoing else COLORS["border_light"]
    
    return f"""
        background-color: {bg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 10px 14px;
    """
