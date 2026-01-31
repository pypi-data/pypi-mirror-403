"""
DecentMesh Python SDK

A modular Python client for the DecentMesh decentralized network.
"""

from decent_mesh.client import DecentMeshClient
from decent_mesh.models.packets import DataPacket, MediaChunk, CallSignal
from decent_mesh.models.messages import ChatMessage, ChatHistory
from decent_mesh.models.blocks import BlockInfo

__version__ = "0.1.0"
__all__ = [
    "DecentMeshClient",
    "DataPacket",
    "MediaChunk", 
    "CallSignal",
    "ChatMessage",
    "ChatHistory",
    "BlockInfo",
]
