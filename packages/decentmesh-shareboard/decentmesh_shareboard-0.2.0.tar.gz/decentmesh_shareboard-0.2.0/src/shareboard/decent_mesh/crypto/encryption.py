"""
E2E encryption utilities for DecentMesh.

Provides X25519 ECDH key exchange and AES-256-GCM encryption for
end-to-end encrypted messaging, matching the Rust AsymCrypt implementation.

Usage:
    from decent_mesh.crypto.encryption import encrypt_e2e, decrypt_e2e
    
    # Sender encrypts for recipient
    ciphertext = encrypt_e2e(
        sender_private_hex=my_private_key,
        recipient_public_hex=their_public_key,
        plaintext=message_bytes
    )
    
    # Recipient decrypts
    plaintext = decrypt_e2e(
        recipient_private_hex=my_private_key,
        sender_public_hex=their_public_key,
        ciphertext=ciphertext
    )
"""

import os
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def _ed25519_to_x25519_private(ed_private_hex: str) -> X25519PrivateKey:
    """
    Convert Ed25519 private key to X25519 for ECDH.
    
    Uses the same 32-byte seed for both curves (common practice).
    """
    raw_bytes = bytes.fromhex(ed_private_hex)
    # X25519 accepts 32 raw bytes
    return X25519PrivateKey.from_private_bytes(raw_bytes)


def _ed25519_to_x25519_public(ed_public_hex: str) -> bytes:
    """
    Convert Ed25519 public key bytes to X25519 format.
    
    Note: In practice, the network may exchange X25519 public keys directly.
    This is a simplified conversion for demonstration.
    """
    # For full compatibility, you'd need proper Ed25519->X25519 conversion
    # Here we assume the public key is already X25519-compatible (32 bytes)
    return bytes.fromhex(ed_public_hex)


def derive_shared_secret(
    my_private_hex: str,
    their_public_hex: str
) -> bytes:
    """
    Derive shared secret using X25519 ECDH.
    
    Args:
        my_private_hex: My Ed25519/X25519 private key (hex)
        their_public_hex: Their X25519 public key (hex)
        
    Returns:
        32-byte shared secret
    """
    my_x25519 = _ed25519_to_x25519_private(my_private_hex)
    their_public_bytes = bytes.fromhex(their_public_hex)
    their_x25519 = X25519PublicKey.from_public_bytes(their_public_bytes)
    
    return my_x25519.exchange(their_x25519)


def _derive_aes_key(shared_secret: bytes, context: bytes = b"decent_mesh_e2e") -> bytes:
    """Derive AES-256 key from ECDH shared secret using HKDF."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=context,
    )
    return hkdf.derive(shared_secret)


def encrypt_e2e(
    sender_private_hex: str,
    recipient_public_hex: str,
    plaintext: bytes
) -> bytes:
    """
    Encrypt message with E2E encryption (X25519 + AES-256-GCM).
    
    Args:
        sender_private_hex: Sender's private key (hex)
        recipient_public_hex: Recipient's X25519 public key (hex)
        plaintext: Message bytes to encrypt
        
    Returns:
        Ciphertext: nonce (12 bytes) + encrypted data + auth tag
    """
    # Derive shared secret
    shared_secret = derive_shared_secret(sender_private_hex, recipient_public_hex)
    aes_key = _derive_aes_key(shared_secret)
    
    # Encrypt with AES-256-GCM
    nonce = os.urandom(12)
    cipher = AESGCM(aes_key)
    ciphertext = cipher.encrypt(nonce, plaintext, None)
    
    return nonce + ciphertext


def decrypt_e2e(
    recipient_private_hex: str,
    sender_public_hex: str,
    ciphertext: bytes
) -> bytes:
    """
    Decrypt E2E encrypted message.
    
    Args:
        recipient_private_hex: Recipient's private key (hex)
        sender_public_hex: Sender's X25519 public key (hex)
        ciphertext: Encrypted data (nonce + ciphertext + tag)
        
    Returns:
        Decrypted plaintext bytes
        
    Raises:
        ValueError: If decryption fails (invalid key or corrupted data)
    """
    if len(ciphertext) < 12:
        raise ValueError("Ciphertext too short")
    
    nonce, encrypted = ciphertext[:12], ciphertext[12:]
    
    # Derive same shared secret (ECDH is symmetric)
    shared_secret = derive_shared_secret(recipient_private_hex, sender_public_hex)
    aes_key = _derive_aes_key(shared_secret)
    
    # Decrypt
    cipher = AESGCM(aes_key)
    try:
        return cipher.decrypt(nonce, encrypted, None)
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}") from e


def encrypt_symmetric(key_seed: bytes, plaintext: bytes) -> bytes:
    """
    Symmetric encryption with AES-256-GCM.
    
    Args:
        key_seed: Seed for key derivation (any length)
        plaintext: Data to encrypt
        
    Returns:
        nonce (12 bytes) + ciphertext + auth tag
    """
    key = _derive_aes_key(key_seed, b"decent_mesh_symmetric")
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    return nonce + cipher.encrypt(nonce, plaintext, None)


def decrypt_symmetric(key_seed: bytes, ciphertext: bytes) -> bytes:
    """
    Symmetric decryption with AES-256-GCM.
    
    Args:
        key_seed: Same seed used for encryption
        ciphertext: Encrypted data
        
    Returns:
        Decrypted plaintext
    """
    key = _derive_aes_key(key_seed, b"decent_mesh_symmetric")
    nonce, encrypted = ciphertext[:12], ciphertext[12:]
    cipher = AESGCM(key)
    return cipher.decrypt(nonce, encrypted, None)
