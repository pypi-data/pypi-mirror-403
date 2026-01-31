"""
Data packet models for DecentMesh wire protocol.

All packets use CBOR encoding via cbor2. The packet types mirror the Rust
Android bridge implementation for cross-platform compatibility.

Usage:
    from shareboard.decent_mesh.models.packets import DataPacket, MediaChunk, CallSignal
    
    # Create a message packet
    packet = DataPacket.msg(encrypted_content)
    
    # Create media packet
    audio = MediaChunk.audio(sample_idx=0, data=pcm_bytes, timestamp=now_ms, sample_rate=16000)
    packet = DataPacket.media(audio)
    
    # Serialize/deserialize
    from shareboard.decent_mesh.utils.encoding import cbor_encode, cbor_decode
    wire_data = cbor_encode(packet.to_cbor())
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Union


class PacketType(IntEnum):
    """Packet type discriminator matching Rust enum indices."""
    MSG = 0
    MEDIA = 1
    SIGNAL = 2


class MediaType(IntEnum):
    """Media chunk type discriminator."""
    VIDEO = 0
    AUDIO = 1


class SignalType(IntEnum):
    """Call signaling type."""
    REQUEST = 0
    ACCEPT = 1
    REJECT = 2
    END = 3


@dataclass
class CallSignal:
    """
    Call signaling packet for voice/video calls.
    
    Mirrors Rust: CallSignal { Request { video }, Accept, Reject, End }
    
    Attributes:
        signal_type: SignalType enum value
        video: For REQUEST, whether video is requested (default False)
    """
    signal_type: SignalType
    video: bool = False
    
    @classmethod
    def request(cls, video: bool = False) -> "CallSignal":
        """Create a call request signal."""
        return cls(SignalType.REQUEST, video)
    
    @classmethod
    def accept(cls) -> "CallSignal":
        """Create a call accept signal."""
        return cls(SignalType.ACCEPT)
    
    @classmethod
    def reject(cls) -> "CallSignal":
        """Create a call reject signal."""
        return cls(SignalType.REJECT)
    
    @classmethod
    def end(cls) -> "CallSignal":
        """Create a call end signal."""
        return cls(SignalType.END)
    
    def to_cbor(self) -> list:
        """Encode to CBOR-compatible structure (indexed array)."""
        if self.signal_type == SignalType.REQUEST:
            return [self.signal_type.value, {"video": self.video}]
        return [self.signal_type.value]
    
    @classmethod
    def from_cbor(cls, data: list) -> "CallSignal":
        """Decode from CBOR structure."""
        sig_type = SignalType(data[0])
        video = data[1].get("video", False) if len(data) > 1 else False
        return cls(sig_type, video)


@dataclass
class MediaChunk:
    """
    Media data chunk for streaming audio/video.
    
    Mirrors Rust: MediaChunk { Video { frame_idx, data, timestamp }, 
                               Audio { sample_idx, data, timestamp, sample_rate } }
    
    Attributes:
        media_type: VIDEO or AUDIO
        index: Frame index (video) or sample index (audio)
        data: Raw media bytes
        timestamp: Unix timestamp in milliseconds
        sample_rate: Audio sample rate (only for AUDIO, default 16000)
    """
    media_type: MediaType
    index: int
    data: bytes
    timestamp: int
    sample_rate: int = 16000
    
    @classmethod
    def video(cls, frame_idx: int, data: bytes, timestamp: int) -> "MediaChunk":
        """Create a video frame chunk."""
        return cls(MediaType.VIDEO, frame_idx, data, timestamp)
    
    @classmethod
    def audio(cls, sample_idx: int, data: bytes, timestamp: int, 
              sample_rate: int = 16000) -> "MediaChunk":
        """Create an audio sample chunk (default 16kHz)."""
        return cls(MediaType.AUDIO, sample_idx, data, timestamp, sample_rate)
    
    def to_cbor(self) -> list:
        """Encode to CBOR-compatible structure."""
        if self.media_type == MediaType.VIDEO:
            return [self.media_type.value, {
                0: self.index,      # frame_idx
                1: self.data,       # data (bytes)
                2: self.timestamp,  # timestamp
            }]
        else:  # AUDIO
            return [self.media_type.value, {
                0: self.index,       # sample_idx
                1: self.data,        # data (bytes)
                2: self.timestamp,   # timestamp
                3: self.sample_rate, # sample_rate
            }]
    
    @classmethod
    def from_cbor(cls, data: list) -> "MediaChunk":
        """Decode from CBOR structure."""
        media_type = MediaType(data[0])
        payload = data[1]
        if media_type == MediaType.VIDEO:
            return cls.video(payload[0], payload[1], payload[2])
        else:
            return cls.audio(payload[0], payload[1], payload[2], payload.get(3, 16000))


@dataclass
class DataPacket:
    """
    Top-level wire packet wrapping message, media, or signal data.
    
    Mirrors Rust: DataPacket { Msg(Vec<u8>), Media(MediaChunk), Signal(CallSignal) }
    
    Attributes:
        packet_type: MSG, MEDIA, or SIGNAL
        payload: bytes (for MSG), MediaChunk, or CallSignal
    """
    packet_type: PacketType
    payload: Union[bytes, MediaChunk, CallSignal]
    
    @classmethod
    def msg(cls, encrypted_content: bytes) -> "DataPacket":
        """Create a message packet with encrypted content."""
        return cls(PacketType.MSG, encrypted_content)
    
    @classmethod
    def media(cls, chunk: MediaChunk) -> "DataPacket":
        """Create a media packet."""
        return cls(PacketType.MEDIA, chunk)
    
    @classmethod
    def signal(cls, sig: CallSignal) -> "DataPacket":
        """Create a signaling packet."""
        return cls(PacketType.SIGNAL, sig)
    
    def to_cbor(self) -> list:
        """
        Encode to CBOR-compatible structure.
        
        Returns indexed array: [type_index, payload_data]
        """
        if self.packet_type == PacketType.MSG:
            return [self.packet_type.value, self.payload]
        elif self.packet_type == PacketType.MEDIA:
            return [self.packet_type.value, self.payload.to_cbor()]
        else:  # SIGNAL
            return [self.packet_type.value, self.payload.to_cbor()]
    
    @classmethod
    def from_cbor(cls, data: list) -> "DataPacket":
        """Decode from CBOR structure."""
        ptype = PacketType(data[0])
        if ptype == PacketType.MSG:
            return cls.msg(data[1])
        elif ptype == PacketType.MEDIA:
            return cls.media(MediaChunk.from_cbor(data[1]))
        else:
            return cls.signal(CallSignal.from_cbor(data[1]))
