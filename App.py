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
# Datenhaltung & Logik (Unverändert & stabil)
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
# Page Setup & Exact CSS Layout
# ---------------------------------------------------------
st.set_page_config(
    page_title="NXP ServiceMGMT Meeting Rotation",
    page_icon="📅",
    layout="centered",
)

# Wir nutzen CSS Grid für die Meeting-Zeile um alles perfekt auszurichten
st.markdown(
    """
<style>
    /* Dunkles Grund-Theme */
    .stApp {
        background-color: #242322;
        color: #FFFFFF;
    }

    .main .block-container {
        max-width: 680px !important;
        padding-top: 2rem !important;
    }

    /* Überschrift */
    .header-title {
        color: #FFFFFF;
        font-weight: 800;
        font-size: 1.8rem;
        margin-bottom: 12px;
        white-space: nowrap;
    }

    /* Kalenderblock */
    div.cal-block-wrapper div.stHorizontalBlock {
        background-color: #1C1B1A;
        border: 1px solid #3A3836;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        margin-bottom: 16px;
    }

    .month-header-row {
        margin-bottom: 16px;
    }

    .month-header-text {
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        height: 36px;
    }

    /* Pfeil-Buttons oben rechts */
    div[data-testid="stHorizontalBlock"] div.stButton > button {
        border-radius: 8px !important;
        background-color: #D9383A !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: bold !important;
        height: 36px !important;
        width: 36px !important;
        padding: 0 !important;
    }

    /* Trennstriche */
    .cal-divider {
        border-bottom: 1px solid #3A3836;
        margin: 14px 0 16px 0;
    }

    /* FIX FÜR SPALTEN-ALIGNMENT & KEIN NEULADEN */
    /* Wir zwingen alle Spalten auf exakt dieselbe Breite und dasselbe Padding, 
       egal ob Button oder Text */
    div[data-testid="column"] {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0 3px !important;
    }

    .day-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #E0E0E0;
        text-align: center;
        margin-bottom: 6px;
    }

    .day-cell {
        width: 100%;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05rem;
        font-weight: 600;
        color: #FFFFFF;
        border-radius: 8px;
        box-sizing: border-box;
    }

    .day-cell.weekend {
        background-color: #333230;
    }

    /* ISOLIERTER STYLING-CONTAINER FÜR DONNERSTAGE */
    /* Das CSS im div-Wrapper sorgt dafür, dass nur Donnerstage rot sind, 
       ohne das globale st.button Design anzufassen. 
       Gleichzeitig bleibt es ein nativer Streamlit-Button (kein Neuladen!) */
    .thursday-btn-container {
        width: 100%;
    }

    .thursday-btn-container div.stButton {
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }

    .thursday-btn-container div.stButton > button {
        width: 100% !important;
        height: 44px !important;
        background-color: #D9383A !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        padding: 0 !important;
        box-shadow: 0 3px 8px rgba(217, 56, 58, 0.3) !important;
    }

    .thursday-btn-container div.stButton > button:hover {
        background-color: #B52B2D !important;
    }

    /* Button für abgesagte Meetings */
    .thursday-btn-container.cancelled div.stButton > button {
        background-color: #55514E !important;
        box-shadow: none !important;
    }

    /* --- UNTERER BEREICH: MEETING HEADER ZEILE --- */
    /* Wir nutzen CSS Grid um die Überschrift und den Button auf eine Höhe 
       und rechtsbündig zu zwingen */
    .meeting-header-zeile {
        display: grid;
        grid-template-columns: 1fr auto;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 15px;
    }

    .meeting-section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* BEARBEITEN BUTTON: Exakt rechtsbündig und höhenmäßig bündig */
    .bearbeiten-btn-wrapper {
        text-align: right;
    }

    .bearbeiten-btn-wrapper div.stButton > button {
        background-color: #1E1E1D !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
        padding: 6px 12px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        box-shadow: none !important;
        height: 32px !important;
        border: 1px solid #3A3836 !important;
    }

    .bearbeiten-btn-wrapper div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-color: #FFFFFF !important;
    }

    /* Rollenkarten */
    .role-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }

    .role-card {
        background-color: #1C1B1A;
        border-radius: 8px;
        padding: 14px;
        border: 1px solid #333230;
        border-left: 4px solid #4A90E2;
    }
    .role-card.mod { border-left-color: #D9383A; }
    .role-card.proto { border-left-color: #2ECC71; }
    .role-card.pause { border-left-color: #F39C12; }
    .role-card.cancelled { 
        border-left-color: #E74C3C; 
        background-color: #2A1C1C; 
        grid-column: span 3;
    }

    .role-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #9E9E9E;
        margin-bottom: 4px;
    }
    .role-person {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
    }
</style>
""",
    unsafe_allow_html=True,
)

# App-Titel
st.markdown(
    "<h1 class='header-title'>NXP ServiceMGMT Meeting Rotation</h1>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# State Handling
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
# Monats-Header & Navigation (Rote Pfeile)
# ---------------------------------------------------------
st.markdown("<div class='month-header-row cal-block-wrapper'>", unsafe_allow_html=True)
col_title, col_prev, col_next = st.columns([6, 1, 1])

with col_title:
    st.markdown(
        f"<div class='month-header-text'>{monate_namen[st.session_state['current_month'] - 1]} {st.session_state['current_year']}</div>",
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
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# KALENDER RENDERN (Perfect Columns)
# ---------------------------------------------------------
st.markdown("<div class='cal-block-wrapper'>", unsafe_allow_html=True)
wochentage_kurz = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
cols_header = st.columns(7)
for i, col in enumerate(cols_header):
    col.markdown(
        f"<div class='day-header'>{wochentage_kurz[i]}</div>",
        unsafe_allow_html=True,
    )

cal = calendar.Calendar(firstweekday=0)
monats_tage = cal.monthdatescalendar(
    st.session_state["current_year"], st.session_state["current_month"]
)

for woche in monats_tage:
    st.markdown("<div class='cal-divider'></div>", unsafe_allow_html=True)
    cols = st.columns(7)
    for i, tag in enumerate(woche):
        with cols[i]:
            if tag.month != st.session_state["current_month"]:
                st.markdown(
                    "<div class='day-cell'></div>", unsafe_allow_html=True
                )
            elif tag.weekday() == 3 and tag >= START_DATUM:
                rot = berechne_rotation_fuer_datum(tag, daten)
                btn_class = (
                    "thursday-btn-container cancelled"
                    if rot["ausfall"]
                    else "thursday-btn-container"
                )

                # Wir nutzen Streamlit-native st.button, um kein Neuladen zu erzwingen
                st.markdown(f"<div class='{btn_class}'>", unsafe_allow_html=True)
                if st.button(f"{tag.day}", key=f"btn_{tag.isoformat()}"):
                    st.session_state["selected_date"] = tag
                    st.session_state["edit_mode"] = False
                    # st.rerun() entfernt -> Verhindert das Neuladen
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                is_weekend = i >= 5
                weekend_cls = "weekend" if is_weekend else ""
                st.markdown(
                    f"<div class='day-cell {weekend_cls}'>{tag.day}</div>",
                    unsafe_allow_html=True,
                )
st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# UNTERER BEREICH: ROLLENANZEIGE & EDITING
# ---------------------------------------------------------
sel_tag = st.session_state.get("selected_date")

if (
    sel_tag
    and sel_tag.month == st.session_state["current_month"]
    and sel_tag.year == st.session_state["current_year"]
):
    sel_str = sel_tag.isoformat()
    rot_info = berechne_rotation_fuer_datum(sel_tag, daten)

    # MEETING HEADER ZEILE: GRID FÜR PERFEKTES ALIGNMENT
    st.markdown("<div class='meeting-header-zeile'>", unsafe_allow_html=True)
    
    # Teil 1: Die Überschrift (Links)
    st.markdown(
        f"<div class='meeting-section-header'>👥 Meeting am {sel_tag.strftime('%d.%m.%Y')}</div>",
        unsafe_allow_html=True,
    )
    
    # Teil 2: Der Bearbeiten-Button (Rechts)
    st.markdown("<div class='bearbeiten-btn-wrapper'>", unsafe_allow_html=True)
    if st.button("Bearbeiten", key="toggle_edit_link"):
        st.session_state["edit_mode"] = not st.session_state["edit_mode"]
        # st.rerun() entfernt -> Kein Neuladen
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True) # Ende meeting-header-zeile

    # Bearbeitungs-Formular
    if st.session_state["edit_mode"]:
        st.info("🛠️ **Anpassung für diesen Tag**")
        with st.form("edit_form"):
            ist_ausfall_chk = st.checkbox(
                "❌ Meeting fällt aus (Rotation verschiebt sich)",
                value=rot_info["ausfall"],
            )

            personen_liste = ["Moritz", "Lissi", "Veronika"]

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

    # Normalansicht der Rollen
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
