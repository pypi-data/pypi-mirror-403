"""
Main LCM to Foxglove bridge implementation.
"""

import asyncio
import importlib
import json
import logging
import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import traceback

from foxglove_websocket.server import FoxgloveServer
from foxglove_websocket.types import ChannelId

import lcm

from .config import (
    DEFAULT_THREAD_POOL_SIZE,
    HARDCODED_SCHEMAS,
    MAX_QUEUE_SIZE,
    MESSAGE_BATCH_SIZE,
    logger,
)
from .message_processor import MessageProcessor
from .models import LcmMessage, TopicInfo
from .schema_generator import SchemaGenerator
from .topic_discovery import LcmTopicDiscoverer


class FoxgloveBridge:
    """Main bridge class that orchestrates LCM to Foxglove message forwarding"""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        schema_map: Optional[Dict[str, str]] = None,
        debug: bool = False,
        num_threads: int = DEFAULT_THREAD_POOL_SIZE,
        shm_channels: Optional[List[str]] = None,
        jpeg_shm_channels: Optional[List[str]] = None,
    ):
        self.host = host
        self.port = port
        self.discoverer: Optional[LcmTopicDiscoverer] = None
        self.lcm_thread: Optional[threading.Thread] = None
        self.running = True
        self.lc = lcm.LCM()
        self.topics: Dict[str, TopicInfo] = {}
        self.shm_topic_to_topic: Dict[str, str] = {}
        self.schema_generator = SchemaGenerator()
        self.message_handlers: Dict[str, Any] = {}
        self.schema_map = schema_map or {}
        self.debug = debug
        self.num_threads = num_threads

        self.shm_channels = shm_channels or []
        self.jpeg_shm_channels = jpeg_shm_channels or []
        self.shm_subscribers: Dict[str, Callable[[], None]] = {} # topic -> unsubscribe function
        self.shm_thread: Optional[threading.Thread] = None
        self.jpeg_shm_thread: Optional[threading.Thread] = None

        # For cross-thread communication
        self.topic_queue: asyncio.Queue = asyncio.Queue()
        self.message_queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=MAX_QUEUE_SIZE)
        self.server_queue: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.server: Optional[FoxgloveServer] = None

        # For parallelization
        self.message_processor: Optional[MessageProcessor] = None

        # Configure verbose debugging
        if debug:
            logger.setLevel(logging.DEBUG)

    async def run(self):
        """Run the bridge with proper context management for FoxgloveServer"""
        logger.info(
            f"Starting LCM-Foxglove bridge on {self.host}:{self.port} with {self.num_threads} threads"
        )

        # Store reference to the event loop that will be used for all async operations
        self.loop = asyncio.get_running_loop()

        # Start the message processor
        self.message_processor = MessageProcessor(
            self.message_queue, self.server_queue, num_threads=self.num_threads, debug=self.debug
        )
        self.message_processor.start()

        # Start topic discovery
        self.discoverer = LcmTopicDiscoverer(self._on_topic_discovered, self.schema_map)
        self.discoverer.start()

        # Start LCM handling thread
        self.lcm_thread = threading.Thread(target=self._lcm_thread_func)
        self.lcm_thread.daemon = True
        self.lcm_thread.start()

        # Start SHM handling thread if we have SHM topics
        if self.shm_channels:
            self.shm_thread = threading.Thread(target=self._shm_thread_func)
            self.shm_thread.daemon = True
            self.shm_thread.start()

        # Start JPEG SHM handling thread if we have JPEG SHM topics
        if self.jpeg_shm_channels:
            self.jpeg_shm_thread = threading.Thread(target=self._jpeg_shm_thread_func)
            self.jpeg_shm_thread.daemon = True
            self.jpeg_shm_thread.start()

        # Create and start Foxglove WebSocket server as a context manager
        async with FoxgloveServer(
            host=self.host,
            port=self.port,
            name="LCM-Foxglove Bridge",
            capabilities=["clientPublish"],
            supported_encodings=["json"],
        ) as server:
            self.server = server
            logger.info(f"WebSocket server started on {self.host}:{self.port}")
            logger.info("Waiting for LCM topics...")

            # Start task to process new topics
            topic_processor_task = asyncio.create_task(self._process_topic_queue())

            # Start task to process messages for sending to server
            server_processor_task = asyncio.create_task(self._process_server_queue())

            try:
                # Keep running until interrupted
                while self.running:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("\nTask cancelled")
            finally:
                # Cancel the processor tasks
                topic_processor_task.cancel()
                server_processor_task.cancel()
                try:
                    await topic_processor_task
                    await server_processor_task
                except asyncio.CancelledError:
                    pass
                self.stop()

    async def _process_topic_queue(self):
        """Process new topics from the queue"""
        while True:
            try:
                # Get next topic from the queue
                topic_info = await self.topic_queue.get()

                # Only register the topic if the server is available
                if self.server:
                    try:
                        # Get the foxglove schema name (either from hardcoded schemas or standard conversion)
                        if topic_info.schema_type in HARDCODED_SCHEMAS:
                            foxglove_schema_name = HARDCODED_SCHEMAS[topic_info.schema_type][
                                "foxglove_name"
                            ]
                        else:
                            # Convert from package.MsgType to package/msg/MsgType format for Foxglove
                            foxglove_schema_name = topic_info.schema_type.replace(".", "/msg/")

                        # Store for reference
                        topic_info.foxglove_schema_name = foxglove_schema_name

                        # Format the schema for Foxglove
                        channel_info = {
                            "topic": topic_info.name,
                            "encoding": "json",
                            "schemaName": foxglove_schema_name,
                            "schemaEncoding": "jsonschema",
                            "schema": json.dumps(topic_info.schema),
                        }

                        # Add channel to Foxglove server
                        channel_id = await self.server.add_channel(channel_info)
                        topic_info.channel_id = channel_id

                        logger.info(
                            f"Registered Foxglove channel: {topic_info.name} with schema: {foxglove_schema_name}"
                        )

                        # Special handling for different message types
                        schema_type_lower = topic_info.schema_type.lower()
                        if schema_type_lower == "tf2_msgs.tfmessage":
                            logger.info(f"TF topic registered with channel ID: {channel_id}")
                            # Prioritize TF messages
                            topic_info.priority = 10
                        elif schema_type_lower == "sensor_msgs.pointcloud2":
                            logger.info(
                                f"PointCloud2 topic registered with channel ID: {channel_id}"
                            )
                            # Rate limit PointCloud2 messages (they're large)
                            topic_info.rate_limit_ms = 100  # 10 Hz max
                        elif schema_type_lower in [
                            "sensor_msgs.image",
                            "sensor_msgs.compressedimage",
                        ]:
                            # Rate limit image messages
                            topic_info.rate_limit_ms = 50  # 20 Hz max
                    except Exception as e:
                        logger.error(
                            f"Error registering Foxglove channel for {topic_info.name}: {e}"
                        )
                        traceback.print_exc()

                # Mark task as done
                self.topic_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in topic processor: {e}")
                traceback.print_exc()

    async def _process_server_queue(self):
        """Process messages from the queue and send to Foxglove server"""
        while True:
            try:
                # Collect a batch of messages from the queue
                batched_messages = []

                # Try to get a message (blocking with timeout)
                try:
                    item = self.server_queue.get(block=True, timeout=0.01)
                    batched_messages.append(item)

                    # Try to get more messages non-blocking
                    for _ in range(MESSAGE_BATCH_SIZE - 1):
                        try:
                            item = self.server_queue.get(block=False)
                            batched_messages.append(item)
                        except queue.Empty:
                            break
                except queue.Empty:
                    # No messages, just wait and try again
                    await asyncio.sleep(0.01)
                    continue

                # Process all collected messages
                for topic_info, msg_dict, timestamp_ns in batched_messages:
                    try:
                        if self.server and topic_info and topic_info.channel_id is not None:
                            # Convert the message to JSON
                            json_data = json.dumps(msg_dict).encode("utf-8")

                            # Send to Foxglove
                            await self.server.send_message(
                                topic_info.channel_id, timestamp_ns, json_data
                            )

                            # Log important messages being sent
                            schema_type_lower = topic_info.schema_type.lower()
                            if (
                                schema_type_lower
                                in ["tf2_msgs.tfmessage", "sensor_msgs.pointcloud2"]
                                and self.debug
                            ):
                                logger.debug(
                                    f"Sent {schema_type_lower} message on channel {topic_info.name}"
                                )

                        # Mark as done
                        self.server_queue.task_done()
                    except Exception as e:
                        logger.error(f"Error sending message for {topic_info.name}: {e}")
                        # Make sure to mark as done even if there's an error
                        self.server_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in server processor: {e}")

    def _lcm_thread_func(self):
        """Thread for handling LCM messages"""
        while self.running:
            try:
                # Handle LCM messages until interrupted
                self.lc.handle_timeout(100)  # 100ms timeout
            except Exception as e:
                logger.error(f"Error handling LCM message: {e}")

    def _shm_thread_func(self):
        """Thread for handling SharedMemory topics"""
        try:
            from dimos.protocol.pubsub.shmpubsub import PickleSharedMemory

            logger.info(f"Starting SHM thread for topics: {self.shm_channels}")

            shm = PickleSharedMemory()
            shm.start()

            for channel in self.shm_channels:
                self._subscribe_to_shm_channel(shm, channel, is_jpeg=False)

            while self.running:
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in SHM thread: {e}")
            traceback.print_exc()

    def _jpeg_shm_thread_func(self):
        """Thread for handling JPEG SharedMemory topics"""
        try:
            from dimos.protocol.pubsub.jpeg_shm import JpegSharedMemory

            logger.info(f"Starting JPEG SHM thread for topics: {self.jpeg_shm_channels}")

            shm = JpegSharedMemory()
            shm.start()

            for channel in self.jpeg_shm_channels:
                self._subscribe_to_shm_channel(shm, channel, is_jpeg=True)

            while self.running:
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in JPEG SHM thread: {e}")
            traceback.print_exc()

    def _add_topic(self, topic_name: str):
        try:
            logger.info(f"Discovered topic: {topic_name}")

            # Extract base topic name and schema type
            base_topic, schema_type = topic_name.split("#", 1)
            package, msg_type = schema_type.split(".", 1)

            # Generate schema from ROS message definition
            logger.info(f"Generating schema for {schema_type}...")
            schema = self.schema_generator.generate_schema(schema_type)

            # Try to import the LCM message class
            try:
                module_name = f"lcm_msgs.{package}.{msg_type}"
                logger.info(f"Importing LCM module {module_name}...")
                module = importlib.import_module(module_name)
                lcm_class = getattr(module, msg_type)
            except Exception as e:
                logger.warning(f"Error importing LCM class for {schema_type}: {e}")
                logger.warning(f"Will try to continue without decoding...")
                lcm_class = None

            # Create topic info
            topic_info = TopicInfo(
                name=base_topic,
                full_topic_name=topic_name,
                schema_type=schema_type,
                schema=schema,
                lcm_class=lcm_class,
                package=package,
                msg_type=msg_type,
            )

            # Set message priority based on message type
            schema_type_lower = schema_type.lower()
            if schema_type_lower == "tf2_msgs.tfmessage":
                topic_info.priority = 10  # Highest priority for TF
            elif schema_type_lower in ["sensor_msgs.pointcloud2"]:
                topic_info.priority = 5  # High priority for point clouds

            # Add topic to our map
            self.topics[topic_name] = topic_info

            # Queue the topic for registration with Foxglove
            if self.loop:
                self.loop.call_soon_threadsafe(self.topic_queue.put_nowait, topic_info)
        except Exception as e:
            logger.error(f"Error processing topic {topic_name}: {e}")
            traceback.print_exc()
    

    def _on_topic_discovered(self, topic_name: str):
        """Called when a new topic is discovered"""
        # Skip if we've already processed this topic
        if topic_name in self.topics:
            return

        try:
            self._add_topic(topic_name)

            # Subscribe to the FULL LCM topic name (including schema annotation)
            subscription = self.lc.subscribe(topic_name, self._on_lcm_message)
            self.message_handlers[topic_name] = subscription  # TODO: Is this used?

            logger.info(f"Subscribed to LCM topic: {topic_name}")
        except Exception as e:
            logger.error(f"Error processing topic {topic_name}: {e}")
            traceback.print_exc()
    
    def _subscribe_to_shm_channel(self, shm, channel: str, is_jpeg: bool = False):
        try:
            self._add_topic(channel)
            base_topic = channel.split("#", 1)[0]
            self.shm_topic_to_topic[base_topic] = channel

            def shm_callback(msg, topic_name):
                self._on_shm_message(topic_name, msg, is_jpeg=is_jpeg)

            unsub = shm.subscribe(base_topic, shm_callback)
            self.shm_subscribers[base_topic] = unsub

        except Exception as e:
            logger.error(f"Error subscribing to SHM topic {channel}: {e}")
            traceback.print_exc()

    def _on_lcm_message(self, channel: str, data: bytes):
        """Called when an LCM message is received"""
        # Get topic info
        topic_info = self.topics.get(channel)

        if not topic_info:
            if self.debug:
                logger.warning(f"Received message for unknown channel: {channel}")
            return

        try:
            # Calculate priority based on message type (higher = more important)
            priority = 0
            schema_type_lower = topic_info.schema_type.lower()
            if schema_type_lower == "tf2_msgs.tfmessage":
                priority = 10  # Highest priority for TF
            elif schema_type_lower in ["sensor_msgs.pointcloud2"]:
                priority = 5  # High priority for point clouds

            # Create a message container
            msg = LcmMessage(
                topic_info=topic_info, data=data, receive_time=time.time(), priority=priority
            )

            # Skip rate-limited topics early to avoid filling the queue
            min_interval_sec = topic_info.rate_limit_ms / 1000.0
            if (
                min_interval_sec > 0
                and topic_info.is_high_frequency
                and time.time() - topic_info.last_sent_timestamp < min_interval_sec
            ):
                # Too frequent, skip this message
                if self.debug:
                    logger.debug(f"Rate limiting message for {channel}")
                return

            # Skip if not yet registered with Foxglove
            if topic_info.channel_id is None:
                if self.debug:
                    logger.debug(f"Channel not yet registered for {channel}, skipping message")
                return

            # Push to queue for processing by the thread pool
            try:
                self.message_queue.put(msg, block=False)
            except queue.Full:
                # Queue is full, drop this message
                if self.debug:
                    logger.warning(f"Message queue full, dropping message for {channel}")
        except Exception as e:
            logger.error(f"Error queuing message on {channel}: {e}")

    def _on_shm_message(self, topic: str, msg, is_jpeg: bool = False):
        topic_info = self.topics.get(self.shm_topic_to_topic.get(topic, ''))

        if not topic_info:
            logger.warning(f"Received SHM message for unknown topic: {topic}")
            return

        try:
            # Skip if not yet registered with Foxglove
            if topic_info.channel_id is None:
                return

            if is_jpeg:
                # For JPEG SHM, msg is already a sensor_msgs.Image object
                # We need to convert it back to LCM format, then use the standard converter
                if topic_info.lcm_class:
                    # Convert Image object to LCM bytes and back
                    lcm_msg = topic_info.lcm_class.lcm_decode(msg.lcm_encode())
                    msg_dict = self.message_processor.converter.convert_message(topic_info, lcm_msg)
                else:
                    logger.error(f"No LCM class available for JPEG SHM topic {topic}")
                    return
            else:
                # Use the existing message converter - SHM already gives us the typed object
                # This takes an average of 0.005062 seconds
                msg = topic_info.lcm_class.lcm_decode(msg.lcm_encode())
                # This takes an average of 0.013835 seconds
                msg_dict = self.message_processor.converter.convert_message(topic_info, msg)

            if not msg_dict:
                logger.error(f"Failed to convert SHM message for {topic}")
                return

            timestamp_ns = int(time.time() * 1e9)

            try:
                self.server_queue.put((topic_info, msg_dict, timestamp_ns), block=False)
            except queue.Full:
                logger.warning(f"Server queue full, dropping SHM message for {topic}")

        except Exception as e:
            logger.error(f"Error processing SHM message on {topic}: {e}")
            traceback.print_exc()

    def stop(self):
        """Stop the bridge cleanly"""
        logger.info("Stopping LCM-Foxglove bridge")
        self.running = False
        if self.discoverer:
            self.discoverer.stop()
        if self.message_processor:
            self.message_processor.stop()

        for topic, unsub in self.shm_subscribers.items():
            try:
                unsub()
            except Exception as e:
                logger.error(f"Error stopping SHM subscription for {topic}: {e}")
