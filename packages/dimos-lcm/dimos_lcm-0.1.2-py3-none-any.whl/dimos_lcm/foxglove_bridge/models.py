"""
Data models and classes for the LCM-Foxglove bridge.
"""

from dataclasses import dataclass
from typing import Any, Optional
from foxglove_websocket.types import ChannelId


@dataclass
class TopicInfo:
    """Information about an LCM topic with schema"""
    name: str  # Base topic name (without schema) for Foxglove
    full_topic_name: str  # Full LCM topic name including schema annotation
    schema_type: str  # Schema type (e.g., "sensor_msgs.Image")
    schema: dict  # JSON schema
    channel_id: Optional[ChannelId] = None  # Foxglove channel ID
    lcm_class: Any = None  # LCM message class
    package: str = ""  # ROS package name
    msg_type: str = ""  # ROS message type
    foxglove_schema_name: str = ""  # Schema name in Foxglove format
    last_sent_timestamp: float = 0.0  # Time the last message was sent (for throttling)
    message_count: int = 0  # Number of messages received
    is_high_frequency: bool = False  # Flag for topics that send many messages
    cache_hash: Optional[int] = None  # Hash of the last message (for message deduplication)
    rate_limit_ms: int = 0  # Rate limit in milliseconds (0 = no limit)
    priority: int = 0  # Message priority (higher = more important)


@dataclass
class LcmMessage:
    """Container for an LCM message"""
    topic_info: TopicInfo
    data: bytes
    receive_time: float
    priority: int = 0  # Higher priority will be processed first
    
    def __lt__(self, other):
        # Compare based on priority (higher priority comes first)
        if not isinstance(other, LcmMessage):
            return NotImplemented
        return self.priority > other.priority  # Reversed for higher priority first
    
    def __gt__(self, other):
        if not isinstance(other, LcmMessage):
            return NotImplemented
        return self.priority < other.priority  # Reversed for higher priority first
    
    def __eq__(self, other):
        if not isinstance(other, LcmMessage):
            return NotImplemented
        return self.priority == other.priority