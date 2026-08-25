import pandas as pd
from sheets_db import read_tab


def is_week_complete(games_week: pd.DataFrame) -> bool:
    """True solo cuando todos los partidos de la semana ya terminaron (status 'final')."""
    if games_week.empty:
        return False
    return bool((games_week["status"] == "final").all())


def get_team_pick_counts(week: int) -> dict:
    """Cuántos usuarios eligieron cada equipo esta semana, sin decir quiénes."""
    picks = read_tab("Picks")
    if picks.empty:
        return {}
    picks_week = picks[picks["week"].astype(str) == str(week)]
    if picks_week.empty:
        return {}
    return picks_week.groupby("team").size().to_dict()


def get_week_reveal(week: int) -> pd.DataFrame:
    """Quién jugó qué equipo y el resultado. Solo debe mostrarse cuando la semana
    ya terminó (usar junto con is_week_complete)."""
    picks = read_tab("Picks")
    if picks.empty:
        return pd.DataFrame(columns=["display_name", "team", "result"])
    picks_week = picks[picks["week"].astype(str) == str(week)].copy()
    if picks_week.empty:
        return pd.DataFrame(columns=["display_name", "team", "result"])
    users = read_tab("Users")
    merged = picks_week.merge(users[["username", "display_name"]], on="username", how="left")
    merged["display_name"] = merged["display_name"].fillna(merged["username"])
    return merged[["display_name", "team", "result"]].sort_values("display_name")
