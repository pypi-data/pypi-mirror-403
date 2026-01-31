"""
Main entry point for the LCM-Foxglove bridge.
"""

import asyncio
import argparse
import json
import os
import sys
import logging
from foxglove_websocket import run_cancellable

from .bridge import LcmFoxgloveBridge
from .config import logger, DEFAULT_THREAD_POOL_SIZE


async def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='LCM to Foxglove WebSocket Bridge')
    parser.add_argument('--host', default='0.0.0.0', help='WebSocket server host')
    parser.add_argument('--port', type=int, default=8765, help='WebSocket server port')
    parser.add_argument('--debug', action='store_true', help='Enable verbose debug output')
    parser.add_argument('--map-file', type=str, help='JSON file mapping topic names to schema types')
    parser.add_argument('--threads', type=int, default=DEFAULT_THREAD_POOL_SIZE, 
                        help=f'Number of threads for message processing (default: {DEFAULT_THREAD_POOL_SIZE})')
    args = parser.parse_args()
    
    # Configure debug logging
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Load schema map if provided
    schema_map = {}
    if args.map_file:
        try:
            with open(args.map_file, 'r') as f:
                schema_map = json.load(f)
            logger.info(f"Loaded schema map from {args.map_file} with {len(schema_map)} entries")
        except Exception as e:
            logger.error(f"Error loading schema map file: {e}")
    
    # Create and run the bridge
    bridge = LcmFoxgloveBridge(
        host=args.host, 
        port=args.port, 
        schema_map=schema_map,
        debug=args.debug,
        num_threads=args.threads
    )
    await bridge.run()


if __name__ == "__main__":
    # Add python_lcm_msgs to path so we can import LCM message modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to get to the main directory
    parent_dir = os.path.dirname(current_dir)
    lcm_module_dir = os.path.join(parent_dir, "python_lcm_msgs")
    sys.path.append(lcm_module_dir)
    
    # Run the main function
    run_cancellable(main())