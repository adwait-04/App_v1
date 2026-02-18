import numpy as np
from pymavlink import mavutil


# ---------------- SAFE HELPERS ----------------

def safe_array(arr):
    if arr is None or len(arr) == 0:
        return np.array([])
    return np.array(arr)


def safe_hover(throttle):
    if throttle is None or len(throttle) == 0:
        return 0.4
    h = np.median(throttle)
    if h <= 0:
        return 0.4
    return h


def safe_div(a, b, default=0):
    if b is None or b == 0 or np.isnan(b):
        return default
    return a / b


# ---------------- LOG EXTRACTION ----------------

def load_log(bin_path):
    return mavutil.mavlink_connection(bin_path)


def extract_ctun_throttle(mlog):
    vals = []
    mlog.rewind()
    while True:
        msg = mlog.recv_match(type="CTUN", blocking=False)
        if msg is None:
            break
        if hasattr(msg, "ThO"):
            vals.append(msg.ThO)
    return safe_array(vals)


def extract_attitude(mlog):
    roll = []
    pitch = []
    mlog.rewind()
    while True:
        msg = mlog.recv_match(type="ATT", blocking=False)
        if msg is None:
            break
        roll.append(msg.Roll)
        pitch.append(msg.Pitch)
    return safe_array(roll), safe_array(pitch)


def extract_vibe_xyz(mlog):
    vx, vy, vz = [], [], []
    mlog.rewind()
    while True:
        msg = mlog.recv_match(type="VIBE", blocking=False)
        if msg is None:
            break
        vx.append(msg.VibeX)
        vy.append(msg.VibeY)
        vz.append(msg.VibeZ)
    return safe_array(vx), safe_array(vy), safe_array(vz)


def extract_vcc(mlog):
    vcc = []
    mlog.rewind()
    while True:
        msg = mlog.recv_match(type="POWR", blocking=False)
        if msg is None:
            break
        vcc.append(msg.Vcc)
    return safe_array(vcc)


def extract_battery(mlog):
    volt = []
    mlog.rewind()
    while True:
        msg = mlog.recv_match(type="BAT", blocking=False)
        if msg is None:
            break
        if hasattr(msg, "Volt"):
            volt.append(msg.Volt)
    return safe_array(volt)

# ---------------- ADVANCED METRICS ----------------

def estimate_endurance(volt, throttle):
    """
    Physics-based endurance estimate using voltage slope.
    Returns: endurance_samples, remaining_samples
    """
    if len(volt) < 2:
        return None, None

    volt = np.array(volt)

    dv = volt[-1] - volt[0]
    dt = len(volt)

    if dt <= 0:
        return None, None

    slope = dv / dt  # V per sample

    if slope >= 0:
        return None, None

    v_cutoff = np.percentile(volt, 5)
    remaining_v = volt[-1] - v_cutoff

    remaining = remaining_v / abs(slope)
    endurance = dt + remaining

    return float(endurance), float(remaining)


# ---------------- BATTERY ----------------

def battery_metrics(volt, throttle):
    if len(volt) == 0:
        return {
            "avg_voltage": None,
            "min_voltage": None,
            "voltage_sag_pct": None,
            "battery_health": None,
            "endurance_est": None
        }

    volt = np.array(volt)

    avg_v = float(np.mean(volt))
    min_v = float(np.min(volt))

    v_nom = 22.2  # 6S nominal
    sag_pct = (v_nom - min_v) / v_nom * 100

    endurance, remaining = estimate_endurance(volt, throttle)

    if endurance is not None:
        health = np.clip(endurance / 2000 * 100, 0, 100)
    else:
        health = None

    return {
        "avg_voltage": avg_v,
        "min_voltage": min_v,
        "voltage_sag_pct": float(sag_pct),
        "battery_health": health,
        "endurance_est": endurance,
        "remaining_est": remaining
    }


# ---------------- VIBRATION ----------------

def vibration_metrics(vx, vy, vz):
    if len(vx) == 0:
        return {
            "max_vibe": None,
            "rms_vibe": None,
            "vibe_severity": None
        }

    vx = np.array(vx)
    vy = np.array(vy)
    vz = np.array(vz)

    max_v = float(max(np.max(np.abs(vx)),
                      np.max(np.abs(vy)),
                      np.max(np.abs(vz))))

    rms = float(np.sqrt(np.mean(vx**2 + vy**2 + vz**2)))

    if rms < 10:
        sev = "LOW"
    elif rms < 20:
        sev = "MODERATE"
    else:
        sev = "HIGH"

    return {
        "max_vibe": max_v,
        "rms_vibe": rms,
        "vibe_severity": sev
    }


# ---------------- STABILITY ----------------

def stability_metrics(roll, pitch):
    if len(roll) == 0:
        return {
            "roll_var": None,
            "pitch_var": None
        }

    roll = np.array(roll)
    pitch = np.array(pitch)

    return {
        "roll_var": float(np.var(roll)),
        "pitch_var": float(np.var(pitch))
    }


# ---------------- CONTROL ----------------

def control_metrics(throttle):
    if len(throttle) == 0:
        return {
            "avg_throttle": None,
            "peak_throttle": None,
            "motor_sat_pct": None,
            "hover_throttle": 0.4
        }

    throttle = np.array(throttle)

    hover = safe_hover(throttle)
    avg_thr = float(np.mean(throttle))
    peak = float(np.max(throttle))

    sat = float(np.sum(throttle > 0.9) / len(throttle) * 100)

    return {
        "avg_throttle": avg_thr,
        "peak_throttle": peak,
        "motor_sat_pct": sat,
        "hover_throttle": hover
    }


# ---------------- ELECTRICAL ----------------

def electrical_metrics(vcc):
    if len(vcc) == 0:
        return {
            "vcc_std": None
        }

    return {
        "vcc_std": float(np.std(vcc))
    }


# ---------------- ENERGY ----------------

def energy_metrics(volt):
    if len(volt) < 2:
        return {
            "volt_drop": None
        }

    volt = np.array(volt)
    drop = float(volt[0] - volt[-1])

    return {
        "volt_drop": drop
    }

# ---------------- SCORES (NORMALIZED 0–100) ----------------

def stability_score(roll, pitch, throttle):
    if len(throttle) == 0:
        return 0

    hover = safe_hover(throttle)

    thr_var = np.std(throttle) if len(throttle) > 0 else 0
    att_var = np.sqrt(np.std(roll)**2 + np.std(pitch)**2) if len(roll) > 0 else 0

    att_norm = safe_div(att_var, 6)
    thr_norm = safe_div(thr_var, hover) / 0.12

    idx = 0.6 * att_norm + 0.4 * thr_norm
    score = 100 * (1 - idx)
    return float(np.clip(score, 0, 100))


def control_authority_score(throttle):
    if len(throttle) == 0:
        return 0

    hover = safe_hover(throttle)
    margin = 1 - hover
    score = safe_div(margin, 0.6) * 100
    return float(np.clip(score, 0, 100))


def propulsion_efficiency_score(throttle):
    if len(throttle) == 0:
        return 0

    hover = safe_hover(throttle)
    score = (1 - abs(hover - 0.4) / 0.4) * 100
    return float(np.clip(score, 0, 100))


def mechanical_smoothness_score(rms_vibe, hover):
    if rms_vibe is None:
        return 50

    norm = safe_div(rms_vibe, hover)
    score = 100 * (1 - norm / 60)
    return float(np.clip(score, 0, 100))


def electrical_score(vcc_std):
    if vcc_std is None:
        return 50

    score = 100 * (1 - vcc_std / 0.15)
    return float(np.clip(score, 0, 100))


def energy_efficiency_score(volt_drop, hover):
    if volt_drop is None:
        return 50

    norm = safe_div(volt_drop, hover)
    score = 100 * (1 - norm / 3.0)
    return float(np.clip(score, 0, 100))


def endurance_score(endurance_est):
    if endurance_est is None:
        return 50

    score = endurance_est / 2000 * 100
    return float(np.clip(score, 0, 100))


# ---------------- FINAL FLIGHTSCORE ----------------

def compute_flight_score(bin_path):

    mlog = load_log(bin_path)

    throttle = extract_ctun_throttle(mlog)
    roll, pitch = extract_attitude(mlog)
    vx, vy, vz = extract_vibe_xyz(mlog)
    vcc = extract_vcc(mlog)
    volt = extract_battery(mlog)

    # --- metrics ---
    bat = battery_metrics(volt, throttle)
    vib = vibration_metrics(vx, vy, vz)
    stab = stability_metrics(roll, pitch)
    ctrl = control_metrics(throttle)
    elec = electrical_metrics(vcc)
    eng = energy_metrics(volt)

    hover = ctrl["hover_throttle"]

    # --- scores ---
    s1 = stability_score(roll, pitch, throttle)
    s2 = control_authority_score(throttle)
    s3 = propulsion_efficiency_score(throttle)
    s4 = mechanical_smoothness_score(vib["rms_vibe"], hover)
    s5 = electrical_score(elec["vcc_std"])
    s6 = energy_efficiency_score(eng["volt_drop"], hover)
    s7 = endurance_score(bat["endurance_est"])

    final = (
        0.20 * s1 +
        0.20 * s2 +
        0.20 * s3 +
        0.15 * s4 +
        0.10 * s5 +
        0.10 * s6 +
        0.05 * s7
    )

    if np.isnan(final):
        return 0.0

    return float(np.clip(final, 0, 100))


# ---------------- FULL METRICS OUTPUT ----------------

def compute_flight_metrics(bin_path):

    mlog = load_log(bin_path)

    throttle = extract_ctun_throttle(mlog)
    roll, pitch = extract_attitude(mlog)
    vx, vy, vz = extract_vibe_xyz(mlog)
    vcc = extract_vcc(mlog)
    volt = extract_battery(mlog)

    bat = battery_metrics(volt, throttle)
    vib = vibration_metrics(vx, vy, vz)
    stab = stability_metrics(roll, pitch)
    ctrl = control_metrics(throttle)
    elec = electrical_metrics(vcc)
    eng = energy_metrics(volt)

    final = compute_flight_score(bin_path)

    return {
        # ---- Battery ----
        "avg_voltage": bat["avg_voltage"],
        "min_voltage": bat["min_voltage"],
        "voltage_sag_pct": bat["voltage_sag_pct"],
        "battery_health": bat["battery_health"],
        "endurance_est": bat["endurance_est"],
        "remaining_est": bat["remaining_est"],

        # ---- Vibration ----
        "max_vibe": vib["max_vibe"],
        "rms_vibe": vib["rms_vibe"],
        "vibe_severity": vib["vibe_severity"],

        # ---- Stability ----
        "roll_var": stab["roll_var"],
        "pitch_var": stab["pitch_var"],

        # ---- Control ----
        "avg_throttle": ctrl["avg_throttle"],
        "peak_throttle": ctrl["peak_throttle"],
        "motor_sat_pct": ctrl["motor_sat_pct"],
        "hover_throttle": ctrl["hover_throttle"],

        # ---- Electrical ----
        "vcc_std": elec["vcc_std"],

        # ---- Energy ----
        "volt_drop": eng["volt_drop"],

        # ---- Final ----
        "flight_score": final
    }