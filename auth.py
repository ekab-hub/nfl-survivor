import bcrypt
import streamlit as st
from sheets_db import read_tab, append_row


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def register_user(username: str, password: str, display_name: str) -> tuple[bool, str]:
    users = read_tab("Users")
    if not users.empty and username in users["username"].values:
        return False, "Ese usuario ya existe. Elige otro."
    append_row("Users", [
        username,
        hash_password(password),
        display_name,
        "TRUE",   # is_alive
        "FALSE",  # used_reentry
        "",       # eliminated_week
    ])
    return True, "Registro exitoso. Ya puedes iniciar sesión."


def login_user(username: str, password: str) -> tuple[bool, str]:
    users = read_tab("Users")
    if users.empty or username not in users["username"].values:
        return False, "Usuario no encontrado."
    row = users[users["username"] == username].iloc[0]
    if check_password(password, row["password_hash"]):
        return True, row["display_name"]
    return False, "Contraseña incorrecta."