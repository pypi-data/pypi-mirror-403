"""
JSON schema generation from ROS message definitions.
"""

import os
import re
import importlib
from typing import Dict, Optional, Any
from .config import HARDCODED_SCHEMAS, TYPE_MAPPING, ROS_MSGS_DIR, logger


class SchemaGenerator:
    """Generates JSON schemas from ROS message definitions"""
    
    def __init__(self):
        self.schema_cache: Dict[str, dict] = {}
        
    def generate_schema(self, schema_type: str) -> dict:
        """Generate a JSON schema for the given schema type (e.g., 'sensor_msgs.Image')"""
        # Check if we have a hardcoded schema for this type
        if schema_type in HARDCODED_SCHEMAS:
            logger.info(f"Using hardcoded schema for {schema_type}")
            return HARDCODED_SCHEMAS[schema_type]["schema"]
            
        # Check if schema is already cached
        if schema_type in self.schema_cache:
            return self.schema_cache[schema_type]
        
        # Parse schema type to get package and message type
        if "." not in schema_type:
            raise ValueError(f"Invalid schema type format: {schema_type}")
        
        package, msg_type = schema_type.split(".", 1)
        
        # Find the .msg file
        msg_file_path = os.path.join(ROS_MSGS_DIR, package, "msg", f"{msg_type}.msg")
        if not os.path.exists(msg_file_path):
            raise FileNotFoundError(f"Message file not found: {msg_file_path}")
        
        # Parse the .msg file and generate schema
        schema = self._parse_msg_file(msg_file_path, package)
        self.schema_cache[schema_type] = schema
        return schema
    
    def _parse_msg_file(self, msg_file_path: str, package_name: str) -> dict:
        """Parse a ROS .msg file and create a JSON schema"""
        with open(msg_file_path, 'r') as f:
            msg_content = f.read()
        
        # Create basic schema structure
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Parse each line in the .msg file
        for line in msg_content.splitlines():
            # Remove comments (anything after #)
            if '#' in line:
                line = line.split('#', 1)[0]
                
            line = line.strip()
            if not line:
                continue
            
            # Parse field definition (type field_name)
            if ' ' not in line:
                continue
            
            parts = line.split(None, 1)  # Split on any whitespace
            if len(parts) < 2:
                continue
                
            field_type, field_name = parts
            field_name = field_name.strip()  # Ensure no trailing whitespace
            
            # Check if it's an array type
            is_array = False
            array_size = None
            if field_type.endswith('[]'):
                is_array = True
                field_type = field_type[:-2]
            elif '[' in field_type and field_type.endswith(']'):
                match = re.match(r'(.*)\[(\d+)\]', field_type)
                if match:
                    field_type = match.group(1)
                    array_size = int(match.group(2))
                    is_array = True
            
            # Process the field and add to schema
            field_schema = self._convert_type_to_schema(field_type, package_name, is_array, array_size)
            if field_schema:
                schema["properties"][field_name] = field_schema
                schema["required"].append(field_name)
        
        return schema
    
    def _lcm_to_schema(self, topic_name: str, lcm_class: Any) -> Optional[dict]:
        """Dynamically generate a schema from an LCM class"""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Get fields from LCM class
        slots = getattr(lcm_class, "__slots__", [])
        typenames = getattr(lcm_class, "__typenames__", [])
        dimensions = getattr(lcm_class, "__dimensions__", [])
        
        if not slots or len(slots) != len(typenames):
            logger.error(f"Cannot generate schema for {topic_name}: missing slots or typenames")
            return None
        
        # First identify all length fields
        length_fields = {}
        for i, field in enumerate(slots):
            if field.endswith('_length'):
                base_field = field[:-7]  # Remove '_length' suffix
                length_fields[base_field] = field
        
        # Process each field
        for i, (field, typename) in enumerate(zip(slots, typenames)):
            # Skip length fields, they're handled implicitly
            if field.endswith('_length'):
                continue
                
            # Get dimension info if available (for arrays)
            dimension = dimensions[i] if i < len(dimensions) else None
            is_array = dimension is not None and dimension != [None]
            
            # For known array fields, make sure we're marking them properly
            if field in length_fields:
                is_array = True
            
            # Get the JSON schema for this field
            field_schema = self._lcm_type_to_schema(typename, field, is_array, dimension)
            
            if field_schema:
                schema["properties"][field] = field_schema
                schema["required"].append(field)
                
        return schema
        
    def _lcm_type_to_schema(self, typename: str, field: str, is_array: bool = False, dimension: Any = None) -> Optional[dict]:
        """Convert an LCM type to a JSON schema"""
        # Check for primitive types
        primitive_map = {
            "int8_t": {"type": "integer"},
            "int16_t": {"type": "integer"},
            "int32_t": {"type": "integer"},
            "int64_t": {"type": "integer"},
            "uint8_t": {"type": "integer", "minimum": 0},
            "uint16_t": {"type": "integer", "minimum": 0},
            "uint32_t": {"type": "integer", "minimum": 0},
            "uint64_t": {"type": "integer", "minimum": 0},
            "boolean": {"type": "boolean"},
            "bool": {"type": "boolean"},  # Add 'bool' as alias for boolean
            "float": {"type": "number"},
            "double": {"type": "number"},
            "string": {"type": "string"},
            "bytes": {"type": "string", "contentEncoding": "base64"}
        }
        
        # Special check for arrays with common LCM naming patterns
        if field in ['axes', 'buttons']:
            is_array = True
            
        if typename in primitive_map:
            base_schema = primitive_map[typename]
            
            # Handle array type
            if is_array:
                # Make sure arrays are properly defined - this is crucial for Foxglove
                return {
                    "type": "array", 
                    "items": base_schema,
                    "description": f"Array of {typename} values"
                }
            return base_schema
        
        # Handle complex types
        if "." in typename:
            # This is a complex type reference, like 'std_msgs.Header'
            # For these, we'll create a reference to their schema
            if is_array:
                return {
                    "type": "array", 
                    "items": {"type": "object"},
                    "description": f"Array of {typename} objects"
                }
            return {"type": "object", "description": f"Object of type {typename}"}
        
        # If we get here, we don't know how to handle the type
        logger.warning(f"Unknown LCM type {typename} for field {field}")
        if is_array:
            return {"type": "array", "items": {"type": "object"}, "description": f"Array of unknown type: {typename}"}
        return {"type": "object", "description": f"Unknown type: {typename}"}  # Fallback
    
    def _convert_type_to_schema(self, field_type: str, package_name: str, is_array: bool = False, array_size: Optional[int] = None) -> Optional[dict]:
        """Convert a ROS field type to a JSON schema type"""
        # Check for primitive types
        if field_type in TYPE_MAPPING:
            field_schema = dict(TYPE_MAPPING[field_type])
            if is_array:
                schema = {"type": "array", "items": field_schema}
                if array_size is not None:
                    schema["maxItems"] = array_size
                    schema["minItems"] = array_size
                return schema
            return field_schema
            
        # Special case for Header
        elif field_type == "Header" or field_type == "std_msgs/Header":
            header_schema = {
                "type": "object",
                "properties": {
                    "seq": {"type": "integer"},
                    "stamp": {
                        "type": "object",
                        "properties": {
                            "sec": {"type": "integer"},
                            "nsec": {"type": "integer"}  # Use nanosec instead of nsec for Foxglove compatibility
                        },
                        "required": ["sec", "nsec"]
                    },
                    "frame_id": {"type": "string"}
                },
                "required": ["seq", "stamp", "frame_id"]
            }
            
            if is_array:
                schema = {"type": "array", "items": header_schema}
                if array_size is not None:
                    schema["maxItems"] = array_size
                    schema["minItems"] = array_size
                return schema
            return header_schema
            
        # Complex type - could be from another package
        else:
            # Check if type contains a package name
            if "/" in field_type:
                pkg, msg = field_type.split("/", 1)
                complex_schema_type = f"{pkg}.{msg}"
            else:
                # Assume it's from the same package
                complex_schema_type = f"{package_name}.{field_type}"
            
            try:
                # Try to recursively generate schema
                complex_schema = self.generate_schema(complex_schema_type)
                
                if is_array:
                    schema = {"type": "array", "items": complex_schema}
                    if array_size is not None:
                        schema["maxItems"] = array_size
                        schema["minItems"] = array_size
                    return schema
                return complex_schema
            except Exception as e:
                logger.error(f"Error processing complex type {field_type}: {e}")
                # Return a placeholder schema
                return {"type": "object", "description": f"Error: could not process type {field_type}"}