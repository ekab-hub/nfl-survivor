import pandas as pd
from datetime import datetime, timezone
from sheets_db import read_tab, append_row, update_cells_by_match, delete_row_by_match


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
    has_existing = False
    if not picks.empty:
        mask = (picks["username"] == username) & (picks["week"].astype(str) == str(week))
        if mask.any():
            has_existing = True
            old_team = picks.loc[mask, "team"].iloc[0]

    # Antes esto leía TODA la pestaña Picks, la modificaba en memoria y la
    # reescribía completa con overwrite_tab — con carga real (varios jugadores
    # picando casi al mismo tiempo, ej. antes del kickoff del domingo) eso
    # pierde picks: el último overwrite_tab en llegar pisa lo que hayan
    # guardado los demás mientras tanto. append_row es atómico (nunca pisa
    # filas existentes), y para reemplazar un pick ya existente solo tocamos
    # esa fila puntual.
    if has_existing:
        update_cells_by_match(
            "Picks", {"username": username, "week": week},
            {"team": team, "timestamp": now, "result": "pending"},
        )
    else:
        append_row("Picks", [username, week, team, now, "pending"])

    # Si el usuario cambió de equipo esta misma semana, el equipo anterior nunca
    # se llegó a jugar: hay que liberarlo para que no quede marcado como usado.
    if old_team is not None and old_team != team:
        delete_row_by_match("Teams_Used", {"username": username, "team": old_team, "week": week})

    teams_used = read_tab("Teams_Used")
    already = False
    if not teams_used.empty:
        already = ((teams_used["username"] == username) & (teams_used["team"] == team)).any()
    if not already:
        append_row("Teams_Used", [username, team, week])