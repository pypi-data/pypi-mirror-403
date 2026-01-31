# Copyright 2026 Dimensional Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Configuration constants and settings for the LCM-Foxglove bridge.
"""

import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("lcm_foxglove_bridge")

# Get the directory where this config.py file is located
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
# One level up from foxglove_bridge/ to get to package root (dimos_lcm/ when installed)
_PACKAGE_ROOT = os.path.dirname(_CONFIG_DIR)

# Directory paths - try installed location first, fall back to editable
ROS_MSGS_DIR = os.path.join(_PACKAGE_ROOT, "sources", "ros_msgs")
if not os.path.isdir(ROS_MSGS_DIR):
    # Editable install - project root is two levels up from tools/foxglove_bridge/
    _PROJECT_ROOT = os.path.dirname(_PACKAGE_ROOT)
    ROS_MSGS_DIR = os.path.join(_PROJECT_ROOT, "sources", "ros_msgs")

LCM_PYTHON_MODULES_PATH = os.path.join(_PACKAGE_ROOT, "generated", "python_lcm_msgs", "lcm_msgs")
if not os.path.isdir(LCM_PYTHON_MODULES_PATH):
    _PROJECT_ROOT = os.path.dirname(_PACKAGE_ROOT)
    LCM_PYTHON_MODULES_PATH = os.path.join(
        _PROJECT_ROOT, "generated", "python_lcm_msgs", "lcm_msgs"
    )

# Thread pool settings
DEFAULT_THREAD_POOL_SIZE = 8
MESSAGE_BATCH_SIZE = 10
MAX_QUEUE_SIZE = 100

# Hardcoded schemas for Foxglove compatibility
HARDCODED_SCHEMAS = {
    "sensor_msgs.Image": {
        "foxglove_name": "sensor_msgs/msg/Image",
        "schema": {
            "type": "object",
            "properties": {
                "header": {
                    "type": "object",
                    "properties": {
                        "stamp": {
                            "type": "object",
                            "properties": {"sec": {"type": "integer"}, "nsec": {"type": "integer"}},
                        },
                        "frame_id": {"type": "string"},
                    },
                },
                "height": {"type": "integer"},
                "width": {"type": "integer"},
                "encoding": {"type": "string"},
                "is_bigendian": {"type": "boolean"},
                "step": {"type": "integer"},
                "data": {"type": "string", "contentEncoding": "base64"},
            },
        },
    },
    "sensor_msgs.CompressedImage": {
        "foxglove_name": "sensor_msgs/msg/CompressedImage",
        "schema": {
            "type": "object",
            "properties": {
                "header": {
                    "type": "object",
                    "properties": {
                        "stamp": {
                            "type": "object",
                            "properties": {"sec": {"type": "integer"}, "nsec": {"type": "integer"}},
                        },
                        "frame_id": {"type": "string"},
                    },
                },
                "format": {"type": "string"},
                "data": {"type": "string", "contentEncoding": "base64"},
            },
        },
    },
    "sensor_msgs.JointState": {
        "foxglove_name": "sensor_msgs/msg/JointState",
        "schema": {
            "type": "object",
            "properties": {
                "header": {
                    "type": "object",
                    "properties": {
                        "stamp": {
                            "type": "object",
                            "properties": {"sec": {"type": "integer"}, "nsec": {"type": "integer"}},
                        },
                        "frame_id": {"type": "string"},
                    },
                },
                "name": {"type": "array", "items": {"type": "string"}},
                "position": {"type": "array", "items": {"type": "number"}},
                "velocity": {"type": "array", "items": {"type": "number"}},
                "effort": {"type": "array", "items": {"type": "number"}},
            },
            "required": ["header", "name", "position", "velocity", "effort"],
        },
    },
    "tf2_msgs.TFMessage": {
        "foxglove_name": "tf2_msgs/msg/TFMessage",
        "schema": {
            "type": "object",
            "properties": {
                "transforms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "header": {
                                "type": "object",
                                "properties": {
                                    "stamp": {
                                        "type": "object",
                                        "properties": {
                                            "sec": {"type": "integer"},
                                            "nsec": {"type": "integer"},
                                        },
                                    },
                                    "frame_id": {"type": "string"},
                                },
                            },
                            "child_frame_id": {"type": "string"},
                            "transform": {
                                "type": "object",
                                "properties": {
                                    "translation": {
                                        "type": "object",
                                        "properties": {
                                            "x": {"type": "number"},
                                            "y": {"type": "number"},
                                            "z": {"type": "number"},
                                        },
                                    },
                                    "rotation": {
                                        "type": "object",
                                        "properties": {
                                            "x": {"type": "number"},
                                            "y": {"type": "number"},
                                            "z": {"type": "number"},
                                            "w": {"type": "number"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                }
            },
        },
    },
    "sensor_msgs.PointCloud2": {
        "foxglove_name": "sensor_msgs/msg/PointCloud2",
        "schema": {
            "type": "object",
            "properties": {
                "header": {
                    "type": "object",
                    "properties": {
                        "stamp": {
                            "type": "object",
                            "properties": {"sec": {"type": "integer"}, "nsec": {"type": "integer"}},
                            "required": ["sec", "nsec"],
                        },
                        "frame_id": {"type": "string"},
                    },
                    "required": ["stamp", "frame_id"],
                },
                "height": {"type": "integer"},
                "width": {"type": "integer"},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "offset": {"type": "integer"},
                            "datatype": {"type": "integer"},
                            "count": {"type": "integer"},
                        },
                        "required": ["name", "offset", "datatype", "count"],
                    },
                },
                "is_bigendian": {"type": "boolean"},
                "point_step": {"type": "integer"},
                "row_step": {"type": "integer"},
                "data": {"type": "string", "contentEncoding": "base64"},
                "is_dense": {"type": "boolean"},
            },
            "required": [
                "header",
                "height",
                "width",
                "fields",
                "is_bigendian",
                "point_step",
                "row_step",
                "data",
                "is_dense",
            ],
        },
    },
}

# Mapping of ROS primitive types to JSON schema types
TYPE_MAPPING = {
    "bool": {"type": "boolean"},
    "int8": {"type": "integer", "minimum": -128, "maximum": 127},
    "uint8": {"type": "integer", "minimum": 0, "maximum": 255},
    "int16": {"type": "integer", "minimum": -32768, "maximum": 32767},
    "uint16": {"type": "integer", "minimum": 0, "maximum": 65535},
    "int32": {"type": "integer", "minimum": -2147483648, "maximum": 2147483647},
    "uint32": {"type": "integer", "minimum": 0, "maximum": 4294967295},
    "int64": {"type": "integer"},
    "uint64": {"type": "integer", "minimum": 0},
    "float32": {"type": "number"},
    "float64": {"type": "number"},
    "string": {"type": "string"},
    "char": {"type": "integer", "minimum": 0, "maximum": 255},
    "byte": {"type": "integer", "minimum": 0, "maximum": 255},
    "time": {
        "type": "object",
        "properties": {"sec": {"type": "integer"}, "nsec": {"type": "integer"}},
        "required": ["sec", "nsec"],
    },
    "duration": {
        "type": "object",
        "properties": {"sec": {"type": "integer"}, "nsec": {"type": "integer"}},
        "required": ["sec", "nsec"],
    },
}
