"""Capa puramente visual: colores/CSS del tema y helpers de render en HTML.
No contiene lógica de negocio — solo lee datos que ya le pasan las otras vistas.
"""
import html
import streamlit as st

NAVY = "#0A1630"
NAVY_CARD = "#132A52"
NAVY_CARD_LIGHT = "#1B3765"
RED = "#D6162B"
RED_DARK = "#9E0F20"
GREEN = "#2FB170"
GOLD = "#E8B93E"
INK = "#F5F7FA"
MUTED = "#8FA1C4"

# Colores oficiales por equipo (primario / secundario). Sin logos externos:
# esto evita depender de un servicio de imágenes fuera de la app.
TEAM_INFO = {
    "ARI": ("Arizona Cardinals", "#97233F", "#FFFFFF"),
    "ATL": ("Atlanta Falcons", "#A71930", "#000000"),
    "BAL": ("Baltimore Ravens", "#241773", "#9E7C0C"),
    "BUF": ("Buffalo Bills", "#00338D", "#C60C30"),
    "CAR": ("Carolina Panthers", "#0085CA", "#101820"),
    "CHI": ("Chicago Bears", "#0B162A", "#C83803"),
    "CIN": ("Cincinnati Bengals", "#FB4F14", "#000000"),
    "CLE": ("Cleveland Browns", "#472A08", "#FF3C00"),
    "DAL": ("Dallas Cowboys", "#003594", "#869397"),
    "DEN": ("Denver Broncos", "#FB4F14", "#002244"),
    "DET": ("Detroit Lions", "#0076B6", "#B0B7BC"),
    "GB": ("Green Bay Packers", "#203731", "#FFB612"),
    "HOU": ("Houston Texans", "#03202F", "#A71930"),
    "IND": ("Indianapolis Colts", "#002C5F", "#A2AAAD"),
    "JAX": ("Jacksonville Jaguars", "#101820", "#D7A22A"),
    "JAC": ("Jacksonville Jaguars", "#101820", "#D7A22A"),
    "KC": ("Kansas City Chiefs", "#E31837", "#FFB81C"),
    "LV": ("Las Vegas Raiders", "#000000", "#A5ACAF"),
    "LAC": ("Los Angeles Chargers", "#0080C6", "#FFC20E"),
    "LA": ("Los Angeles Rams", "#003594", "#FFA300"),
    "LAR": ("Los Angeles Rams", "#003594", "#FFA300"),
    "MIA": ("Miami Dolphins", "#008E97", "#FC4C02"),
    "MIN": ("Minnesota Vikings", "#4F2683", "#FFC62F"),
    "NE": ("New England Patriots", "#002244", "#C60C30"),
    "NO": ("New Orleans Saints", "#8C7A4B", "#101820"),
    "NYG": ("New York Giants", "#0B2265", "#A71930"),
    "NYJ": ("New York Jets", "#125740", "#000000"),
    "PHI": ("Philadelphia Eagles", "#004C54", "#A5ACAF"),
    "PIT": ("Pittsburgh Steelers", "#FFB612", "#101820"),
    "SEA": ("Seattle Seahawks", "#002244", "#69BE28"),
    "SF": ("San Francisco 49ers", "#AA0000", "#B3995D"),
    "TB": ("Tampa Bay Buccaneers", "#D50A0A", "#34302B"),
    "TEN": ("Tennessee Titans", "#0C2340", "#4B92DB"),
    "WAS": ("Washington Commanders", "#5A1414", "#FFB612"),
    "WSH": ("Washington Commanders", "#5A1414", "#FFB612"),
}

_AVATAR_PALETTE = [RED, "#2E6FD9", GREEN, GOLD, "#8E5FD9", "#D97A2E", "#2EA6D9", "#D92E6F"]


def get_team_meta(abbr: str):
    name, primary, secondary = TEAM_INFO.get(abbr, (abbr, "#2B3E63", MUTED))
    return {"name": name, "primary": primary, "secondary": secondary}


def _avatar_color(seed: str) -> str:
    return _AVATAR_PALETTE[sum(ord(c) for c in seed) % len(_AVATAR_PALETTE)]


def _initials(display_name: str) -> str:
    raw_parts = str(display_name).strip().split()
    parts = [p.strip("()[]{}.,\"'") for p in raw_parts]
    parts = [p for p in parts if p and p[0].isalpha()]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def inject_css():
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-size: 18px;
        }}
        .stApp {{
            background: radial-gradient(circle at top, {NAVY_CARD} 0%, {NAVY} 55%);
        }}
        #MainMenu, footer {{ visibility: hidden; }}

        /* ---------- Hero header ---------- */
        .hero {{
            background: linear-gradient(135deg, {RED_DARK} 0%, {NAVY_CARD} 70%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1.4rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }}
        .hero h1 {{
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
            color: {INK};
            letter-spacing: 0.5px;
        }}
        .hero p {{
            margin: 0.3rem 0 0 0;
            color: {MUTED};
            font-size: 1.05rem;
        }}

        .week-banner {{
            background: {NAVY_CARD};
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 6px solid {RED};
            border-radius: 14px;
            padding: 1rem 1.3rem;
            margin: 1rem 0 1.3rem 0;
            font-size: 1.3rem;
            font-weight: 700;
            color: {INK};
        }}

        .section-title {{
            font-size: 1.4rem;
            font-weight: 800;
            color: {INK};
            margin: 1.6rem 0 0.8rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        /* ---------- Botones grandes y táctiles ---------- */
        .stButton > button {{
            min-height: 3.1rem;
            font-size: 1.1rem;
            font-weight: 700;
            border-radius: 14px;
            border: 2px solid rgba(255,255,255,0.12);
            width: 100%;
        }}
        .stButton > button[kind="primary"] {{
            background: {RED};
            border-color: {RED};
        }}
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {{
            font-size: 1.1rem;
            padding: 0.6rem 0.8rem;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 1.15rem;
            font-weight: 700;
            padding: 0.8rem 1.2rem;
        }}

        /* ---------- Tarjetas de equipo ---------- */
        .matchup-card {{
            background: {NAVY_CARD};
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 1rem 1rem 0.4rem 1rem;
            margin-bottom: 1.1rem;
        }}
        .matchup-vs {{
            text-align: center;
            color: {MUTED};
            font-weight: 700;
            font-size: 0.95rem;
            letter-spacing: 2px;
            margin-bottom: 0.6rem;
        }}
        .team-card {{
            border-radius: 16px;
            padding: 1rem 0.8rem;
            text-align: center;
            border: 3px solid transparent;
            margin-bottom: 0.6rem;
            min-height: 118px;
        }}
        .team-card .abbr {{
            font-size: 1.6rem;
            font-weight: 900;
            letter-spacing: 1px;
        }}
        .team-card .name {{
            font-size: 0.95rem;
            opacity: 0.92;
            margin-top: 0.15rem;
        }}
        .team-card .rival {{
            font-size: 0.85rem;
            opacity: 0.8;
            margin-top: 0.35rem;
        }}
        .team-card .tag {{
            display: inline-block;
            margin-top: 0.45rem;
            font-size: 0.8rem;
            font-weight: 800;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
        }}
        .team-card.selected {{
            border-color: {GOLD};
            box-shadow: 0 0 0 3px rgba(232,185,62,0.25);
        }}
        .team-card.unavailable {{
            opacity: 0.45;
            filter: grayscale(35%);
        }}
        .tag.tag-selected {{ background: {GOLD}; color: #1a1400; }}
        .tag.tag-unavailable {{ background: rgba(0,0,0,0.35); color: {INK}; }}

        /* ---------- Leaderboard ---------- */
        .board {{
            background: {NAVY_CARD};
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            overflow: hidden;
        }}
        .board-row {{
            display: flex;
            align-items: center;
            gap: 0.9rem;
            padding: 0.85rem 1.1rem;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        .board-row:last-child {{ border-bottom: none; }}
        .board-row.eliminated {{ opacity: 0.55; }}
        .avatar {{
            flex-shrink: 0;
            width: 46px;
            height: 46px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1rem;
            color: #ffffff;
        }}
        .board-info {{
            flex-grow: 1;
            min-width: 0;
        }}
        .board-name {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {INK};
            overflow-wrap: break-word;
        }}
        .board-row.eliminated .board-name {{
            text-decoration: line-through;
            color: {MUTED};
        }}
        .board-sub {{
            font-size: 0.85rem;
            color: {MUTED};
            font-weight: 500;
        }}
        .status-pill {{
            flex-shrink: 0;
            font-size: 0.85rem;
            font-weight: 800;
            padding: 0.35rem 0.8rem;
            border-radius: 999px;
            white-space: nowrap;
        }}
        .status-pill.alive {{ background: rgba(47,177,112,0.18); color: {GREEN}; border: 1px solid {GREEN}; }}
        .status-pill.out {{ background: rgba(214,22,43,0.18); color: #ff6b7a; border: 1px solid {RED}; }}

        /* ---------- Reveal de fin de semana ---------- */
        .reveal-row {{
            display: flex;
            align-items: center;
            gap: 0.9rem;
            padding: 0.85rem 1.1rem;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        .reveal-row:last-child {{ border-bottom: none; }}
        .reveal-name {{
            flex-grow: 1;
            min-width: 0;
            font-size: 1.1rem;
            font-weight: 700;
            color: {INK};
        }}
        .reveal-team {{
            flex-shrink: 0;
            font-size: 0.95rem;
            font-weight: 800;
            color: {MUTED};
        }}
        .result-pill {{
            flex-shrink: 0;
            font-size: 0.85rem;
            font-weight: 800;
            padding: 0.35rem 0.8rem;
            border-radius: 999px;
            white-space: nowrap;
        }}
        .result-pill.win {{ background: rgba(47,177,112,0.18); color: {GREEN}; border: 1px solid {GREEN}; }}
        .result-pill.loss {{ background: rgba(214,22,43,0.18); color: #ff6b7a; border: 1px solid {RED}; }}
        .result-pill.tie {{ background: rgba(232,185,62,0.18); color: {GOLD}; border: 1px solid {GOLD}; }}

        .privacy-note {{
            color: {MUTED};
            font-size: 0.95rem;
            font-style: italic;
            margin: 0.6rem 0 1.2rem 0;
        }}

        /* ---------- Responsive: celulares y pantallas angostas ---------- */
        html, body {{ overflow-x: hidden; }}
        @media (max-width: 640px) {{
            [data-testid="stMainBlockContainer"], .block-container {{
                padding-left: 0.9rem !important;
                padding-right: 0.9rem !important;
                padding-top: 1.2rem !important;
            }}
            .hero {{
                padding: 1.2rem 1.2rem;
                border-radius: 16px;
            }}
            .hero h1 {{
                font-size: 1.4rem;
                line-height: 1.25;
            }}
            .hero p {{
                font-size: 0.95rem;
            }}
            .week-banner {{
                font-size: 1.1rem;
                padding: 0.85rem 1rem;
            }}
            .section-title {{
                font-size: 1.2rem;
            }}
            .matchup-card {{
                padding: 0.8rem 0.8rem 0.2rem 0.8rem;
            }}
            .team-card {{
                min-height: 100px;
                padding: 0.9rem 0.7rem;
            }}
            .team-card .abbr {{
                font-size: 1.8rem;
            }}
            .stTabs [data-baseweb="tab"] {{
                font-size: 0.95rem;
                padding: 0.7rem 0.6rem;
            }}
            .board-row, .reveal-row {{
                padding: 0.75rem 0.85rem;
                gap: 0.6rem;
            }}
            .avatar {{
                width: 38px;
                height: 38px;
                font-size: 0.85rem;
            }}
            .board-name, .reveal-name {{
                font-size: 1rem;
                min-width: 0;
                overflow-wrap: break-word;
            }}
            .status-pill, .result-pill {{
                font-size: 0.75rem;
                padding: 0.3rem 0.6rem;
            }}
            .reveal-team {{
                font-size: 0.85rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(subtitle: str):
    # Nota: todo el HTML va en una sola línea (sin saltos de línea internos) a
    # propósito. Si Markdown ve una línea en blanco dentro de un bloque HTML
    # crudo, corta el bloque ahí y el resto se muestra como texto sin estilo
    # — y una interpolación vacía en su propia línea produce justo eso.
    st.markdown(
        f'<div class="hero"><h1>🏈 NFL Survivor 2026/27</h1><p>{html.escape(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def render_week_banner(week: int):
    st.markdown(f'<div class="week-banner">📅 Semana {week}</div>', unsafe_allow_html=True)


def render_team_card_html(abbr: str, rival: str, prefix: str, available: bool, selected: bool):
    meta = get_team_meta(abbr)
    classes = "team-card"
    if selected:
        classes += " selected"
    if not available:
        classes += " unavailable"

    if selected:
        tag_html = '<span class="tag tag-selected">✅ Seleccionado</span>'
    elif not available:
        tag_html = '<span class="tag tag-unavailable">🚫 No disponible</span>'
    else:
        tag_html = ""

    style = (
        f"background: linear-gradient(160deg, {meta['primary']} 0%, {meta['secondary']} 140%); "
        f"color: #ffffff;"
    )
    st.markdown(
        f'<div class="{classes}" style="{style}">'
        f'<div class="abbr">{html.escape(abbr)}</div>'
        f'<div class="name">{html.escape(meta["name"])}</div>'
        f'<div class="rival">{html.escape(prefix)} {html.escape(str(rival))}</div>'
        f'{tag_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_leaderboard(board_rows):
    """board_rows: lista de dicts {display_name, alive(bool), eliminated_week}"""
    rows_html = []
    for row in board_rows:
        name = str(row["display_name"])
        alive = row["alive"]
        elim_week = row.get("eliminated_week", "")
        row_class = "board-row" if alive else "board-row eliminated"
        pill_class = "status-pill alive" if alive else "status-pill out"
        pill_text = "✅ Vivo" if alive else "❌ Eliminado"
        sub = ""
        if not alive and elim_week not in ("", None):
            sub = f'<div class="board-sub">Eliminado en semana {html.escape(str(elim_week))}</div>'
        # Todo en una sola línea (sin saltos internos): una línea en blanco dentro de
        # un bloque HTML crudo de Markdown lo corta ahí y el resto se muestra como
        # texto literal — y eso incluye la línea que queda en blanco cuando `sub`
        # está vacío (usuarios vivos no tienen semana de eliminación).
        rows_html.append(
            f'<div class="{row_class}">'
            f'<div class="avatar" style="background:{_avatar_color(name)};">{html.escape(_initials(name))}</div>'
            f'<div class="board-info"><div class="board-name">{html.escape(name)}</div>{sub}</div>'
            f'<div class="{pill_class}">{pill_text}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="board">{"".join(rows_html)}</div>', unsafe_allow_html=True)


_RESULT_META = {
    "win": ("win", "✅ Ganó"),
    "loss": ("loss", "❌ Perdió"),
    "tie": ("tie", "➖ Empate"),
}


def render_week_reveal(reveal_rows):
    """reveal_rows: lista de dicts {display_name, team, result}. Solo llamar
    cuando ya terminó la semana (is_week_complete)."""
    rows_html = []
    for row in reveal_rows:
        name = str(row["display_name"])
        team = str(row["team"])
        result_key = str(row.get("result", "")).lower()
        pill_class, pill_text = _RESULT_META.get(result_key, ("tie", "⏳ Pendiente"))
        rows_html.append(
            f'<div class="reveal-row">'
            f'<div class="avatar" style="background:{_avatar_color(name)};">{html.escape(_initials(name))}</div>'
            f'<div class="reveal-name">{html.escape(name)}</div>'
            f'<div class="reveal-team">{html.escape(team)}</div>'
            f'<div class="result-pill {pill_class}">{pill_text}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="board">{"".join(rows_html)}</div>', unsafe_allow_html=True)


def render_privacy_note(text: str):
    st.markdown(f'<div class="privacy-note">🔒 {html.escape(text)}</div>', unsafe_allow_html=True)
