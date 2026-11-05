# schemas.py -> Pydantic models.
# Ye batate hain ki request/response ka shape kya hoga. Galat data aaye (jaise count="abc")
# to Pydantic khud rok deta hai aur 422 error banta hai - hamein if-else nahi likhne padte.

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app import config


# Ek hi jagah type define kiya, taaki POST body aur GET query dono wahi rules use karein.
# (config.SUPPORTED_DEVICES / config.SCENARIOS se match rakhna.)
DeviceName = Literal["neonatal_patch", "belly_band"]
ScenarioName = Literal["normal", "stress"]


class ReadingRequest(BaseModel):
    """POST /readings ki body."""

    # extra="forbid": koi anjaani field bheji (jaise typo "cnt") to error, chupchaap ignore nahi.
    model_config = ConfigDict(extra="forbid")

    # Literal = sirf ye do values allowed. (config.SUPPORTED_DEVICES se match rakhna.)
    device: DeviceName
    # ge=1 (>=1), le=MAX_COUNT (<=500)
    count: int = Field(default=config.DEFAULT_COUNT, ge=1, le=config.MAX_COUNT)
    # seed optional hai; na diya to config.DEFAULT_SEED use hoga (routes.py mein).
    seed: Optional[int] = Field(default=None, ge=0, le=2 ** 32 - 1)
    scenario: ScenarioName = "normal"


class Flag(BaseModel):
    """Ek signal jo normal range ke bahar gaya."""

    signal: str
    value: float
    status: Literal["low", "high"]
    normal_range: List[float]
    message: str


class Reading(BaseModel):
    """Ek time-point: kaun se signals ki kya value, aur kaun si flags."""

    t_seconds: int
    values: Dict[str, float]
    flags: List[Flag]


class ReadingsResponse(BaseModel):
    """POST /readings ka poora jawab."""

    simulated: bool  # hamesha True - data nakli hai, ye har response mein saaf likha aata hai
    device: str
    scenario: str
    seed: int
    count: int
    flagged_readings: int  # kitni readings mein kam se kam ek flag tha
    disclaimer: str
    readings: List[Reading]


class LatestReadingResponse(BaseModel):
    """GET /readings/latest ka jawab: sabse taaza ek reading + asli (UTC) timestamp."""

    simulated: bool
    device: str
    scenario: str
    seed: int
    timestamp: datetime  # abhi ka UTC time, ISO 8601 format mein
    values: Dict[str, float]
    flags: List[Flag]
    disclaimer: str


class SignalInfo(BaseModel):
    name: str
    unit: str


class DeviceInfo(BaseModel):
    name: str
    signals: List[SignalInfo]


class DevicesResponse(BaseModel):
    default_device: str
    devices: List[DeviceInfo]
