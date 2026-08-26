import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from nfl_data import fetch_schedule
from sheets_db import read_tab, overwrite_tab, update_cells_by_match

SEASON = 2026


@st.cache_data(ttl=3600)  # se refresca máximo una vez por hora
def sync_games():
    schedule = fetch_schedule(SEASON)
    schedule["status"] = schedule.apply(_status, axis=1)
    schedule_to_save = schedule.copy()
    schedule_to_save["kickoff_utc"] = schedule_to_save["kickoff_utc"].astype(str)
    overwrite_tab("Games", schedule_to_save)
    resolve_eliminations(schedule)

    settings = read_tab("Settings")
    week_row = settings[settings["key"] == "current_week"]
    if not week_row.empty:
        try:
            current_week = int(week_row["value"].iloc[0])
        except (ValueError, TypeError):
            current_week = None
        if current_week is not None:
            resolve_missing_picks(schedule, current_week)

    return schedule


def _status(row):
    if pd.notna(row["home_score"]) and pd.notna(row["away_score"]):
        return "final"
    return "scheduled"


def resolve_eliminations(games_df: pd.DataFrame):
    picks = read_tab("Picks")
    if picks.empty:
        return

    finals = games_df[games_df["status"] == "final"]

    for i, pick in picks.iterrows():
        if str(pick.get("result", "")) not in ("", "pending", "nan"):
            continue
        week = int(pick["week"])
        team = pick["team"]
        username = pick["username"]
        game = finals[(finals["week"] == week) & ((finals["home_team"] == team) | (finals["away_team"] == team))]
        if game.empty:
            continue
        g = game.iloc[0]
        if g["home_team"] == team:
            team_score, opp_score = g["home_score"], g["away_score"]
        else:
            team_score, opp_score = g["away_score"], g["home_score"]

        # convertir a número de forma segura (vienen como string desde el Sheet)
        try:
            team_score = float(team_score)
            opp_score = float(opp_score)
        except (ValueError, TypeError):
            continue  # no hay marcador todavía, se resuelve después

        if team_score > opp_score:
            result = "win"
        elif team_score == opp_score:
            result = "tie"
        else:
            result = "loss"

        # Antes se acumulaban todos los cambios en memoria y se hacía UN SOLO
        # overwrite_tab al final para Picks y Users. Se confirmó con carga
        # real que overwrite_tab (leer TODA la pestaña, reescribir TODA la
        # pestaña) puede perder o incluso BORRAR POR COMPLETO datos de otros
        # usuarios si hay una escritura concurrente en el medio — se
        # reprodujo en pruebas: una corrida con usuarios concurrentes borró
        # los picks de toda la temporada. Actualizamos cada fila puntual.
        update_cells_by_match("Picks", {"username": username, "week": week}, {"result": result})

        if result == "loss":
            update_cells_by_match("Users", {"username": username}, {
                "is_alive": "FALSE", "eliminated_week": str(week),
            })


def resolve_missing_picks(games_df: pd.DataFrame, current_week: int):
    """Elimina automáticamente a los usuarios vivos que no hicieron pick esta
    semana, una vez que ya arrancaron TODOS los partidos de la semana (ya no
    queda ningún equipo disponible para elegir)."""
    week_games = games_df[games_df["week"] == current_week]
    if week_games.empty:
        return

    now = datetime.now(timezone.utc)
    kickoffs = pd.to_datetime(week_games["kickoff_utc"], utc=True)
    if not (kickoffs <= now).all():
        return  # todavía hay partidos de la semana sin empezar

    users = read_tab("Users")
    if users.empty:
        return

    alive_mask = users["is_alive"].astype(str).str.upper() == "TRUE"
    if not alive_mask.any():
        return

    picks = read_tab("Picks")
    picked_usernames = set()
    if not picks.empty:
        week_picks = picks[picks["week"].astype(str) == str(current_week)]
        picked_usernames = set(week_picks["username"])

    missing_mask = alive_mask & ~users["username"].isin(picked_usernames)
    if not missing_mask.any():
        return

    # Un update puntual por usuario en vez de overwrite_tab sobre toda la
    # pestaña Users (mismo motivo: evitar pisar/borrar cambios concurrentes
    # de otros usuarios, ej. alguien activando su reentry al mismo tiempo).
    for username in users.loc[missing_mask, "username"]:
        update_cells_by_match("Users", {"username": username}, {
            "is_alive": "FALSE", "eliminated_week": str(current_week),
        })
