"""End-to-end run on the fallback snapshot, with the network switched off."""
import json

import joblib
import pandas as pd
import requests

from quakes import config, run
from quakes.fetch import geojson_to_df


def test_pipeline_runs_offline_and_merges_stream(monkeypatch, tmp_path, capsys):
    def no_network(feed):
        raise requests.ConnectionError("offline")

    # One stream row: a newer version of an event that is already in the snapshot.
    payload = json.loads(config.FALLBACK_PATH.read_text(encoding="utf-8"))
    newer = payload["features"][0]
    newer["properties"]["updated"] += 60_000
    stream_dir = tmp_path / "stream"
    stream_dir.mkdir()
    geojson_to_df({"features": [newer]}).to_json(
        stream_dir / "stream.jsonl", orient="records", lines=True)

    monkeypatch.setattr(run, "fetch_feed", no_network)
    monkeypatch.setattr(config, "STREAM_DIR", stream_dir)
    monkeypatch.setattr(config, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr("sys.argv", ["run"])
    run.main()

    printed = capsys.readouterr().out
    assert "Live fetch failed" in printed
    assert "stream rows merged:       1" in printed
    assert "events with new 'updated': 1" in printed

    train = pd.read_csv(tmp_path / "processed" / "train.csv")
    test = pd.read_csv(tmp_path / "processed" / "test.csv")
    assert list(train.columns) == list(test.columns)
    assert {"mag", config.TARGET} <= set(train.columns)
    assert not train.isna().any().any() and not test.isna().any().any()
    assert set(train[config.TARGET]) == {0, 1}

    pre = joblib.load(tmp_path / "processed" / "preprocessor.joblib")
    assert len(pre.get_feature_names_out()) == train.shape[1] - 2
