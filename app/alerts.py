# alerts.py -> threshold flags.
# DHYAN DO: ye sirf "value range ke bahar hai ya nahi" check karta hai. Ye diagnosis NAHI hai.
# Ranges aam taur pe quote kiye jaane wale reference values hain, clinically validated nahi.

# Har device ke har signal ka (low, high) normal range. Dono end "normal" maane jaate hain.
# Jis signal ka yahan entry nahi (jaise uterine_activity) uspe flag nahi lagta.
THRESHOLDS = {
    "neonatal_patch": {
        "temperature_c": (36.5, 37.5),
        "heart_rate_bpm": (100.0, 160.0),
        "spo2_pct": (95.0, 100.0),
    },
    "belly_band": {
        "maternal_heart_rate_bpm": (60.0, 100.0),
        "fetal_heart_rate_bpm": (110.0, 160.0),
    },
}


def check_value(value: float, low: float, high: float) -> str:
    """Ek value ko range se milata hai. Return: 'low', 'high' ya 'normal'.

    Boundary pe value (jaise exactly 36.5) 'normal' hai - isliye < aur > use kiya, <= ya >= nahi.
    """
    if value < low:
        return "low"
    if value > high:
        return "high"
    return "normal"


def evaluate(device: str, values: dict) -> list:
    """Ek reading ke saare signals check karta hai; sirf gadbad wale signals ki flag list lautata hai."""
    flags = []
    for signal, (low, high) in THRESHOLDS.get(device, {}).items():
        if signal not in values:
            continue
        value = values[signal]
        status = check_value(value, low, high)
        if status == "normal":
            continue  # normal pe flag nahi lagate
        flags.append(
            {
                "signal": signal,
                "value": value,
                "status": status,
                "normal_range": [low, high],
                "message": (
                    f"{signal} is {status} (value {value}, expected {low} to {high}). "
                    "Screening flag only, not a diagnosis."
                ),
            }
        )
    return flags
