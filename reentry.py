from sheets_db import read_tab, update_cells_by_match


def get_user_row(username: str):
    users = read_tab("Users")
    match = users[users["username"] == username]
    if match.empty:
        return None
    return match.iloc[0]


def can_use_reentry(user_row, current_week: int, reentry_deadline_week: int) -> bool:
    is_alive = str(user_row["is_alive"]).upper() == "TRUE"
    used_reentry = str(user_row["used_reentry"]).upper() == "TRUE"
    eliminated_week = user_row.get("eliminated_week", "")

    if is_alive or used_reentry:
        return False
    if eliminated_week == "" or eliminated_week is None:
        return False

    try:
        eliminated_week = int(eliminated_week)
    except (ValueError, TypeError):
        return False

    return eliminated_week < reentry_deadline_week and current_week < reentry_deadline_week


def activate_reentry(username: str):
    # update puntual en vez de overwrite_tab sobre toda Users, para no
    # arriesgarse a pisar cambios concurrentes de otros usuarios.
    update_cells_by_match("Users", {"username": username}, {
        "is_alive": "TRUE", "used_reentry": "TRUE",
    })