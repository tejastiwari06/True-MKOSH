"""
build_profiles.py -> CTU-UHB dataset se belly_band profile ke do signals ka summary nikalta hai.
Ye script APNE LAPTOP PE EK BAAR chalani hai. Dataset ZIP mein nahi jaata, sirf nikla hua chhota JSON jaata hai.

Kya karta hai:
  1. Dataset folder ke saare records (.hea/.dat) padhta hai (wfdb library se).
  2. Har record se FHR (fetal heart rate) aur UC (uterine contractions) nikalta hai.
  3. 4 Hz signal ko 1 Hz banata hai (simulator mein 1 reading/second hai).
  4. Missing/dropout samples (0 ya NaN) hata deta hai.
  5. Mean, std, min/max (0.5 aur 99.5 percentile) aur autocorr (agla sample pichhle se kitna juda hai) nikalta hai.
  6. app/profiles/belly_band.json mein sirf fetal_heart_rate_bpm aur uterine_activity update karta hai.

Chalane ka tareeka:
  pip install -r requirements-dev.txt
  python scripts/build_profiles.py --data-dir "C:/path/to/ctu-uhb-ctgs-database-1.0.0"

Dataset: "CTU-UHB Intrapartum Cardiotocography Database" on PhysioNet. Use karo to citation dena zaroori hai
(Chudacek et al., BMC Pregnancy and Childbirth 2014; Goldberger et al., Circulation 2000 - PhysioNet).
"""

import argparse
import json
from pathlib import Path

import numpy as np
import wfdb

PROFILE_PATH = Path(__file__).resolve().parent.parent / "app" / "profiles" / "belly_band.json"
TARGET_HZ = 1  # simulator ki speed: 1 reading per second


def find_channel(sig_names, prefix):
    """Channel ka index dhoondta hai jiska naam prefix se shuru ho (jaise 'FHR1' ya 'UC'). Na mile to None."""
    for i, name in enumerate(sig_names):
        if name.upper().startswith(prefix):
            return i
    return None


def collect(data_dir: Path, limit=None):
    """Saare records padh ke FHR aur UC ke samples jama karta hai."""
    names = sorted(p.with_suffix("") for p in data_dir.rglob("*.hea"))
    if limit:
        names = names[:limit]
    if not names:
        raise SystemExit(f"'{data_dir}' mein koi .hea record nahi mila. Sahi folder diya?")

    pooled = {"FHR": [], "UC": []}   # saare records ke valid samples
    lag_corrs = {"FHR": [], "UC": []}  # har record ka lag-1 autocorr

    for path in names:
        rec = wfdb.rdrecord(str(path))
        # Sampling rate (Hz) se pata chalta hai ki kitne samples chhod ke 1 Hz milega.
        step = max(int(round(rec.fs / TARGET_HZ)), 1)

        for key in ("FHR", "UC"):
            idx = find_channel(rec.sig_name, key)
            if idx is None:
                continue
            x = rec.p_signal[::step, idx]
            # 0 aur NaN is dataset mein "signal gaya" ka matlab hain -> valid nahi maante.
            valid = np.isfinite(x) & (x > 0)
            pooled[key].append(x[valid])

            # Autocorr sirf wahan jahan do consecutive samples dono valid hon.
            a, b = x[:-1], x[1:]
            both = valid[:-1] & valid[1:]
            if both.sum() > 100:
                lag_corrs[key].append(np.corrcoef(a[both], b[both])[0, 1])

    print(f"{len(names)} records padhe.")
    return pooled, lag_corrs


def summarize(samples, corrs):
    """Samples se mean/std/min/max/autocorr. min/max ke liye percentile (extreme glitches se bachne ke liye)."""
    x = np.concatenate(samples)
    autocorr = float(np.clip(np.median(corrs), 0.0, 0.99))
    return {
        "mean": round(float(x.mean()), 2),
        "std": round(float(x.std()), 2),
        "min": round(float(np.percentile(x, 0.5)), 2),
        "max": round(float(np.percentile(x, 99.5)), 2),
        "autocorr": round(autocorr, 3),
    }


def main():
    parser = argparse.ArgumentParser(description="Build belly_band profile from CTU-UHB.")
    parser.add_argument("--data-dir", required=True, type=Path, help="CTU-UHB dataset folder")
    parser.add_argument("--limit", type=int, default=None, help="Sirf pehle N records (quick test)")
    args = parser.parse_args()

    pooled, corrs = collect(args.data_dir, args.limit)

    with open(PROFILE_PATH, encoding="utf-8") as f:
        profile = json.load(f)

    # Dataset ke signal naam -> hamare profile ke signal naam
    mapping = {"FHR": "fetal_heart_rate_bpm", "UC": "uterine_activity"}
    for key, signal_name in mapping.items():
        if not pooled[key]:
            print(f"Warning: {key} channel kisi record mein nahi mila, {signal_name} nahi badla.")
            continue
        stats = summarize(pooled[key], corrs[key])
        profile["signals"][signal_name].update(stats)  # unit aur stress_shift jaise ke taise rehte hain
        print(f"{signal_name}: {stats}")

    profile["source"] = (
        "fetal_heart_rate_bpm and uterine_activity derived from CTU-UHB (1 Hz, dropouts removed) "
        "by scripts/build_profiles.py. maternal_heart_rate_bpm is a reference value, not from the dataset."
    )

    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Likh diya: {PROFILE_PATH}")


if __name__ == "__main__":
    main()
