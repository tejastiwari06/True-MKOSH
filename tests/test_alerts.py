# test_alerts.py -> threshold check ke boundary cases (sabse zyada galti yahin hoti hai).

from app.alerts import check_value, evaluate


def test_boundaries_are_normal():
    # exactly range ke edge pe value 'normal' honi chahiye
    assert check_value(36.5, 36.5, 37.5) == "normal"
    assert check_value(37.5, 36.5, 37.5) == "normal"


def test_just_outside_boundaries():
    assert check_value(36.49, 36.5, 37.5) == "low"
    assert check_value(37.51, 36.5, 37.5) == "high"


def test_evaluate_all_normal_gives_no_flags():
    values = {"temperature_c": 36.9, "heart_rate_bpm": 130.0, "spo2_pct": 98.0}
    assert evaluate("neonatal_patch", values) == []


def test_evaluate_flags_only_bad_signals():
    values = {"temperature_c": 35.8, "heart_rate_bpm": 130.0, "spo2_pct": 98.0}
    flags = evaluate("neonatal_patch", values)
    assert len(flags) == 1
    assert flags[0]["signal"] == "temperature_c"
    assert flags[0]["status"] == "low"
    assert flags[0]["normal_range"] == [36.5, 37.5]


def test_signal_without_threshold_is_never_flagged():
    # uterine_activity ka koi threshold nahi, chahe value kitni bhi ho
    values = {
        "maternal_heart_rate_bpm": 80.0,
        "fetal_heart_rate_bpm": 140.0,
        "uterine_activity": 99.0,
    }
    assert evaluate("belly_band", values) == []


def test_unknown_device_gives_no_flags():
    assert evaluate("toaster", {"x": 1.0}) == []
