"""Task 2: simulate streaming by polling a feed on a timer."""
import argparse
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from .fetch import fetch_feed, geojson_to_df


def filter_unseen(df: pd.DataFrame, seen: set) -> pd.DataFrame:
    """Return only rows whose (id, updated) pair is not in `seen`.

    Add the new pairs to `seen` (modify the set in place).
    """
    ...


def run_stream(feed: str, interval_s: int, duration_s: int, out_path: str) -> None:
    """Poll `feed` every `interval_s` seconds for `duration_s` seconds.

    Each poll: fetch, parse, keep unseen rows, append them to `out_path`
    as JSON lines, and print e.g. "[14:02:11] 3 new / 12 fetched".
    A failed poll must not stop the loop.
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    seen: set = set()
    deadline = time.monotonic() + duration_s
    while True:
        stamp = datetime.now().strftime("%H:%M:%S")
        try:
            df = geojson_to_df(fetch_feed(feed))
            new = filter_unseen(df, seen)
            if not new.empty:
                lines = new.to_json(orient="records", lines=True)
                with open(out, "a", encoding="utf-8") as f:
                    f.write(lines if lines.endswith("\n") else lines + "\n")
            print(f"[{stamp}] {len(new)} new / {len(df)} fetched")
        except (requests.RequestException, ValueError) as exc:
            print(f"[{stamp}] poll failed: {exc}")
        if time.monotonic() + interval_s > deadline:
            break
        time.sleep(interval_s)


def main() -> None:
    """argparse: --feed (default all_hour), --interval (60), --duration (2400),
    --out (data/stream/stream.jsonl), then call run_stream."""
    ...


if __name__ == "__main__":
    main()
