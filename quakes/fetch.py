"""Task 1: fetch the USGS GeoJSON feed and turn it into a DataFrame."""
import pandas as pd
import requests

BASE = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"


def fetch_feed(feed: str = "all_week") -> dict:
    """GET {BASE}/{feed}.geojson and return the parsed dict.

    Use a timeout and raise_for_status(). A misspelled feed name returns
    HTTP 200 with a plain-text body, so raise a clear error if the body
    is not valid JSON.
    """
    resp = requests.get(f"{BASE}/{feed}.geojson", timeout=15)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError as exc:
        raise ValueError(
            f"Feed {feed!r} did not return JSON; check the feed name") from exc


def geojson_to_df(payload: dict) -> pd.DataFrame:
    """One row per event.

    Columns: 'id' (top level of each feature), every key in 'properties',
    plus 'lon', 'lat', 'depth_km' from geometry.coordinates = [lon, lat, depth].
    """
    rows = []
    for feature in payload["features"]:
        lon, lat, depth_km = feature["geometry"]["coordinates"]
        rows.append({"id": feature["id"], **feature["properties"],
                     "lon": lon, "lat": lat, "depth_km": depth_km})
    return pd.DataFrame(rows)
