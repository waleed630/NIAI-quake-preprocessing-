"""Tests for the functions the provided test files do not cover."""
import json
import types

import pandas as pd
import pytest
import requests

from quakes import fetch, stream
from quakes.cleaning import clean
from quakes.features import add_location_features, add_region_activity


def test_clean_chains_steps():
    df = pd.DataFrame({
        "id": ["a", "a", "b", "c", "d"],
        "updated": [1700000100000, 1700000200000, 1700000100000,
                    1700000100000, 1700000100000],
        "time": [1700000000000] * 5,
        "mag": [1.0, 2.0, 3.0, None, 3.5],
        "type": ["earthquake", "earthquake", "explosion", "earthquake", " Earthquake"],
        "place": ["5 km N of X, CA", "5 km N of X, CA", "Y, NV", "Z, AK", None],
    })
    out = clean(df)
    assert out["id"].tolist() == ["a", "d"]
    assert out["mag"].tolist() == [2.0, 3.5]
    assert out["region"].tolist() == ["CA", "Unknown"]
    assert pd.api.types.is_datetime64_any_dtype(out["time"])


def test_add_location_features():
    df = pd.DataFrame({"lat": [-33.5, 10.0, 0.0], "depth_km": [10.0, 70.0, 120.0]})
    out = add_location_features(df)
    assert out["abs_lat"].tolist() == [33.5, 10.0, 0.0]
    assert out["is_shallow"].tolist() == [1, 0, 0]


def test_add_region_activity():
    t = pd.Timestamp("2023-11-14", tz="UTC")
    hours = [0, 1, 25, 26, 0]
    df = pd.DataFrame({"time": [t + pd.Timedelta(hours=h) for h in hours],
                       "region": ["A", "A", "A", "A", "B"]})
    out = add_region_activity(df)
    assert out["events_last_24h_in_region"].tolist() == [0, 1, 1, 1, 0]


class FakeResponse:
    def __init__(self, payload=None):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        if self.payload is None:
            raise ValueError("not json")
        return self.payload


def test_fetch_feed_returns_payload(monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeResponse({"features": []})

    monkeypatch.setattr(fetch.requests, "get", fake_get)
    assert fetch.fetch_feed("all_day") == {"features": []}
    assert calls == [(f"{fetch.BASE}/all_day.geojson", 15)]


def test_fetch_feed_rejects_non_json(monkeypatch):
    monkeypatch.setattr(fetch.requests, "get", lambda url, timeout: FakeResponse())
    with pytest.raises(ValueError, match="all_weak"):
        fetch.fetch_feed("all_weak")


def feature(id_, updated):
    return {"id": id_, "properties": {"mag": 1.0, "updated": updated},
            "geometry": {"coordinates": [1.0, 2.0, 3.0]}}


def test_run_stream_appends_new_rows_and_survives_failure(monkeypatch, tmp_path, capsys):
    polls = iter([
        {"features": [feature("a", 1), feature("b", 1)]},
        requests.ConnectionError("network down"),
        {"features": [feature("a", 2), feature("b", 1)]},
    ])

    def fake_fetch(feed):
        result = next(polls)
        if isinstance(result, Exception):
            raise result
        return result

    clock = {"now": 0}
    fake_time = types.SimpleNamespace(
        monotonic=lambda: clock["now"],
        sleep=lambda s: clock.update(now=clock["now"] + s))
    monkeypatch.setattr(stream, "fetch_feed", fake_fetch)
    monkeypatch.setattr(stream, "time", fake_time)

    out = tmp_path / "nested" / "stream.jsonl"
    stream.run_stream("all_hour", interval_s=10, duration_s=20, out_path=str(out))

    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(r["id"], r["updated"]) for r in rows] == [("a", 1), ("b", 1), ("a", 2)]
    printed = capsys.readouterr().out
    assert "2 new / 2 fetched" in printed
    assert "poll failed: network down" in printed
    assert "1 new / 2 fetched" in printed


def test_stream_main_passes_arguments(monkeypatch):
    seen = []
    monkeypatch.setattr(stream, "run_stream", lambda *args: seen.append(args))
    monkeypatch.setattr("sys.argv", ["stream", "--interval", "5", "--out", "x.jsonl"])
    stream.main()
    assert seen == [("all_hour", 5, 2400, "x.jsonl")]
