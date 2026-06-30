#!/usr/bin/env python3
"""
Standalone touch diagnostic script.
Shows raw touch events from all input devices.
"""

import os
import struct
import sys

EV_SYN, EV_KEY, EV_ABS, EV_REL = 0, 1, 3, 2
BTN_TOUCH = 330
ABS_X, ABS_Y = 0, 1

def read_device(device_path):
    """Read raw events from a single input device."""
    try:
        f = open(device_path, "rb")
    except Exception as e:
        print(f"  ✗ Cannot open: {e}")
        return False
    
    print(f"  ✓ Opened successfully")
    
    # Detect struct format
    fmt24, fmt16 = "qqHHi", "llHHi"
    ev_size = 24 if struct.calcsize(fmt24) == 24 else 16
    fmt = fmt24 if ev_size == 24 else fmt16
    print(f"  → Event size: {ev_size} bytes (format: {fmt})")
    
    print(f"\n  Listening for events (press Ctrl+C to skip to next device)...")
    event_count = [0]
    touch_events = []
    
    try:
        while len(touch_events) < 50:  # Collect up to 50 events
            try:
                data = f.read(ev_size)
                if len(data) < ev_size:
                    print(f"  EOF after {event_count[0]} events")
                    break
                
                sec, usec, etype, code, value = struct.unpack(fmt, data)
                event_count[0] += 1
                
                # Show touch-related events
                if etype == EV_ABS:
                    if code == ABS_X:
                        print(f"    ABS_X: {value}")
                        touch_events.append(("ABS_X", value))
                    elif code == ABS_Y:
                        print(f"    ABS_Y: {value}")
                        touch_events.append(("ABS_Y", value))
                elif etype == EV_KEY and code == BTN_TOUCH:
                    status = "PRESS" if value == 1 else "RELEASE"
                    print(f"    BTN_TOUCH: {status}")
                    touch_events.append(("BTN_TOUCH", status))
                elif etype == EV_SYN:
                    if touch_events:
                        print(f"    [SYN] Sync")
                        touch_events = []
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"    Error reading: {e}")
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        f.close()
    
    print(f"\n  Total events: {event_count[0]}")
    return event_count[0] > 0

def main():
    print("=" * 60)
    print("TOUCH DEVICE DIAGNOSTIC")
    print("=" * 60)
    
    # List all input devices
    print("\n1. Available input devices in /dev/input/:")
    input_dir = "/dev/input"
    if os.path.exists(input_dir):
        devices = sorted(os.listdir(input_dir))
        for d in devices:
            path = os.path.join(input_dir, d)
            print(f"  • {d:20} → {path}")
    else:
        print("  ✗ /dev/input does not exist!")
        return
    
    # Try event devices
    print("\n2. Testing event devices:")
    found_touch = False
    for i in range(10):
        device_path = f"/dev/input/event{i}"
        if os.path.exists(device_path):
            print(f"\n  Testing {device_path}:")
            if read_device(device_path):
                found_touch = True
    
    # Try known touchscreen paths
    if not found_touch:
        print("\n3. Trying alternate paths:")
        for alt_path in ["/dev/input/touchscreen", "/dev/input/ts", "/dev/touchscreen"]:
            if os.path.exists(alt_path):
                print(f"\n  Testing {alt_path}:")
                read_device(alt_path)
    
    print("\n" + "=" * 60)
    print("Diagnostic complete. Check output above for touch events.")
    print("=" * 60)

if __name__ == "__main__":
    main()
