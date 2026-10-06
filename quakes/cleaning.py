"""Task 3: cleaning."""
import pandas as pd


def epoch_ms_to_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Convert 'time' and 'updated' (epoch milliseconds) to UTC datetimes."""
    out = df.copy()
    for col in ("time", "updated"):
        out[col] = pd.to_datetime(out[col], unit="ms", utc=True)
    return out


def dedupe_latest(df: pd.DataFrame) -> pd.DataFrame:
    """One row per 'id', keeping the row with the greatest 'updated'."""
    return (df.sort_values("updated")
              .drop_duplicates(subset="id", keep="last")
              .sort_index())


def keep_earthquakes(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise 'type' (strip, lowercase) and keep only 'earthquake'."""
    out = df.copy()
    out["type"] = out["type"].str.strip().str.lower()
    return out[out["type"] == "earthquake"]


def extract_region(place: pd.Series) -> pd.Series:
    """Text after the last comma, or the whole string if there is no comma.
    Missing places become 'Unknown'."""
    return place.str.rsplit(",", n=1).str[-1].str.strip().fillna("Unknown")


def iqr_outlier_mask(s: pd.Series, k: float = 1.5) -> pd.Series:
    """True where a value lies outside [Q1 - k*IQR, Q3 + k*IQR]."""
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return (s < q1 - k * iqr) | (s > q3 + k * iqr)


def drop_missing_target(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where 'mag' is missing."""
    return df.dropna(subset=["mag"])


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Chain the steps above (think about the order) and add a 'region' column."""
    # Dedupe first so the latest revision of each event decides its type and mag.
    out = dedupe_latest(df)
    out = keep_earthquakes(out)
    out = drop_missing_target(out)
    out = epoch_ms_to_datetime(out)
    out["region"] = extract_region(out["place"])
    return out.reset_index(drop=True)
