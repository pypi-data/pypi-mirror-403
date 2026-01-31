"""
JSON persistence layer for ShareBoard.

Manages storage of identities, contacts, and message history
in the ~/.shareboard/ directory.
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from shareboard.models import Identity, MyIdentity, SharedText


class ShareBoardStorage:
    """
    Persistent storage manager for ShareBoard data.
    
    All data is stored in ~/.shareboard/ as JSON files:
    - my_identity.json: User's own identity
    - identities.json: List of peer contacts
    - history.json: Rolling message history
    """
    
    DEFAULT_DIR = ".shareboard"
    MAX_HISTORY = 500
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize storage at the given directory.
        
        Args:
            storage_dir: Custom storage path. Defaults to ~/.shareboard/
        """
        if storage_dir:
            self.storage_path = Path(storage_dir)
        else:
            self.storage_path = Path.home() / self.DEFAULT_DIR
        
        # Ensure directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    @property
    def my_identity_file(self) -> Path:
        return self.storage_path / "my_identity.json"
    
    @property
    def identities_file(self) -> Path:
        return self.storage_path / "identities.json"
    
    @property
    def history_file(self) -> Path:
        return self.storage_path / "history.json"
    
    # ============ My Identity ============
    
    def load_my_identity(self) -> Optional[MyIdentity]:
        """Load user's own identity from storage."""
        if not self.my_identity_file.exists():
            return None
        
        try:
            with open(self.my_identity_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return MyIdentity.from_dict(data)
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return None
    
    def save_my_identity(self, identity: MyIdentity) -> None:
        """Save user's own identity to storage."""
        with open(self.my_identity_file, "w", encoding="utf-8") as f:
            json.dump(identity.to_dict(), f, indent=2)
    
    def has_identity(self) -> bool:
        """Check if user has a saved identity."""
        return self.my_identity_file.exists()
    
    # ============ Peer Identities ============
    
    def load_identities(self) -> List[Identity]:
        """Load all peer identities from storage."""
        if not self.identities_file.exists():
            return []
        
        try:
            with open(self.identities_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Identity.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return []
    
    def save_identities(self, identities: List[Identity]) -> None:
        """Save all peer identities to storage."""
        data = [identity.to_dict() for identity in identities]
        with open(self.identities_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def add_identity(self, identity: Identity) -> None:
        """Add a new identity to storage."""
        identities = self.load_identities()
        
        # Check for duplicate key
        for existing in identities:
            if existing.public_key == identity.public_key:
                # Update name if already exists
                existing.name = identity.name
                self.save_identities(identities)
                return
        
        identities.append(identity)
        self.save_identities(identities)
    
    def remove_identity(self, public_key: str) -> bool:
        """Remove an identity by public key. Returns True if found and removed."""
        identities = self.load_identities()
        original_count = len(identities)
        
        identities = [i for i in identities if i.public_key != public_key]
        
        if len(identities) < original_count:
            self.save_identities(identities)
            return True
        return False
    
    def update_identity_active(self, public_key: str, is_active: bool) -> None:
        """Toggle active state of an identity."""
        identities = self.load_identities()
        
        for identity in identities:
            if identity.public_key == public_key:
                identity.is_active = is_active
                break
        
        self.save_identities(identities)
    
    # ============ History ============
    
    def load_history(self) -> List[SharedText]:
        """Load message history from storage."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [SharedText.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return []
    
    def save_history(self, history: List[SharedText]) -> None:
        """Save message history, trimming to MAX_HISTORY."""
        # Keep only the most recent messages
        if len(history) > self.MAX_HISTORY:
            history = history[-self.MAX_HISTORY:]
        
        data = [msg.to_dict() for msg in history]
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def add_to_history(self, message: SharedText) -> None:
        """Add a message to history with auto-trim."""
        history = self.load_history()
        
        # Check for duplicate ID
        if any(m.id == message.id for m in history):
            return
        
        history.append(message)
        self.save_history(history)
    
    def clear_history(self) -> None:
        """Clear all message history."""
        self.save_history([])
