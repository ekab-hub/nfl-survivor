import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "NFL_Survivor_2026"  # ajusta si le pusiste otro nombre


@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource
def get_sheet():
    """Se abre UNA sola vez por sesión de la app, no en cada llamada."""
    client = get_client()
    return client.open(SHEET_NAME)


@st.cache_data(ttl=30)  # comparte lecturas repetidas dentro de una ventana de 30s
def read_tab(tab_name: str) -> pd.DataFrame:
    ws = get_sheet().worksheet(tab_name)
    records = ws.get_all_records()
    return pd.DataFrame(records)


def _invalidate_cache():
    """Se llama después de cualquier escritura para que la próxima lectura sea fresca."""
    read_tab.clear()


def append_row(tab_name: str, row: list):
    ws = get_sheet().worksheet(tab_name)
    ws.append_row(row, value_input_option="USER_ENTERED")
    _invalidate_cache()


def update_cell_by_match(tab_name: str, match_col: str, match_value, target_col: str, new_value):
    """Busca la fila donde match_col == match_value y actualiza target_col."""
    ws = get_sheet().worksheet(tab_name)
    df = read_tab(tab_name)
    if match_col not in df.columns or target_col not in df.columns:
        raise ValueError(f"Columna no encontrada en {tab_name}")
    matches = df.index[df[match_col].astype(str) == str(match_value)].tolist()
    if not matches:
        return False
    row_idx = matches[0] + 2
    col_idx = df.columns.get_loc(target_col) + 1
    ws.update_cell(row_idx, col_idx, new_value)
    _invalidate_cache()
    return True


def overwrite_tab(tab_name: str, df: pd.DataFrame):
    """Reescribe toda la pestaña con un DataFrame (útil para el sync semanal)."""
    ws = get_sheet().worksheet(tab_name)
    clean_df = df.fillna("").astype(str)
    ws.clear()
    ws.update([clean_df.columns.values.tolist()] + clean_df.values.tolist())
    _invalidate_cache()