# routes.py -> saare endpoints (URLs) yahan hain.
# Rule: yahan sirf "request lo, kaam ke liye simulator/alerts ko bulao, jawab lautao".
# Asli logic simulator.py aur alerts.py mein hai, taaki har file ek hi kaam kare.

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query

from app import config
from app.alerts import evaluate
from app.schemas import (
    DeviceInfo,
    DeviceName,
    DevicesResponse,
    LatestReadingResponse,
    Reading,
    ReadingRequest,
    ReadingsResponse,
    ScenarioName,
    SignalInfo,
)
from app.simulator import generate_readings, load_profile

router = APIRouter()


@router.get("/health")
def health():
    """Server zinda hai ya nahi, bas ye check."""
    return {"status": "ok"}


@router.get("/devices", response_model=DevicesResponse)
def list_devices():
    """Kaun se devices hain aur unke signals kaun se hain."""
    devices = []
    for name in config.SUPPORTED_DEVICES:
        profile = load_profile(name)
        signals = [
            SignalInfo(name=sig, unit=p["unit"]) for sig, p in profile["signals"].items()
        ]
        devices.append(DeviceInfo(name=name, signals=signals))
    return DevicesResponse(default_device=config.DEFAULT_DEVICE, devices=devices)


@router.get("/devices/{device_name}/profile")
def device_profile(device_name: str):
    """Device ki profile (mean, std...) dikhata hai. Device galat ho to load_profile 404 uthata hai."""
    return load_profile(device_name)


@router.get("/readings/latest", response_model=LatestReadingResponse)
def latest_reading(
    device: DeviceName = config.DEFAULT_DEVICE,
    scenario: ScenarioName = "normal",
    seed: Optional[int] = Query(default=None, ge=0, le=2 ** 32 - 1),
):
    """Ek 'sabse taaza' nakli reading, abhi ke UTC timestamp ke saath.

    Query params galat hon (jaise scenario=panic) to FastAPI khud 422 deta hai.
    - seed diya  -> values repeatable (timestamp phir bhi abhi ka rehta hai).
    - seed nahi  -> seed = abhi ka epoch second, isliye har second nayi value (live device jaisa).
    """
    now = datetime.now(timezone.utc)
    used_seed = seed if seed is not None else int(now.timestamp())

    row = generate_readings(device, 1, used_seed, scenario)[0]

    return LatestReadingResponse(
        simulated=True,
        device=device,
        scenario=scenario,
        seed=used_seed,
        timestamp=now,
        values=row["values"],
        flags=evaluate(device, row["values"]),
        disclaimer=config.DISCLAIMER,
    )


@router.post("/readings", response_model=ReadingsResponse)
def create_readings(req: ReadingRequest):
    """Nakli readings banao, har reading pe threshold flags lagao, aur jawab do."""
    # Seed nahi diya to default; isse bina seed ke bhi result repeatable rehta hai.
    seed = req.seed if req.seed is not None else config.DEFAULT_SEED

    rows = generate_readings(req.device, req.count, seed, req.scenario)

    readings = [
        Reading(
            t_seconds=row["t_seconds"],
            values=row["values"],
            flags=evaluate(req.device, row["values"]),
        )
        for row in rows
    ]
    flagged = sum(1 for r in readings if r.flags)

    return ReadingsResponse(
        simulated=True,
        device=req.device,
        scenario=req.scenario,
        seed=seed,
        count=len(readings),
        flagged_readings=flagged,
        disclaimer=config.DISCLAIMER,
        readings=readings,
    )
