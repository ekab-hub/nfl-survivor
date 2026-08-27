import streamlit as st
from auth import register_user, login_user
from games_sync import sync_games
from picks import get_available_teams, get_current_pick, submit_pick
from reentry import get_user_row, can_use_reentry, activate_reentry
from admin import is_admin, render_admin_panel
from sheets_db import read_tab
from week_reveal import is_week_complete, get_week_reveal
from theme import (
    inject_css, render_hero, render_week_banner, render_team_card_html,
    render_leaderboard, render_week_reveal, render_privacy_note,
)

st.set_page_config(page_title="NFL Survivor 2026", page_icon="🏈", layout="centered")
inject_css()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.display_name = None

if not st.session_state.logged_in:
    render_hero("Inicia sesión o regístrate para hacer tu pick de la semana.")

    with st.container(border=True):
        tab_login, tab_register = st.tabs(["🔑 Iniciar sesión", "📝 Registrarme"])

        with tab_login:
            u = st.text_input("Usuario", key="login_u")
            p = st.text_input("Contraseña", type="password", key="login_p")
            if st.button("Entrar", type="primary"):
                ok, msg = login_user(u, p)
                if ok:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.display_name = msg
                    st.rerun()
                else:
                    st.error(msg)

        with tab_register:
            new_u = st.text_input("Usuario", key="reg_u")
            new_p = st.text_input("Contraseña", type="password", key="reg_p")
            if st.button("Crear cuenta", type="primary"):
                if not new_u or not new_p:
                    st.error("Llena todos los campos.")
                else:
                    ok, msg = register_user(new_u, new_p, new_u)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

else:
    render_hero(f"Sesión iniciada como {st.session_state.display_name}")

    settings = read_tab("Settings")
    current_week = int(settings[settings["key"] == "current_week"]["value"].iloc[0])
    reentry_deadline = int(settings[settings["key"] == "reentry_deadline_week"]["value"].iloc[0])

    render_week_banner(current_week)

    user_row = get_user_row(st.session_state.username)

    if user_row is not None and can_use_reentry(user_row, current_week, reentry_deadline):
        st.warning("Fuiste eliminado, pero todavía puedes usar tu vida extra (reentry).")
        if st.button("🔄 Activar reentry y seguir jugando", type="primary"):
            activate_reentry(st.session_state.username)
            st.success("¡Reentry activado! Ya puedes elegir equipo esta semana.")
            st.rerun()
        st.stop()

    if user_row is not None and str(user_row["is_alive"]).upper() != "TRUE":
        st.error("Fuiste eliminado y ya no tienes reentry disponible. ¡Gracias por jugar!")
        st.stop()

    with st.spinner("Sincronizando calendario NFL..."):
        all_games = sync_games()

    games_week = all_games[all_games["week"] == current_week]

    if games_week.empty:
        st.warning("No hay partidos cargados para esta semana todavía.")
    else:
        games_week = get_available_teams(st.session_state.username, current_week, games_week)
        current_pick = get_current_pick(st.session_state.username, current_week)
        current_team = current_pick["team"] if current_pick is not None else None

        st.markdown('<div class="section-title">🎯 Elige tu equipo de la semana</div>', unsafe_allow_html=True)

        # Misma info que antes (equipo, rival, disponibilidad) — solo cambia cómo se muestra.
        options = []
        for _, g in games_week.iterrows():
            for side in ["home", "away"]:
                team = g[f"{side}_team"]
                disponible = g[f"{side}_disponible"] or team == current_team
                rival = g["away_team"] if side == "home" else g["home_team"]
                prefix = "vs" if side == "home" else "@"
                options.append({"team": team, "disponible": disponible, "rival": rival, "prefix": prefix})

        pending_key = f"pending_pick__{st.session_state.username}__{current_week}"
        if pending_key not in st.session_state:
            # Si ya tenía un pick confirmado esta semana lo mostramos seleccionado;
            # si no, no preseleccionamos nada — que el usuario elija a propósito.
            default_team = current_team if any(o["team"] == current_team for o in options) else None
            st.session_state[pending_key] = default_team

        for _, g in games_week.iterrows():
            st.markdown('<div class="matchup-card">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="matchup-vs">{g["home_team"]}  vs  {g["away_team"]}</div>',
                unsafe_allow_html=True,
            )
            col_home, col_away = st.columns(2)
            for col, side in [(col_home, "home"), (col_away, "away")]:
                with col:
                    team = g[f"{side}_team"]
                    opt = next(o for o in options if o["team"] == team)
                    selected = st.session_state[pending_key] == team
                    render_team_card_html(team, opt["rival"], opt["prefix"], opt["disponible"], selected)
                    btn_label = "Seleccionado ✅" if selected else "Elegir este equipo"
                    if st.button(
                        btn_label,
                        key=f"pick_btn_{team}_{current_week}",
                        type="primary" if selected else "secondary",
                    ):
                        st.session_state[pending_key] = team
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        selected_team = st.session_state[pending_key]
        selected_opt = next((o for o in options if o["team"] == selected_team), None)
        is_valid = selected_opt["disponible"] if selected_opt else False

        if selected_team is None:
            st.info("Selecciona un equipo para continuar.")
        elif selected_team == current_team:
            st.button("✅ Pick confirmado", disabled=True)
        elif not is_valid:
            st.error("Ese equipo ya no está disponible (ya lo usaste o su partido ya empezó).")
        else:
            if st.button("✅ Confirmar pick", type="primary"):
                submit_pick(st.session_state.username, current_week, selected_team)
                st.success(f"Pick confirmado: {selected_team}")
                st.rerun()

        st.markdown('<div class="section-title">🔒 Picks de la semana</div>', unsafe_allow_html=True)
        if is_week_complete(games_week):
            reveal_rows = get_week_reveal(current_week).to_dict("records")
            if reveal_rows:
                render_week_reveal(reveal_rows)
            else:
                st.info("Nadie hizo pick esta semana.")
        else:
            render_privacy_note(
                "Los picks de los demás jugadores son privados. Se revelan automáticamente "
                "(con nombre y resultado) cuando terminan todos los partidos de la semana."
            )

    st.divider()
    st.markdown('<div class="section-title">🏆 Tabla general</div>', unsafe_allow_html=True)
    users = read_tab("Users")
    board_rows = [
        {
            "display_name": u["display_name"],
            "alive": str(u["is_alive"]).upper() == "TRUE",
            "eliminated_week": u.get("eliminated_week", ""),
        }
        for _, u in users.iterrows()
    ]
    board_rows.sort(key=lambda r: not r["alive"])
    render_leaderboard(board_rows)

    if is_admin(st.session_state.username):
        render_admin_panel()

    st.divider()
    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.rerun()
