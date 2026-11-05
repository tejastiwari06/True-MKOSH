# test_readings.py -> success cases: sab kuch sahi bheja to sahi jawab aana chahiye.

from datetime import datetime, timezone

import pytest


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_devices_list(client):
    res = client.get("/devices")
    assert res.status_code == 200
    data = res.json()
    assert data["default_device"] == "neonatal_patch"
    names = [d["name"] for d in data["devices"]]
    assert names == ["neonatal_patch", "belly_band"]


def test_profile_endpoint(client):
    res = client.get("/devices/belly_band/profile")
    assert res.status_code == 200
    assert "fetal_heart_rate_bpm" in res.json()["signals"]


@pytest.mark.parametrize("device", ["neonatal_patch", "belly_band"])
def test_post_readings_shape(client, device):
    res = client.post("/readings", json={"device": device, "count": 7, "seed": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["device"] == device
    assert data["count"] == 7
    assert len(data["readings"]) == 7
    assert "disclaimer" in data
    # time har reading ke saath 1 second badhna chahiye
    assert [r["t_seconds"] for r in data["readings"]] == list(range(7))


def test_defaults_are_applied(client):
    # sirf device diya: count=10, seed=42, scenario=normal default hone chahiye
    res = client.post("/readings", json={"device": "neonatal_patch"})
    data = res.json()
    assert data["count"] == 10
    assert data["seed"] == 42
    assert data["scenario"] == "normal"


def test_stress_scenario_raises_flags(client):
    res = client.post(
        "/readings",
        json={"device": "neonatal_patch", "count": 20, "seed": 42, "scenario": "stress"},
    )
    data = res.json()
    # stress mein temperature ~35.9 hota hai, 36.5 se neeche -> flags aane hi chahiye
    assert data["flagged_readings"] > 0
    first_flag = next(r["flags"][0] for r in data["readings"] if r["flags"])
    assert first_flag["status"] in ("low", "high")
    assert "not a diagnosis" in first_flag["message"]


def test_same_request_gives_same_response(client):
    body = {"device": "belly_band", "count": 15, "seed": 99}
    assert client.post("/readings", json=body).json() == client.post("/readings", json=body).json()


def test_home_page_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "MaaKosh Simulator" in res.text


def test_latest_reading_success(client):
    res = client.get("/readings/latest")
    assert res.status_code == 200
    data = res.json()
    assert data["simulated"] is True
    assert data["device"] == "neonatal_patch"  # default device
    assert set(data["values"]) == {"temperature_c", "heart_rate_bpm", "spo2_pct"}
    assert "disclaimer" in data
    # timestamp ISO format mein hona chahiye, timezone ke saath, aur abhi ke aaspaas
    ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert ts.tzinfo is not None
    assert abs((datetime.now(timezone.utc) - ts).total_seconds()) < 60


def test_latest_reading_with_seed_is_repeatable(client):
    url = "/readings/latest?device=belly_band&seed=5"
    a, b = client.get(url).json(), client.get(url).json()
    assert a["values"] == b["values"]  # timestamp alag ho sakta hai, values nahi


def test_post_response_is_labelled_simulated(client):
    assert client.post("/readings", json={"device": "belly_band"}).json()["simulated"] is True
