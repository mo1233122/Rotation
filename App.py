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
# Page Setup & Clean CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Patho ServiceMGMT Rotation", page_icon="📅", layout="centered"
)

st.markdown(
    """
<style>
    /* Hintergrund & Grundstruktur */
    .stApp {
        background-color: #E6E1DA;
        color: #2D2B2A;
    }

    .header-title {
        text-align: center;
        color: #2D2B2A;
        font-weight: 800;
        font-size: clamp(1.4rem, 4vw, 2.0rem);
        margin-top: -10px;
        margin-bottom: 25px;
    }

    /* Weicher, heller Kalender-Behälter */
    .cal-card-wrapper {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.05);
        border: 1px solid #D8D2C9;
        max-width: 480px;
        margin: 0 auto;
    }

    .month-header {
        font-size: 1.35rem;
        font-weight: 700;
        color: #1F1E1D;
    }

    /* Pfeil-Buttons oben rechts */
    div[data-testid="stHorizontalBlock"] div.stButton > button {
        border-radius: 8px !important;
        background-color: #FF2A55 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        height: 36px !important;
        width: 36px !important;
        padding: 0 !important;
    }

    /* Trennlinie unter dem Monat */
    .cal-divider {
        border-bottom: 1px solid #E5E0D8;
        margin: 15px 0 10px 0;
    }

    /* Einheits-Button für Donnerstage in Streamlit */
    .thursday-btn-wrapper div.stButton > button {
        background-color: #FF2A55 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 700 !important;
        height: 32px !important;
        width: 32px !important;
        margin: 0 auto !important;
        padding: 0 !important;
        box-shadow: 0 3px 8px rgba(255, 42, 85, 0.3) !important;
    }
    .thursday-btn-wrapper.cancelled div.stButton > button {
        background-color: #8C857B !important;
        box-shadow: none !important;
    }

    /* Zellen styling */
    .cal-cell-text {
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.95rem;
        color: #383533;
    }
    .cal-cell-text.weekend {
        background-color: #F2EFE9;
        border-radius: 4px;
    }
    .cal-cell-text.empty {
        opacity: 0.15;
    }

    .cal-header-text {
        font-weight: 700;
        font-size: 0.85rem;
        text-align: center;
        color: #5C5650;
        padding: 4px 0;
    }
    .cal-header-text.weekend {
        background-color: #F2EFE9;
        border-radius: 4px 4px 0 0;
    }

    /* Rollenkarten */
    .role-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 20px;
    }

    .role-card {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 16px 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        text-align: center;
        border: 1px solid #D8D2C9;
        border-top: 4px solid #FF2A55;
    }
    .role-card.proto { border-top-color: #10B981; }
    .role-card.pause { border-top-color: #F59E0B; }
    .role-card.cancelled { 
        border-top-color: #EF4444; 
        background-color: #FDF2F2; 
        border: 1px solid #FCA5A5;
        grid-column: span 3;
    }

    .role-title {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #78726A;
        margin-bottom: 4px;
    }
    .role-person {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1F1E1D;
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
# Kalender Container
# ---------------------------------------------------------
st.markdown("<div class='cal-card-wrapper'>", unsafe_allow_html=True)

# Monatszeile + Pfeile
col_title, col_prev, col_next = st.columns([5, 1, 1])

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

# Trennstrich nach Monat / Pfeilen
st.markdown("<div class='cal-divider'></div>", unsafe_allow_html=True)

# Kalender Kopfzeile (Wochentage)
wochentage_kurz = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
cols_header = st.columns(7)
for i, col in enumerate(cols_header):
    is_weekend = i >= 5
    css = "cal-header-text weekend" if is_weekend else "cal-header-text"
    col.markdown(
        f"<div class='{css}'>{wochentage_kurz[i]}</div>", unsafe_allow_html=True
    )

# Tage Rendern
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

            # Tage anderer Monate
            if tag.month != st.session_state["current_month"]:
                st.markdown(
                    f"<div class='cal-cell-text empty {weekend_class}'>•</div>",
                    unsafe_allow_html=True,
                )
                continue

            tag_str = tag.isoformat()
            ist_donnerstag = tag.weekday() == 3

            # Donnerstage mit interaktivem Button
            if ist_donnerstag and tag >= START_DATUM:
                rot = berechne_rotation_fuer_datum(tag, daten)
                btn_class = "cancelled" if rot["ausfall"] else ""

                st.markdown(
                    f"<div class='thursday-btn-wrapper {btn_class}'>",
                    unsafe_allow_html=True,
                )
                if st.button(f"{tag.day}", key=f"btn_{tag_str}"):
                    st.session_state["selected_date"] = tag
                    st.session_state["edit_mode"] = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Normale Tage & Wochenenden
                st.markdown(
                    f"<div class='cal-cell-text {weekend_class}'>{tag.day}</div>",
                    unsafe_allow_html=True,
                )

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Rollenanzeige (NUR WENN EIN DATUM IM AKTUELLEN MONAT GEWÄHLT IST)
# ---------------------------------------------------------
sel_tag = st.session_state.get("selected_date")

if (
    sel_tag
    and sel_tag.month == st.session_state["current_month"]
    and sel_tag.year == st.session_state["current_year"]
):
    sel_str = sel_tag.isoformat()
    rot_info = berechne_rotation_fuer_datum(sel_tag, daten)

    st.markdown("<br>", unsafe_allow_html=True)
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
                    st.rerun()

    # --- ANZEIGE-MODUS ---
    else:
        if rot_info["ausfall"]:
            st.markdown(
                """
                <div class='role-container'>
                    <div class='role-card cancelled'>
                        <div class='role-title' style='color: #EF4444;'>Meeting Status</div>
                        <div class='role-person' style='color: #DC2626;'>❌ Abgesagt / Ausfall</div>
                        <p style='color: #78726A; margin-top: 8px; font-size: 0.85rem;'>
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
