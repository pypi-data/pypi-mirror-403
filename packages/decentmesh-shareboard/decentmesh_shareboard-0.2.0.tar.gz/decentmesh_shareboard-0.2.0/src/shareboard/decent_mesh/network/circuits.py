"""
Circuit management interface for DecentMesh.

Provides data structures for onion routing circuit information,
matching the Rust CircuitManager API.

Usage:
    from decent_mesh.network.circuits import CircuitInfo, CircuitNode
    
    # Parse circuit details
    circuits = client.get_circuits_detailed()
    for c in circuits:
        print(f"Circuit {c['id']}: {c['length']} hops, verified={c['verified']}")
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class CircuitNode:
    """
    A node in a circuit path.
    
    Attributes:
        id: Node's public key (hex)
        ip: Node's IP address
        port: Node's port number
    """
    id: str
    ip: str
    port: int = 0
    
    def __str__(self) -> str:
        return f"{self.id[:8]}...@{self.ip}:{self.port}"


@dataclass
class CircuitInfo:
    """
    Information about an onion routing circuit.
    
    Mirrors Rust circuit data returned by get_circuits_detailed().
    
    Attributes:
        id: Unique circuit identifier
        path: List of nodes in the circuit
        created_at: Circuit creation time
        used_blocks: Number of blocks routed through circuit
        verified: Whether circuit has been verified
    """
    id: str
    path: List[CircuitNode] = field(default_factory=list)
    created_at: Optional[datetime] = None
    used_blocks: int = 0
    verified: bool = False
    
    @property
    def length(self) -> int:
        """Number of relay hops (excludes self)."""
        return max(0, len(self.path) - 1)
    
    @property
    def hop_count(self) -> int:
        """Alias for length."""
        return self.length
    
    @classmethod
    def from_dict(cls, data: dict) -> "CircuitInfo":
        """
        Parse from dict returned by client.
        
        Args:
            data: Dict with id, length, path, created_ago_secs, used_blocks, verified
        """
        path = []
        for node_str in data.get("path", []):
            # Format: "id:ip" or "id:ip:port"
            parts = node_str.split(":")
            if len(parts) >= 2:
                path.append(CircuitNode(
                    id=parts[0],
                    ip=parts[1],
                    port=int(parts[2]) if len(parts) > 2 else 0
                ))
        
        created_ago = data.get("created_ago_secs", 0)
        created_at = datetime.now()
        if created_ago:
            from datetime import timedelta
            created_at = datetime.now() - timedelta(seconds=created_ago)
        
        return cls(
            id=data.get("id", ""),
            path=path,
            created_at=created_at,
            used_blocks=data.get("used_blocks", 0),
            verified=data.get("verified", False),
        )


@dataclass
class CircuitCounts:
    """
    Summary of circuit hop distribution.
    
    Attributes:
        total: Total number of circuits
        one_hop: Circuits with 1 relay hop
        two_hop: Circuits with 2 relay hops
        three_hop_plus: Circuits with 3+ relay hops
    """
    total: int = 0
    one_hop: int = 0
    two_hop: int = 0
    three_hop_plus: int = 0
    
    @classmethod
    def from_dict(cls, data: dict) -> "CircuitCounts":
        """Parse from client response dict."""
        return cls(
            total=data.get("total", 0),
            one_hop=data.get("1_hop", 0),
            two_hop=data.get("2_hop", 0),
            three_hop_plus=data.get("3_hop_plus", 0),
        )
