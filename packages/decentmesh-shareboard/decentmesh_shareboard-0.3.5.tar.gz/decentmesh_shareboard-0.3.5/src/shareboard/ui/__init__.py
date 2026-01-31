"""
ShareBoard UI package.

Contains all visual components, styles, and widgets.
"""

from shareboard.ui.styles import COLORS, get_stylesheet
from shareboard.ui.widgets import ChatBubble, CopyButton, IdentityCard, StatusBadge
from shareboard.ui.sidebar import SidebarPanel
from shareboard.ui.board import BoardPanel

__all__ = [
    "COLORS",
    "get_stylesheet",
    "ChatBubble",
    "CopyButton", 
    "IdentityCard",
    "StatusBadge",
    "SidebarPanel",
    "BoardPanel",
]
