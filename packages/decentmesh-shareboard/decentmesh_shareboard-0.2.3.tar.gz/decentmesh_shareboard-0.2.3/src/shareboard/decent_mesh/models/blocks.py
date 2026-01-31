"""
Block metadata models for DecentMesh.

BlockInfo represents the metadata attached to received blocks, parsed from
CBOR bytes in message callbacks.

Usage:
    from shareboard.decent_mesh.models.blocks import BlockInfo
    from shareboard.decent_mesh.utils.encoding import parse_block_info
    
    # In message callback
    def on_message(sender: str, content: str, block_info: bytes):
        info = parse_block_info(block_info)
        print(f"From: {info.pub_key}, at: {info.datetime}")
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import cbor2


@dataclass
class BlockInfo:
    """
    Block metadata received with messages.
    
    Mirrors Android bridge block_info CBOR structure:
    {"hash": bytes, "timestamp": i64, "pub_key": str, "nonce": u32, "index": u64}
    
    Attributes:
        hash: Block hash bytes
        timestamp: Block creation time (Unix seconds)
        pub_key: Sender's public key (hex string)
        nonce: Proof-of-work nonce
        index: Block index in sender's chain
    """
    hash: bytes
    timestamp: int
    pub_key: str
    nonce: int
    index: int
    
    @classmethod
    def from_cbor(cls, data: bytes) -> "BlockInfo":
        """
        Parse BlockInfo from CBOR bytes.
        
        Args:
            data: CBOR-encoded block_info bytes from callback
            
        Returns:
            BlockInfo instance
        """
        decoded = cbor2.loads(data)
        return cls(
            hash=decoded.get("hash", b""),
            timestamp=decoded.get("timestamp", 0),
            pub_key=decoded.get("pub_key", ""),
            nonce=decoded.get("nonce", 0),
            index=decoded.get("index", 0),
        )
    
    def to_cbor(self) -> bytes:
        """Encode to CBOR bytes."""
        return cbor2.dumps({
            "hash": self.hash,
            "timestamp": self.timestamp,
            "pub_key": self.pub_key,
            "nonce": self.nonce,
            "index": self.index,
        })
    
    @property
    def datetime(self) -> datetime:
        """Get timestamp as datetime object."""
        return datetime.fromtimestamp(self.timestamp)
    
    @property
    def hash_hex(self) -> str:
        """Get hash as hex string."""
        return self.hash.hex()
