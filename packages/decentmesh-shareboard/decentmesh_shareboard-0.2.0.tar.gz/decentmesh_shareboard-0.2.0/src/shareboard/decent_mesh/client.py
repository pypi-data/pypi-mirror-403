"""
Main DecentMesh client interface.

Provides DecentMeshClient as the primary entry point for the SDK,
mirroring the Android bridge's AndroidClient API.

Usage:
    from decent_mesh import DecentMeshClient
    from decent_mesh.network import SimpleListener
    
    # Create client
    client = DecentMeshClient()
    
    # Generate identity
    private_key = client.generate_identity()
    public_key = client.get_public_key_from_private(private_key)
    
    # Connect with listener
    listener = SimpleListener(
        on_message=lambda s, c, b: print(f"{s}: {c}"),
        on_status=print,
        on_ready=lambda: print("Ready!")
    )
    await client.connect_to_network(private_key, listener)
    
    # Send message
    client.send_message("msg-001", recipient_key, "Hello!", ack=True)
"""

import asyncio
import uuid
from typing import List, Optional, Dict, Any

from decent_mesh.crypto.identity import (
    generate_identity as _generate_identity,
    get_public_key,
    get_identity_details as _get_identity_details,
)
from decent_mesh.crypto.encryption import encrypt_e2e
from decent_mesh.models.messages import ChatMessage
from decent_mesh.models.packets import DataPacket
from decent_mesh.network.manager import NetworkManager, MessageListener
from decent_mesh.network.circuits import CircuitInfo, CircuitCounts
from decent_mesh.utils.encoding import cbor_encode


class DecentMeshClient:
    """
    Main DecentMesh client interface.
    
    Provides identity management, network connection, messaging,
    and circuit management APIs matching the Android bridge.
    
    Example:
        client = DecentMeshClient()
        key = client.generate_identity()
        await client.connect_to_network(key, my_listener)
        client.send_message("id", target, "Hello", ack=True)
    """
    
    def __init__(self, seed_relays: Optional[List[str]] = None):
        """
        Initialize client.
        
        Args:
            seed_relays: Optional list of seed relay addresses.
                        Uses defaults if not specified.
        """
        self._manager = NetworkManager(seed_relays=seed_relays)
        self._private_key_hex: Optional[str] = None
        self._public_key_hex: Optional[str] = None
    
    # ============ Identity ============
    
    def generate_identity(self) -> str:
        """
        Generate a new Ed25519 identity keypair.
        
        Returns:
            Private key as 64-character hex string
        """
        return _generate_identity()
    
    def get_public_key_from_private(self, private_key_hex: str) -> str:
        """
        Derive public key from private key.
        
        Args:
            private_key_hex: 64-character hex private key
            
        Returns:
            Public key as 64-character hex string
            
        Raises:
            ValueError: If private key is invalid
        """
        return get_public_key(private_key_hex)
    
    def get_identity_details(self, private_key_hex: str) -> Dict[str, str]:
        """
        Get full identity details from private key.
        
        Args:
            private_key_hex: 64-character hex private key
            
        Returns:
            Dict with private_key_base64, public_key_base64, public_key_hex
        """
        return _get_identity_details(private_key_hex)
    
    # ============ Network ============
    
    async def connect_to_network(
        self,
        private_key_hex: str,
        listener: MessageListener
    ) -> None:
        """
        Connect to the DecentMesh network.
        
        Args:
            private_key_hex: Your Ed25519 private key (hex)
            listener: Callback interface for events
        """
        self._private_key_hex = private_key_hex
        self._public_key_hex = get_public_key(private_key_hex)
        
        self._manager.set_listener(listener)
        await self._manager.connect_to_network(private_key_hex)
    
    def connect_to_network_sync(
        self,
        private_key_hex: str,
        listener: MessageListener
    ) -> None:
        """
        Synchronous wrapper for connect_to_network.
        
        Creates event loop if needed.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.connect_to_network(private_key_hex, listener))
        except RuntimeError:
            asyncio.run(self.connect_to_network(private_key_hex, listener))
    
    async def disconnect(self) -> None:
        """Disconnect from network."""
        await self._manager.disconnect()
    
    def is_ready(self) -> bool:
        """
        Check if network is ready.
        
        Returns:
            True if connected relays > 0 and circuits > 0
        """
        return self._manager.is_ready
    
    def get_connected_relays(self) -> List[str]:
        """
        Get list of connected relay addresses.
        
        Returns:
            List of "host:port" strings
        """
        return self._manager.get_connected_relays()
    
    def get_relays_with_latency(self) -> List[Dict[str, Any]]:
        """
        Get relays with connection latency.
        
        Returns:
            List of {"address": str, "latency_ms": int}
        """
        return self._manager.get_relays_with_latency()
    
    # ============ Messaging ============
    
    def send_message(
        self,
        id: str,
        target_pubkey: str,
        content: str,
        ack: bool = True
    ) -> bool:
        """
        Send a text message to target.
        
        Args:
            id: Unique message ID
            target_pubkey: Recipient's public key (hex)
            content: Message text content
            ack: Request delivery acknowledgment
            
        Returns:
            True if sent immediately, False if queued
        """
        if not self._private_key_hex:
            return False
        
        # Create ChatMessage
        msg = ChatMessage(
            id=id,
            sender=self._public_key_hex or "",
            content=content,
            timestamp=int(asyncio.get_event_loop().time() * 1000),
            is_outgoing=True,
        )
        
        # Encode and encrypt
        msg_cbor = cbor_encode(msg.to_cbor())
        encrypted = encrypt_e2e(self._private_key_hex, target_pubkey, msg_cbor)
        
        # Wrap in DataPacket
        packet = DataPacket.msg(encrypted)
        packet_data = cbor_encode(packet.to_cbor())
        
        # Queue for sending
        self._manager.queue_message(id, target_pubkey, packet_data)
        
        # In real impl: attempt immediate send via CircuitManager
        return len(self._manager.get_connected_relays()) > 0
    
    def send_block_message(
        self,
        target_pubkey: str,
        data: bytes,
        ack: bool = True
    ) -> None:
        """
        Send raw binary data to target.
        
        Args:
            target_pubkey: Recipient's public key (hex)
            data: Raw bytes to send
            ack: Request delivery acknowledgment
        """
        if not self._private_key_hex:
            raise RuntimeError("Not connected to network")
        
        # Encrypt data
        encrypted = encrypt_e2e(self._private_key_hex, target_pubkey, data)
        
        # Wrap in DataPacket
        packet = DataPacket.msg(encrypted)
        packet_data = cbor_encode(packet.to_cbor())
        
        msg_id = str(uuid.uuid4())
        self._manager.queue_message(msg_id, target_pubkey, packet_data)
    
    # ============ Circuits ============
    
    def get_circuit_counts(self) -> Dict[str, int]:
        """
        Get circuit hop distribution summary.
        
        Returns:
            {"total": int, "1_hop": int, "2_hop": int, "3_hop_plus": int}
        """
        # In real impl: query CircuitManager
        return {
            "total": self._manager._circuit_count,
            "1_hop": self._manager._circuit_count,
            "2_hop": 0,
            "3_hop_plus": 0,
        }
    
    def get_circuits_detailed(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about all circuits.
        
        Returns:
            List of circuit info dicts with id, length, path, verified, etc.
        """
        # In real impl: query CircuitManager.get_active_circuits()
        return []
    
    def set_hop_range(self, min_hops: int, max_hops: int) -> None:
        """
        Configure circuit hop count range.
        
        Args:
            min_hops: Minimum relay hops (1-3)
            max_hops: Maximum relay hops (1-3)
        """
        self._manager.set_hop_range(min_hops, max_hops)
    
    def delete_circuit(self, circuit_id: str) -> None:
        """
        Delete a specific circuit.
        
        Args:
            circuit_id: Circuit identifier to remove
        """
        # In real impl: CircuitManager.remove_circuit()
        pass
    
    # ============ Peers ============
    
    def get_peers_info(self) -> Dict[str, Any]:
        """
        Get information about discovered peers.
        
        Returns:
            {"known_relays_db_count": int, "discovered_peers_count": int, "peers_list": []}
        """
        return {
            "known_relays_db_count": len(self._manager._known_relays),
            "discovered_peers_count": 0,
            "peers_list": [],
        }
