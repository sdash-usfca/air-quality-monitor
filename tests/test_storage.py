from aqm.models import METRICS
from aqm.sensors.mock import MockSensor
from aqm.storage.db import Database


def test_store_latest_and_history(tmp_path):
    db = Database(str(tmp_path / "t.db"))
    db.init_schema()
    db.insert_readings(1000, {"co2": 500.0, "pm2_5": 10.0})
    db.insert_readings(1010, {"co2": 600.0})

    latest = db.latest()
    assert latest["co2"][0] == 600.0          # newest CO2 wins
    assert latest["pm2_5"][0] == 10.0         # untouched metric still present

    co2_hist = db.history("co2", since_ts=0)
    assert [v for _, v in co2_hist] == [500.0, 600.0]


def test_prune_drops_old_rows(tmp_path):
    db = Database(str(tmp_path / "t.db"))
    db.init_schema()
    db.insert_readings(100, {"co2": 400.0})
    db.insert_readings(200, {"co2": 410.0})
    db.prune(older_than_ts=150)
    assert [v for _, v in db.history("co2", 0)] == [410.0]


def test_history_bucketed_averages(tmp_path):
    db = Database(str(tmp_path / "t.db"))
    db.init_schema()
    db.insert_readings(1000, {"co2": 400.0})   # 1000 // 60 * 60 -> bucket 960
    db.insert_readings(1010, {"co2": 500.0})   # same bucket 960 -> avg 450
    db.insert_readings(1080, {"co2": 800.0})   # bucket 1080
    assert db.history_bucketed("co2", since_ts=0, bucket_seconds=60) == [(960, 450.0), (1080, 800.0)]


def test_mock_sensor_uses_known_metrics():
    values = MockSensor().read()
    assert "co2" in values
    assert values["co2"] >= 420
    for key in values:
        assert key in METRICS, f"mock produced unknown metric '{key}'"
