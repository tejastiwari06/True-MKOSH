# test_simulator.py -> simulator ka behaviour: repeatable hai? ranges ke andar hai? stress kaam karta hai?

import pytest

from app import config
from app.errors import DeviceNotFound
from app.simulator import generate_readings, load_profile


def test_same_seed_same_output():
    a = generate_readings("neonatal_patch", 50, seed=7)
    b = generate_readings("neonatal_patch", 50, seed=7)
    assert a == b


def test_different_seed_different_output():
    a = generate_readings("neonatal_patch", 50, seed=7)
    b = generate_readings("neonatal_patch", 50, seed=8)
    assert a != b


@pytest.mark.parametrize("device", config.SUPPORTED_DEVICES)
def test_values_stay_inside_profile_limits(device):
    profile = load_profile(device)
    for scenario in config.SCENARIOS:
        rows = generate_readings(device, 300, seed=3, scenario=scenario)
        for row in rows:
            for name, value in row["values"].items():
                p = profile["signals"][name]
                assert p["min"] <= value <= p["max"]


def test_requested_count_is_respected():
    assert len(generate_readings("belly_band", 1, seed=1)) == 1
    assert len(generate_readings("belly_band", 123, seed=1)) == 123


def test_stress_shifts_temperature_down():
    def avg_temp(scenario):
        rows = generate_readings("neonatal_patch", 300, seed=5, scenario=scenario)
        return sum(r["values"]["temperature_c"] for r in rows) / len(rows)

    assert avg_temp("stress") < avg_temp("normal") - 0.5


def test_unknown_device_raises():
    with pytest.raises(DeviceNotFound):
        load_profile("toaster")


@pytest.mark.parametrize("device", config.SUPPORTED_DEVICES)
def test_profile_files_are_well_formed(device):
    profile = load_profile(device)
    assert profile["signals"], "profile mein kam se kam ek signal hona chahiye"
    for p in profile["signals"].values():
        assert p["min"] <= p["mean"] <= p["max"]
        assert p["std"] > 0
        assert 0 <= p["autocorr"] < 1
