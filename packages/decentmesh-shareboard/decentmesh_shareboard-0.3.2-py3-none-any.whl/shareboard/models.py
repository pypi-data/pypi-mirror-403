"""
Data models for ShareBoard application.

Defines Identity (contact) and SharedText (message) dataclasses
for use throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Identity:
    """
    A peer identity (contact) in the ShareBoard network.
    
    Attributes:
        name: User-friendly display name
        public_key: 64-character hex public key
        is_active: Whether to send shares to this contact
        added_at: Timestamp when contact was added
    """
    name: str
    public_key: str
    is_active: bool = True
    added_at: float = field(default_factory=lambda: datetime.now().timestamp())
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "name": self.name,
            "public_key": self.public_key,
            "is_active": self.is_active,
            "added_at": self.added_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Identity":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            public_key=data["public_key"],
            is_active=data.get("is_active", True),
            added_at=data.get("added_at", datetime.now().timestamp()),
        )
    
    @property
    def short_key(self) -> str:
        """Return truncated key for display (first 8 + last 4 chars)."""
        if len(self.public_key) >= 12:
            return f"{self.public_key[:8]}...{self.public_key[-4:]}"
        return self.public_key


@dataclass
class MyIdentity:
    """
    The user's own identity with private key.
    
    Attributes:
        name: User's display name
        private_key: 64-character hex private key (secret!)
        public_key: 64-character hex public key (shareable)
    """
    name: str
    private_key: str
    public_key: str
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "name": self.name,
            "private_key": self.private_key,
            "public_key": self.public_key,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MyIdentity":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            private_key=data["private_key"],
            public_key=data["public_key"],
        )
    
    @property
    def short_key(self) -> str:
        """Return truncated public key for display."""
        if len(self.public_key) >= 12:
            return f"{self.public_key[:8]}...{self.public_key[-4:]}"
        return self.public_key


@dataclass
class SharedText:
    """
    A shared text message in the ShareBoard.
    
    Attributes:
        id: Unique message identifier
        content: The shared text content
        sender_name: Display name of the sender
        sender_key: Public key of the sender
        timestamp: Unix timestamp of when it was shared
        is_incoming: True if received, False if sent by user
    """
    id: str
    content: str
    sender_name: str
    sender_key: str
    timestamp: float
    is_incoming: bool
    
    @classmethod
    def new(
        cls,
        content: str,
        sender_name: str,
        sender_key: str,
        is_incoming: bool = False,
    ) -> "SharedText":
        """Create a new SharedText with auto-generated ID and timestamp."""
        return cls(
            id=str(uuid.uuid4()),
            content=content,
            sender_name=sender_name,
            sender_key=sender_key,
            timestamp=datetime.now().timestamp(),
            is_incoming=is_incoming,
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "id": self.id,
            "content": self.content,
            "sender_name": self.sender_name,
            "sender_key": self.sender_key,
            "timestamp": self.timestamp,
            "is_incoming": self.is_incoming,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SharedText":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            sender_name=data["sender_name"],
            sender_key=data["sender_key"],
            timestamp=data["timestamp"],
            is_incoming=data["is_incoming"],
        )
    
    @property
    def formatted_time(self) -> str:
        """Return human-readable timestamp."""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%H:%M")
    
    @property
    def formatted_date(self) -> str:
        """Return full date string."""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
