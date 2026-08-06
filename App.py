import calendar
from datetime import datetime, date, timedelta
import json
from pathlib import Path
import streamlit as st

# Speicherdatei-Pfad
DATEI = Path(__file__).with_name("patho_rotation.json")

STANDARD_PERSONEN = ["Moritz", "Lissi", "Veronika"]
START_DATUM = date(2026, 8, 6)


# ---------------------------------------------------------
# Datenhaltung
# ---------------------------------------------------------
def lade_daten():
    if DATEI.exists():
        try:
            return json.loads(DATEI.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "personen": STANDARD_PERSONEN,
        "ausfaelle": [],
        "manuelle_anpassungen": {},
    }


def speichere_daten(daten):
    DATEI.write_text(
        json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8"
    )


daten = lade_daten()


# ---------------------------------------------------------
# Rotations-Logik
# ---------------------------------------------------------
def alle_donnerstage_bis(ziel_datum: date):
    aktuell = START_DATUM
    donnerstage = []
    while aktuell <= ziel_datum:
        donnerstage.append(aktuell)
        aktuell += timedelta(days=7)
    return donnerstage


def berechne_rotation_fuer_datum(ziel_datum: date, daten: dict):
    if ziel_datum.weekday() != 3:
        return None

    ziel_str = ziel_datum.isoformat()
    alle_ststage = alle_donnerstage_bis(ziel_datum)
    personen = daten.get("personen", STANDARD_PERSONEN)
    n = len(personen)

    aktiver_index = 0

    for d in alle_ststage:
        d_str = d.isoformat()
        ist_ausfall = d_str in daten.get("ausfaelle", [])

        if d_str in daten.get("manuelle_anpassungen", {}):
            man_mod = daten["manuelle_anpassungen"][d_str]["mod"]
            if man_mod in personen:
                aktiver_index = personen.index(man_mod)

        if d == ziel_datum:
            if ist_ausfall:
                return {
                    "datum": ziel_datum,
                    "ausfall": True,
                    "mod": "-",
                    "proto": "-",
                    "pause": "-",
                    "manuell": ziel_str in daten.get("manuelle_anpassungen", {}),
                }

            if ziel_str in daten.get("manuelle_anpassungen", {}):
                anpassung = daten["manuelle_anpassungen"][ziel_str]
                return {
                    "datum": ziel_datum,
                    "ausfall": False,
                    "mod": anpassung["mod"],
                    "proto": anpassung["proto"],
                    "pause": anpassung["pause"],
                    "manuell": True,
                }

            mod = personen[aktiver_index % n]
            proto = personen[(aktiver_index + 1) % n]
            pause = personen[(aktiver_index + 2) % n]

            return {
                "datum": ziel_datum,
                "ausfall": False,
                "mod": mod,
                "proto": proto,
                "pause": pause,
                "manuell": False,
            }

        if not ist_ausfall:
            aktiver_index += 1


# ---------------------------------------------------------
# Page Setup & Exact Dark CSS (Matching Screenshot)
# ---------------------------------------------------------
st.set_page_config(
    page_title="NXP ServiceMGMT Meeting Rotation",
    page_icon="📅",
    layout="centered",
)

st.markdown(
    """
<style>
    /* Dunkler Theme Hintergrund */
    .stApp {
        background-color: #262524;
        color: #FFFFFF;
    }

    /* Streamlit Padding minimieren */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 650px !important;
    }

    /* Überschrift */
    .header-title {
        color: #FFFFFF;
        font-weight: 700;
        font-size: 1.8rem;
        margin-bottom: 20px;
        letter-spacing: -0.5px;
    }

    .month-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
    }

    /* Pfeilbuttons oben rechts */
    div[data-testid="stHorizontalBlock"] div.stButton > button {
        border-radius: 6px !important;
        background-color: #333230 !important;
        color: #E0E0E0 !important;
        border: 1px solid #444240 !important;
        font-weight: bold !important;
        height: 32px !important;
        width: 32px !important;
        padding: 0 !important;
    }
    div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
        background-color: #444240 !important;
        color: #FFFFFF !important;
    }

    /* Trennstriche */
    .cal-divider {
        border-bottom: 1px solid #3A3836;
        margin: 12px 0 16px 0;
    }

    /* Donnerstags-Buttons (Rot wie im Bild) */
    .thursday-btn-wrapper div.stButton > button {
        background-color: #D9383A !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 700 !important;
        height: 40px !important;
        width: 100% !important;
        max-width: 48px !important;
        margin: 0 auto !important;
        padding: 0 !important;
    }
    .thursday-btn-wrapper.cancelled div.stButton > button {
        background-color: #55514E !important;
    }

    /* Wochentage & Normale Tage */
    .cal-header-text {
        font-weight: 700;
        font-size: 0.95rem;
        text-align: center;
        color: #E0E0E0;
        padding-bottom: 8px;
    }

    .cal-cell-container {
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .cal-cell-text {
        font-weight: 600;
        font-size: 0.95rem;
        color: #FFFFFF;
        width: 100%;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Samstag & Sonntag dunkelgrau hinterlegt */
    .cal-cell-text.weekend {
        background-color: #333230;
        border-radius: 8px;
        border: 1px solid #3A3836;
    }

    .cal-cell-text.empty {
        opacity: 0;
    }

    /* Unterer Bereich: Rollen-Karten (Matching Screenshot) */
    .meeting-title {
        color: #FFFFFF;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .role-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }

    .role-card {
        background-color: #1E1D1C;
        border-radius: 8px;
        padding: 12px 14px;
        border: 1px solid #333230;
        border-left: 3px solid #666;
        text-align: left;
    }
    .role-card.mod { border-left-color: #4A90E2; }
    .role-card.proto { border-left-color: #2ECC71; }
    .role-card.pause { border-left-color: #F39C12; }
    .role-card.cancelled { 
        border-left-color: #E74C3C; 
        background-color: #2A1C1C; 
        grid-column: span 3;
    }

    .role-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #A0A0A0;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .role-person {
        font-size: 1.15rem;
        font-weight: 700;
        color: #FFFFFF;
    }

    @media (max-width: 640px) {
        .role-container { grid-template-columns: 1fr; }
        .role-card.cancelled { grid-column: span 1; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# Titel
st.markdown(
    "<h1 class='header-title'>NXP ServiceMGMT Meeting Rotation</h1>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------
heute = date.today()

if "current_year" not in st.session_state:
    st.session_state["current_year"] = (
        2026 if heute.year < 2026 else heute.year
    )
if "current_month" not in st.session_state:
    st.session_state["current_month"] = (
        8 if heute.year == 2026 else heute.month
    )
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None
if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = False

monate_namen = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
]

# ---------------------------------------------------------
# Monatszeile & Steuerung
# ---------------------------------------------------------
col_title, col_prev, col_next = st.columns([6, 1, 1])

with col_title:
    st.markdown(
        f"<div class='month-header'>{monate_namen[st.session_state['current_month'] - 1]} {st.session_state['current_year']}</div>",
        unsafe_allow_html=True,
    )

with col_prev:
    if st.button("❮", key="prev_month"):
        if st.session_state["current_month"] == 1:
            st.session_state["current_month"] = 12
            st.session_state["current_year"] -= 1
        else:
            st.session_state["current_month"] -= 1
        st.session_state["selected_date"] = None
        st.session_state["edit_mode"] = False
        st.rerun()

with col_next:
    if st.button("❯", key="next_month"):
        if st.session_state["current_month"] == 12:
            st.session_state["current_month"] = 1
            st.session_state["current_year"] += 1
        else:
            st.session_state["current_month"] += 1
        st.session_state["selected_date"] = None
        st.session_state["edit_mode"] = False
        st.rerun()

# ---------------------------------------------------------
# Kalender Grid
# ---------------------------------------------------------
wochentage_kurz = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
cols_header = st.columns(7)
for i, col in enumerate(cols_header):
    col.markdown(
        f"<div class='cal-header-text'>{wochentage_kurz[i]}</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div class='cal-divider'></div>", unsafe_allow_html=True)

cal = calendar.Calendar(firstweekday=0)
monats_tage = cal.monthdatescalendar(
    st.session_state["current_year"], st.session_state["current_month"]
)

for woche in monats_tage:
    cols = st.columns(7)
    for i, tag in enumerate(woche):
        with cols[i]:
            is_weekend = i >= 5
            weekend_class = "weekend" if is_weekend else ""

            if tag.month != st.session_state["current_month"]:
                st.markdown(
                    "<div class='cal-cell-container'><div class='cal-cell-text empty'></div></div>",
                    unsafe_allow_html=True,
                )
                continue

            tag_str = tag.isoformat()
            ist_donnerstag = tag.weekday() == 3

            # Donnerstage erhalten die roten Buttons
            if ist_donnerstag and tag >= START_DATUM:
                rot = berechne_rotation_fuer_datum(tag, daten)
                btn_class = "cancelled" if rot["ausfall"] else ""

                st.markdown(
                    f"<div class='cal-cell-container'><div class='thursday-btn-wrapper {btn_class}' style='width:100%; text-align:center;'>",
                    unsafe_allow_html=True,
                )
                if st.button(f"{tag.day}", key=f"btn_{tag_str}"):
                    st.session_state["selected_date"] = tag
                    st.session_state["edit_mode"] = False
                    st.rerun()
                st.markdown("</div></div>", unsafe_allow_html=True)
            else:
                # Samstag & Sonntag sind dunkelgrau hinterlegt
                st.markdown(
                    f"<div class='cal-cell-container'><div class='cal-cell-text {weekend_class}'>{tag.day}</div></div>",
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------
# Rollenanzeige (Unterer Bereich)
# ---------------------------------------------------------
sel_tag = st.session_state.get("selected_date")

if (
    sel_tag
    and sel_tag.month == st.session_state["current_month"]
    and sel_tag.year == st.session_state["current_year"]
):
    sel_str = sel_tag.isoformat()
    rot_info = berechne_rotation_fuer_datum(sel_tag, daten)

    st.markdown("<div class='cal-divider'></div>", unsafe_allow_html=True)

    head_col1, head_col2 = st.columns([4, 1])
    with head_col1:
        st.markdown(
            f"<div class='meeting-title'>👥 Meeting am {sel_tag.strftime('%d.%m.%Y')}</div>",
            unsafe_allow_html=True,
        )
    with head_col2:
        if st.button("✏️ Bearbeiten", key="edit_btn"):
            st.session_state["edit_mode"] = not st.session_state["edit_mode"]

    # --- BEARBEITUNGS-MODUS ---
    if st.session_state["edit_mode"]:
        st.info("🛠️ **Anpassung für diesen Tag**")
        with st.form("edit_form"):
            ist_ausfall_chk = st.checkbox(
                "❌ Meeting fällt aus (Rotation verschiebt sich)",
                value=rot_info["ausfall"],
            )

            st.write("**Eingeteilte Personen anpassen:**")
            personen_liste = ["Lissi", "Veronika", "Moritz"]

            def get_idx(person_name, default_idx=0):
                return (
                    personen_liste.index(person_name)
                    if person_name in personen_liste
                    else default_idx
                )

            mod_wahl = st.selectbox(
                "👑 Moderator*in",
                personen_liste,
                index=get_idx(rot_info["mod"], 0),
            )
            proto_wahl = st.selectbox(
                "✏️ Protokollant*in",
                personen_liste,
                index=get_idx(rot_info["proto"], 1),
            )
            pause_wahl = st.selectbox(
                "☕ Pause",
                personen_liste,
                index=get_idx(rot_info["pause"], 2),
            )

            speichern_btn = st.form_submit_button("Speichern")

            if speichern_btn:
                ausgewaehlt = [mod_wahl, proto_wahl, pause_wahl]
                if len(set(ausgewaehlt)) < 3 and not ist_ausfall_chk:
                    st.error("⚠️ Bitte wähle drei unterschiedliche Personen!")
                else:
                    if ist_ausfall_chk:
                        if sel_str not in daten["ausfaelle"]:
                            daten["ausfaelle"].append(sel_str)
                    else:
                        if sel_str in daten["ausfaelle"]:
                            daten["ausfaelle"].remove(sel_str)

                    if "manuelle_anpassungen" not in daten:
                        daten["manuelle_anpassungen"] = {}

                    daten["manuelle_anpassungen"][sel_str] = {
                        "mod": mod_wahl,
                        "proto": proto_wahl,
                        "pause": pause_wahl,
                    }

                    speichere_daten(daten)
                    st.session_state["edit_mode"] = False
                    st.rerun()

    # --- ANZEIGE-MODUS ---
    else:
        if rot_info["ausfall"]:
            st.markdown(
                """
                <div class='role-container'>
                    <div class='role-card cancelled'>
                        <div class='role-title'>⚠️ STATUS</div>
                        <div class='role-person' style='color: #E74C3C;'>Abgesagt / Ausfall</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class='role-container'>
                    <div class='role-card mod'>
                        <div class='role-title'>👑 Moderator*in</div>
                        <div class='role-person'>{rot_info['mod']}</div>
                    </div>
                    <div class='role-card proto'>
                        <div class='role-title'>✏️ Protokollant*in</div>
                        <div class='role-person'>{rot_info['proto']}</div>
                    </div>
                    <div class='role-card pause'>
                        <div class='role-title'>☕ Pause</div>
                        <div class='role-person'>{rot_info['pause']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
