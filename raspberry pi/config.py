# ─────────────────────────────────────────────────────────────
#  config.py  –  Global configuration & shared application state
# ─────────────────────────────────────────────────────────────

# ── Navigation states ─────────────────────────────────────────
class State:
    HOME          = "HOME"
    MENU          = "MENU"
    SETTINGS      = "SETTINGS"
    GRAPHS        = "GRAPHS"
    YOUNGS_MODULUS= "YOUNGS_MODULUS"
    WIFI          = "WIFI"
    AD3           = "AD3"
    CONFIGURE     = "CONFIGURE"

# ── Sensor / calculation config ───────────────────────────────
cfg = {
    # Wheatstone bridge / strain-gauge parameters
    "offset"      : 0.0,   # voltage offset (V) – user adjustable
    "gauge_factor": 2.0,   # GF of the strain gauge – user adjustable

    # Material / geometry parameters
    "v_ref"       : 3.3,   # reference voltage (V) – W1 supply
    "cross_section": 1e-4, # beam cross-section area (m²)  – placeholder
    "elastic_area" : 1e-4, # same as above for stress calc

    # AD3 live readings (updated by sensor module)
    "voltage"     : 0.0,
    "strain"      : 0.0,
    "stress"      : 0.0,
    "youngs"      : 0.0,

    # Graph history buffers  (circular, last 100 points)
    "strain_buf"  : [0.0] * 100,
    "stress_buf"  : [0.0] * 100,
    "buf_head"    : 0,

    # Device status flags
    "ad3_connected" : False,
    "wifi_connected": False,
    "wifi_ssid"     : "",
}

def push_sample(strain, stress):
    """Append one sample to the circular graph buffers."""
    h = cfg["buf_head"]
    cfg["strain_buf"][h] = strain
    cfg["stress_buf"][h] = stress
    cfg["buf_head"] = (h + 1) % 100
