# test_validation.py -> galat input pe sahi error aana chahiye (422 / 404 / 405) aur format ek jaisa ho.


import pytest


def assert_error_format(res, status, code):
    """Helper: error ka shape {"error": {"code", "message", "details"}} check karta hai."""
    assert res.status_code == status
    err = res.json()["error"]
    assert err["code"] == code
    assert isinstance(err["message"], str)
    assert isinstance(err["details"], list)
    return err


def test_missing_device_field(client):
    res = client.post("/readings", json={"count": 5})
    err = assert_error_format(res, 422, "validation_error")
    assert err["details"][0]["field"] == "device"


def test_wrong_type_for_count(client):
    res = client.post("/readings", json={"device": "belly_band", "count": "abc"})
    err = assert_error_format(res, 422, "validation_error")
    assert err["details"][0]["field"] == "count"


def test_fractional_count_rejected(client):
    res = client.post("/readings", json={"device": "belly_band", "count": 3.5})
    assert_error_format(res, 422, "validation_error")


@pytest.mark.parametrize("count", [0, -1, 501])
def test_count_out_of_range(client, count):
    res = client.post("/readings", json={"device": "belly_band", "count": count})
    assert_error_format(res, 422, "validation_error")


def test_unknown_device_in_body(client):
    res = client.post("/readings", json={"device": "toaster"})
    assert_error_format(res, 422, "validation_error")


def test_negative_seed(client):
    res = client.post("/readings", json={"device": "belly_band", "seed": -5})
    assert_error_format(res, 422, "validation_error")


def test_unknown_scenario(client):
    res = client.post("/readings", json={"device": "belly_band", "scenario": "panic"})
    assert_error_format(res, 422, "validation_error")


def test_extra_field_rejected(client):
    res = client.post("/readings", json={"device": "belly_band", "cnt": 5})
    assert_error_format(res, 422, "validation_error")


def test_broken_json_body(client):
    res = client.post(
        "/readings", content="{not json", headers={"Content-Type": "application/json"}
    )
    assert_error_format(res, 422, "validation_error")


def test_unknown_device_profile_is_404(client):
    res = client.get("/devices/toaster/profile")
    assert_error_format(res, 404, "device_not_found")


def test_unknown_url_is_404(client):
    res = client.get("/nope")
    assert_error_format(res, 404, "not_found")


def test_wrong_method_is_405(client):
    res = client.get("/readings")  # /readings sirf POST leta hai
    assert_error_format(res, 405, "method_not_allowed")


@pytest.mark.parametrize(
    "query",
    ["device=toaster", "scenario=panic", "seed=-1", "seed=abc"],
)
def test_latest_rejects_bad_query(client, query):
    res = client.get(f"/readings/latest?{query}")
    assert_error_format(res, 422, "validation_error")


def test_latest_error_names_the_field(client):
    err = assert_error_format(client.get("/readings/latest?scenario=panic"), 422, "validation_error")
    assert err["details"][0]["field"] == "scenario"
