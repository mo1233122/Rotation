import calendar
from datetime import datetime, date, timedelta
import json
from pathlib import Path
import streamlit as st

# Speicherdatei-Pfad
DATEI = Path(__file__).with_name("patho_rotation.json")

# Standard-Personen für die Rotation (Reihenfolge: Moritz -> Lissi -> Veronika)
STANDARD_PERSONEN = ["Moritz", "Lissi", "Veronika"]
START_DATUM = date(2026, 8, 6)  # Erster bekannter Donnerstag


# ---------------------------------------------------------
# Datenhaltung (Laden / Speichern)
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
# Kaskadierende Rotations-Logik
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
# Page Setup & Greige / Eggshell Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Patho ServiceMGMT Rotation", page_icon="📅", layout="centered"
)

st.markdown(
    """
<style>
    /* Warmes Eggshell/Greige Theme */
    .stApp {
        background-color: #f4f1ea;
        color: #2c2a29;
    }

    .header-title {
        text-align: center;
        color: #2c2a29;
        font-weight: 700;
        font-size: clamp(1.4rem, 4vw, 1.9rem);
        white-space: nowrap;
        margin-top: -15px;
        margin-bottom: 25px;
        letter-spacing: -0.5px;
    }

    /* Kalender-Card */
    .calendar-card {
        background-color: #efece6;
        border-radius: 20px;
        padding: 24px 20px 16px 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2ddd5;
        margin-bottom: 25px;
    }

    /* Monatszeile & Pfeile */
    .month-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f1e1d;
    }

    /* Kalender Grid CSS */
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        text-align: center;
        margin-top: 15px;
        border-radius: 12px;
        overflow: hidden;
    }

    .cal-header-cell {
        font-weight: 700;
        font-size: 0.95rem;
        padding: 10px 0;
        color: #4a4744;
    }
    .cal-header-cell.weekend {
        background-color: #e5e0d8;
        color: #383533;
    }

    .cal-day-cell {
        padding: 10px 0;
        font-size: 0.95rem;
        font-weight: 500;
        color: #2c2a29;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 44px;
    }
    .cal-day-cell.weekend {
        background-color: #e5e0d8;
        color: #6e6963;
    }
    .cal-day-cell.empty {
        opacity: 0.15;
    }

    /* Streamlit PfeilbuttonsStyling */
    div[data-testid="stHorizontalBlock"] div.stButton > button {
        border-radius: 8px !important;
        background-color: #ff2a55 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 3px 8px rgba(255, 42, 85, 0.3) !important;
    }
    div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
        background-color: #e01f47 !important;
    }

    /* Donnerstags-Buttons (Pill Style wie auf Bild) */
    .thursday-btn button {
        background-color: #ff2a55 !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 6px 0 !important;
        width: 85% !important;
        margin: 0 auto !important;
        box-shadow: 0 4px 10px rgba(255, 42, 85, 0.25) !important;
    }
    .thursday-btn.cancelled button {
        background-color: #6e6963 !important;
        box-shadow: none !important;
    }

    /* Rollenkarten im Greige Look */
    .role-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 10px;
    }

    .role-card {
        background-color: #efece6;
        border-radius: 14px;
        padding: 18px 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        text-align: center;
        border: 1px solid #e2ddd5;
        border-top: 4px solid #3b82f6;
    }
    .role-card.mod { border-top-color: #ff2a55; }
    .role-card.proto { border-top-color: #10b981; }
    .role-card.pause { border-top-color: #f59e0b; }
    .role-card.cancelled { 
        border-top-color: #ef4444; 
        background-color: #fcf0f0; 
        border: 1px solid #f87171;
        grid-column: span 3;
    }

    .role-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #78726a;
        margin-bottom: 6px;
    }
    .role-person {
        font-size: 1.35rem;
        font-weight: 700;
        color: #1f1e1d;
    }

    /* Formularelemente in hellen Farben */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #ffffff !important;
        color: #2c2a29 !important;
        border-color: #d6d0c4 !important;
        border-radius: 8px !important;
    }

    @media (max-width: 640px) {
        .role-container { grid-template-columns: 1fr; }
        .role-card.cancelled { grid-column: span 1; }
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "<h1 class='header-title'>Patho ServiceMGMT Rotation</h1>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Monats- & Jahres-Navigation über Pfeiltasten
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

# Monatsanzeige und Buttons wie im Referenzbild
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
        st.rerun()

with col_next:
    if st.button("❯", key="next_month"):
        if st.session_state["current_month"] == 12:
            st.session_state["current_month"] = 1
            st.session_state["current_year"] += 1
        else:
            st.session_state["current_month"] += 1
        st.rerun()

# ---------------------------------------------------------
# Nahtloses Kalender-Grid (Wochenende rechts leicht grau)
# ---------------------------------------------------------
cal = calendar.Calendar(firstweekday=0)
monats_tage = cal.monthdatescalendar(
    st.session_state["current_year"], st.session_state["current_month"]
)

# Wochentage Header
cols_header = st.columns(7)
wochentage_kurz = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

for i, col in enumerate(cols_header):
    is_weekend = i >= 5
    css = "cal-header-cell weekend" if is_weekend else "cal-header-cell"
    col.markdown(
        f"<div class='{css}'>{wochentage_kurz[i]}</div>", unsafe_allow_html=True
    )

# Tage durchgehen
for woche in monats_tage:
    cols = st.columns(7)
    for i, tag in enumerate(woche):
        with cols[i]:
            is_weekend = i >= 5
            weekend_class = "weekend" if is_weekend else ""

            if tag.month != st.session_state["current_month"]:
                st.markdown(
                    f"<div class='cal-day-cell empty {weekend_class}'>•</div>",
                    unsafe_allow_html=True,
                )
                continue

            tag_str = tag.isoformat()
            ist_donnerstag = tag.weekday() == 3

            if ist_donnerstag and tag >= START_DATUM:
                rot = berechne_rotation_fuer_datum(tag, daten)
                btn_class = "cancelled" if rot["ausfall"] else ""
                btn_label = f"{tag.day}"

                st.markdown(
                    f"<div class='thursday-btn {btn_class}'>",
                    unsafe_allow_html=True,
                )
                if st.button(btn_label, key=f"btn_{tag_str}"):
                    st.session_state["selected_date"] = tag
                    st.session_state["edit_mode"] = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div class='cal-day-cell {weekend_class}'>{tag.day}</div>",
                    unsafe_allow_html=True,
                )

st.divider()

# ---------------------------------------------------------
# Rollenanzeige & Details zum gewählten Tag
# ---------------------------------------------------------
sel_tag = st.session_state.get("selected_date")

if sel_tag:
    sel_str = sel_tag.isoformat()
    rot_info = berechne_rotation_fuer_datum(sel_tag, daten)

    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown(
            f"### Meeting am **{sel_tag.strftime('%d.%m.%Y')}**"
        )
    with head_col2:
        if st.button("✏️ Bearbeiten", key="edit_btn"):
            st.session_state["edit_mode"] = not st.session_state["edit_mode"]

    # --- BEARBEITUNGS-MODUS ---
    if st.session_state["edit_mode"]:
        st.info("🛠️ **Anpassung für diesen Tag**")
        with st.form("edit_form"):
            ist_ausfall_chk = st.checkbox(
                "❌ Meeting fällt aus (Rotation verschiebt sich automatisch)",
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
                "🎤 Moderator*in",
                personen_liste,
                index=get_idx(rot_info["mod"], 0),
            )
            proto_wahl = st.selectbox(
                "📝 Protokollant*in",
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
                    st.error(
                        "⚠️ Bitte wähle für jede Rolle eine unterschiedliche Person aus!"
                    )
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
                    st.success(
                        "Erfolgreich gespeichert! Alle nachfolgenden Tage passen sich an."
                    )
                    st.rerun()

    # --- ANZEIGE-MODUS ---
    else:
        if rot_info["ausfall"]:
            st.markdown(
                """
                <div class='role-container'>
                    <div class='role-card cancelled'>
                        <div class='role-title' style='color: #ef4444;'>Meeting Status</div>
                        <div class='role-person' style='color: #dc2626;'>❌ Abgesagt / Ausfall</div>
                        <p style='color: #78726a; margin-top: 8px; font-size: 0.85rem;'>
                            Die Rotation wird für die darauffolgende Woche fortgesetzt.
                        </p>
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
                        <div class='role-title'>🎤 Moderator*in</div>
                        <div class='role-person'>{rot_info['mod']}</div>
                    </div>
                    <div class='role-card proto'>
                        <div class='role-title'>📝 Protokollant*in</div>
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

else:
    st.info(
        "👈 Klicken Sie auf einen rot markierten Donnerstag im Kalender, um die Rollenverteilung anzuzeigen."
    )
