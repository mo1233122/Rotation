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
# Datenhaltung & Logik
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


def erster_donnerstag_des_monats(year: int, month: int) -> date:
    """Ermittelt den ersten Donnerstag eines Monats (oder START_DATUM, falls davor)."""
    cal = calendar.Calendar(firstweekday=0)
    for tag in cal.itermonthdates(year, month):
        if tag.month == month and tag.weekday() == 3:
            return max(tag, START_DATUM)
    return date(year, month, 1)


def berechne_rotation_fuer_datum(ziel_datum: date, daten: dict):
    if ziel_datum.weekday() != 3 or ziel_datum < START_DATUM:
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
# Page Setup & CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="NXP ServiceMGMT Meeting Rotation",
    page_icon="📅",
    layout="centered",
)

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

    /* Haupt-Überschrift einzeilig */
    .header-title {
        color: #FFFFFF;
        font-weight: 800;
        font-size: 1.45rem;
        margin-bottom: 20px;
        white-space: nowrap !important;
    }

    /* KALENDER CARD WRAPPER */
    .calendar-card {
        background-color: #1C1B1A;
        border: 1px solid #3A3836;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    .cal-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }

    .month-header-text {
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF;
    }

    .nav-btn-link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        background-color: #D9383A;
        color: #FFFFFF !important;
        text-decoration: none !important;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.1rem;
        transition: background-color 0.2s;
    }

    .nav-btn-link:hover {
        background-color: #B52B2D;
    }

    /* Grid Layout */
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 8px;
        text-align: center;
    }

    .day-name {
        font-size: 1rem;
        font-weight: 700;
        color: #B0B0B0;
        padding-bottom: 8px;
    }

    .cal-day {
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
        color: #FFFFFF;
    }

    .cal-day.weekend {
        background-color: #2A2928;
    }

    /* Rote Donnerstage */
    a.thursday-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 42px;
        background-color: #D9383A;
        color: #FFFFFF !important;
        text-decoration: none !important;
        font-weight: 700;
        border-radius: 8px;
        box-shadow: 0 3px 8px rgba(217, 56, 58, 0.3);
        transition: transform 0.1s, background-color 0.2s;
    }

    a.thursday-btn:hover {
        background-color: #B52B2D;
        transform: translateY(-1px);
    }

    a.thursday-btn.cancelled {
        background-color: #55514E !important;
        box-shadow: none !important;
    }

    .cal-divider {
        border-bottom: 1px solid #3A3836;
        margin: 20px 0;
    }

    /* MEETING UNTERZEILE */
    .meeting-section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 15px;
    }

    /* LINK UNTER DEN ROLLEN */
    .edit-text-link div.stButton > button {
        background-color: transparent !important;
        color: #A0A0A0 !important;
        border: none !important;
        text-decoration: underline !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        padding: 0 !important;
        margin-top: 15px !important;
        box-shadow: none !important;
        height: auto !important;
        cursor: pointer !important;
    }

    .edit-text-link div.stButton > button:hover {
        color: #FFFFFF !important;
        background-color: transparent !important;
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
        font-size: 0.98rem;
        font-weight: 700;
        color: #C0C0C0;
        margin-bottom: 6px;
    }
    .role-person {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
    }

    /* INFO AREA BOTTOM */
    .info-card {
        background-color: #1C1B1A;
        border: 1px solid #333230;
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 5px;
    }

    .info-card-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #D9383A;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .info-card-list {
        margin: 0;
        padding-left: 18px;
        color: #B0B0B0;
        font-size: 0.85rem;
        line-height: 1.5;
    }

    .info-card-list li {
        margin-bottom: 4px;
    }
    .info-card-list li:last-child {
        margin-bottom: 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# State & URL Parameters
# ---------------------------------------------------------
params = st.query_params
heute = date.today()

current_year = int(params.get("year", 2026 if heute.year < 2026 else heute.year))
current_month = int(params.get("month", 8 if heute.year == 2026 else heute.month))

# Datum aus URL parsen
selected_date_str = params.get("selected_date", None)
selected_date = None

if selected_date_str:
    try:
        selected_date = date.fromisoformat(selected_date_str)
    except Exception:
        pass

# Falls das gewählte Datum NICHT zum aktuellen Jahr/Monat passt,
# springen wir automatisch auf den ersten Donnerstag des neuen Monats!
if not selected_date or selected_date.year != current_year or selected_date.month != current_month:
    selected_date = erster_donnerstag_des_monats(current_year, current_month)

selected_date_str = selected_date.isoformat()

if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = False

monate_namen = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]

# Title
st.markdown(
    "<h1 class='header-title'>NXP ServiceMGMT Meeting Rotation</h1>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# KALENDER CARD
# ---------------------------------------------------------
if current_month == 1:
    prev_m, prev_y = 12, current_year - 1
else:
    prev_m, prev_y = current_month - 1, current_year

if current_month == 12:
    next_m, next_y = 1, current_year + 1
else:
    next_m, next_y = current_month + 1, current_year

# Ersten Donnerstag für Vor- und Folgemonat berechnen für nahtlose Navigation
prev_first_do = erster_donnerstag_des_monats(prev_y, prev_m)
next_first_do = erster_donnerstag_des_monats(next_y, next_m)

card_html = f"""
<div class="calendar-card">
    <div class="cal-header-row">
        <div class="month-header-text">{monate_namen[current_month - 1]} {current_year}</div>
        <div>
            <a href="?month={prev_m}&year={prev_y}&selected_date={prev_first_do.isoformat()}" target="_self" class="nav-btn-link">❮</a>
            <a href="?month={next_m}&year={next_y}&selected_date={next_first_do.isoformat()}" target="_self" class="nav-btn-link" style="margin-left: 6px;">❯</a>
        </div>
    </div>
    <div class="cal-grid">
        <div class="day-name">Mo</div>
        <div class="day-name">Di</div>
        <div class="day-name">Mi</div>
        <div class="day-name">Do</div>
        <div class="day-name">Fr</div>
        <div class="day-name">Sa</div>
        <div class="day-name">So</div>
"""

cal = calendar.Calendar(firstweekday=0)
monats_tage = cal.monthdatescalendar(current_year, current_month)

for woche in monats_tage:
    for i, tag in enumerate(woche):
        if tag.month != current_month:
            card_html += '<div class="cal-day"></div>'
        elif tag.weekday() == 3 and tag >= START_DATUM:
            rot = berechne_rotation_fuer_datum(tag, daten)
            is_cancelled = rot["ausfall"] if rot else False

            cls = "thursday-btn"
            if is_cancelled:
                cls += " cancelled"

            link = f"?month={current_month}&year={current_year}&selected_date={tag.isoformat()}"
            card_html += f'<a href="{link}" target="_self" class="{cls}">{tag.day}</a>'
        else:
            weekend_cls = "weekend" if i >= 5 else ""
            card_html += f'<div class="cal-day {weekend_cls}">{tag.day}</div>'

card_html += """
    </div>
</div>
"""

st.markdown(card_html, unsafe_allow_html=True)
st.markdown("<div class='cal-divider'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MEETING ANZEIGE & BEARBEITEN
# ---------------------------------------------------------
if selected_date and selected_date.weekday() == 3 and selected_date >= START_DATUM:
    rot_info = berechne_rotation_fuer_datum(selected_date, daten)

    st.markdown(
        f"<div class='meeting-section-header'>👥 Meeting am {selected_date.strftime('%d.%m.%Y')}</div>",
        unsafe_allow_html=True,
    )

    # Bearbeitungs-Formular (falls offen)
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
                sel_str = selected_date.isoformat()
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

    # Normalansicht der Karten
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

    # Text-Link unter den Rollen
    st.markdown("<div class='edit-text-link'>", unsafe_allow_html=True)
    btn_text = "Abbrechen" if st.session_state["edit_mode"] else "Bearbeiten"
    if st.button(btn_text, key="toggle_edit_mode"):
        st.session_state["edit_mode"] = not st.session_state["edit_mode"]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# ZWEITER TRENNSTRICH & INFO BEREICH
# ---------------------------------------------------------
st.markdown("<div class='cal-divider'></div>", unsafe_allow_html=True)

st.markdown(
    """
<div class="info-card">
    <div class="info-card-title">ℹ️ Funktionsweise & Rotation</div>
    <ul class="info-card-list">
        <li><b>Automatische Rotation:</b> Die Rollen (Moderator*in, Protokollant*in, Pause) rotieren jeden Donnerstag automatisch unter Moritz, Lissi und Veronika.</li>
        <li><b>Manuelle Anpassung:</b> Über <u>Bearbeiten</u> lassen sich Rollen für ein gewählte Datum individuell festlegen. Nachfolgende Donnerstage passen sich automatisch an.</li>
        <li><b>Ausfälle:</b> Fällt ein Meeting aus, pausiert der Turnus für diese Woche und wird am nächsten Donnerstag nahtlos fortgesetzt.</li>
    </ul>
</div>
""",
    unsafe_allow_html=True,
)
