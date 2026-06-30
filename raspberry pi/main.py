#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
#  main.py  –  Entry point · State machine · Main loop
# ─────────────────────────────────────────────────────────────
#
#  ╔══════════════════════════════════════════════════════════╗
#  ║  INTEGRATION POINT 1 — YOUR DISPLAY MODULE               ║
#  ║                                                          ║
#  ║  Option A (recommended):                                 ║
#  ║    Place your display code in  display.py                ║
#  ║    and uncomment the import below.                       ║
#  ║                                                          ║
#  ║  Option B:                                               ║
#  ║    Paste your display code directly after this block.    ║
#  ╚══════════════════════════════════════════════════════════╝
#
from display import *          # <── uncomment when ready
#
# ─────────────────────────────────────────────────────────────
#  INTEGRATION POINT 2 — YOUR AD3 / DIGILENT CODE
#
#  Paste your AD3 initialisation and read_voltage() wrapper
#  in the section marked "AD3 MODULE" below.
# ─────────────────────────────────────────────────────────────

import time
import threading
from config import cfg, State
from calculations import update_calculations
from ui_screens import (
    render_home, render_menu, render_settings,
    render_graphs, render_youngs, render_wifi,
    render_ad3, render_configure,
    scan_wifi_networks, hit_test,
)

# ─────────────────────────────────────────────────────────────
#  AD3 MODULE  –  insert / adapt your AD3 code here
# ─────────────────────────────────────────────────────────────
#
# The system calls  ad3_connect()  and  ad3_read_voltage()
# at runtime.  Replace the stubs below with your real code.
#
try:
    from ctypes import cdll, c_int, c_bool, c_double, c_byte, byref, POINTER

    # ── Paste / import your AD3 initialisation here ──────────
    # Example (mirrors your existing code):
    #
    # dwf      = cdll.LoadLibrary("libdwf.so")
    # _hdwf    = c_int()
    # _sts     = c_byte()
    # _BUF_SZ  = 256
    # _buf     = (c_double * _BUF_SZ)()
    #
    # def ad3_connect() -> bool:
    #     dwf.FDwfDeviceOpen(c_int(-1), byref(_hdwf))
    #     if _hdwf.value == 0:
    #         return False
    #     # W1 → 3.3 V DC
    #     dwf.FDwfAnalogOutNodeEnableSet(_hdwf, c_int(0), c_int(0), c_bool(True))
    #     dwf.FDwfAnalogOutNodeFunctionSet(_hdwf, c_int(0), c_int(0), c_int(0))
    #     dwf.FDwfAnalogOutNodeOffsetSet  (_hdwf, c_int(0), c_int(0), c_double(3.3))
    #     dwf.FDwfAnalogOutNodeAmplitudeSet(_hdwf,c_int(0), c_int(0), c_double(0.0))
    #     dwf.FDwfAnalogOutConfigure(_hdwf, c_int(0), c_bool(True))
    #     # CH1 config
    #     dwf.FDwfAnalogInChannelEnableSet (_hdwf, c_int(0), c_bool(True))
    #     dwf.FDwfAnalogInChannelRangeSet  (_hdwf, c_int(0), c_double(10.0))
    #     dwf.FDwfAnalogInChannelOffsetSet (_hdwf, c_int(0), c_double(0.0))
    #     dwf.FDwfAnalogInChannelCouplingSet(_hdwf,c_int(0), c_int(0))
    #     dwf.FDwfAnalogInFrequencySet     (_hdwf, c_double(1000.0))
    #     dwf.FDwfAnalogInBufferSizeSet    (_hdwf, c_int(_BUF_SZ))
    #     dwf.FDwfAnalogInAcquisitionModeSet(_hdwf,c_int(0))
    #     return True
    #
    # def ad3_read_voltage() -> float:
    #     dwf.FDwfAnalogInConfigure(_hdwf, c_bool(False), c_bool(True))
    #     for _ in range(200):
    #         dwf.FDwfAnalogInStatus(_hdwf, c_bool(True), byref(_sts))
    #         if _sts.value == 2:
    #             break
    #         time.sleep(0.01)
    #     dwf.FDwfAnalogInStatusData(_hdwf, c_int(0), _buf, c_int(_BUF_SZ))
    #     return sum(_buf) / _BUF_SZ
    #
    # def ad3_disconnect():
    #     dwf.FDwfAnalogOutConfigure(_hdwf, c_int(0), c_bool(False))
    #     dwf.FDwfDeviceClose(_hdwf)

    # ── Stub fallback (remove when real code is inserted) ─────
    raise ImportError("stub")

except Exception:
    # Simulation: sine wave so graphs are visible without hardware
    import math as _math
    _sim_t = [0.0]

    def ad3_connect() -> bool:
        print("[AD3] Simulation mode – no hardware")
        return True  # pretend it connected

    def ad3_read_voltage() -> float:
        _sim_t[0] += 0.05
        return 0.015 * _math.sin(_sim_t[0]) + 0.002 * _math.sin(_sim_t[0] * 7)

    def ad3_disconnect():
        pass


# ─────────────────────────────────────────────────────────────
#  Touch-input integration
#  (your existing touch_reader thread lives in display.py;
#   we access touch_lock / last_touch / touch_just through the module)
# ─────────────────────────────────────────────────────────────
try:
    import display  # real hardware
except ImportError:
    # Simulation stubs
    import threading
    class display:
        touch_lock = threading.Lock()
        last_touch = None
        touch_just = False


def poll_touch():
    """Consume one touch event; return (x,y) or None."""
    try:
        with display.touch_lock:
            if display.touch_just:
                result = display.last_touch
                display.touch_just = False
                print(f"[poll_touch] CONSUMED touch: {result}")
                return result
    except TypeError as e:
        print(f"[poll_touch] Error: {e}")
    return None


# ─────────────────────────────────────────────────────────────
#  Sensor polling thread
# ─────────────────────────────────────────────────────────────
_sensor_lock = threading.Lock()

def sensor_loop():
    """Background thread: read AD3, update cfg, 10 Hz."""
    while True:
        if cfg["ad3_connected"]:
            try:
                v = ad3_read_voltage()
                with _sensor_lock:
                    update_calculations(v)
            except Exception as e:
                print(f"[sensor] Read error: {e}")
        time.sleep(0.1)


# ─────────────────────────────────────────────────────────────
#  State machine
# ─────────────────────────────────────────────────────────────
class App:
    FPS   = 30
    FRAME = 1.0 / FPS

    def __init__(self):
        self.state       = State.HOME
        self.prev_state  = None
        self.t           = 0.0
        self.wifi_nets   = []
        self.wifi_sel    = [0]        # mutable list for wifi screen
        self._dirty      = True       # force first draw

    # ── navigate ─────────────────────────────────────────────
    def goto(self, new_state):
        self.prev_state = self.state
        self.state      = new_state
        self._dirty     = True
        print(f"[nav] {self.prev_state} → {self.state}")

    # ── handle a confirmed touch ──────────────────────────────
    def handle_touch(self, sx, sy, buttons, extra=None):
        print(f"[handle_touch] Touch at ({sx},{sy}), buttons={len(buttons)}, state={self.state}")
        hit = hit_test(buttons, sx, sy)
        print(f"[handle_touch] hit_test result: {hit}")
        if hit is None:
            print(f"[handle_touch] No button hit")
            return

        s = self.state

        if s == State.HOME:
            if hit == "GET STARTED":
                self.goto(State.MENU)

        elif s == State.MENU:
            if hit == "<BACK":       self.goto(State.HOME)
            elif hit == "SETTINGS":  self.goto(State.SETTINGS)
            elif hit == "LIVE GRAPHS":    self.goto(State.GRAPHS)
            elif hit == "YOUNGS MODULUS": self.goto(State.YOUNGS_MODULUS)

        elif s == State.SETTINGS:
            if hit == "<BACK":           self.goto(State.MENU)
            elif hit == "CONNECT WIFI":  self.goto(State.WIFI)
            elif hit == "CONNECT AD3":   self.goto(State.AD3)
            elif hit == "CONFIGURE":     self.goto(State.CONFIGURE)

        elif s == State.GRAPHS:
            if hit == "<BACK":   self.goto(State.MENU)

        elif s == State.YOUNGS_MODULUS:
            if hit == "<BACK":   self.goto(State.MENU)

        elif s == State.WIFI:
            if hit == "<BACK":
                self.goto(State.SETTINGS)
            elif hit == "CONNECT":
                nets = extra if extra else self.wifi_nets
                sel  = self.wifi_sel[0]
                ssid = nets[sel] if sel < len(nets) else ""
                # Try nmcli, fall back to simulation
                try:
                    import subprocess
                    subprocess.run(
                        ["nmcli", "dev", "wifi", "connect", ssid],
                        timeout=10, check=True
                    )
                    cfg["wifi_connected"] = True
                    cfg["wifi_ssid"]      = ssid
                    print(f"[wifi] Connected to {ssid}")
                except Exception:
                    # Simulate success
                    cfg["wifi_connected"] = True
                    cfg["wifi_ssid"]      = ssid
                    print(f"[wifi] Simulated connect to {ssid}")
            else:
                # A network label was tapped → select it
                nets = extra if extra else self.wifi_nets
                for i, n in enumerate(nets):
                    if n[:20] == hit:
                        self.wifi_sel[0] = i
                        break

        elif s == State.AD3:
            if hit == "<BACK":
                self.goto(State.SETTINGS)
            elif hit in ("CONNECT AD3", "DISCONNECT"):
                if cfg["ad3_connected"]:
                    ad3_disconnect()
                    cfg["ad3_connected"] = False
                    print("[ad3] Disconnected")
                else:
                    ok = ad3_connect()
                    cfg["ad3_connected"] = ok
                    print(f"[ad3] {'Connected' if ok else 'Failed'}")

        elif s == State.CONFIGURE:
            if hit == "<BACK":   self.goto(State.SETTINGS)
            elif hit == "off+":  cfg["offset"]       = round(cfg["offset"]       + 0.001, 4)
            elif hit == "off-":  cfg["offset"]       = round(cfg["offset"]       - 0.001, 4)
            elif hit == "gf+":   cfg["gauge_factor"] = round(cfg["gauge_factor"] + 0.1,   2)
            elif hit == "gf-":   cfg["gauge_factor"] = max(0.1, round(cfg["gauge_factor"] - 0.1, 2))

    # ── render current state ──────────────────────────────────
    def render(self):
        s = self.state
        t = self.t
        extra = None

        if s == State.HOME:
            buttons = render_home(t)

        elif s == State.MENU:
            buttons = render_menu(t)

        elif s == State.SETTINGS:
            buttons = render_settings(t)

        elif s == State.GRAPHS:
            buttons = render_graphs(t)

        elif s == State.YOUNGS_MODULUS:
            buttons = render_youngs(t)

        elif s == State.WIFI:
            if not self.wifi_nets:
                self.wifi_nets = scan_wifi_networks()
            result  = render_wifi(t, self.wifi_nets)
            # render_wifi returns (buttons, sel_ref, nets)
            buttons, self.wifi_sel, extra = result

        elif s == State.AD3:
            buttons = render_ad3(t)

        elif s == State.CONFIGURE:
            buttons = render_configure(t)

        else:
            buttons = []

        return buttons, extra

    # ── main loop ─────────────────────────────────────────────
    def run(self):
        print("=" * 52)
        print("  Design Lab UI  |  Ctrl+C to quit")
        print("=" * 52)

        # Start sensor thread
        threading.Thread(target=sensor_loop, daemon=True).start()

        buttons = []
        extra   = None

        try:
            while True:
                t0 = time.time()

                # ── input ────────────────────────────────────
                tap = poll_touch()
                if tap:
                    print(f"[main loop] Got tap at {tap}")
                    self.handle_touch(tap[0], tap[1], buttons, extra)
                else:
                    if self.t % 3.0 < 0.1:  # print every ~3 seconds
                        print(f"[main loop] No touch, display.touch_just={display.touch_just}")

                # ── render ───────────────────────────────────
                buttons, extra = self.render()

                # ── timing ───────────────────────────────────
                elapsed = time.time() - t0
                time.sleep(max(0.0, self.FRAME - elapsed))
                self.t += self.FRAME

        except KeyboardInterrupt:
            print("\n[main] Quit requested")
        finally:
            try:
                from ui_screens import clear, flush
                clear(0)
                flush()
            except Exception:
                pass
            if cfg["ad3_connected"]:
                ad3_disconnect()
            print("[main] Bye!")


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().run()
