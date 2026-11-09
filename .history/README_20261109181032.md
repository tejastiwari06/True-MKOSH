# MaaKosh fake valyes generator API (`maakosh-sim-api`)

A small FastAPI prototype that generates **simulated** monitoring readings for a fictional MaaKosh device
and serves them as JSON. **All data is synthetic. Nothing here diagnoses or clinically assesses anyone.**

| Device | Signals |
|---|---|
| `neonatal_patch` (default) | `temperature_c`, `heart_rate_bpm`, `spo2_pct` |
| `belly_band` | `maternal_heart_rate_bpm`, `fetal_heart_rate_bpm`, `uterine_activity` |

## Setup and run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Swagger UI : http://127.0.0.1:8000/docs
- Minimal web page : http://127.0.0.1:8000/
- render deployed link : https://true-mkosh.onrender.com

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/readings/latest` | Latest simulated reading with a UTC timestamp |
| POST | `/readings` | Generate a batch of simulated readings |
| GET | `/devices` | Devices and their signals |
| GET | `/devices/{name}/profile` | Statistical profile behind the simulator (404 if unknown) |
| GET | `/health` | Liveness check |

### `GET /readings/latest`

| Query param | Type | Default | Notes |
|---|---|---|---|
| `device` | `neonatal_patch` / `belly_band` | `neonatal_patch` | |
| `scenario` | `normal` / `stress` | `normal` | `stress` shifts signals so flags appear |
| `seed` | int >= 0 | current epoch second | with a seed the values are repeatable |

```bash
curl "http://127.0.0.1:8000/readings/latest?seed=42&scenario=stress"
```

```json
{
  "simulated": true,
  "device": "neonatal_patch",
  "scenario": "stress",
  "seed": 42,
  "timestamp": "2026-11-05T11:03:51.018663Z",
  "values": {"temperature_c": 35.86, "heart_rate_bpm": 168.27, "spo2_pct": 91.39},
  "flags": [
    {"signal": "temperature_c", "value": 35.86, "status": "low", "normal_range": [36.5, 37.5],
     "message": "temperature_c is low (value 35.86, expected 36.5 to 37.5). Screening flag only, not a diagnosis."}
  ],
  "disclaimer": "Simulated data for software testing only. Flags are simple threshold checks, not a medical diagnosis.(काल्पनिक) "
}
```
(`flags` is shortened here; the real response also flags heart rate and SpO2 in this stress example.)

### `POST /readings`

Body fields: `device` (required), `count` (1 to 500, default 10), `seed` (default 42), `scenario` (default `normal`).
Unknown fields are rejected. Each reading has `t_seconds` (simulated time offset), `values` and `flags`.

```bash
curl -X POST http://127.0.0.1:8000/readings -H "Content-Type: application/json" \
  -d '{"device": "belly_band", "count": 2, "seed": 1}'
```

### Errors

Every error uses the same shape. Example: `GET /readings/latest?scenario=panic` returns HTTP 422:

```json
{"error": {"code": "validation_error", "message": "Request data is invalid.",
           "details": [{"field": "scenario", "problem": "Input should be 'normal' or 'stress'", "type": "literal_error"}]}}
```

| Situation | Status | `code` |
|---|---|---|
| Missing field, wrong type, out-of-range value, unknown field, broken JSON | 422 | `validation_error` |
| Unknown device in `/devices/{name}/profile` | 404 | `device_not_found` |
| Unknown URL | 404 | `not_found` |
| Wrong HTTP method | 405 | `method_not_allowed` |
| Unexpected server bug | 500 | `internal_error` (no internal details leaked) |

## Design choices

- **Simulation:** each signal is a mean-reverting random walk (AR(1)) from a per-signal profile (mean, std, min, max, lag-1 autocorrelation), so traces look smooth rather than like white noise.
- **Repeatability:** each request uses its own seeded random generator, so the same seed always gives the same values.
- **Labelled as simulated:** every response has `simulated: true` and a disclaimer.
- **Flags, not diagnosis:** `alerts.py` only compares values to fixed ranges (range edges count as normal).
- **Validation with Pydantic:** types, required fields and ranges are declared once in `schemas.py`; one handler turns every error into the common format.
- **One file, one job:** `routes.py` (endpoints), `simulator.py`, `alerts.py`, `schemas.py`, `errors.py`, `config.py`.
- **Profiles from data (optional):** `scripts/build_profiles.py` summarises the CTU-UHB dataset into the belly-band profile. The dataset is not included (size and license; cite it if used). Run: `python scripts/build_profiles.py --data-dir /path/to/ctu-uhb-folder`.

## Known limitations

- Prototype only: no database, authentication, rate limiting or real device input.
- `/readings/latest` without a seed draws each reading independently per second, so consecutive calls are not a smooth continuous stream.
- Signals are generated independently (no physiological coupling, e.g. between contractions and fetal heart rate).
- Thresholds are commonly cited reference values, **not clinically validated**.
- The shipped profiles are starter values. Newborn temperature/SpO2 and maternal heart rate are reference values (CTU-UHB does not contain them). Fetal heart rate and uterine activity become dataset-derived only after running the script.
- Timestamps are the server's UTC clock; `POST /readings` uses a simple `t_seconds` offset instead.
