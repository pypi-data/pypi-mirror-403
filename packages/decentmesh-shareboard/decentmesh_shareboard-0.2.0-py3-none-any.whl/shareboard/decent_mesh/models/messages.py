"""
Chat message models for DecentMesh messaging.

Provides ChatMessage and ChatHistory classes matching the Rust client library
for cross-platform message handling.

Usage:
    from decent_mesh.models.messages import ChatMessage, ChatHistory
    
    # Create message
    msg = ChatMessage.new(sender="abc123", content="Hello!", is_outgoing=True)
    
    # Manage history
    history = ChatHistory()
    history.add_message(msg)
    
    # Save/load encrypted
    history.save_encrypted("history.dat", key_seed=b"secret")
    history = ChatHistory.load_encrypted("history.dat", key_seed=b"secret")
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import cbor2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os


@dataclass
class ChatMessage:
    """
    A single chat message.
    
    Mirrors Rust: ChatMessage { id, sender, content, timestamp, is_outgoing, acked, ack_latency }
    
    Attributes:
        id: Unique message identifier (UUID)
        sender: Sender's public key or display name
        content: Message text content
        timestamp: Message creation time (Unix ms)
        is_outgoing: True if sent by local user
        acked: True if delivery was acknowledged
        ack_latency: Round-trip ack latency in ms (if acked)
    """
    id: str
    sender: str
    content: str
    timestamp: int  # Unix timestamp in milliseconds
    is_outgoing: bool
    acked: bool = False
    ack_latency: Optional[int] = None
    
    @classmethod
    def new(cls, sender: str, content: str, is_outgoing: bool) -> "ChatMessage":
        """Create a new message with auto-generated ID and current timestamp."""
        return cls(
            id=str(uuid.uuid4()),
            sender=sender,
            content=content,
            timestamp=int(datetime.now().timestamp() * 1000),
            is_outgoing=is_outgoing,
        )
    
    def to_cbor(self) -> dict:
        """
        Encode to CBOR-compatible indexed dict.
        
        Uses integer keys matching Rust #[n(x)] annotations.
        """
        result = {
            0: self.id,
            1: self.sender,
            2: self.content,
            3: self.timestamp,
            4: self.is_outgoing,
            5: self.acked,
        }
        if self.ack_latency is not None:
            result[6] = self.ack_latency
        return result
    
    @classmethod
    def from_cbor(cls, data: dict) -> "ChatMessage":
        """Decode from CBOR indexed dict."""
        return cls(
            id=data[0],
            sender=data[1],
            content=data[2],
            timestamp=data[3],
            is_outgoing=data[4],
            acked=data.get(5, False),
            ack_latency=data.get(6),
        )
    
    @property
    def datetime(self) -> datetime:
        """Get timestamp as datetime object."""
        return datetime.fromtimestamp(self.timestamp / 1000)


@dataclass
class ChatHistory:
    """
    Message history manager with encrypted persistence.
    
    Mirrors Rust: ChatHistory { messages, max_messages }
    
    Attributes:
        messages: List of ChatMessage objects
        max_messages: Maximum messages to retain (default 1000)
    """
    messages: List[ChatMessage] = field(default_factory=list)
    max_messages: int = 1000
    
    def add_message(self, msg: ChatMessage) -> None:
        """
        Add message to history with deduplication.
        
        Ignores messages with duplicate IDs. Trims oldest messages
        if max_messages exceeded.
        """
        if any(m.id == msg.id for m in self.messages):
            return
        self.messages.append(msg)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def get_messages(self) -> List[ChatMessage]:
        """Get all messages in history."""
        return self.messages
    
    def to_cbor(self) -> dict:
        """Encode to CBOR-compatible structure."""
        return {
            0: [m.to_cbor() for m in self.messages],
            1: self.max_messages,
        }
    
    @classmethod
    def from_cbor(cls, data: dict) -> "ChatHistory":
        """Decode from CBOR structure."""
        history = cls(max_messages=data.get(1, 1000))
        history.messages = [ChatMessage.from_cbor(m) for m in data.get(0, [])]
        return history
    
    def save_encrypted(self, path: str | Path, key_seed: bytes) -> None:
        """
        Save history encrypted with AES-256-GCM.
        
        Args:
            path: File path to save to
            key_seed: Seed bytes for key derivation (any length)
        """
        # Derive 256-bit key from seed
        key = _derive_key(key_seed)
        
        # Serialize to CBOR
        plaintext = cbor2.dumps(self.to_cbor())
        
        # Encrypt with AES-256-GCM
        nonce = os.urandom(12)
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        # Write nonce + ciphertext
        Path(path).write_bytes(nonce + ciphertext)
    
    @classmethod
    def load_encrypted(cls, path: str | Path, key_seed: bytes) -> "ChatHistory":
        """
        Load history from encrypted file.
        
        Args:
            path: File path to load from
            key_seed: Seed bytes for key derivation
            
        Returns:
            ChatHistory instance (empty if file doesn't exist)
        """
        path = Path(path)
        if not path.exists():
            return cls()
        
        data = path.read_bytes()
        if len(data) < 12:
            return cls()
        
        # Derive key and decrypt
        key = _derive_key(key_seed)
        nonce, ciphertext = data[:12], data[12:]
        
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        
        return cls.from_cbor(cbor2.loads(plaintext))


def _derive_key(seed: bytes) -> bytes:
    """Derive 256-bit AES key from arbitrary seed using HKDF."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"decent_mesh_history",
    )
    return hkdf.derive(seed)
