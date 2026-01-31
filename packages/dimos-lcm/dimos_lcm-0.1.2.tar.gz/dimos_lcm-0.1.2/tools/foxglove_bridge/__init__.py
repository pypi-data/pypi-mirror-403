"""
Modular LCM to Foxglove WebSocket Bridge

This package provides a modular implementation of the LCM to Foxglove bridge,
split into logical components for better maintainability and organization.
"""

from .bridge import FoxgloveBridge
from .models import LcmMessage, TopicInfo

__all__ = ["FoxgloveBridge", "TopicInfo", "LcmMessage"]
