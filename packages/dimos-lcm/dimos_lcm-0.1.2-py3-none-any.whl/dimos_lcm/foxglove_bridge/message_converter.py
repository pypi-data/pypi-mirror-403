"""
Message conversion from LCM to Foxglove format.
"""

import base64
import time
import struct
from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict
import numpy as np
from .config import logger
from .models import TopicInfo
from turbojpeg import TurboJPEG


class MessageConverter:
    """Handles conversion of LCM messages to JSON format for Foxglove"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.conversion_methods: Dict[str, Callable] = {
            "sensor_msgs.image": self._format_image_msg,
            "sensor_msgs.compressedimage": self._format_compressed_image_msg,
            "tf2_msgs.tfmessage": self._format_tf_msg,
            "sensor_msgs.jointstate": self._format_joint_state_msg,
            "sensor_msgs.JointState": self._format_joint_state_msg,
            "sensor_msgs.pointcloud2": self._format_pointcloud2_msg,
            "sensor_msgs.PointCloud2": self._format_pointcloud2_msg,
        }
        # Cache for previously converted messages
        self.conversion_cache: Dict[str, Any] = {}
        # Stats for conversion timing
        self.conversion_times: Dict[str, List[float]] = defaultdict(list)
        
    def convert_message(self, topic_info: TopicInfo, msg: Any) -> Dict[str, Any]:
        """Convert an LCM message to Foxglove format"""
        # Try with exact type first
        if topic_info.schema_type in self.conversion_methods:
            converter = self.conversion_methods[topic_info.schema_type]
        else:
            # Fall back to case-insensitive check
            schema_type_lower = topic_info.schema_type.lower()
            if schema_type_lower in self.conversion_methods:
                converter = self.conversion_methods[schema_type_lower]
            else:
                # Log when we don't have a specialized converter
                logger.debug(f"No specialized converter for {topic_info.schema_type}, using generic conversion")
                return self._lcm_to_dict(msg)
        
        # Convert using the specialized converter
        try:
            start_time = time.time()
            result = converter(msg, topic_info)
            elapsed = time.time() - start_time
            
            # Update stats
            schema_key = topic_info.schema_type.lower()  # Use lowercase for stats
            self.conversion_times[schema_key].append(elapsed)
            if len(self.conversion_times[schema_key]) > 100:
                self.conversion_times[schema_key] = self.conversion_times[schema_key][-100:]
                
            # Log timing for slow conversions
            if elapsed > 0.1:  # More than 100ms
                avg_time = sum(self.conversion_times[schema_key]) / len(self.conversion_times[schema_key])
                logger.warning(f"Slow conversion for {topic_info.name}: {elapsed:.3f}s (avg: {avg_time:.3f}s)")
                
            return result
        except Exception as e:
            logger.error(f"Error in converter for {topic_info.schema_type}, falling back to generic: {e}")
            return self._lcm_to_dict(msg)

    def _lcm_to_dict(self, msg: Any) -> Any:
        """Convert an LCM message to a dictionary"""
        if isinstance(msg, (int, float, bool, str, type(None))):
            return msg
        elif isinstance(msg, bytes):
            # Convert bytes to base64
            return base64.b64encode(msg).decode("ascii")
        elif isinstance(msg, (list, tuple)):
            # Handle array case - this is the key change
            # For foxglove visualization, arrays need to have proper format
            # Return as a simple array of converted values rather than an object with numeric keys
            return [self._lcm_to_dict(item) for item in msg]
        elif isinstance(msg, dict):
            return {k: self._lcm_to_dict(v) for k, v in msg.items()}
        elif isinstance(msg, np.ndarray):
            # Handle numpy arrays - convert to list first
            return [self._lcm_to_dict(item) for item in msg.tolist()]
        else:
            # Try to convert a custom LCM message object
            result = {}
            
            # First gather all attributes and their types
            length_fields = {}
            
            # First pass: identify all length fields and their values
            for attr in dir(msg):
                if attr.startswith('_') or callable(getattr(msg, attr)):
                    continue
                
                # Check for length fields
                if attr.endswith('_length'):
                    base_attr = attr[:-7]  # Remove '_length' suffix
                    length_value = getattr(msg, attr)
                    length_fields[base_attr] = length_value
            
            # Second pass: process all attributes
            for attr in dir(msg):
                if attr.startswith('_') or callable(getattr(msg, attr)) or attr.endswith('_length'):
                    continue
                
                value = getattr(msg, attr)
                
                # Handle arrays with corresponding length fields
                if attr in length_fields and isinstance(value, (list, tuple)):
                    length = length_fields[attr]
                    if isinstance(length, int) and length >= 0 and length <= len(value):
                        # Truncate array to specified length
                        value = value[:length]
                
                # Recursively convert the value
                try:
                    result[attr] = self._lcm_to_dict(value)
                except Exception as e:
                    logger.error(f"Error converting attribute {attr}: {e}")
                    result[attr] = None
            
            return result
    
    def _get_header_dict(self, header: Any) -> Dict[str, Any]:
        """Extract a properly formatted header dictionary from a ROS Header"""
        try:
            # Standard ROS header has seq, stamp, and frame_id
            stamp = {}
            
            # Handle stamp which might be a struct or separate sec/nsec fields
            if hasattr(header, "stamp") and not isinstance(header.stamp, (int, float)):
                if hasattr(header.stamp, "sec") and hasattr(header.stamp, "nsec"):
                    stamp = {
                        "sec": int(header.stamp.sec) if hasattr(header.stamp, "sec") else 0,
                        "nsec": int(header.stamp.nsec) if hasattr(header.stamp, "nsec") else 0
                    }
                else:
                    # Handle builtin_interfaces/Time which might use nanosec instead of nsec
                    stamp = {
                        "sec": int(header.stamp.sec) if hasattr(header.stamp, "sec") else 0,
                        "nsec": int(
                            header.stamp.nanosec if hasattr(header.stamp, "nanosec") 
                            else (header.stamp.nsec if hasattr(header.stamp, "nsec") else 0)
                        )
                    }
            elif hasattr(header, "sec") and hasattr(header, "nsec"):
                # Some messages have sec/nsec directly in the header
                stamp = {
                    "sec": int(header.sec),
                    "nsec": int(header.nsec)
                }
            else:
                # Default to current time if no valid stamp found
                now = time.time()
                stamp = {
                    "sec": int(now),
                    "nsec": int((now % 1) * 1e9)
                }
                
            # Ensure frame_id is a string (convert bytes if needed)
            frame_id = header.frame_id if hasattr(header, "frame_id") else ""
            if isinstance(frame_id, bytes):
                frame_id = frame_id.decode('utf-8', errors='replace')
                
            return {
                "seq": int(header.seq) if hasattr(header, "seq") else 0,
                "stamp": stamp,
                "frame_id": frame_id
            }
        except Exception as e:
            logger.error(f"Error formatting header: {e}")
            # Return a minimal valid header
            now = time.time()
            return {
                "seq": 0,
                "stamp": {"sec": int(now), "nsec": int((now % 1) * 1e9)},
                "frame_id": ""
            }
        
    def _format_image_msg(self, msg: Any, topic_info: Optional[TopicInfo] = None) -> Dict[str, Any]:
        """Format a sensor_msgs/Image message for Foxglove"""
        try:
            # Get header
            header = self._get_header_dict(msg.header)
            
            # For Image messages, we need to encode the data as base64
            data_length = getattr(msg, "data_length", len(msg.data) if hasattr(msg, "data") else 0)
            
            # Check if this is a JPEG-compressed image
            encoding = msg.encoding if hasattr(msg, "encoding") and msg.encoding else "rgb8"

            if encoding.lower() == "jpeg":
                # This is JPEG-compressed data - we need to decode it back to raw pixels
                # for Foxglove to display it correctly with the Image schema
                if hasattr(msg, "data") and data_length > 0:
                    jpeg = TurboJPEG()
                    # Decode JPEG to BGR array
                    bgr_array = jpeg.decode(msg.data[:data_length])

                    # Update the message properties to reflect raw image
                    height, width = bgr_array.shape[:2]
                    step = width * 3  # 3 bytes per pixel for BGR

                    # Convert BGR array back to bytes
                    image_data_bytes = bgr_array.tobytes()
                    image_data = base64.b64encode(image_data_bytes).decode("ascii")

                    # Return as raw Image with rgb8 encoding (Foxglove prefers RGB)
                    return {
                        "header": header,
                        "height": height,
                        "width": width,
                        "encoding": "rgb8",  # Foxglove expects rgb8
                        "is_bigendian": False,
                        "step": step,
                        "data": image_data
                    }
                else:
                    image_data = ""

            # Foxglove might need rgb8 instead of bgr8
            if encoding.lower() == "bgr8":
                # Change the encoding string to rgb8
                encoding = "rgb8"
            
            if hasattr(msg, "data") and data_length > 0:
                # Get image data as bytes
                image_data_bytes = msg.data[:data_length]
                
                # Convert to base64
                image_data = base64.b64encode(image_data_bytes).decode("ascii")
            else:
                # If no data, return empty string
                image_data = ""
            
            # Return properly formatted message dict for Foxglove
            return {
                "header": header,
                "height": int(msg.height),
                "width": int(msg.width),
                "encoding": encoding,
                "is_bigendian": bool(msg.is_bigendian),
                "step": int(msg.step),
                "data": image_data
            }
        except Exception as e:
            logger.error(f"Error formatting Image message: {e}")
            return self._lcm_to_dict(msg)  # Fallback to generic conversion
    
    def _format_compressed_image_msg(self, msg: Any, topic_info: Optional[TopicInfo] = None) -> Dict[str, Any]:
        """Format a sensor_msgs/CompressedImage message for Foxglove"""
        try:
            # Get header
            header = self._get_header_dict(msg.header)
            
            # For CompressedImage messages, format must be jpg or png
            image_format = msg.format.lower() if hasattr(msg, "format") and msg.format else "jpeg"
            
            # Convert data to base64
            data_length = getattr(msg, "data_length", len(msg.data) if hasattr(msg, "data") else 0)
            
            if hasattr(msg, "data") and data_length > 0:
                # Get image data as bytes
                image_data_bytes = msg.data[:data_length]
                
                # Convert to base64
                image_data = base64.b64encode(image_data_bytes).decode("ascii")
            else:
                # If no data, return empty string
                image_data = ""
            
            # Return properly formatted message for Foxglove
            return {
                "header": header, 
                "format": image_format,
                "data": image_data
            }
        except Exception as e:
            logger.error(f"Error formatting CompressedImage message: {e}")
            return self._lcm_to_dict(msg)  # Fallback to generic conversion
    
    def _format_tf_msg(self, msg: Any, topic_info: Optional[TopicInfo] = None) -> Dict[str, Any]:
        """Format a tf2_msgs/TFMessage for Foxglove"""
        try:
            # Get the transforms array with correct length
            transforms_length = getattr(msg, "transforms_length", 0)
            transforms = []
            
            # Process each transform in the array
            if hasattr(msg, "transforms") and transforms_length > 0:
                for i in range(min(transforms_length, len(msg.transforms))):
                    transform = msg.transforms[i]
                    transform_dict = self._format_transform_stamped(transform)
                    if transform_dict:
                        transforms.append(transform_dict)
            
            # Return properly formatted message
            return {"transforms": transforms}
            
        except Exception as e:
            logger.error(f"Error formatting TFMessage: {e}")
            return {"transforms": []}  # Return empty transforms array on error
    
    def _format_transform_stamped(self, transform: Any) -> Optional[Dict[str, Any]]:
        """Format a geometry_msgs/TransformStamped message for Foxglove"""
        try:
            # Format header
            header = self._get_header_dict(transform.header)
            
            # Check for required attributes
            if not hasattr(transform, "transform"):
                logger.warning("Warning: TransformStamped missing 'transform' attribute")
                return None
                
            if not hasattr(transform.transform, "translation") or not hasattr(transform.transform, "rotation"):
                logger.warning("Warning: Transform missing translation or rotation")
                return None
            
            # Format translation (defaulting to zeros if missing)
            translation = {
                "x": float(getattr(transform.transform.translation, "x", 0.0)),
                "y": float(getattr(transform.transform.translation, "y", 0.0)),
                "z": float(getattr(transform.transform.translation, "z", 0.0))
            }
            
            # Format rotation (defaulting to identity if missing)
            rotation = {
                "x": float(getattr(transform.transform.rotation, "x", 0.0)),
                "y": float(getattr(transform.transform.rotation, "y", 0.0)),
                "z": float(getattr(transform.transform.rotation, "z", 0.0)),
                "w": float(getattr(transform.transform.rotation, "w", 1.0))
            }
            
            # Get child frame id
            child_frame_id = transform.child_frame_id
            if isinstance(child_frame_id, bytes):
                child_frame_id = child_frame_id.decode('utf-8', errors='replace')
            
            # Return formatted transform (exactly as Foxglove TF expects)
            return {
                "header": header,
                "child_frame_id": child_frame_id,
                "transform": {
                    "translation": translation,
                    "rotation": rotation
                }
            }
        except Exception as e:
            logger.error(f"Error formatting TransformStamped: {e}")
            return None
    
    def _format_joint_state_msg(self, msg: Any, topic_info: Optional[TopicInfo] = None) -> Dict[str, Any]:
        """Format a sensor_msgs/JointState message for Foxglove"""
        try:
            # Debug log when processing a joint state
            logger.info(f"Processing JointState message from {topic_info.name if topic_info else 'unknown'}")
            
            # Format the header
            header = self._get_header_dict(msg.header)
            
            # Get array lengths and print debug info
            name_length = getattr(msg, "name_length", 0)
            position_length = getattr(msg, "position_length", 0)
            velocity_length = getattr(msg, "velocity_length", 0)
            effort_length = getattr(msg, "effort_length", 0)
            
            logger.info(f"JointState arrays: names={name_length}, positions={position_length}, velocities={velocity_length}, efforts={effort_length}")
            
            # Check if message has required attributes
            if not hasattr(msg, "name") or not hasattr(msg, "position"):
                logger.warning(f"JointState message missing required attributes name or position")
                # Log available attributes
                logger.warning(f"JointState available attributes: {[a for a in dir(msg) if not a.startswith('_')]}")
            
            # Format arrays with correct lengths
            names = msg.name[:name_length] if hasattr(msg, "name") and name_length > 0 else []
            positions = msg.position[:position_length] if hasattr(msg, "position") and position_length > 0 else []
            velocities = msg.velocity[:velocity_length] if hasattr(msg, "velocity") and velocity_length > 0 else []
            efforts = msg.effort[:effort_length] if hasattr(msg, "effort") and effort_length > 0 else []
            
            # Convert name list items from bytes to strings if needed
            names = [name.decode('utf-8', errors='replace') if isinstance(name, bytes) else name for name in names]
            
            # Convert array elements to Python primitives
            positions = [float(p) for p in positions]
            velocities = [float(v) for v in velocities] 
            efforts = [float(e) for e in efforts]
            
            # Log the conversion result
            logger.info(f"Converted JointState with {len(names)} joints: {names}")
            
            # Return properly formatted message for Foxglove
            return {
                "header": header,
                "name": names,
                "position": positions,
                "velocity": velocities,
                "effort": efforts
            }
        except Exception as e:
            logger.error(f"Error formatting JointState: {e}")
            import traceback
            traceback.print_exc()
            return {"header": self._get_header_dict(msg.header), "name": [], "position": [], "velocity": [], "effort": []}
    
    def _format_pointcloud2_msg(self, msg: Any, topic_info: Optional[TopicInfo] = None) -> Dict[str, Any]:
        """Format a sensor_msgs/PointCloud2 message for Foxglove"""
        try:
            # Format the header
            header = self._get_header_dict(msg.header)
            
            # Get fields with correct length
            fields_length = getattr(msg, "fields_length", 0)
            fields = []
            
            # Get basic properties
            data_len = len(msg.data) if hasattr(msg, 'data') else 0
            point_step = int(msg.point_step) if hasattr(msg, 'point_step') else 16
            
            # Basic validation check to avoid the "not a multiple of point_step" error
            if data_len % point_step != 0:
                logger.warning(f"PointCloud2 data length {data_len} is not a multiple of point_step {point_step}!")
                # Adjust the data to make it a multiple of point_step
                missing_bytes = point_step - (data_len % point_step)
                padded_data = msg.data + bytes(missing_bytes)
                msg.data = padded_data
                data_len = len(msg.data)
                
                # Also adjust width to match the new number of points
                adjusted_points = data_len // point_step
                msg.width = adjusted_points
            
            # Check if this is a colored point cloud by scanning field names
            has_rgb_fields = False
            has_rgba_field = False
            rgb_field_names = {"r", "g", "b"}
            
            # Extract field definitions
            if hasattr(msg, "fields") and fields_length > 0:
                for i in range(min(fields_length, len(msg.fields))):
                    field = msg.fields[i]
                    field_name = field.name.decode('utf-8', errors='replace') if isinstance(field.name, bytes) else field.name
                    
                    field_dict = {
                        "name": field_name,
                        "offset": int(field.offset),
                        "datatype": int(field.datatype),
                        "count": int(field.count)
                    }
                    fields.append(field_dict)
                    
                    # Check for RGB fields or RGBA packed field
                    if field_name.lower() in rgb_field_names:
                        has_rgb_fields = True
                    elif field_name.lower() == "rgba":
                        has_rgba_field = True
            
            # If no fields provided, create default ones
            if not fields:
                if point_step == 16:
                    # This might be a colored point cloud, determine format based on data analysis
                    # First try with RGBA packed (better for Foxglove)
                    fields = [
                        {"name": "x", "offset": 0, "datatype": 7, "count": 1},  # Float32
                        {"name": "y", "offset": 4, "datatype": 7, "count": 1},  # Float32
                        {"name": "z", "offset": 8, "datatype": 7, "count": 1},  # Float32
                        {"name": "rgba", "offset": 12, "datatype": 6, "count": 1}  # UInt32
                    ]
                    has_rgba_field = True
                    logger.info("Detected possible colored PointCloud2, using XYZRGBA packed format")
                else:
                    # Default to standard XYZ + intensity format
                    fields = [
                        {"name": "x", "offset": 0, "datatype": 7, "count": 1},  # Float32
                        {"name": "y", "offset": 4, "datatype": 7, "count": 1},  # Float32
                        {"name": "z", "offset": 8, "datatype": 7, "count": 1},  # Float32
                        {"name": "intensity", "offset": 12, "datatype": 7, "count": 1}  # Float32
                    ]
            
            # Convert data to base64
            if hasattr(msg, "data") and len(msg.data) > 0:
                # Get point cloud data as bytes
                cloud_data_bytes = msg.data
                
                # Convert to base64
                cloud_data = base64.b64encode(cloud_data_bytes).decode("ascii")
            else:
                # Create a small point cloud with a single point at origin
                if has_rgba_field:
                    # Create a colored point with packed RGBA (red)
                    # RGBA = (R << 24) | (G << 16) | (B << 8) | A
                    red_rgba = (255 << 24) | (0 << 16) | (0 << 8) | 255  # Red with alpha=255
                    cloud_data_bytes = struct.pack("<fffi", 0, 0, 0, red_rgba)  # XYZ+RGBA (red point)
                elif has_rgb_fields:
                    # Create a colored point with separate RGB components (red)
                    cloud_data_bytes = struct.pack("<fffBBBB", 0, 0, 0, 255, 0, 0, 255)  # XYZRGBA (red point)
                else:
                    # Create a standard point with intensity
                    cloud_data_bytes = struct.pack("<ffff", 0, 0, 0, 1.0)  # XYZ+intensity
                
                cloud_data = base64.b64encode(cloud_data_bytes).decode("ascii")
                # Set width to 1 if no data
                msg.width = 1
                msg.height = 1
            
            # Return properly formatted message for Foxglove
            return {
                "header": header,
                "height": int(msg.height) if hasattr(msg, "height") else 1,
                "width": int(msg.width) if hasattr(msg, "width") else 1,
                "fields": fields,
                "is_bigendian": bool(msg.is_bigendian) if hasattr(msg, "is_bigendian") else False,
                "point_step": point_step,
                "row_step": point_step * int(msg.width) if hasattr(msg, "width") else point_step,
                "data": cloud_data,
                "is_dense": bool(msg.is_dense) if hasattr(msg, "is_dense") else True
            }
        except Exception as e:
            logger.error(f"Error formatting PointCloud2: {e}")
            return self._lcm_to_dict(msg)  # Fallback to generic conversion
