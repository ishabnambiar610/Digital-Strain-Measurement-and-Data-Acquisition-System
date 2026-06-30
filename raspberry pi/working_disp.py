import numpy as np
import mmap
import time
import math
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
    try:
        ef = open("/dev/input/event4", "rb")
    except OSError as e:
        print(f"[touch] Cannot open event4: {e}")
        return

    # detect 64-bit (24 byte) vs 32-bit (16 byte) struct
    fmt24, fmt16 = "qqHHi", "llHHi"
    ev_size = 24 if struct.calcsize(fmt24) == 24 else 16
    fmt     = fmt24 if ev_size == 24 else fmt16
    print(f"[touch] Running — event size {ev_size} bytes")

    raw_x = raw_y = 0
    pressed = False

    while True:
        data = ef.read(ev_size)
        if len(data) < ev_size:
            break
        _, _, etype, code, value = struct.unpack(fmt, data)

        if   etype == EV_KEY and code == BTN_TOUCH:
            pressed = (value == 1)
        elif etype == EV_ABS and code == ABS_X:
            raw_x = value
        elif etype == EV_ABS and code == ABS_Y:
            raw_y = value
        elif etype == EV_SYN and pressed:
            sx, sy = map_touch(raw_x, raw_y)
            with touch_lock:
                last_touch = (sx, sy)
                touch_just = True

    ef.close()

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
def flush():        mm[:FBSIZE] = frame.tobytes()
def clear(c=0):     frame[:] = c

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
    'A':[0b01110,0b10001,0b10001,0b11111,0b10001,0b10001,0b10001],
    'B':[0b11110,0b10001,0b10001,0b11110,0b10001,0b10001,0b11110],
    'C':[0b01110,0b10001,0b10000,0b10000,0b10000,0b10001,0b01110],
    'D':[0b11110,0b10001,0b10001,0b10001,0b10001,0b10001,0b11110],
    'E':[0b11111,0b10000,0b10000,0b11110,0b10000,0b10000,0b11111],
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
    'R':[0b11110,0b10001,0b10001,0b11110,0b10100,0b10010,0b10001],
    'S':[0b01111,0b10000,0b10000,0b01110,0b00001,0b00001,0b11110],
    'T':[0b11111,0b00100,0b00100,0b00100,0b00100,0b00100,0b00100],
    'U':[0b10001,0b10001,0b10001,0b10001,0b10001,0b10001,0b01110],
    'V':[0b10001,0b10001,0b10001,0b10001,0b01010,0b01010,0b00100],
    'W':[0b10001,0b10001,0b10001,0b10101,0b10101,0b11011,0b10001],
    'X':[0b10001,0b01010,0b00100,0b00100,0b00100,0b01010,0b10001],
    'Y':[0b10001,0b10001,0b01010,0b00100,0b00100,0b00100,0b00100],
    'Z':[0b11111,0b00001,0b00010,0b00100,0b01000,0b10000,0b11111],
    '0':[0b01110,0b10001,0b10011,0b10101,0b11001,0b10001,0b01110],
    '1':[0b00100,0b01100,0b00100,0b00100,0b00100,0b00100,0b11111],
    '2':[0b01110,0b10001,0b00001,0b00110,0b01000,0b10000,0b11111],
    '3':[0b11111,0b00001,0b00010,0b00110,0b00001,0b10001,0b01110],
    'F':[0b11111,0b10000,0b10000,0b11110,0b10000,0b10000,0b10000],
    'Q':[0b01110,0b10001,0b10001,0b10001,0b10101,0b10010,0b01101],
}

def draw_char(ch, cx, cy, color, sc=1):
    for row, bits in enumerate(FONT.get(ch.upper(), FONT[' '])):
        for col in range(5):
            if bits & (1 << (4-col)):
                draw_rect(cx+col*sc, cy+row*sc, sc, sc, color)

def text_width(s, sc=1): return len(s)*(5*sc+sc)

def draw_text(s, x, y, c, sc=1):
    for ch in s:
        draw_char(ch, x, y, c, sc);  x += 5*sc+sc

# ── Buttons ───────────────────────────────────────────────────────────────────
BTN_Y = HEIGHT - 36
BUTTONS = [
    {"id":"pause", "label":"PAUSE", "x": 10, "y":BTN_Y, "w":75, "h":28},
    {"id":"spd+",  "label":"SPD+",  "x":203, "y":BTN_Y, "w":75, "h":28},
    {"id":"spd-",  "label":"SPD-",  "x":395, "y":BTN_Y, "w":75, "h":28},
]

def hit_test(sx, sy):
    for b in BUTTONS:
        if b["x"]<=sx<b["x"]+b["w"] and b["y"]<=sy<b["y"]+b["h"]:
            return b["id"]
    return None

def draw_buttons(paused, flash_btn):
    for b in BUTTONS:
        bx,by,bw,bh,bid = b["x"],b["y"],b["w"],b["h"],b["id"]
        if   bid=="pause": bg = rgb565(180,60,60) if paused else rgb565(30,120,30)
        elif bid=="spd+":  bg = rgb565(30,80,160)
        else:              bg = rgb565(100,50,150)
        if flash_btn==bid: bg = rgb565(255,255,255)
        draw_rect(bx,by,bw,bh,bg)
        bc = rgb565(200,200,200)
        draw_hline(bx,by,bw,bc);  draw_hline(bx,by+bh-1,bw,bc)
        draw_vline(bx,by,bh,bc);  draw_vline(bx+bw-1,by,bh,bc)
        label = "PLAY" if (bid=="pause" and paused) else b["label"]
        lw = text_width(label,1)
        tc = rgb565(0,0,0) if flash_btn==bid else rgb565(255,255,255)
        draw_text(label, bx+(bw-lw)//2, by+(bh-7)//2, tc, 1)

# ── Starfield ─────────────────────────────────────────────────────────────────
rng    = np.random.default_rng(42)
star_x = rng.integers(0,WIDTH, 120).astype(float)
star_y = rng.integers(0,HEIGHT,120).astype(float)
star_z = rng.uniform(0.5,3.0,  120)

def draw_stars():
    for i in range(120):
        star_x[i] = (star_x[i] - star_z[i]) % WIDTH
        b = int(min(255, 80 + star_z[i]*60))
        draw_pixel(int(star_x[i]), int(star_y[i]), rgb565(b,b,b))

def draw_bg(t):
    for y in range(HEIGHT):
        frame[y,:] = hsv_to_rgb565((t*30 + y*0.4) % 360, 0.85, 0.18)

def draw_border(c):
    draw_hline(0,0,WIDTH,c);  draw_hline(0,HEIGHT-1,WIDTH,c)
    draw_vline(0,0,HEIGHT,c); draw_vline(WIDTH-1,0,HEIGHT,c)
    draw_hline(3,3,WIDTH-6,c);  draw_hline(3,HEIGHT-4,WIDTH-6,c)
    draw_vline(3,3,HEIGHT-6,c); draw_vline(WIDTH-4,3,HEIGHT-6,c)

def draw_diamond(cx,cy,r,c):
    for i in range(-r,r+1):
        j=r-abs(i); draw_pixel(cx+i,cy-j,c); draw_pixel(cx+i,cy+j,c)

SPARK_POS = [(20,20),(WIDTH-20,20),(20,HEIGHT-20),(WIDTH-20,HEIGHT-20)]
def draw_sparkles(t):
    for idx,(sx,sy) in enumerate(SPARK_POS):
        r = int(3+2*math.sin(t*5+idx*1.5))
        c = hsv_to_rgb565((t*120+idx*90)%360)
        draw_diamond(sx,sy,r,c)
        draw_hline(sx-r-3,sy,r*2+7,c); draw_vline(sx,sy-r-3,r*2+7,c)

# Ticker sits just above button row
TICKER      = "  HELLO GUYS !   DESIGN LAB PROJECT   WELCOME TO THE FUTURE   "
TICKER_SC   = 2
TICKER_Y    = BTN_Y - 7*TICKER_SC - 8
ticker_x    = float(WIDTH)

def draw_ticker(c, speed):
    global ticker_x
    ticker_x -= speed
    tw = text_width(TICKER, TICKER_SC)
    if ticker_x < -tw: ticker_x = WIDTH
    draw_text(TICKER, int(ticker_x),    TICKER_Y, c, TICKER_SC)
    draw_text(TICKER, int(ticker_x)+tw, TICKER_Y, c, TICKER_SC)

def draw_divider(t):
    y = TICKER_Y - 4
    for x in range(WIDTH):
        h = (t*60 + x*0.75) % 360
        frame[y,  x] = hsv_to_rgb565(h)
        frame[y+1,x] = hsv_to_rgb565((h+10)%360, 0.6, 0.8)

def draw_headlines(t):
    pulse = 0.5+0.5*math.sin(t*3)
    s1,s2 = 3,2
    w1 = text_width("HELLO GUYS",s1);  x1=(WIDTH-w1)//2;  y1=int(30+pulse*4)
    for i,ch in enumerate("HELLO GUYS"):
        draw_char(ch, x1+i*(5*s1+s1), y1, hsv_to_rgb565((t*80+i*36)%360), s1)

    w2 = text_width("DESIGN LAB",s2); x2=(WIDTH-w2)//2; y2=y1+7*s1+10
    for i,ch in enumerate("DESIGN LAB"):
        draw_char(ch, x2+i*(5*s2+s2), y2, hsv_to_rgb565((t*60+i*25+180)%360,0.6,1.0), s2)

    w3 = text_width("PROJECT",s2); x3=(WIDTH-w3)//2; y3=y2+7*s2+8
    for i,ch in enumerate("PROJECT"):
        v = 0.7+0.3*math.sin(t*4+i*0.8)
        draw_char(ch, x3+i*(5*s2+s2), y3, hsv_to_rgb565(50,0.9,v), s2)

# ── Main ──────────────────────────────────────────────────────────────────────
print("Design Lab  |  Buttons: PAUSE · SPD+ · SPD-  |  Ctrl+C to quit")
t=0.0; dt=1/30; paused=False; spd=1.8
flash_btn=None; flash_until=0.0

try:
    while True:
        t0 = time.time()

        # process touch
        with touch_lock:
            new_tap=touch_just; tap_pos=last_touch; touch_just=False
        if new_tap and tap_pos:
            hit = hit_test(*tap_pos)
            if   hit=="pause": paused=not paused; print("PAUSE" if paused else "PLAY")
            elif hit=="spd+":  spd=min(spd+0.5,8.0); print(f"Speed {spd:.1f}")
            elif hit=="spd-":  spd=max(spd-0.5,0.5); print(f"Speed {spd:.1f}")
            if hit: flash_btn=hit; flash_until=time.time()+0.12
        if flash_btn and time.time()>flash_until: flash_btn=None

        # render
        draw_bg(t)
        draw_stars()
        draw_border(hsv_to_rgb565((t*60)%360,0.9,0.9))
        draw_sparkles(t)
        if not paused:
            draw_headlines(t)
            draw_divider(t)
            draw_ticker(hsv_to_rgb565((t*90+200)%360), spd)
        else:
            msg="PAUSED"; mw=text_width(msg,3)
            draw_text(msg,(WIDTH-mw)//2,HEIGHT//2-12,rgb565(255,80,80),3)
        draw_buttons(paused, flash_btn)
        flush()

        time.sleep(max(0, dt-(time.time()-t0)))
        if not paused: t+=dt

except KeyboardInterrupt:
    clear(0); flush(); print("Bye!")
finally:
    mm.close(); fb.close()