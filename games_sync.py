import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from nfl_data import fetch_schedule
from sheets_db import read_tab, overwrite_tab

SEASON = 2026


@st.cache_data(ttl=3600)  # se refresca máximo una vez por hora
def sync_games():
    schedule = fetch_schedule(SEASON)
    schedule["status"] = schedule.apply(_status, axis=1)
    schedule_to_save = schedule.copy()
    schedule_to_save["kickoff_utc"] = schedule_to_save["kickoff_utc"].astype(str)
    overwrite_tab("Games", schedule_to_save)
    resolve_eliminations(schedule)
    return schedule


def _status(row):
    if pd.notna(row["home_score"]) and pd.notna(row["away_score"]):
        return "final"
    return "scheduled"


def resolve_eliminations(games_df: pd.DataFrame):
    picks = read_tab("Picks")
    users = read_tab("Users")
    if picks.empty:
        return

    finals = games_df[games_df["status"] == "final"]
    picks["result"] = picks.get("result", "")
    changed = False

    for i, pick in picks.iterrows():
        if str(pick["result"]) not in ("", "pending", "nan"):
            continue
        week = int(pick["week"])
        team = pick["team"]
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

        picks.at[i, "result"] = result
        changed = True

        if result == "loss":
            u_idx = users.index[users["username"] == pick["username"]]
            if len(u_idx):
                users.loc[u_idx, "is_alive"] = "FALSE"
                users.loc[u_idx, "eliminated_week"] = str(week)

    if changed:
        overwrite_tab("Picks", picks)
        overwrite_tab("Users", users)
