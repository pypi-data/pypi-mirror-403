#!/usr/bin/env python3
"""
Test script for the modular LCM-Foxglove bridge.
"""

import sys
import os
import asyncio
from foxglove_websocket import run_cancellable

# Add the parent directory to the path so we can import the bridge
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add python_lcm_msgs to path so we can import LCM message modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
lcm_module_dir = os.path.join(parent_dir, "python_lcm_msgs")
sys.path.append(lcm_module_dir)

from foxglove_bridge import LcmFoxgloveBridge


async def test_bridge():
    """Test the modular bridge implementation"""
    print("Testing modular LCM-Foxglove bridge...")
    
    # Create a bridge instance
    bridge = LcmFoxgloveBridge(
        host="localhost",
        port=8765,
        debug=True,
        num_threads=4
    )
    
    print("Bridge created successfully!")
    print("Starting bridge (press Ctrl+C to stop)...")
    
    try:
        await bridge.run()
    except KeyboardInterrupt:
        print("\nBridge stopped by user")
    except Exception as e:
        print(f"Error running bridge: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_cancellable(test_bridge())