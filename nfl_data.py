import nflreadpy as nfl
import pandas as pd
from datetime import datetime
import pytz

ET = pytz.timezone("America/New_York")


def fetch_schedule(season: int) -> pd.DataFrame:
    df = nfl.load_schedules(seasons=[season]).to_pandas()
    df = df[df["game_type"] == "REG"].copy()
    df["kickoff_utc"] = df.apply(_to_utc, axis=1)
    cols = ["week", "game_id", "home_team", "away_team", "kickoff_utc", "home_score", "away_score"]
    return df[cols]


def _to_utc(row):
    dt_str = f"{row['gameday']} {row['gametime']}"
    naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    local = ET.localize(naive)
    return local.astimezone(pytz.UTC)