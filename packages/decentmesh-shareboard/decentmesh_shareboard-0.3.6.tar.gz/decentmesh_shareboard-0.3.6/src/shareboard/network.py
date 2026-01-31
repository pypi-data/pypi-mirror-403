"""
Network integration for ShareBoard using DecentMesh native Rust bindings.

Provides a Qt-compatible wrapper around the native DecentMesh client
with signal-based event delivery for thread-safe UI updates.
"""

import threading
import time
import os
from typing import List, Optional

from PySide6.QtCore import QObject, Signal

# Import native Rust bindings
try:
    import decent_mesh
    NATIVE_AVAILABLE = True
except ImportError:
    NATIVE_AVAILABLE = False
    print("[Network] WARNING: Native decent_mesh module not available!")

from shareboard.models import Identity


# Default seed relays for production
DEFAULT_SEED_RELAYS = [
    "fe.decentmesh.net:8888",
    "fa.decentmesh.net:8888",
    "93.153.22.172:8888",
    "cn.decentmesh.net:8888",
]

# Local development relays
LOCAL_RELAYS = [
    "127.0.0.1:8888",
    "127.0.0.1:8889",
]


class NetworkSignals(QObject):
    """
    Qt signals for thread-safe network event delivery.
    
    These signals bridge the network thread to the Qt main thread.
    """
    
    # Emitted when a text message is received
    # Args: sender_key (str), content (str), timestamp (float)
    message_received = Signal(str, str, float)
    
    # Emitted when connection status changes
    # Args: status (str)
    status_changed = Signal(str)
    
    # Emitted when network is ready (connected to a relay)
    connection_ready = Signal()
    
    # Emitted when a message was successfully sent
    # Args: msg_id (str)
    message_sent = Signal(str)


class NetworkManager:
    """
    Manages DecentMesh network connection for ShareBoard.
    
    Uses native Rust bindings for real QUIC-based network transport.
    All network operations are thread-safe.
    
    Usage:
        manager = NetworkManager()
        manager.signals.message_received.connect(on_message)
        manager.start(private_key_hex)
        manager.send_to_all("Hello!", active_contacts)
    """
    
    def __init__(self, use_local_relays: bool = False, config_path: Optional[str] = None):
        """
        Initialize network manager.
        
        Args:
            use_local_relays: If True, connect to localhost relays (for testing)
            config_path: Path to network_config.toml (defaults to current dir)
        """
        self.signals = NetworkSignals()
        self._client = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._private_key: Optional[str] = None
        self._public_key: Optional[str] = None
        self._use_local = use_local_relays
        self._config_path = config_path or self._find_config_path()
        
    def _find_config_path(self) -> str:
        """Find network_config.toml in standard locations."""
        candidates = [
            "network_config.toml",
            os.path.join(os.path.dirname(__file__), "network_config.toml"),
            os.path.expanduser("~/.decentmesh/network_config.toml"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        # Return default - client will error if not found
        return "network_config.toml"
    
    @property
    def is_running(self) -> bool:
        """Check if network manager is running."""
        return self._running and self._thread is not None and self._thread.is_alive()
    
    @property
    def is_ready(self) -> bool:
        """Check if network is ready for messaging."""
        if not NATIVE_AVAILABLE:
            return False
        return self._client is not None and self._client.is_ready()
    
    @property
    def public_key(self) -> Optional[str]:
        """Get user's public key."""
        return self._public_key
    
    def start(self, private_key_hex: str) -> None:
        """
        Start the network manager with the given identity.
        
        Args:
            private_key_hex: 64-character hex private key
        """
        if self._running:
            return
        
        if not NATIVE_AVAILABLE:
            self.signals.status_changed.emit("Native module not available!")
            return
        
        self._private_key = private_key_hex
        self._running = True
        
        # Get public key from native module
        try:
            self._client = decent_mesh.DecentMeshClient()
            self._public_key = self._client.get_public_key(private_key_hex)
        except Exception as e:
            self.signals.status_changed.emit(f"Key error: {e}")
            self._running = False
            return
        
        # Start background thread for connection
        self._thread = threading.Thread(target=self._connect_thread, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the network manager."""
        self._running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        self._thread = None
        self._client = None
    
    def send_to_all(self, content: str, identities: List[Identity]) -> None:
        """
        Send a text message to all active identities.
        
        Args:
            content: Text content to share
            identities: List of contacts (only active ones will receive)
        """
        if not self._client or not self._running:
            print("[Network] Cannot send - not connected")
            return
        
        if not self.is_ready:
            print("[Network] Cannot send - network not ready")
            return
        
        active = [i for i in identities if i.is_active]
        
        for identity in active:
            try:
                msg_id = f"share-{identity.public_key[:8]}-{int(time.time() * 1000)}"
                print(f"[Network] Sending to {identity.public_key[:16]}...")
                
                success = self._client.send_message(
                    target_pubkey=identity.public_key,
                    content=content,
                    msg_id=msg_id
                )
                
                if success:
                    print(f"[Network] Message sent: {msg_id}")
                    self.signals.message_sent.emit(msg_id)
                else:
                    print(f"[Network] Send failed for {identity.public_key[:16]}")
                    self.signals.status_changed.emit(f"Send failed to {identity.name}")
                    
            except Exception as e:
                print(f"[Network] Send error: {e}")
                self.signals.status_changed.emit(f"Send error: {e}")
    
    def _connect_thread(self) -> None:
        """Background thread: connect to relays."""
        try:
            self._do_connect()
        except Exception as e:
            print(f"[Network] Connection error: {e}")
            self.signals.status_changed.emit(f"Network error: {e}")
    
    def _do_connect(self) -> None:
        """Perform the actual connection."""
        # Choose relay list
        relays = LOCAL_RELAYS if self._use_local else DEFAULT_SEED_RELAYS
        
        # Set up callbacks
        def on_status(msg):
            print(f"[Network] {msg}")
            self.signals.status_changed.emit(msg)
        
        def on_ready():
            print("[Network] READY!")
            self.signals.connection_ready.emit()
        
        self._client.set_callbacks(
            on_message=None,  # Not implemented yet in Rust binding
            on_status=on_status,
            on_ready=on_ready,
        )
        
        self.signals.status_changed.emit("Connecting to network...")
        print(f"[Network] Connecting with config: {self._config_path}")
        print(f"[Network] Relays: {relays}")
        
        try:
            connected = self._client.connect(
                private_key_hex=self._private_key,
                relay_addresses=relays,
                config_path=self._config_path
            )
            
            if connected:
                print(f"[Network] Connected! My key: {self._public_key[:16]}...")
            else:
                print("[Network] Failed to connect to any relay")
                self.signals.status_changed.emit("Connection failed - no relays available")
                
        except Exception as e:
            print(f"[Network] Connect exception: {e}")
            self.signals.status_changed.emit(f"Connection error: {e}")


# ============ Utility Functions ============

def create_identity() -> tuple[str, str]:
    """
    Generate a new identity keypair.
    
    Returns:
        Tuple of (private_key_hex, public_key_hex)
    """
    if not NATIVE_AVAILABLE:
        # Fallback to Python crypto
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        private_key = Ed25519PrivateKey.generate()
        private_bytes = private_key.private_bytes_raw()
        public_bytes = private_key.public_key().public_bytes_raw()
        return private_bytes.hex(), public_bytes.hex()
    
    client = decent_mesh.DecentMeshClient()
    private_key = client.generate_identity()
    public_key = client.get_public_key(private_key)
    return private_key, public_key


def validate_public_key(key: str) -> bool:
    """
    Validate a public key string.
    
    Args:
        key: Potential public key string
        
    Returns:
        True if valid 64-char hex string
    """
    if not isinstance(key, str):
        return False
    if len(key) != 64:
        return False
    try:
        int(key, 16)
        return True
    except ValueError:
        return False
