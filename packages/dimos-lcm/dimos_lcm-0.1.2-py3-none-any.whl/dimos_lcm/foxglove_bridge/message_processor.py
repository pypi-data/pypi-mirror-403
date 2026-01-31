"""
Threaded message processing for the LCM-Foxglove bridge.
"""

import queue
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from .config import DEFAULT_THREAD_POOL_SIZE, MESSAGE_BATCH_SIZE, logger
from .message_converter import MessageConverter
from .models import LcmMessage


class MessageProcessor:
    """Processes LCM messages for conversion and sending to Foxglove"""

    def __init__(
        self,
        message_queue: queue.PriorityQueue,
        server_queue: queue.Queue,
        num_threads: int = DEFAULT_THREAD_POOL_SIZE,
        debug: bool = False,
    ):
        self.message_queue = message_queue
        self.server_queue = server_queue
        self.converter = MessageConverter(debug=debug)
        self.running = True
        self.executor = ThreadPoolExecutor(
            max_workers=num_threads, thread_name_prefix="msg_processor"
        )
        self.debug = debug
        self.message_cache: Dict[str, Any] = {}  # Cache for message hashes

    def start(self):
        """Start the message processor"""
        self.running = True
        self.executor.submit(self._process_messages_loop)
        logger.info(f"Message processor started with {self.executor._max_workers} threads")

    def stop(self):
        """Stop the message processor"""
        self.running = False
        self.executor.shutdown(wait=False)
        logger.info("Message processor stopped")

    def _process_messages_loop(self):
        """Main loop for processing messages"""
        while self.running:
            try:
                # Get a batch of messages to process
                messages = []
                message_count = 0

                try:
                    # Get the first message (blocking with timeout)
                    message = self.message_queue.get(block=True, timeout=0.1)
                    messages.append(message)
                    message_count += 1

                    # Try to get more messages up to batch size (non-blocking)
                    for _ in range(MESSAGE_BATCH_SIZE - 1):
                        try:
                            message = self.message_queue.get(block=False)
                            messages.append(message)
                            message_count += 1
                        except queue.Empty:
                            break
                except queue.Empty:
                    # No messages to process
                    continue

                if not messages:
                    continue

                try:
                    # Group messages by topic
                    grouped_messages = defaultdict(list)
                    for msg in messages:
                        grouped_messages[msg.topic_info.full_topic_name].append(msg)

                    # Process each topic's messages in parallel
                    futures = []
                    messages_to_process = []

                    for topic_name, topic_messages in grouped_messages.items():
                        # Sort by priority
                        topic_messages.sort(key=lambda m: m.priority, reverse=True)

                        # Only process the latest message for each topic if we have too many
                        if len(topic_messages) > 5:
                            to_process = [topic_messages[0]]  # Process the highest priority message
                            messages_to_process.extend(to_process)
                            # We'll mark the rest as done later
                            logger.debug(
                                f"Skipping {len(topic_messages) - 1} old messages for {topic_name}"
                            )
                        else:
                            messages_to_process.extend(topic_messages)

                    # Submit all messages for processing
                    for msg in messages_to_process:
                        if self.executor._shutdown:
                            break
                        futures.append(self.executor.submit(self._process_single_message, msg))

                    # Wait for all processing to complete
                    for future in futures:
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Error in message processing: {e}")

                finally:
                    # Mark all fetched messages as done, regardless of processing success
                    # This ensures we don't call task_done too many times
                    for _ in range(message_count):
                        try:
                            self.message_queue.task_done()
                        except ValueError:
                            # If we already called task_done somewhere else, ignore the error
                            pass

            except Exception as e:
                logger.error(f"Error in message processor loop: {e}")

    def _process_single_message(self, lcm_message: LcmMessage):
        """Process a single LCM message"""
        try:
            topic_info = lcm_message.topic_info
            data = lcm_message.data

            # Skip throttled topics
            now = time.time()
            min_interval_sec = topic_info.rate_limit_ms / 1000.0
            if min_interval_sec > 0 and now - topic_info.last_sent_timestamp < min_interval_sec:
                if self.debug:
                    logger.debug(f"Throttling message on {topic_info.name}")
                return

            # Skip if channel isn't registered yet
            if topic_info.channel_id is None:
                if self.debug:
                    logger.debug(f"Channel not registered for {topic_info.name}")
                return

            # Try to decode and convert the message
            if topic_info.lcm_class:
                try:
                    msg = topic_info.lcm_class.lcm_decode(data)

                    # Check message caching
                    should_process = True
                    if topic_info.is_high_frequency:
                        # For high-frequency topics, check if the message is different from the last one
                        msg_hash = hash(data)
                        if topic_info.cache_hash == msg_hash:
                            should_process = False
                        else:
                            topic_info.cache_hash = msg_hash

                    if should_process:
                        # Convert the message to dict format for Foxglove
                        msg_dict = self.converter.convert_message(topic_info, msg)

                        # Update topic info
                        topic_info.last_sent_timestamp = now
                        topic_info.message_count += 1

                        # Detect high-frequency topics
                        if topic_info.message_count >= 100 and not topic_info.is_high_frequency:
                            elapsed = now - lcm_message.receive_time
                            if elapsed < 5.0:  # 100 messages in less than 5 seconds
                                # This is a high-frequency topic
                                topic_info.is_high_frequency = True
                                # Set rate limit for high-frequency topics (100ms)
                                if topic_info.rate_limit_ms == 0:
                                    topic_info.rate_limit_ms = 100
                                logger.info(
                                    f"Detected high-frequency topic {topic_info.name}, rate limiting to {topic_info.rate_limit_ms}ms"
                                )

                        # Put on server queue for sending
                        try:
                            timestamp_ns = int(now * 1e9)
                            self.server_queue.put((topic_info, msg_dict, timestamp_ns), block=False)
                        except queue.Full:
                            logger.debug(
                                f"Server queue full, dropping message for {topic_info.name}"
                            )

                except Exception as e:
                    logger.error(f"Error processing message for {topic_info.name}: {e}")

        except Exception as e:
            logger.error(f"Error in _process_single_message: {e}")
            # We no longer call task_done() here - it's handled in the main loop
