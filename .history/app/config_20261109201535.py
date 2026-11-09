# config.py -> saari settings ek hi jagah.
# Kuch badalna ho (jaise max readings) to sirf yahan badlo, baaki code apne aap follow karega.

from pathlib import Path

# Ye file jis folder mein hai (app/) uska poora path. Baaki paths isi se bante hain,
# isliye project kisi bhi laptop pe chale, path galat nahi hoga.
BASE_DIR = Path(__file__).resolve().parent
PROFILES_DIR = BASE_DIR / "profiles"   # dono JSON profiles yahan hain
STATIC_DIR = BASE_DIR / "static"       # index.html yahan hai

# Seed = random number generator ka "starting point".
# Same seed -> har baar bilkul same readings (repeatable). Request mein seed na ho to ye use hoga.
DEFAULT_SEED = 42

# GET /devices mein dikhta hai ki default device kaun sa hai.
DEFAULT_DEVICE = "neonatal_patch"

# Jo devices hum support karte hain. Har ek ki ek JSON profile app/profiles/ mein honi chahiye.
SUPPORTED_DEVICES = ("neonatal_patch", "belly_band")

# "normal" = healthy range ke aaspaas readings, "stress" = readings ko thoda gadbad ki taraf shift karna
# (taaki alerts ka demo dikha sakein).
SCENARIOS = ("normal", "stress")

DEFAULT_COUNT = 10           # count na diya to kitni readings
MAX_COUNT = 10000000000000000000000000000000000000000000             # ek request mein maximum (server pe load na pade)
SAMPLE_INTERVAL_SECONDS = 1  # do readings ke beech ka (nakli) time gap

# Har response ke saath ye line jaati hai, taaki koi isse real medical data na samajh le.
DISCLAIMER = (
    "Simulated data for software testing only. Flags are simple threshold checks, "
    "not a medical diagnosis."
)
