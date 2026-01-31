"""
Ed25519 identity management for DecentMesh.

Provides key generation and manipulation using the cryptography library,
matching the Rust bridge's ed25519-dalek implementation.

Usage:
    from decent_mesh.crypto.identity import generate_identity, get_public_key, get_identity_details
    
    # Generate new keypair
    private_hex = generate_identity()
    
    # Derive public key
    public_hex = get_public_key(private_hex)
    
    # Get full details
    details = get_identity_details(private_hex)
    # {"private_key_base64": "...", "public_key_base64": "...", "public_key_hex": "..."}
"""

import base64
from typing import TypedDict

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


class IdentityDetails(TypedDict):
    """Full identity key details."""
    private_key_base64: str
    public_key_base64: str
    public_key_hex: str


def generate_identity() -> str:
    """
    Generate a new Ed25519 private key.
    
    Returns:
        Private key as 64-character hex string (32 bytes)
    """
    private_key = Ed25519PrivateKey.generate()
    # Extract raw 32-byte seed
    raw_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    return raw_bytes.hex()


def get_public_key(private_key_hex: str) -> str:
    """
    Derive public key from private key.
    
    Args:
        private_key_hex: 64-character hex string (32-byte private key)
        
    Returns:
        Public key as 64-character hex string (32 bytes)
        
    Raises:
        ValueError: If private_key_hex is invalid
    """
    try:
        raw_bytes = bytes.fromhex(private_key_hex)
        if len(raw_bytes) != 32:
            raise ValueError(f"Private key must be 32 bytes, got {len(raw_bytes)}")
        
        private_key = Ed25519PrivateKey.from_private_bytes(raw_bytes)
        public_key = private_key.public_key()
        
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return public_bytes.hex()
    except Exception as e:
        raise ValueError(f"Invalid private key: {e}") from e


def get_identity_details(private_key_hex: str) -> IdentityDetails:
    """
    Get full identity details from private key.
    
    Args:
        private_key_hex: 64-character hex string
        
    Returns:
        Dict with private_key_base64, public_key_base64, public_key_hex
        
    Raises:
        ValueError: If private_key_hex is invalid
    """
    raw_bytes = bytes.fromhex(private_key_hex)
    if len(raw_bytes) != 32:
        raise ValueError(f"Private key must be 32 bytes, got {len(raw_bytes)}")
    
    private_key = Ed25519PrivateKey.from_private_bytes(raw_bytes)
    public_key = private_key.public_key()
    
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    return IdentityDetails(
        private_key_base64=base64.standard_b64encode(raw_bytes).decode(),
        public_key_base64=base64.standard_b64encode(public_bytes).decode(),
        public_key_hex=public_bytes.hex(),
    )


def private_key_from_hex(private_key_hex: str) -> Ed25519PrivateKey:
    """
    Load Ed25519 private key from hex string.
    
    Args:
        private_key_hex: 64-character hex string
        
    Returns:
        Ed25519PrivateKey instance
    """
    raw_bytes = bytes.fromhex(private_key_hex)
    return Ed25519PrivateKey.from_private_bytes(raw_bytes)


def sign_message(private_key_hex: str, message: bytes) -> bytes:
    """
    Sign a message with Ed25519.
    
    Args:
        private_key_hex: Signer's private key (hex)
        message: Message bytes to sign
        
    Returns:
        64-byte signature
    """
    private_key = private_key_from_hex(private_key_hex)
    return private_key.sign(message)


def verify_signature(public_key_hex: str, message: bytes, signature: bytes) -> bool:
    """
    Verify an Ed25519 signature.
    
    Args:
        public_key_hex: Signer's public key (hex)
        message: Original message bytes
        signature: 64-byte signature to verify
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        public_bytes = bytes.fromhex(public_key_hex)
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        public_key.verify(signature, message)
        return True
    except Exception:
        return False
