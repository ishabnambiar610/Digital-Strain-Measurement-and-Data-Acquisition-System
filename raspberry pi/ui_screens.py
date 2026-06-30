# ─────────────────────────────────────────────────────────────
#  ui_screens.py  –  Screen renderers for every UI state
# ─────────────────────────────────────────────────────────────
#
#  ╔══════════════════════════════════════════════════════════╗
#  ║  INTEGRATION POINT — display primitives                  ║
#  ║  Import (or paste) YOUR display code below.              ║
#  ║  The functions that must exist:                          ║
#  ║    rgb565(r,g,b)                                         ║
#  ║    hsv_to_rgb565(h,s,v)                                  ║
#  ║    draw_rect(x,y,w,h,c)                                  ║
#  ║    draw_hline(x,y,w,c)                                   ║
#  ║    draw_vline(x,y,h,c)                                   ║
#  ║    draw_pixel(x,y,c)                                     ║
#  ║    draw_text(s,x,y,c,sc=1)                               ║
#  ║    text_width(s,sc=1)                                    ║
#  ║    draw_char(ch,cx,cy,color,sc=1)                        ║
#  ║    clear(c=0)                                            ║
#  ║    flush()                                               ║
#  ║    WIDTH, HEIGHT  (int constants)                        ║
#  ╚══════════════════════════════════════════════════════════╝
#
# ── BEGIN: paste your display module here ────────────────────
# from display import *           # <-- or inline the code
# ─────────────────────────────────────────────────────────────
#
# For standalone testing a minimal stub is provided at the bottom.
# Remove the stub once your real display module is inserted.

import math
import time
import subprocess
from config import cfg, State
from display import *

# ─────────────────────────────────────────────────────────────
#  Shared palette helpers (thin wrappers so screens are readable)
# ─────────────────────────────────────────────────────────────
def C_BG():       return rgb565(8, 12, 24)
def C_PANEL():    return rgb565(20, 28, 50)
def C_ACCENT():   return rgb565(0, 200, 180)
def C_ACCENT2():  return rgb565(255, 140, 0)
def C_WHITE():    return rgb565(230, 235, 245)
def C_GREY():     return rgb565(100, 110, 130)
def C_RED():      return rgb565(220, 50, 60)
def C_GREEN():    return rgb565(50, 200, 80)
def C_BLUE():     return rgb565(50, 100, 240)
def C_YELLOW():   return rgb565(240, 200, 0)
def C_PURPLE():   return rgb565(160, 60, 220)

# ─────────────────────────────────────────────────────────────
#  Generic UI widgets
# ─────────────────────────────────────────────────────────────

def draw_status_bar(t):
    """Top-right: WiFi + AD3 indicators (used on every screen)."""
    # WiFi
    wc = C_GREEN() if cfg["wifi_connected"] else C_RED()
    draw_rect(WIDTH - 80, 4, 34, 12, C_PANEL())
    draw_text("WF", WIDTH - 78, 6, wc, 1)
    draw_pixel(WIDTH - 62, 10, wc)

    # AD3
    ac = C_GREEN() if cfg["ad3_connected"] else C_RED()
    draw_rect(WIDTH - 44, 4, 38, 12, C_PANEL())
    draw_text("AD3", WIDTH - 42, 6, ac, 1)
    draw_pixel(WIDTH - 8, 10, ac)


def draw_panel(x, y, w, h, title="", color=None):
    """Filled rounded-ish panel with optional title."""
    c = color if color else C_PANEL()
    draw_rect(x, y, w, h, c)
    # border
    bc = C_ACCENT()
    draw_hline(x, y, w, bc)
    draw_hline(x, y + h - 1, w, bc)
    draw_vline(x, y, h, bc)
    draw_vline(x + w - 1, y, h, bc)
    if title:
        tw = text_width(title, 1)
        draw_text(title, x + (w - tw) // 2, y + 3, C_ACCENT(), 1)


def make_button(label, x, y, w, h, color=None, text_color=None, scale=1):
    """Draw a button; returns its hit-box dict."""
    bg = color if color else C_BLUE()
    tc = text_color if text_color else C_WHITE()
    draw_rect(x, y, w, h, bg)
    draw_hline(x, y, w, C_WHITE())
    draw_hline(x, y + h - 1, w, C_GREY())
    draw_vline(x, y, h, C_WHITE())
    draw_vline(x + w - 1, y, h, C_GREY())
    lw = text_width(label, scale)
    draw_text(label, x + (w - lw) // 2, y + (h - 7 * scale) // 2, tc, scale)
    return {"label": label, "x": x, "y": y, "w": w, "h": h}


def hit_test(buttons, sx, sy):
    """Return the label of the button that contains (sx,sy), or None."""
    for b in buttons:
        if b["x"] <= sx < b["x"] + b["w"] and b["y"] <= sy < b["y"] + b["h"]:
            return b["label"]
    return None


def draw_back_button():
    """Standard back arrow in top-left; returns its hit-box."""
    return make_button("<BACK", 4, 4, 52, 18, C_PANEL(), C_ACCENT(), 1)


# Scrolling ticker state (per-screen instance via a mutable dict)
def make_ticker(text, sc=1):
    return {"text": text, "sc": sc, "x": float(WIDTH)}


def draw_ticker_widget(tk, y, color, speed, paused=False):
    sc   = tk["sc"]
    text = tk["text"]
    if not paused:
        tk["x"] -= speed
    tw = text_width(text, sc)
    if tk["x"] < -tw:
        tk["x"] = float(WIDTH)
    xi = int(tk["x"])
    draw_text(text, xi,      y, color, sc)
    draw_text(text, xi + tw, y, color, sc)


# ─────────────────────────────────────────────────────────────
#  PAGE 1 – HOME
# ─────────────────────────────────────────────────────────────
_home_ticker = make_ticker(
    "  CREDITS: PIYUSH  •  KANIKA  •  DIVYAMSHI  •  ISHA   ", sc=1
)

def render_home(t, paused=False):
    clear(C_BG())

    # Subtle animated gradient background rows
    for y in range(HEIGHT):
        c = hsv_to_rgb565((t * 20 + y * 0.3) % 360, 0.7, 0.12)
        draw_hline(0, y, WIDTH, c)

    draw_status_bar(t)

    # Centre panel
    draw_panel(WIDTH // 2 - 120, 40, 240, 100, "")

    # "Design Lab 1"
    title = "DESIGN LAB 1"
    tw = text_width(title, 2)
    for i, ch in enumerate(title):
        hue = (t * 60 + i * 28) % 360
        draw_char(ch, WIDTH // 2 - tw // 2 + i * (5 * 2 + 2), 50,
                  hsv_to_rgb565(hue), 2)

    # Subtitle
    sub = "PROJECT UNDER PRABHATH SIR"
    sw = text_width(sub, 1)
    draw_text(sub, WIDTH // 2 - sw // 2, 82, C_GREY(), 1)

    # Decorative divider
    for x in range(WIDTH // 2 - 80, WIDTH // 2 + 80):
        draw_pixel(x, 98, hsv_to_rgb565((t * 90 + x) % 360))

    # GET STARTED button
    btn = make_button("GET STARTED", WIDTH // 2 - 60, 118, 120, 26,
                      C_ACCENT(), rgb565(0, 0, 0), 1)

    # Bottom ticker
    TICKER_Y = HEIGHT - 16
    draw_hline(0, TICKER_Y - 3, WIDTH, C_ACCENT())
    draw_ticker_widget(_home_ticker, TICKER_Y, C_ACCENT2(), 1.5, paused)

    flush()
    return [btn]


# ─────────────────────────────────────────────────────────────
#  PAGE 2 – MENU
# ─────────────────────────────────────────────────────────────
def render_menu(t):
    clear(C_BG())
    for y in range(HEIGHT):
        draw_hline(0, y, WIDTH, hsv_to_rgb565((t * 15 + y * 0.25) % 360, 0.6, 0.10))

    draw_status_bar(t)
    back = draw_back_button()

    # Title
    title = "MAIN MENU"
    tw = text_width(title, 2)
    draw_text(title, WIDTH // 2 - tw // 2, 6, C_ACCENT(), 2)
    draw_hline(WIDTH // 2 - 70, 24, 140, C_ACCENT())

    # Three menu buttons
    bw, bh = 180, 34
    bx = WIDTH // 2 - bw // 2
    btns = [
        make_button("SETTINGS",     bx, 40,  bw, bh, C_PANEL(), C_WHITE()),
        make_button("LIVE GRAPHS",  bx, 82,  bw, bh, C_PANEL(), C_WHITE()),
        make_button("YOUNGS MODULUS", bx, 124, bw, bh, C_PANEL(), C_WHITE()),
    ]
    # Accent left stripe on each
    for b, hue in zip(btns, [200, 120, 40]):
        draw_vline(b["x"], b["y"], b["h"], hsv_to_rgb565(hue))
        draw_vline(b["x"] + 1, b["y"], b["h"], hsv_to_rgb565(hue, 0.5, 0.5))

    flush()
    return [back] + btns


# ─────────────────────────────────────────────────────────────
#  PAGE 3 – SETTINGS
# ─────────────────────────────────────────────────────────────
def render_settings(t):
    clear(C_BG())
    for y in range(HEIGHT):
        draw_hline(0, y, WIDTH, hsv_to_rgb565((t * 15 + y * 0.25) % 360, 0.6, 0.10))

    draw_status_bar(t)
    back = draw_back_button()

    title = "SETTINGS"
    tw = text_width(title, 2)
    draw_text(title, WIDTH // 2 - tw // 2, 6, C_ACCENT(), 2)
    draw_hline(WIDTH // 2 - 55, 24, 110, C_ACCENT())

    bw, bh = 170, 30
    bx = WIDTH // 2 - bw // 2
    btns = [
        make_button("CONNECT WIFI", bx, 40,  bw, bh, C_PANEL()),
        make_button("CONNECT AD3",  bx, 78,  bw, bh, C_PANEL()),
        make_button("CONFIGURE",    bx, 116, bw, bh, C_PANEL()),
    ]
    flush()
    return [back] + btns


# ─────────────────────────────────────────────────────────────
#  PAGE 4 – LIVE GRAPHS
# ─────────────────────────────────────────────────────────────
def render_graphs(t):
    clear(C_BG())

    draw_status_bar(t)
    back = draw_back_button()

    title = "LIVE GRAPHS"
    tw = text_width(title, 1)
    draw_text(title, WIDTH // 2 - tw // 2, 6, C_ACCENT(), 1)

    # ── Strain vs Time (top half) ──────────────────────────
    GRAPH1_X, GRAPH1_Y = 10, 22
    GRAPH1_W, GRAPH1_H = WIDTH - 20, (HEIGHT // 2) - 28

    draw_panel(GRAPH1_X, GRAPH1_Y, GRAPH1_W, GRAPH1_H, "STRAIN VS TIME")

    sbuf = cfg["strain_buf"]
    head = cfg["buf_head"]
    # Re-order so oldest→newest = left→right
    ordered = [sbuf[(head + i) % 100] for i in range(100)]

    if max(ordered) != min(ordered):
        s_min, s_max = min(ordered), max(ordered)
    else:
        s_min, s_max = -1e-6, 1e-6

    prev_x = prev_y = None
    for i, val in enumerate(ordered):
        gx = GRAPH1_X + 4 + int(i * (GRAPH1_W - 8) / 99)
        norm = (val - s_min) / (s_max - s_min)
        gy = GRAPH1_Y + GRAPH1_H - 4 - int(norm * (GRAPH1_H - 12))
        hue = (200 + i * 1.2) % 360
        draw_pixel(gx, gy, hsv_to_rgb565(hue))
        if prev_x is not None:
            # simple 1-step line connect
            steps = max(abs(gx - prev_x), abs(gy - prev_y), 1)
            for s in range(steps + 1):
                lx = prev_x + int(s * (gx - prev_x) / steps)
                ly = prev_y + int(s * (gy - prev_y) / steps)
                draw_pixel(lx, ly, hsv_to_rgb565(hue))
        prev_x, prev_y = gx, gy

    # ── Stress vs Strain (bottom half) ────────────────────
    GRAPH2_X, GRAPH2_Y = 10, HEIGHT // 2
    GRAPH2_W, GRAPH2_H = WIDTH - 20, (HEIGHT // 2) - 14

    draw_panel(GRAPH2_X, GRAPH2_Y, GRAPH2_W, GRAPH2_H, "STRESS VS STRAIN")

    xbuf = cfg["strain_buf"]
    ybuf = cfg["stress_buf"]
    xs = [xbuf[(head + i) % 100] for i in range(100)]
    ys = [ybuf[(head + i) % 100] for i in range(100)]

    x_min, x_max = (min(xs), max(xs)) if max(xs) != min(xs) else (-1e-6, 1e-6)
    y_min, y_max = (min(ys), max(ys)) if max(ys) != min(ys) else (-1e9, 1e9)

    prev_x = prev_y = None
    for i in range(100):
        nx = (xs[i] - x_min) / (x_max - x_min)
        ny = (ys[i] - y_min) / (y_max - y_min)
        gx = GRAPH2_X + 4 + int(nx * (GRAPH2_W - 8))
        gy = GRAPH2_Y + GRAPH2_H - 4 - int(ny * (GRAPH2_H - 12))
        c  = hsv_to_rgb565((40 + i * 1.2) % 360)
        draw_pixel(gx, gy, c)
        if prev_x is not None:
            steps = max(abs(gx - prev_x), abs(gy - prev_y), 1)
            for s in range(steps + 1):
                lx = prev_x + int(s * (gx - prev_x) / steps)
                ly = prev_y + int(s * (gy - prev_y) / steps)
                draw_pixel(lx, ly, c)
        prev_x, prev_y = gx, gy

    flush()
    return [back]


# ─────────────────────────────────────────────────────────────
#  PAGE 5 – YOUNG'S MODULUS
# ─────────────────────────────────────────────────────────────
def render_youngs(t):
    clear(C_BG())
    for y in range(HEIGHT):
        draw_hline(0, y, WIDTH, hsv_to_rgb565((t * 10 + y * 0.2) % 360, 0.5, 0.08))

    draw_status_bar(t)
    back = draw_back_button()

    title = "YOUNGS MODULUS"
    tw = text_width(title, 1)
    draw_text(title, WIDTH // 2 - tw // 2, 6, C_ACCENT(), 1)

    voltage = cfg["voltage"]
    strain  = cfg["strain"]
    stress  = cfg["stress"]
    youngs  = cfg["youngs"]

    rows = [
        ("VOLTAGE",        f"{voltage:+.4f} V",   C_BLUE(),   C_WHITE()),
        ("STRAIN",         f"{strain:.6f}",        C_GREEN(),  C_WHITE()),
        ("STRESS",         f"{stress:.3e} Pa",     C_YELLOW(), C_WHITE()),
        ("YOUNGS MODULUS", f"{youngs:.3e} Pa",     C_ACCENT(), C_ACCENT()),
    ]

    py = 28
    for label, value, label_c, val_c in rows:
        is_youngs = label == "YOUNGS MODULUS"
        panel_c   = rgb565(30, 20, 50) if is_youngs else C_PANEL()
        draw_panel(8, py, WIDTH - 16, 32, "", panel_c)
        # Left label
        draw_text(label, 14, py + 5, label_c, 1)
        # Right value
        vw = text_width(value, 1 if not is_youngs else 1)
        sc = 2 if is_youngs else 1
        vw = text_width(value, sc)
        draw_text(value, WIDTH - 12 - vw, py + (32 - 7 * sc) // 2, val_c, sc)
        py += 38

    # Animated pulse ring around Young's panel
    if len(rows) > 0:
        ry = 28 + 3 * 38
        r  = int(4 + 2 * math.sin(t * 5))
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if abs(abs(dx) + abs(dy) - r) < 2:
                    draw_pixel(WIDTH // 2 + dx, ry + 16 + dy,
                               hsv_to_rgb565((t * 120) % 360))

    flush()
    return [back]


# ─────────────────────────────────────────────────────────────
#  PAGE 6 – WIFI
# ─────────────────────────────────────────────────────────────
# Simulated network list (replace with nmcli scan if available)
_SIMULATED_NETWORKS = ["DesignLab_5G", "Prabhath_Office", "RPi_Hotspot", "Lab_IoT"]
_wifi_selected = [0]   # mutable for closure

def scan_wifi_networks():
    """Try nmcli; fall back to simulated list."""
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "SSID", "dev", "wifi", "list"],
            timeout=4, stderr=subprocess.DEVNULL
        ).decode()
        nets = [l.strip() for l in out.splitlines() if l.strip()]
        return nets[:8] if nets else _SIMULATED_NETWORKS
    except Exception:
        return _SIMULATED_NETWORKS


def render_wifi(t, networks=None):
    if networks is None:
        networks = _SIMULATED_NETWORKS

    clear(C_BG())
    draw_status_bar(t)
    back = draw_back_button()

    title = "WIFI SETUP"
    tw = text_width(title, 1)
    draw_text(title, WIDTH // 2 - tw // 2, 6, C_ACCENT(), 1)

    btns = []
    py = 22
    for i, ssid in enumerate(networks[:6]):
        is_sel = (i == _wifi_selected[0])
        bg = rgb565(20, 60, 40) if is_sel else C_PANEL()
        b  = make_button(ssid[:20], 10, py, WIDTH - 70, 22, bg,
                         C_GREEN() if is_sel else C_WHITE(), 1)
        btns.append(b)
        if is_sel:
            draw_text(">>", WIDTH - 56, py + 7, C_GREEN(), 1)
        py += 26

    # Connect button
    conn_btn = make_button("CONNECT", WIDTH - 62, HEIGHT - 26, 56, 20,
                           C_GREEN(), rgb565(0, 0, 0), 1)
    btns.append(conn_btn)

    # Status
    if cfg["wifi_connected"]:
        msg = "CONNECTED: " + cfg["wifi_ssid"]
        draw_text(msg, 8, HEIGHT - 12, C_GREEN(), 1)

    flush()
    return [back] + btns, _wifi_selected, networks


# ─────────────────────────────────────────────────────────────
#  PAGE 7 – AD3
# ─────────────────────────────────────────────────────────────
def render_ad3(t):
    clear(C_BG())
    draw_status_bar(t)
    back = draw_back_button()

    title = "AD3 / DIGILENT"
    tw = text_width(title, 1)
    draw_text(title, WIDTH // 2 - tw // 2, 6, C_ACCENT(), 1)

    # Status circle animation
    cx, cy, r = WIDTH // 2, 80, 24
    ring_c = C_GREEN() if cfg["ad3_connected"] else C_RED()
    pulse  = int(r + 4 * math.sin(t * 4))
    for angle_deg in range(0, 360, 4):
        rad = math.radians(angle_deg)
        px  = cx + int(pulse * math.cos(rad))
        py  = cy + int(pulse * math.sin(rad))
        draw_pixel(px, py, ring_c)

    # Label
    status_text = "CONNECTED" if cfg["ad3_connected"] else "NOT CONNECTED"
    sw = text_width(status_text, 1)
    draw_text(status_text, WIDTH // 2 - sw // 2, cy + 34, ring_c, 1)

    if cfg["ad3_connected"]:
        v_str = f"CH1: {cfg['voltage']:+.4f} V"
        vw = text_width(v_str, 1)
        draw_text(v_str, WIDTH // 2 - vw // 2, cy + 48, C_WHITE(), 1)

    # Action button
    btn_label = "DISCONNECT" if cfg["ad3_connected"] else "CONNECT AD3"
    btn_c     = C_RED() if cfg["ad3_connected"] else C_GREEN()
    conn_btn  = make_button(btn_label, WIDTH // 2 - 60, HEIGHT - 36,
                            120, 26, btn_c, rgb565(0, 0, 0), 1)

    flush()
    return [back, conn_btn]


# ─────────────────────────────────────────────────────────────
#  PAGE 8 – CONFIGURE
# ─────────────────────────────────────────────────────────────
def render_configure(t):
    clear(C_BG())
    draw_status_bar(t)
    back = draw_back_button()

    title = "CONFIGURE"
    tw = text_width(title, 1)
    draw_text(title, WIDTH // 2 - tw // 2, 6, C_ACCENT(), 1)

    btns = []

    def param_row(label, value, y, inc_id, dec_id):
        draw_panel(6, y, WIDTH - 12, 38, "")
        draw_text(label, 12, y + 4, C_GREY(), 1)
        val_str = f"{value:.4f}"
        vw = text_width(val_str, 2)
        draw_text(val_str, WIDTH // 2 - vw // 2, y + 14, C_WHITE(), 2)
        b_plus  = make_button("+", WIDTH - 52, y + 6, 20, 22, C_GREEN(), C_WHITE(), 1)
        b_minus = make_button("-", WIDTH - 26, y + 6, 20, 22, C_RED(), C_WHITE(), 1)
        b_plus["id"]  = inc_id
        b_minus["id"] = dec_id
        btns.extend([b_plus, b_minus])

    param_row("OFFSET (V)",     cfg["offset"],       30, "off+", "off-")
    param_row("GAUGE FACTOR",   cfg["gauge_factor"], 80, "gf+",  "gf-")

    # Cross-section (read-only display)
    draw_panel(6, 130, WIDTH - 12, 24, "")
    draw_text("CROSS SECTION (m2):", 12, 136, C_GREY(), 1)
    cs_str = f"{cfg['cross_section']:.2e}"
    draw_text(cs_str, WIDTH - 12 - text_width(cs_str, 1), 136, C_WHITE(), 1)

    flush()
    return [back] + btns
