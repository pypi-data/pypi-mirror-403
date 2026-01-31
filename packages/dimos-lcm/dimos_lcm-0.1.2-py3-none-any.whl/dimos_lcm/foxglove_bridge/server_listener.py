"""
Server listener for handling messages from Foxglove clients.
"""

import json
from typing import Dict, Any, Optional
from foxglove_websocket.server import FoxgloveServerListener
from foxglove_websocket.types import ChannelId, ClientChannel, ClientChannelId
from .config import logger
from .reverse_converter import ReverseMessageConverter


class BridgeServerListener(FoxgloveServerListener):
    """Server listener that handles messages from Foxglove clients"""
    
    def __init__(self, bridge):
        """
        Initialize the server listener
        
        Args:
            bridge: Reference to the main bridge instance
        """
        self.bridge = bridge
        self.client_channels: Dict[ChannelId, Dict[str, Any]] = {}
        self.reverse_converter = ReverseMessageConverter()
        
    async def on_subscribe(self, server, channel_id: ChannelId):
        """Called when a client subscribes to a channel"""
        logger.info(f"Client subscribed to channel {channel_id}")
        
    async def on_unsubscribe(self, server, channel_id: ChannelId):
        """Called when a client unsubscribes from a channel"""
        logger.info(f"Client unsubscribed from channel {channel_id}")
        
    async def on_client_advertise(self, server, channel):
        """Called when a client advertises a channel for publishing"""
        logger.info(f"Client advertised channel: {channel}")
        
        # Handle both dict and ClientChannel object
        if isinstance(channel, dict):
            channel_id = channel.get("id")
            topic_name = channel.get("topic", f"foxglove_channel_{channel_id}")
            schema_name = channel.get("schemaName", "unknown")
            encoding = channel.get("encoding", "json")
        else:
            channel_id = channel.id
            topic_name = channel.topic
            schema_name = channel.schema_name
            encoding = channel.encoding
        
        # Store the channel info for later use
        channel_info = {
            "topic": topic_name,
            "encoding": encoding,
            "schemaName": schema_name
        }
        self.client_channels[channel_id] = channel_info
        
        logger.info(f"Client wants to publish to topic '{topic_name}' with schema '{schema_name}' using encoding '{encoding}'")
        
    async def on_client_unadvertise(self, server, channel_id: ChannelId):
        """Called when a client stops advertising a channel"""
        logger.info(f"Client stopped advertising channel {channel_id}")
        
        # Remove the channel from our tracking
        if channel_id in self.client_channels:
            channel_info = self.client_channels.pop(channel_id)
            topic_name = channel_info.get("topic", f"foxglove_channel_{channel_id}")
            logger.info(f"Removed client channel for topic '{topic_name}'")
    
    async def on_client_message(self, server, channel_id: ClientChannelId, payload: bytes):
        """Called when a client publishes a message"""
        logger.info(f"=== RECEIVED CLIENT MESSAGE ===")
        logger.info(f"Channel ID: {channel_id}")
        logger.info(f"Payload length: {len(payload)}")
        
        try:
            # Get channel info
            channel_info = self.client_channels.get(channel_id)
            if not channel_info:
                logger.warning(f"Received message on unknown channel {channel_id}")
                return
            
            topic_name = channel_info.get("topic", f"foxglove_channel_{channel_id}")
            schema_name = channel_info.get("schemaName", "unknown")
            encoding = channel_info.get("encoding", "json")
            
            # Log the received message
            logger.info(f"Received message from Foxglove:")
            logger.info(f"  Topic: {topic_name}")
            logger.info(f"  Schema: {schema_name}")
            logger.info(f"  Encoding: {encoding}")
            logger.info(f"  Data length: {len(payload)} bytes")
            
            # Try to decode the message if it's JSON
            if encoding == "json":
                try:
                    decoded_message = json.loads(payload.decode('utf-8'))
                    logger.info(f"  Decoded JSON: {json.dumps(decoded_message, indent=2)}")
                except Exception as e:
                    logger.warning(f"Failed to decode JSON message: {e}")
                    logger.info(f"  Raw data: {payload}")
            else:
                logger.info(f"  Raw data: {payload}")
            
            # Convert and publish to LCM
            result = self.reverse_converter.convert_foxglove_to_lcm(
                topic_name, schema_name, payload
            )
            
            if result:
                lcm_topic_name, lcm_message_bytes = result
                logger.info(f"Publishing to LCM topic: {lcm_topic_name}")
                
                # Publish to LCM using the bridge's LCM instance
                self.bridge.lc.publish(lcm_topic_name, lcm_message_bytes)
                logger.info(f"Successfully published message to LCM topic: {lcm_topic_name}")
            else:
                logger.error(f"Failed to convert message for topic {topic_name}")
            
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            import traceback
            traceback.print_exc()