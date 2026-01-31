"""
ShareBoard - Decentralized Copy-Paste Sharing Application

A modern PySide6 application for sharing text snippets across
the DecentMesh network with persistent identity management.
"""

__version__ = "0.1.0"
__author__ = "DecentMesh Team"

from shareboard.app import ShareBoardWindow


def main():
    """Entry point for the ShareBoard application."""
    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("ShareBoard")
    app.setApplicationVersion(__version__)
    
    window = ShareBoardWindow()
    window.show()
    
    sys.exit(app.exec())


__all__ = ["ShareBoardWindow", "main", "__version__"]
