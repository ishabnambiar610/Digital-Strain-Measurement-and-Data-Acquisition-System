# ─────────────────────────────────────────────────────────────
#  calculations.py  –  Sensor-data → physical-quantity pipeline
# ─────────────────────────────────────────────────────────────
#
#  Wheatstone-bridge assumptions
#  ─────────────────────────────
#  A quarter-bridge is driven by V_ref.
#  The amplified output voltage is read on CH1 of the AD3.
#  ΔV = (GF · ε · V_ref) / 4   →   ε = 4·ΔV / (GF · V_ref)
#
#  Stress  σ = F / A   (N/m²)
#  Young's E = σ / ε   (Pa)
#
#  NOTE: cross_section and force must be supplied / calibrated
#        by the user in CONFIGURE; defaults are illustrative.
#
from config import cfg, push_sample


def voltage_to_strain(voltage: float) -> float:
    """
    Convert measured bridge output voltage to micro-strain.

    ε = 4 · (V_meas - V_offset) / (GF · V_ref)
    """
    gf    = cfg["gauge_factor"]
    v_ref = cfg["v_ref"]
    offset= cfg["offset"]
    dv    = voltage - offset
    if gf == 0 or v_ref == 0:
        return 0.0
    return 4.0 * dv / (gf * v_ref)


def strain_to_stress(strain: float, force: float = None) -> float:
    """
    Compute stress (Pa) from strain.

    If `force` is supplied:   σ = F / A
    Otherwise uses Hooke's law approximation with a fixed E placeholder.
    The real Young's modulus is computed separately.
    """
    if force is not None:
        area = cfg["cross_section"]
        return force / area if area != 0 else 0.0
    # Fallback: use a nominal E (steel ~200 GPa)
    E_nominal = 200e9
    return strain * E_nominal


def youngs_modulus(stress: float, strain: float) -> float:
    """E = σ / ε  (Pa)"""
    return stress / strain if strain != 0 else 0.0


def update_calculations(voltage: float):
    """
    Full pipeline: voltage → strain → stress → Young's modulus.
    Updates cfg dict and appends to graph buffers.
    """
    strain = voltage_to_strain(voltage)
    stress = strain_to_stress(strain)
    young  = youngs_modulus(stress, strain)

    cfg["voltage"] = voltage
    cfg["strain"]  = strain
    cfg["stress"]  = stress
    cfg["youngs"]  = young

    push_sample(strain, stress)
    return strain, stress, young
