# simulator.py -> nakli readings banata hai.
#
# Idea (simple): har signal ek "mean ke aaspaas ghoomta hua" number hai.
# Agla value = purana value ko mean ki taraf thoda kheencho + thoda random noise.
# Isse graph asli signal jaisa smooth dikhta hai (jhatke se kood-kood ke nahi).
# Is tareeke ko AR(1) kehte hain. Mean/std/autocorr JSON profile se aate hain.

import json
import math
import random
from functools import lru_cache

from app import config
from app.errors import DeviceNotFound


@lru_cache(maxsize=None)
def load_profile(device: str) -> dict:
    """Device ki JSON profile padhta hai. lru_cache = ek baar padhi to yaad rakhta hai (baar-baar disk nahi)."""
    if device not in config.SUPPORTED_DEVICES:
        raise DeviceNotFound(
            f"Unknown device '{device}'.",
            [{"field": "device", "problem": f"Use one of: {', '.join(config.SUPPORTED_DEVICES)}"}],
        )
    path = config.PROFILES_DIR / f"{device}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _target_mean(signal_profile: dict, scenario: str) -> float:
    """Scenario 'stress' ho to mean ko stress_shift se khiska dete hain, warna normal mean."""
    mean = signal_profile["mean"]
    if scenario == "stress":
        mean += signal_profile.get("stress_shift", 0.0)
    return mean


def generate_readings(device: str, count: int, seed: int, scenario: str = "normal") -> list:
    """`count` readings banata hai. Same (device, count, seed, scenario) -> hamesha same output."""
    profile = load_profile(device)
    signals = profile["signals"]

    # Apna alag random generator, seed ke saath. Global random use nahi kiya,
    # taaki ek request doosri ko affect na kare aur result repeatable rahe.
    rng = random.Random(seed)

    # Shuruaati value: mean ke aaspaas ek random jagah se.
    state = {}
    for name, p in signals.items():
        state[name] = _target_mean(p, scenario) + p["std"] * rng.gauss(0, 1)

    readings = []
    for i in range(count):
        values = {}
        for name, p in signals.items():
            mean = _target_mean(p, scenario)
            # phi 1 ke bahut paas ho to signal bilkul hilta nahi; 0.999 pe rok dete hain.
            phi = min(max(p["autocorr"], 0.0), 0.999)
            # Noise ka size aisa ki lambe time mein spread (std) wahi rahe jo profile mein hai.
            noise_scale = p["std"] * math.sqrt(1 - phi ** 2)

            if i > 0:  # pehli reading ke liye state upar bana chuka hai
                state[name] = mean + phi * (state[name] - mean) + noise_scale * rng.gauss(0, 1)

            # Value ko profile ke min/max ke andar rakhte hain (jaise SpO2 100 se upar nahi jaata).
            clipped = min(max(state[name], p["min"]), p["max"])
            values[name] = round(clipped, 2)

        readings.append({"t_seconds": i * config.SAMPLE_INTERVAL_SECONDS, "values": values})
    return readings
