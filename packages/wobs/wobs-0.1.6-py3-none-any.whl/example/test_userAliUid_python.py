#!/usr/bin/env python3
"""
Test userAliUid functionality for Python SDK
This demo outputs a trackpoint every 3 seconds to monitor userAliUid changes
Manually modify wobs.config.json to see real-time updates

Save this file to: wuying-guestos-observer-python/examples/test_userAliUid.py
"""

import sys
import time
import signal
from wobs.observer import init, shutdown, new_track_point
from wobs.userInfo import init_user_info, get_user_info_safe, stop_config_file_watcher

print("=== userAliUid Test Demo (Python) ===")
print("This program will output a trackpoint every 3 seconds.")
print("Manually create or modify wobs.config.json to see userAliUid updates.\n")
print("Config file locations by platform:")
print("  - Android: /data/vendor/log/wuying/wobs.config.json")
print("  - Windows: C:\\ProgramData\\wuying\\wobs.config.json")
print("  - Linux/macOS: /var/log/wuying/wobs.config.json")
print('\nFile format: {"userAliUid": "1234567890"}')
print("\nPress Ctrl+C to stop...\n")

# Initialize observer and user info
init("test_userAliUid", "./", "./")
init_user_info()

counter = 0
running = True


def signal_handler(sig, frame):
    """Handle graceful shutdown."""
    global running
    print("\n\nStopping test...")
    running = False


# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

print("Started monitoring... waiting for trackpoints...\n")

try:
    while running:
        counter += 1
        
        user_info = get_user_info_safe()
        user_ali_uid = user_info.userAliUid if user_info.userAliUid else "not set"
        
        print(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] Trackpoint #{counter}")
        print(f"  userAliUid: {user_ali_uid}")
        print(f"  userName: {user_info.userName}")
        print(f"  osType: {user_info.osType}")
        print(f"  instanceID: {user_info.instanceID if user_info.instanceID else 'N/A'}")
        
        # Send trackpoint with custom attributes
        new_track_point("test_userAliUid_monitoring", {
            "counter": str(counter),
            "userAliUid": user_ali_uid,
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S')
        })
        
        print("  ✓ Trackpoint sent\n")
        
        # Sleep for 3 seconds
        time.sleep(3)

except KeyboardInterrupt:
    print("\n\nStopping test...")

finally:
    # Cleanup
    stop_config_file_watcher()
    shutdown()
    print("Observer shutdown complete. Goodbye!")
