"""
Network manager for DecentMesh relay connections.

Provides the NetworkManager class for managing connections to relay nodes,
handling message receiving, and circuit maintenance.

Note: This is a structural interface. Full QUIC transport integration
requires the actual DecentMesh relay protocol implementation.

Usage:
    from shareboard.decent_mesh.network.manager import NetworkManager, MessageListener
    
    class MyListener(MessageListener):
        def on_message(self, sender, content, block_info):
            print(f"Message from {sender}: {content}")
        # ... other callbacks
    
    manager = NetworkManager()
    manager.set_listener(MyListener())
    await manager.connect_to_network(private_key_hex)
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import time


class MessageListener(ABC):
    """
    Callback interface for receiving network events.
    
    Implement this class to handle messages, status updates, and network events.
    All methods are called from the network receive loop.
    """
    
    @abstractmethod
    def on_message(self, sender: str, content: str, block_info: bytes) -> None:
        """
        Called when a text message is received.
        
        Args:
            sender: Sender's public key (hex)
            content: Decrypted message content
            block_info: CBOR-encoded BlockInfo metadata
        """
        pass
    
    @abstractmethod
    def on_data(self, sender: str, data: bytes, block_info: bytes) -> None:
        """
        Called when raw binary data is received.
        
        Args:
            sender: Sender's public key (hex)
            data: Raw decrypted bytes
            block_info: CBOR-encoded BlockInfo metadata
        """
        pass
    
    @abstractmethod
    def on_status(self, status: str) -> None:
        """
        Called for status updates (connection changes, etc).
        
        Args:
            status: Human-readable status message
        """
        pass
    
    @abstractmethod
    def on_message_sent(self, msg_id: str) -> None:
        """
        Called when a queued message is successfully sent.
        
        Args:
            msg_id: ID of the sent message
        """
        pass
    
    @abstractmethod
    def on_ready(self) -> None:
        """Called when network is ready (relays > 0 and circuits > 0)."""
        pass


class SimpleListener(MessageListener):
    """
    Simple listener implementation with optional callbacks.
    
    Usage:
        listener = SimpleListener(
            on_message=lambda s, c, b: print(f"{s}: {c}"),
            on_status=print
        )
    """
    
    def __init__(
        self,
        on_message: Optional[Callable[[str, str, bytes], None]] = None,
        on_data: Optional[Callable[[str, bytes, bytes], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_message_sent: Optional[Callable[[str], None]] = None,
        on_ready: Optional[Callable[[], None]] = None,
    ):
        self._on_message = on_message
        self._on_data = on_data
        self._on_status = on_status
        self._on_message_sent = on_message_sent
        self._on_ready = on_ready
    
    def on_message(self, sender: str, content: str, block_info: bytes) -> None:
        if self._on_message:
            self._on_message(sender, content, block_info)
    
    def on_data(self, sender: str, data: bytes, block_info: bytes) -> None:
        if self._on_data:
            self._on_data(sender, data, block_info)
    
    def on_status(self, status: str) -> None:
        if self._on_status:
            self._on_status(status)
    
    def on_message_sent(self, msg_id: str) -> None:
        if self._on_message_sent:
            self._on_message_sent(msg_id)
    
    def on_ready(self) -> None:
        if self._on_ready:
            self._on_ready()


@dataclass
class RelayConnection:
    """
    Information about a connected relay.
    
    Attributes:
        address: Relay address (host:port)
        latency_ms: Connection latency in milliseconds
        connected_at: Connection timestamp
        public_key: Relay's public key (if known)
    """
    address: str
    latency_ms: int = 0
    connected_at: datetime = field(default_factory=datetime.now)
    public_key: Optional[str] = None


@dataclass 
class PendingMessage:
    """A message queued for retry."""
    msg_id: str
    target_pubkey: str
    data: bytes
    created_at: float = field(default_factory=time.time)


class NetworkManager:
    """
    Manages DecentMesh relay connections and message routing.
    
    This is a high-level interface matching the Rust NetworkManager.
    Loads seed relays from config.toml if available.
    
    Attributes:
        seed_relays: List of seed relay addresses
        target_relay_count: Desired number of relay connections
        refresh_interval_secs: Maintenance loop interval
    """
    
    def __init__(
        self,
        seed_relays: Optional[List[str]] = None,
        target_relay_count: int = 5,
        refresh_interval_secs: int = 10,
        config_path: Optional[str] = None,
    ):
        """
        Initialize NetworkManager.
        
        Args:
            seed_relays: Override seed relay list. If None, loads from config.
            target_relay_count: Target number of relay connections
            refresh_interval_secs: Maintenance interval after ready
            config_path: Path to config.toml (None = search default paths)
        """
        # Load config
        from shareboard.decent_mesh.config import load_config
        try:
            config = load_config(config_path)
        except FileNotFoundError:
            config = load_config()  # Use defaults
        
        # Use provided seeds or load from config
        if seed_relays:
            self.seed_relays = seed_relays
        else:
            self.seed_relays = config.seed_addresses
        
        self.target_relay_count = target_relay_count or config.target_relay_count
        self.refresh_interval_secs = refresh_interval_secs or config.refresh_interval_secs
        
        # State
        self._connections: Dict[str, RelayConnection] = {}
        self._known_relays: set = set()
        self._pending_messages: Dict[str, PendingMessage] = {}
        self._listener: Optional[MessageListener] = None
        self._private_key_hex: Optional[str] = None
        self._is_running = False
        self._maintenance_task: Optional[asyncio.Task] = None
        
        # Circuit state
        self._circuit_count = 0
        self._hop_range = (config.min_hops, config.max_hops)
    
    def set_listener(self, listener: MessageListener) -> None:
        """Set the message callback listener."""
        self._listener = listener
    
    def notify_status(self, msg: str) -> None:
        """Send status update to listener."""
        if self._listener:
            self._listener.on_status(msg)
    
    @property
    def is_ready(self) -> bool:
        """Check if network is ready (relays + circuits available)."""
        return len(self._connections) > 0 and self._circuit_count > 0
    
    def get_connected_relays(self) -> List[str]:
        """Get list of connected relay addresses."""
        return list(self._connections.keys())
    
    def get_relays_with_latency(self) -> List[dict]:
        """Get relay info with latency."""
        return [
            {"address": addr, "latency_ms": conn.latency_ms}
            for addr, conn in self._connections.items()
        ]
    
    async def connect_to_network(self, private_key_hex: str) -> None:
        """
        Initialize network connection with identity.
        
        Args:
            private_key_hex: Ed25519 private key (hex)
        """
        self._private_key_hex = private_key_hex
        self._is_running = True
        self.notify_status("Network Manager Started")
        
        # Start maintenance loop
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
    
    async def disconnect(self) -> None:
        """Disconnect from network."""
        self._is_running = False
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
        self._connections.clear()
        self.notify_status("Disconnected")
    
    async def _maintenance_loop(self) -> None:
        """Background maintenance task."""
        was_ready = False
        
        while self._is_running:
            try:
                # 1. Check connection health
                dead = [
                    addr for addr, conn in self._connections.items()
                    if (datetime.now() - conn.connected_at).total_seconds() > 300
                    # In real impl: ping check
                ]
                for addr in dead:
                    del self._connections[addr]
                    self.notify_status(f"Relay disconnected: {addr}")
                
                # 2. Replenish connections
                count = len(self._connections)
                if count < self.target_relay_count:
                    self.notify_status(f"Connecting to relays...")
                    # Simulate connecting to first available seed relay
                    if self.seed_relays and count < 1:
                        seed = self.seed_relays[0]
                        self._connections[seed] = RelayConnection(
                            address=seed,
                            latency_ms=50,
                        )
                        self.notify_status(f"Connected to relay: {seed}")
                
                # 3. Maintain circuits (simulated)
                # In real impl: CircuitManager.maintain_circuits()
                self._circuit_count = max(1, len(self._connections))
                
                # 4. Retry pending messages
                if self._pending_messages:
                    sent_ids = []
                    for msg_id, pending in self._pending_messages.items():
                        # In real impl: attempt send
                        if self._connections:
                            sent_ids.append(msg_id)
                            if self._listener:
                                self._listener.on_message_sent(msg_id)
                    
                    for msg_id in sent_ids:
                        del self._pending_messages[msg_id]
                
                # 5. Check readiness
                is_ready = self.is_ready
                if is_ready and not was_ready:
                    self.notify_status("Network READY")
                    if self._listener:
                        self._listener.on_ready()
                    was_ready = True
                elif not is_ready:
                    was_ready = False
                
            except Exception as e:
                self.notify_status(f"Maintenance error: {e}")
            
            await asyncio.sleep(
                1 if not was_ready else self.refresh_interval_secs
            )
    
    def set_hop_range(self, min_hops: int, max_hops: int) -> None:
        """Configure circuit hop count range."""
        self._hop_range = (min_hops, max_hops)
    
    def queue_message(self, msg_id: str, target: str, data: bytes) -> None:
        """Queue a message for delivery/retry."""
        self._pending_messages[msg_id] = PendingMessage(
            msg_id=msg_id,
            target_pubkey=target,
            data=data,
        )
