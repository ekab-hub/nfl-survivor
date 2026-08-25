import pandas as pd
from datetime import datetime, timezone
from sheets_db import read_tab, append_row, overwrite_tab


def get_available_teams(username: str, week: int, games_week: pd.DataFrame) -> pd.DataFrame:
    """Regresa los partidos de la semana con una columna 'disponible' por equipo."""
    teams_used = read_tab("Teams_Used")
    used_by_user = set()
    if not teams_used.empty:
        used_by_user = set(teams_used[teams_used["username"] == username]["team"])

    now = datetime.now(timezone.utc)
    games_week = games_week.copy()
    games_week["kickoff_dt"] = pd.to_datetime(games_week["kickoff_utc"], utc=True)
    games_week["home_disponible"] = games_week.apply(
        lambda r: r["home_team"] not in used_by_user and r["kickoff_dt"] > now, axis=1
    )
    games_week["away_disponible"] = games_week.apply(
        lambda r: r["away_team"] not in used_by_user and r["kickoff_dt"] > now, axis=1
    )
    return games_week


def get_current_pick(username: str, week: int):
    picks = read_tab("Picks")
    if picks.empty:
        return None
    match = picks[(picks["username"] == username) & (picks["week"].astype(str) == str(week))]
    if match.empty:
        return None
    return match.iloc[0]


def submit_pick(username: str, week: int, team: str):
    picks = read_tab("Picks")
    now = datetime.now(timezone.utc).isoformat()

    # si ya existía un pick esta semana, lo reemplazamos (siempre que su equipo anterior no haya jugado ya)
    old_team = None
    if not picks.empty:
        mask = (picks["username"] == username) & (picks["week"].astype(str) == str(week))
        if mask.any():
            old_team = picks.loc[mask, "team"].iloc[0]
            picks = picks[~mask]

    picks = pd.concat([picks, pd.DataFrame([{
        "username": username, "week": week, "team": team, "timestamp": now, "result": "pending"
    }])], ignore_index=True)
    overwrite_tab("Picks", picks)

    teams_used = read_tab("Teams_Used")

    # Si el usuario cambió de equipo esta misma semana, el equipo anterior nunca
    # se llegó a jugar: hay que liberarlo para que no quede marcado como usado.
    if old_team is not None and old_team != team and not teams_used.empty:
        release_mask = (
            (teams_used["username"] == username)
            & (teams_used["team"] == old_team)
            & (teams_used["week"].astype(str) == str(week))
        )
        if release_mask.any():
            teams_used = teams_used[~release_mask]
            overwrite_tab("Teams_Used", teams_used)

    already = False
    if not teams_used.empty:
        already = ((teams_used["username"] == username) & (teams_used["team"] == team)).any()
    if not already:
        append_row("Teams_Used", [username, team, week])