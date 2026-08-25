import streamlit as st
from sheets_db import read_tab, overwrite_tab


def is_admin(username: str) -> bool:
    users = read_tab("Users")
    match = users[users["username"] == username]
    if match.empty:
        return False
    return str(match.iloc[0].get("is_admin", "")).upper() == "TRUE"


def render_admin_panel():
    st.divider()
    with st.expander("⚙️ Panel de administrador"):
        settings = read_tab("Settings")
        current_week_row = settings[settings["key"] == "current_week"]
        current_week = int(current_week_row["value"].iloc[0]) if not current_week_row.empty else 1

        new_week = st.number_input("Semana actual", min_value=1, max_value=18, value=current_week, step=1)
        if st.button("Actualizar semana"):
            idx = settings.index[settings["key"] == "current_week"]
            settings.loc[idx, "value"] = str(new_week)
            overwrite_tab("Settings", settings)
            st.success(f"Semana actualizada a {new_week}")
            st.rerun()

        st.write("#### Vista rápida de usuarios")
        st.dataframe(read_tab("Users"), use_container_width=True)