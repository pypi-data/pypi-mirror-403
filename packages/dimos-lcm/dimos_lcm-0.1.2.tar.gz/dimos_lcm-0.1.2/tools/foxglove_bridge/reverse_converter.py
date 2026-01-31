"""
Reverse message converter - converts Foxglove JSON messages to LCM messages.
"""

import json
import time
import importlib
from typing import Dict, Any, Optional, Tuple
from .config import logger


class ReverseMessageConverter:
    """Converts Foxglove JSON messages back to LCM messages"""
    
    def __init__(self):
        self.lcm_class_cache: Dict[str, Any] = {}
        
    def convert_foxglove_to_lcm(self, topic_name: str, schema_name: str, 
                              json_data: bytes) -> Optional[Tuple[str, bytes]]:
        """
        Convert a Foxglove JSON message to LCM format
        
        Args:
            topic_name: The topic name (e.g., '/clicked_point')
            schema_name: The schema name (e.g., 'geometry_msgs/PointStamped')
            json_data: The JSON message data as bytes
            
        Returns:
            Tuple of (lcm_topic_name, lcm_message_bytes) or None if conversion fails
        """
        try:
            # Parse the JSON data
            message_dict = json.loads(json_data.decode('utf-8'))
            logger.info(f"Converting message for topic {topic_name} with schema {schema_name}")
            logger.info(f"Message data: {json.dumps(message_dict, indent=2)}")
            
            # Convert schema name from ROS format to LCM format
            lcm_schema_type = self._ros_schema_to_lcm_schema(schema_name)
            if not lcm_schema_type:
                logger.warning(f"Cannot convert schema {schema_name} to LCM format")
                return None
            
            # Get the LCM message class
            lcm_class = self._get_lcm_class(lcm_schema_type)
            if not lcm_class:
                logger.warning(f"Cannot find LCM class for {lcm_schema_type}")
                return None
            
            # Convert the message data
            lcm_message = self._convert_dict_to_lcm_message(message_dict, lcm_class)
            if not lcm_message:
                logger.warning(f"Failed to convert message dict to LCM message")
                return None
            
            # Create LCM topic name (add schema annotation)
            lcm_topic_name = f"{topic_name}#{lcm_schema_type}"
            
            # Encode the message
            lcm_message_bytes = lcm_message.encode()
            
            logger.info(f"Successfully converted to LCM topic: {lcm_topic_name}")
            return lcm_topic_name, lcm_message_bytes
            
        except Exception as e:
            logger.error(f"Error converting Foxglove message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _ros_schema_to_lcm_schema(self, ros_schema: str) -> Optional[str]:
        """Convert ROS schema name to LCM schema type"""
        # Convert from 'geometry_msgs/PointStamped' to 'geometry_msgs.PointStamped'
        if '/' in ros_schema:
            parts = ros_schema.split('/')
            if len(parts) == 2:
                package, msg_type = parts
                return f"{package}.{msg_type}"
        return None
    
    def _get_lcm_class(self, schema_type: str) -> Optional[Any]:
        """Get the LCM message class for the given schema type"""
        if schema_type in self.lcm_class_cache:
            return self.lcm_class_cache[schema_type]
        
        try:
            # Parse schema type to get package and message type
            if "." not in schema_type:
                return None
            
            package, msg_type = schema_type.split(".", 1)
            
            # Import the LCM message class
            module_name = f"lcm_msgs.{package}.{msg_type}"
            logger.info(f"Importing LCM module {module_name}...")
            module = importlib.import_module(module_name)
            lcm_class = getattr(module, msg_type)
            
            # Cache the class
            self.lcm_class_cache[schema_type] = lcm_class
            return lcm_class
            
        except Exception as e:
            logger.error(f"Error importing LCM class for {schema_type}: {e}")
            return None
    
    def _convert_dict_to_lcm_message(self, message_dict: Dict[str, Any], lcm_class: Any) -> Optional[Any]:
        """Convert a dictionary to an LCM message instance"""
        try:
            # Create a new instance of the LCM message class
            lcm_message = lcm_class()
            
            # Get the message field information
            slots = getattr(lcm_class, "__slots__", [])
            
            # Set fields from the dictionary
            for slot in slots:
                if slot.startswith('_'):
                    continue
                    
                # Handle length fields
                if slot.endswith('_length'):
                    base_field = slot[:-7]  # Remove '_length' suffix
                    if base_field in message_dict:
                        array_data = message_dict[base_field]
                        if isinstance(array_data, list):
                            setattr(lcm_message, slot, len(array_data))
                        else:
                            setattr(lcm_message, slot, 0)
                    continue
                
                # Set regular fields
                if slot in message_dict:
                    value = message_dict[slot]
                    
                    # Handle nested objects (like header)
                    if isinstance(value, dict) and slot == 'header':
                        converted_value = self._convert_header_dict(value)
                    else:
                        converted_value = self._convert_value(value)
                    
                    setattr(lcm_message, slot, converted_value)
                    
            return lcm_message
            
        except Exception as e:
            logger.error(f"Error converting dict to LCM message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _convert_header_dict(self, header_dict: Dict[str, Any]) -> Any:
        """Convert a header dictionary to appropriate format"""
        try:
            # Create a simple object to hold header data
            class HeaderObj:
                def __init__(self):
                    self.seq = 0
                    self.stamp = None
                    self.frame_id = ""
            
            header = HeaderObj()
            
            # Set sequence number
            header.seq = int(header_dict.get('seq', 0))
            
            # Set frame ID
            header.frame_id = str(header_dict.get('frame_id', ''))
            
            # Handle timestamp
            stamp_dict = header_dict.get('stamp', {})
            if isinstance(stamp_dict, dict):
                class StampObj:
                    def __init__(self):
                        self.sec = 0
                        self.nsec = 0
                
                stamp = StampObj()
                stamp.sec = int(stamp_dict.get('sec', 0))
                stamp.nsec = int(stamp_dict.get('nsec', 0))
                header.stamp = stamp
            else:
                # Use current time if no timestamp provided
                now = time.time()
                class StampObj:
                    def __init__(self):
                        self.sec = 0
                        self.nsec = 0
                
                stamp = StampObj()
                stamp.sec = int(now)
                stamp.nsec = int((now % 1) * 1e9)
                header.stamp = stamp
            
            return header
            
        except Exception as e:
            logger.error(f"Error converting header dict: {e}")
            return None
    
    def _convert_value(self, value: Any) -> Any:
        """Convert a value to appropriate type for LCM"""
        if isinstance(value, dict):
            # Handle nested objects
            return value  # For now, just return as-is
        elif isinstance(value, list):
            # Handle arrays
            return [self._convert_value(item) for item in value]
        elif isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool)):
            return value
        else:
            return value