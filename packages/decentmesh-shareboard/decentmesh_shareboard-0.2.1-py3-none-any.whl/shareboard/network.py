"""
Network integration for ShareBoard using DecentMesh SDK.

Provides a Qt-compatible wrapper around the DecentMesh client
with signal-based event delivery for thread-safe UI updates.
"""

import asyncio
import threading
from typing import List, Optional, Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

# Import from bundled SDK
from shareboard.decent_mesh.client import DecentMeshClient
from shareboard.decent_mesh.network.manager import SimpleListener
from shareboard.decent_mesh.crypto.identity import generate_identity, get_public_key

from shareboard.models import Identity, SharedText


class NetworkSignals(QObject):
    """
    Qt signals for thread-safe network event delivery.
    
    These signals bridge the async network thread to the Qt main thread.
    """
    
    # Emitted when a text message is received
    # Args: sender_key (str), content (str), timestamp (float)
    message_received = Signal(str, str, float)
    
    # Emitted when connection status changes
    # Args: status (str)
    status_changed = Signal(str)
    
    # Emitted when network is ready (relays + circuits available)
    connection_ready = Signal()
    
    # Emitted when a message was successfully sent
    # Args: msg_id (str)
    message_sent = Signal(str)


class NetworkManager:
    """
    Manages DecentMesh network connection for ShareBoard.
    
    Runs the async DecentMesh client in a background thread and
    emits Qt signals for UI updates. All network operations are
    thread-safe.
    
    Usage:
        manager = NetworkManager()
        manager.signals.message_received.connect(on_message)
        manager.start(private_key_hex)
        manager.send_to_all("Hello!", active_contacts)
    """
    
    def __init__(self):
        self.signals = NetworkSignals()
        self._client: Optional[DecentMeshClient] = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._private_key: Optional[str] = None
        self._public_key: Optional[str] = None
    
    @property
    def is_running(self) -> bool:
        """Check if network manager is running."""
        return self._running and self._thread is not None and self._thread.is_alive()
    
    @property
    def is_ready(self) -> bool:
        """Check if network is ready for messaging."""
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
        
        self._private_key = private_key_hex
        self._public_key = get_public_key(private_key_hex)
        self._running = True
        
        # Start background thread
        self._thread = threading.Thread(target=self._run_network_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the network manager."""
        self._running = False
        
        if self._loop:
            # Schedule disconnect on the event loop
            asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        self._thread = None
        self._loop = None
        self._client = None
    
    def send_to_all(self, content: str, identities: List[Identity]) -> None:
        """
        Send a text message to all active identities.
        
        Args:
            content: Text content to share
            identities: List of contacts (only active ones will receive)
        """
        if not self._client or not self._running:
            return
        
        active = [i for i in identities if i.is_active]
        
        for identity in active:
            try:
                msg_id = f"share-{identity.public_key[:8]}-{asyncio.get_event_loop().time()}"
                self._client.send_message(
                    id=msg_id,
                    target_pubkey=identity.public_key,
                    content=content,
                    ack=True
                )
            except Exception as e:
                self.signals.status_changed.emit(f"Send error: {e}")
    
    def _run_network_loop(self) -> None:
        """Background thread: run the async event loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            self.signals.status_changed.emit(f"Network error: {e}")
        finally:
            self._loop.close()
    
    async def _connect_and_listen(self) -> None:
        """Connect to network and listen for messages."""
        self._client = DecentMeshClient()
        
        # Create listener that emits Qt signals AND logs to console
        def on_status_log(s):
            print(f"[Network] {s}")
            self.signals.status_changed.emit(s)
        
        listener = SimpleListener(
            on_message=self._on_message_callback,
            on_status=on_status_log,
            on_ready=lambda: (print("[Network] READY!"), self.signals.connection_ready.emit()),
            on_message_sent=lambda mid: self.signals.message_sent.emit(mid),
        )
        
        self.signals.status_changed.emit("Connecting to network...")
        print("[Network] Starting connection...")
        
        try:
            await self._client.connect_to_network(self._private_key, listener)
            
            # Keep running while active
            while self._running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.signals.status_changed.emit(f"Connection failed: {e}")
    
    async def _disconnect(self) -> None:
        """Disconnect from network."""
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
    
    def _on_message_callback(self, sender: str, content: str, block_info: bytes) -> None:
        """Handle incoming message from network."""
        import time
        # Emit signal with current timestamp (block_info parsing could be added later)
        self.signals.message_received.emit(sender, content, time.time())


# ============ Utility Functions ============

def create_identity() -> tuple[str, str]:
    """
    Generate a new identity keypair.
    
    Returns:
        Tuple of (private_key_hex, public_key_hex)
    """
    private_key = generate_identity()
    public_key = get_public_key(private_key)
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
