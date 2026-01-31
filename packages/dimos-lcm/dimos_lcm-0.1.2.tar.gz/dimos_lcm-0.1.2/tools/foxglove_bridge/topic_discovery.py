"""
LCM topic discovery functionality.
"""

import lcm
import threading
from typing import Dict, Callable, Set
from .config import logger


class LcmTopicDiscoverer:
    """Discovers LCM topics and their schemas"""
    
    def __init__(self, callback: Callable[[str], None], schema_map: Dict[str, str] = None):
        """
        Initialize the topic discoverer
        
        Args:
            callback: Function to call when a new topic is discovered
            schema_map: Optional dict mapping bare topic names to schema types
        """
        self.lc = lcm.LCM()
        self.callback = callback
        self.topics: Set[str] = set()
        self.running = True
        self.thread = threading.Thread(target=self._discovery_thread)
        self.mutex = threading.Lock()
        self.schema_map = schema_map or {}
        
    def start(self):
        """Start the discovery thread"""
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop the discovery thread"""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=2.0)  # Wait up to 2 seconds for clean shutdown
            
    def _discovery_thread(self):
        """Thread function for discovering topics"""
        # Unfortunately LCM doesn't have built-in topic discovery
        # We'll use a special handler to catch all messages and extract topic info
        
        # Subscribe to all messages with a wildcard
        self.lc.subscribe(".*", self._on_any_message)
        
        while self.running:
            try:
                # Handle LCM messages with a timeout
                self.lc.handle_timeout(100)  # 100ms timeout
            except Exception as e:
                logger.error(f"Error in LCM discovery: {e}")
    
    def _on_any_message(self, channel: str, data: bytes):
        """Callback for any LCM message during discovery"""
        with self.mutex:
            if channel not in self.topics:
                # New topic found
                self.topics.add(channel)
                logger.info(f"Discovered new LCM topic: {channel}")
                
                # Special debugging for joint states topic
                if "joint_state" in channel.lower():
                    logger.info(f"Found joint states topic: {channel}")
                
                # Check if the topic has schema information
                if "#" in channel:
                    # Topic already has schema info in the name
                    try:
                        logger.info(f"Processing topic with embedded schema: {channel}")
                        self.callback(channel)
                    except Exception as e:
                        logger.error(f"Error processing discovered topic {channel}: {e}")
                elif channel in self.schema_map:
                    # We have schema info in our map
                    schema_type = self.schema_map[channel]
                    annotated_channel = f"{channel}#{schema_type}"
                    try:
                        logger.info(f"Mapping topic {channel} to {annotated_channel}")
                        self.callback(annotated_channel)
                    except Exception as e:
                        logger.error(f"Error processing mapped topic {channel} with schema {schema_type}: {e}")
                else:
                    # No schema information available
                    logger.warning(f"No schema information for topic: {channel}")
                    if "joint_state" in channel.lower():
                        # Auto-map joint states topic for debugging
                        schema_type = "sensor_msgs.JointState"
                        annotated_channel = f"{channel}#{schema_type}"
                        logger.info(f"Auto-mapping joint states topic: {annotated_channel}")
                        try:
                            self.callback(annotated_channel)
                        except Exception as e:
                            logger.error(f"Error auto-mapping joint states topic: {e}")