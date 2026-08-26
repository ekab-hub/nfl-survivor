import time
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "NFL_Survivor_2026"  # ajusta si le pusiste otro nombre


def _with_retry(fn, *args, max_retries=5, base_delay=2.0, **kwargs):
    """Reintenta con backoff exponencial ante 429 (cuota excedida) de Sheets.
    Confirmado con carga real en pruebas: tanto la cuota de lectura como la de
    escritura (60/min cada una) se agotan con facilidad si varios jugadores
    usan la app casi al mismo tiempo (ej. todos picando antes del kickoff del
    domingo). Sin esto, esos picks fallarían silenciosamente con un error 429."""
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except gspread.exceptions.APIError as e:
            is_quota = "429" in str(e) or "Quota exceeded" in str(e)
            if not is_quota or attempt == max_retries:
                raise
            time.sleep(base_delay * (2 ** attempt))


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


@st.cache_resource
def get_worksheet(tab_name: str):
    """gspread's Spreadsheet.worksheet() hace un fetch_sheet_metadata() -una
    llamada real a la API- cada vez que se invoca, sin cache propio. Como se
    llamaba en cada read_tab/append_row/overwrite_tab, cada operación gastaba
    una llamada extra de cuota de lectura además de la operación real.
    Cacheamos el Worksheet por pestaña para que esa resolución de metadata
    ocurra como máximo una vez por pestaña."""
    return _with_retry(get_sheet().worksheet, tab_name)


@st.cache_data(ttl=30)  # comparte lecturas repetidas dentro de una ventana de 30s
def read_tab(tab_name: str) -> pd.DataFrame:
    ws = get_worksheet(tab_name)
    records = _with_retry(ws.get_all_records)
    return pd.DataFrame(records)


def _invalidate_cache():
    """Se llama después de cualquier escritura para que la próxima lectura sea fresca."""
    read_tab.clear()


def append_row(tab_name: str, row: list):
    ws = get_worksheet(tab_name)
    _with_retry(ws.append_row, row, value_input_option="USER_ENTERED")
    _invalidate_cache()


def update_cell_by_match(tab_name: str, match_col: str, match_value, target_col: str, new_value):
    """Busca la fila donde match_col == match_value y actualiza target_col."""
    ws = get_worksheet(tab_name)
    df = read_tab(tab_name)
    if match_col not in df.columns or target_col not in df.columns:
        raise ValueError(f"Columna no encontrada en {tab_name}")
    matches = df.index[df[match_col].astype(str) == str(match_value)].tolist()
    if not matches:
        return False
    row_idx = matches[0] + 2
    col_idx = df.columns.get_loc(target_col) + 1
    _with_retry(ws.update_cell, row_idx, col_idx, new_value)
    _invalidate_cache()
    return True


def update_cells_by_match(tab_name: str, match: dict, updates: dict):
    """Busca la ÚNICA fila que cumple todas las condiciones en `match` y
    actualiza solo las columnas de `updates`, celda por celda — SIN reescribir
    el resto de la pestaña. Se confirmó con carga real (14 usuarios picando
    casi al mismo tiempo) que overwrite_tab en un pick (leer TODA la pestaña,
    modificar, reescribir TODA la pestaña) pierde ~90% de los picks: el
    último overwrite_tab en llegar pisa lo que hayan guardado los demás
    mientras tanto."""
    ws = get_worksheet(tab_name)
    df = read_tab(tab_name)
    for col in match:
        if col not in df.columns:
            raise ValueError(f"Columna no encontrada en {tab_name}: {col}")
    mask = pd.Series(True, index=df.index)
    for col, val in match.items():
        mask &= (df[col].astype(str) == str(val))
    matches = df.index[mask].tolist()
    if not matches:
        return False
    row_idx = matches[0] + 2
    for col, val in updates.items():
        col_idx = df.columns.get_loc(col) + 1
        _with_retry(ws.update_cell, row_idx, col_idx, val)
    _invalidate_cache()
    return True


def delete_row_by_match(tab_name: str, match: dict):
    """Borra la ÚNICA fila que cumple todas las condiciones en `match`, sin
    reescribir el resto de la pestaña (mismo motivo que update_cells_by_match:
    evitar pisar filas de otros usuarios escritas concurrentemente)."""
    ws = get_worksheet(tab_name)
    df = read_tab(tab_name)
    for col in match:
        if col not in df.columns:
            return False
    mask = pd.Series(True, index=df.index)
    for col, val in match.items():
        mask &= (df[col].astype(str) == str(val))
    matches = df.index[mask].tolist()
    if not matches:
        return False
    row_idx = matches[0] + 2
    _with_retry(ws.delete_rows, row_idx)
    _invalidate_cache()
    return True


def overwrite_tab(tab_name: str, df: pd.DataFrame):
    """Reescribe toda la pestaña con un DataFrame (útil para el sync semanal)."""
    ws = get_worksheet(tab_name)
    clean_df = df.fillna("").astype(str)
    _with_retry(ws.clear)
    _with_retry(ws.update, [clean_df.columns.values.tolist()] + clean_df.values.tolist())
    _invalidate_cache()