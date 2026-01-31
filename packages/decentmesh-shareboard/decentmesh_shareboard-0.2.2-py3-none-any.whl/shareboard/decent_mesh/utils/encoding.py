"""
CBOR encoding utilities for DecentMesh.

Provides helpers for CBOR serialization using cbor2, with convenience
functions for common operations.

Usage:
    from shareboard.decent_mesh.utils.encoding import cbor_encode, cbor_decode, parse_block_info
    
    # Basic encode/decode
    data = cbor_encode({"key": "value"})
    obj = cbor_decode(data)
    
    # Parse block_info from callbacks
    info = parse_block_info(block_info_bytes)
"""

from typing import Any

import cbor2

from shareboard.decent_mesh.models.blocks import BlockInfo


def cbor_encode(obj: Any) -> bytes:
    """
    Encode object to CBOR bytes.
    
    Args:
        obj: Python object to encode (dict, list, primitives)
        
    Returns:
        CBOR-encoded bytes
    """
    return cbor2.dumps(obj)


def cbor_decode(data: bytes) -> Any:
    """
    Decode CBOR bytes to Python object.
    
    Args:
        data: CBOR-encoded bytes
        
    Returns:
        Decoded Python object
    """
    return cbor2.loads(data)


def parse_block_info(data: bytes) -> BlockInfo:
    """
    Parse BlockInfo from CBOR bytes.
    
    Convenience wrapper for BlockInfo.from_cbor().
    
    Args:
        data: CBOR-encoded block_info from message callback
        
    Returns:
        BlockInfo instance
    """
    return BlockInfo.from_cbor(data)


def encode_indexed(obj: dict) -> bytes:
    """
    Encode dict with integer keys for indexed CBOR.
    
    Used for minicbor-compatible encoding where fields use
    #[n(x)] annotations instead of string keys.
    
    Args:
        obj: Dict with integer keys
        
    Returns:
        CBOR bytes
    """
    return cbor2.dumps(obj)


def decode_indexed(data: bytes) -> dict:
    """
    Decode indexed CBOR to dict with integer keys.
    
    Args:
        data: CBOR bytes with integer keys
        
    Returns:
        Dict with integer keys
    """
    return cbor2.loads(data)
