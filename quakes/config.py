from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FALLBACK_PATH = ROOT / "data" / "fallback" / "all_week.geojson"
STREAM_DIR = ROOT / "data" / "stream"
PROCESSED_DIR = ROOT / "data" / "processed"

SEED = 42
TARGET = "big_quake"

NUMERIC: list[str] = [    # numeric feature columns
    "lat", "lon", "depth_km", "abs_lat", "nst", "gap", "dmin", "rms",
    "hour", "dayofweek", "update_lag_hours", "events_last_24h_in_region",
    "is_reviewed", "nst_missing", "is_shallow",
]
NOMINAL: list[str] = [    # categorical feature columns (one-hot encoded)
    "region", "net",
]
LEAKY: list[str] = [      # columns that encode the magnitude: must be dropped
    "title", "sig", "mmi", "cdi", "felt", "alert",
]
