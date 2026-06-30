import numpy as np
import mmap
import time
import struct
import threading

# ── Screen config ─────────────────────────────────────────────────────────────
WIDTH  = 480
HEIGHT = 320
BPP    = 2
FBSIZE = WIDTH * HEIGHT * BPP

fb = open("/dev/fb0", "r+b")
mm = mmap.mmap(fb.fileno(), FBSIZE)
frame = np.zeros((HEIGHT, WIDTH), dtype=np.uint16)

# ── Touch calibration ─────────────────────────────────────────────────────────
# Top-right  touch (290,  273) → screen (480,   0)
# Bot-left   touch (3786, 3890) → screen (  0, 320)
TOUCH_X_MIN, TOUCH_X_MAX = 290,  3786
TOUCH_Y_MIN, TOUCH_Y_MAX = 273,  3890

def map_touch(raw_x, raw_y):
    sx = int(WIDTH  * (1.0 - (raw_x - TOUCH_X_MIN) / (TOUCH_X_MAX - TOUCH_X_MIN)))
    sy = int(HEIGHT *       ((raw_y - TOUCH_Y_MIN)  / (TOUCH_Y_MAX - TOUCH_Y_MIN)))
    return max(0, min(WIDTH-1, sx)), max(0, min(HEIGHT-1, sy))

# ── Touch state ───────────────────────────────────────────────────────────────
touch_lock  = threading.Lock()
last_touch  = None
touch_just  = False

# ── Input event reader (no evdev needed) ─────────────────────────────────────
EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
ABS_X, ABS_Y            = 0, 1
BTN_TOUCH               = 330

def touch_reader():
    global last_touch, touch_just
    import os
    
    # Try to find the correct touch device
    device_path = None
    for i in range(10):
        path = f"/dev/input/event{i}"
        if os.path.exists(path):
            try:
                # Try to open it
                test_f = open(path, "rb")
                test_f.close()
                device_path = path
                print(f"[touch] Found candidate device: {path}")
                break
            except:
                pass
    
    if not device_path:
        print(f"[touch] Cannot find any input device!")
        # Try /dev/input/touchscreen as fallback
        if os.path.exists("/dev/input/touchscreen"):
            device_path = "/dev/input/touchscreen"
            print(f"[touch] Trying fallback: {device_path}")
        else:
            print(f"[touch] No touchscreen device found. Listing /dev/input/:")
            try:
                import subprocess
                subprocess.run(["ls", "-la", "/dev/input/"], timeout=2)
            except:
                pass
            return
    
    try:
        ef = open(device_path, "rb")
        print(f"[touch] Opened {device_path}")
    except OSError as e:
        print(f"[touch] Cannot open {device_path}: {e}")
        return

    # detect 64-bit (24 byte) vs 32-bit (16 byte) struct
    fmt24, fmt16 = "qqHHi", "llHHi"
    ev_size = 24 if struct.calcsize(fmt24) == 24 else 16
    fmt     = fmt24 if ev_size == 24 else fmt16
    print(f"[touch] Running — event size {ev_size} bytes")

    raw_x = raw_y = 0
    pressed = False
    event_count = [0]

    while True:
        try:
            data = ef.read(ev_size)
            if len(data) < ev_size:
                print(f"[touch] EOF or incomplete read ({len(data)} bytes)")
                break
            event_count[0] += 1
            if event_count[0] % 100 == 0:
                print(f"[touch] Processed {event_count[0]} events...")
            
            _, _, etype, code, value = struct.unpack(fmt, data)

            if   etype == EV_KEY and code == BTN_TOUCH:
                pressed = (value == 1)
                print(f"[touch] BTN_TOUCH: {pressed}")
            elif etype == EV_ABS and code == ABS_X:
                raw_x = value
            elif etype == EV_ABS and code == ABS_Y:
                raw_y = value
            elif etype == EV_SYN and pressed:
                sx, sy = map_touch(raw_x, raw_y)
                print(f"[touch_reader] TOUCH DETECTED: raw({raw_x},{raw_y}) → screen({sx},{sy})")
                with touch_lock:
                    last_touch = (sx, sy)
                    touch_just = True
                    print(f"[touch_reader] Set touch_just=True, last_touch={last_touch}")
        except Exception as e:
            print(f"[touch] Read error: {e}")
            break

    ef.close()
    print(f"[touch] Reader exited after {event_count[0]} events")

threading.Thread(target=touch_reader, daemon=True).start()

# ── Color helpers ─────────────────────────────────────────────────────────────
def rgb565(r, g, b):
    r, g, b = int(r) & 0xFF, int(g) & 0xFF, int(b) & 0xFF
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def hsv_to_rgb565(h, s=1.0, v=1.0):
    h = h % 360
    hi = int(h / 60) % 6
    f  = h / 60 - int(h / 60)
    p  = v * (1 - s);  q = v * (1 - f*s);  tv = v * (1 - (1-f)*s)
    r, g, b = [(v,tv,p),(q,v,p),(p,v,tv),(p,q,v),(tv,p,v),(v,p,q)][hi]
    return rgb565(r*255, g*255, b*255)

# ── Drawing ───────────────────────────────────────────────────────────────────
def flush():        
    mm[:FBSIZE] = frame.tobytes()

def clear(c=0):     
    frame[:] = c

def draw_rect(x, y, w, h, c):
    x1,y1 = max(0,x),max(0,y);  x2,y2 = min(WIDTH,x+w),min(HEIGHT,y+h)
    if x2>x1 and y2>y1: frame[y1:y2,x1:x2] = c

def draw_hline(x,y,w,c):
    if 0<=y<HEIGHT: frame[y, max(0,x):min(WIDTH,x+w)] = c

def draw_vline(x,y,h,c):
    if 0<=x<WIDTH: frame[max(0,y):min(HEIGHT,y+h), x] = c

def draw_pixel(x,y,c):
    if 0<=x<WIDTH and 0<=y<HEIGHT: frame[y,x] = c

# ── 5×7 font ─────────────────────────────────────────────────────────────────
FONT = {
    ' ':[0]*7,
    '!':[0b00100,0b00100,0b00100,0b00100,0,0,0b00100],
    '+':[0,0b00100,0b00100,0b11111,0b00100,0b00100,0],
    '-':[0,0,0,0b11111,0,0,0],
    '.':[0,0,0,0,0,0,0b00011],
    ':':[0,0b00100,0,0b00100,0,0,0],
    '0':[0b01110,0b10001,0b10011,0b10101,0b11001,0b10001,0b01110],
    '1':[0b00100,0b01100,0b00100,0b00100,0b00100,0b00100,0b11111],
    '2':[0b01110,0b10001,0b00001,0b00110,0b01000,0b10000,0b11111],
    '3':[0b11111,0b00001,0b00010,0b00110,0b00001,0b10001,0b01110],
    '4':[0b00010,0b00110,0b01010,0b10010,0b11111,0b00010,0b00010],
    '5':[0b11111,0b10000,0b11110,0b00001,0b00001,0b10001,0b01110],
    '6':[0b01110,0b10000,0b10000,0b11110,0b10001,0b10001,0b01110],
    '7':[0b11111,0b00001,0b00010,0b00100,0b01000,0b10000,0b10000],
    '8':[0b01110,0b10001,0b10001,0b01110,0b10001,0b10001,0b01110],
    '9':[0b01110,0b10001,0b10001,0b01111,0b00001,0b00001,0b01110],
    'A':[0b01110,0b10001,0b10001,0b11111,0b10001,0b10001,0b10001],
    'B':[0b11110,0b10001,0b10001,0b11110,0b10001,0b10001,0b11110],
    'C':[0b01110,0b10001,0b10000,0b10000,0b10000,0b10001,0b01110],
    'D':[0b11110,0b10001,0b10001,0b10001,0b10001,0b10001,0b11110],
    'E':[0b11111,0b10000,0b10000,0b11110,0b10000,0b10000,0b11111],
    'F':[0b11111,0b10000,0b10000,0b11110,0b10000,0b10000,0b10000],
    'G':[0b01110,0b10001,0b10000,0b10111,0b10001,0b10001,0b01111],
    'H':[0b10001,0b10001,0b10001,0b11111,0b10001,0b10001,0b10001],
    'I':[0b11111,0b00100,0b00100,0b00100,0b00100,0b00100,0b11111],
    'J':[0b00111,0b00001,0b00001,0b00001,0b10001,0b10001,0b01110],
    'K':[0b10001,0b10010,0b10100,0b11000,0b10100,0b10010,0b10001],
    'L':[0b10000,0b10000,0b10000,0b10000,0b10000,0b10000,0b11111],
    'M':[0b10001,0b11011,0b10101,0b10001,0b10001,0b10001,0b10001],
    'N':[0b10001,0b11001,0b10101,0b10011,0b10001,0b10001,0b10001],
    'O':[0b01110,0b10001,0b10001,0b10001,0b10001,0b10001,0b01110],
    'P':[0b11110,0b10001,0b10001,0b11110,0b10000,0b10000,0b10000],
    'Q':[0b01110,0b10001,0b10001,0b10001,0b10101,0b10010,0b01101],
    'R':[0b11110,0b10001,0b10001,0b11110,0b10100,0b10010,0b10001],
    'S':[0b01111,0b10000,0b10000,0b01110,0b00001,0b00001,0b11110],
    'T':[0b11111,0b00100,0b00100,0b00100,0b00100,0b00100,0b00100],
    'U':[0b10001,0b10001,0b10001,0b10001,0b10001,0b10001,0b01110],
    'V':[0b10001,0b10001,0b10001,0b10001,0b01010,0b01010,0b00100],
    'W':[0b10001,0b10001,0b10001,0b10101,0b10101,0b11011,0b10001],
    'X':[0b10001,0b01010,0b00100,0b00100,0b00100,0b01010,0b10001],
    'Y':[0b10001,0b10001,0b01010,0b00100,0b00100,0b00100,0b00100],
    'Z':[0b11111,0b00001,0b00010,0b00100,0b01000,0b10000,0b11111],
}

def draw_char(ch, cx, cy, color, sc=1):
    for row, bits in enumerate(FONT.get(ch.upper(), FONT[' '])):
        for col in range(5):
            if bits & (1 << (4-col)):
                draw_rect(cx+col*sc, cy+row*sc, sc, sc, color)

def text_width(s, sc=1): 
    return len(s)*(5*sc+sc)

def draw_text(s, x, y, c, sc=1):
    for ch in s:
        draw_char(ch, x, y, c, sc)
        x += 5*sc+sc

print("[display] Initialized 3.5\" RPi display via /dev/fb0")
