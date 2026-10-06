"""Task 5: run the whole pipeline end to end.

Steps (see LAB_GUIDE.md):
 1. fetch all_week (fall back to config.FALLBACK_PATH if the network fails)
 2. merge any data/stream/*.jsonl rows, then dedupe_latest
 3. clean, engineer features, drop leaky columns
 4. split, fit_transform on train only, transform test
 5. print the report, save train.csv, test.csv, preprocessor.joblib
"""
import argparse
import json

import joblib
import pandas as pd
import requests

from . import config
from .cleaning import clean, dedupe_latest
from .features import (add_location_features, add_quality_features,
                       add_region_activity, add_target, add_time_features,
                       drop_leaky_columns, group_rare)
from .fetch import fetch_feed, geojson_to_df
from .transform import SCALERS, build_preprocessor, split_data


def load_raw() -> pd.DataFrame:
    try:
        payload = fetch_feed("all_week")
    except (requests.RequestException, ValueError) as exc:
        print(f"Live fetch failed ({exc}); using {config.FALLBACK_PATH}")
        payload = json.loads(config.FALLBACK_PATH.read_text(encoding="utf-8"))
    return geojson_to_df(payload)


def load_stream() -> pd.DataFrame:
    frames = [pd.read_json(path, lines=True, convert_dates=False, dtype=False)
              for path in sorted(config.STREAM_DIR.glob("*.jsonl"))
              if path.stat().st_size]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def to_frame(pre, X, source: pd.DataFrame) -> pd.DataFrame:
    """Transformed features plus the target and 'mag' (kept for Day 3)."""
    out = pd.DataFrame(X, columns=pre.get_feature_names_out(), index=source.index)
    out["mag"] = source["mag"]
    out[config.TARGET] = source[config.TARGET]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the model-ready quake dataset.")
    parser.add_argument("--scaler", default="robust", choices=sorted(SCALERS))
    args = parser.parse_args()

    raw = load_raw()
    stream = load_stream()
    merged = pd.concat([raw, stream], ignore_index=True)
    changed = int((merged.groupby("id")["updated"].nunique() > 1).sum())
    deduped = dedupe_latest(merged)

    df = clean(deduped)
    df = add_time_features(df)
    df = add_quality_features(df)
    df = add_location_features(df)
    df = add_region_activity(df)
    df["region"] = group_rare(df["region"])
    df = add_target(df)
    df = drop_leaky_columns(df)

    X_train, X_test, y_train, y_test = split_data(df)
    pre = build_preprocessor(args.scaler)
    Xtr = pre.fit_transform(X_train)
    Xte = pre.transform(X_test)

    print(f"raw rows:                 {len(raw)}")
    print(f"stream rows merged:       {len(stream)}")
    print(f"events with new 'updated': {changed}")
    print(f"rows after dedupe:        {len(deduped)}")
    print(f"rows after cleaning:      {len(df)}")
    print(f"train shape:              {Xtr.shape}")
    print(f"test shape:               {Xte.shape}")
    print(f"positive rate train/test: {y_train.mean():.3f} / {y_test.mean():.3f}")

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    to_frame(pre, Xtr, df.loc[X_train.index]).to_csv(
        config.PROCESSED_DIR / "train.csv", index=False)
    to_frame(pre, Xte, df.loc[X_test.index]).to_csv(
        config.PROCESSED_DIR / "test.csv", index=False)
    joblib.dump(pre, config.PROCESSED_DIR / "preprocessor.joblib")
    print(f"saved to {config.PROCESSED_DIR}")


if __name__ == "__main__":
    main()
