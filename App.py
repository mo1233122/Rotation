import calendar
from datetime import datetime, date, timedelta
import json
from pathlib import Path
import streamlit as st

# Speicherdatei-Pfad
DATEI = Path(__file__).with_name("patho_rotation.json")

# Standard-Personen für die Rotation (in fester Reihenfolge)
STANDARD_PERSONEN = ["Veronika", "Moritz", "Lissi"]
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

    if ziel_str in daten.get("manuelle_anpassungen", {}):
        anpassung = daten["manuelle_anpassungen"][ziel_str]
        return {
            "datum": ziel_datum,
            "ausfall": ziel_str in daten.get("ausfaelle", []),
            "mod": anpassung["mod"],
            "proto": anpassung["proto"],
            "pause": anpassung["pause"],
            "manuell": True,
        }

    alle_ststage = alle_donnerstage_bis(ziel_datum)
    aktiver_index = 0

    for d in alle_ststage:
        d_str = d.isoformat()
        ist_ausfall = d_str in daten.get("ausfaelle", [])

        if d == ziel_datum:
            if ist_ausfall:
                return {
                    "datum": ziel_datum,
                    "ausfall": True,
                    "mod": "-",
                    "proto": "-",
                    "pause": "-",
                    "manuell": False,
                }
            break

        if not ist_ausfall:
            aktiver_index += 1

    personen = daten.get("personen", STANDARD_PERSONEN)
    n = len(personen)

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


# ---------------------------------------------------------
# Page Setup & Modern Grey Dark CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Patho ServiceMGMT Rotation", page_icon="📅", layout="centered"
)

st.markdown(
    """
<style>
    /* Haupt-Hintergrund im Modern Dark Grey Style */
    .stApp {
        background-color: #121417;
        color: #e2e8f0;
    }
    
    /* Einzeilige, gut lesbare Überschrift */
    .header-title {
        text-align: center;
        color: #f8fafc;
        font-weight: 700;
        font-size: 1.8rem;
        white-space: nowrap;
        margin-top: -10px;
        margin-bottom: 25px;
        letter-spacing: -0.5px;
    }
    
    /* Rollenkarten */
    .role-card {
        background-color: #1e2228;
        border-radius: 12px;
        padding: 18px 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        text-align: center;
        border: 1px solid #2d333b;
        border-top: 4px solid #3b82f6;
    }
    .role-card.mod { border-top-color: #60a5fa; }
    .role-card.proto { border-top-color: #34d399; }
    .role-card.pause { border-top-color: #fbbf24; }
    .role-card.cancelled { 
        border-top-color: #f87171; 
        background-color: #261a1a; 
        border: 1px solid #451a1a;
    }
    
    .role-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .role-person {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f1f5f9;
    }
    
    /* Kalenderzellen */
    .weekend-cell {
        background-color: #1a1d24;
        border-radius: 6px;
        padding: 8px 0;
        text-align: center;
        color: #475569;
        font-weight: 500;
    }
    .weekday-cell {
        text-align: center;
        padding: 8px 0;
        color: #94a3b8;
    }
    .header-day {
        text-align: center;
        color: #cbd5e1;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .header-weekend {
        text-align: center;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 8px;
    }

    /* Anpassungen für Streamlit-Inputs & Widgets */
    div[data-baseweb="select"] > div {
        background-color: #1e2228 !important;
        color: #f8fafc !important;
        border-color: #2d333b !important;
    }
    div[data-baseweb="input"] > div {
        background-color: #1e2228 !important;
        color: #f8fafc !important;
        border-color: #2d333b !important;
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
# Monats- & Jahresauswahl
# ---------------------------------------------------------
heute = date.today()
col_m, col_y = st.columns(2)

with col_m:
    monate = [
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
    ausgewaehlter_monat_idx = st.selectbox(
        "Monat wählen",
        range(1, 13),
        index=7 if heute.year == 2026 else heute.month - 1,
        format_func=lambda x: monate[x - 1],
    )

with col_y:
    ausgewaehltes_jahr = st.number_input(
        "Jahr wählen", min_value=2026, max_value=2035, value=2026, step=1
    )

st.divider()

# Session State initialisieren
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None
if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = False

# ---------------------------------------------------------
# Kalender-Darstellung
# ---------------------------------------------------------
cal = calendar.Calendar(firstweekday=0)
monats_tage = cal.monthdatescalendar(
    ausgewaehltes_jahr, ausgewaehlter_monat_idx
)

st.markdown(
    f"### 📅 {monate[ausgewaehlter_monat_idx - 1]} {ausgewaehltes_jahr}"
)

# Wochentage Header
cols_header = st.columns(7)
wochentage_kurz = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
for i, col in enumerate(cols_header):
    css_class = "header-weekend" if i >= 5 else "header-day"
    col.markdown(
        f"<div class='{css_class}'>{wochentage_kurz[i]}</div>",
        unsafe_allow_html=True,
    )

# Tage rendern
for woche in monats_tage:
    cols = st.columns(7)
    for i, tag in enumerate(woche):
        with cols[i]:
            if tag.month != ausgewaehlter_monat_idx:
                st.markdown(
                    "<div class='weekday-cell' style='opacity: 0.15;'>•</div>",
                    unsafe_allow_html=True,
                )
                continue

            tag_str = tag.isoformat()
            ist_donnerstag = tag.weekday() == 3
            ist_wochenende = i >= 5

            if ist_donnerstag and tag >= START_DATUM:
                rot = berechne_rotation_fuer_datum(tag, daten)
                btn_label = f"📌 {tag.day}"

                if rot["ausfall"]:
                    btn_type = "secondary"
                    btn_label = f"❌ {tag.day}"
                else:
                    btn_type = "primary"

                if st.button(btn_label, key=f"btn_{tag_str}", type=btn_type):
                    st.session_state["selected_date"] = tag
                    st.session_state["edit_mode"] = False
                    st.rerun()
            elif ist_wochenende:
                st.markdown(
                    f"<div class='weekend-cell'>{tag.day}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='weekday-cell'>{tag.day}</div>",
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
        if st.button("✏️ Bearbeiten"):
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
            mod_val = st.text_input(
                "🎤 Moderierer",
                value=rot_info["mod"] if not rot_info["ausfall"] else "Veronika",
            )
            proto_val = st.text_input(
                "📝 Protokollierer",
                value=rot_info["proto"] if not rot_info["ausfall"] else "Moritz",
            )
            pause_val = st.text_input(
                "☕ Pause",
                value=rot_info["pause"] if not rot_info["ausfall"] else "Lissi",
            )

            speichern_btn = st.form_submit_button("Speichern")

            if speichern_btn:
                if ist_ausfall_chk:
                    if sel_str not in daten["ausfaelle"]:
                        daten["ausfaelle"].append(sel_str)
                else:
                    if sel_str in daten["ausfaelle"]:
                        daten["ausfaelle"].remove(sel_str)

                if "manuelle_anpassungen" not in daten:
                    daten["manuelle_anpassungen"] = {}

                daten["manuelle_anpassungen"][sel_str] = {
                    "mod": mod_val,
                    "proto": proto_val,
                    "pause": pause_val,
                }

                speichere_daten(daten)
                st.session_state["edit_mode"] = False
                st.success("Erfolgreich gespeichert!")
                st.rerun()

    # --- ANZEIGE-MODUS (Farbige Kacheln im Dark Look) ---
    else:
        if rot_info["ausfall"]:
            st.markdown(
                """
                <div class='role-card cancelled'>
                    <div class='role-title' style='color: #f87171;'>Meeting Status</div>
                    <div class='role-person' style='color: #fca5a5;'>❌ Abgesagt / Ausfall</div>
                    <p style='color: #cbd5e1; margin-top: 8px; font-size: 0.85rem;'>
                        Die Rotation wird für die darauffolgende Woche fortgesetzt.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.markdown(
                    f"""
                    <div class='role-card mod'>
                        <div class='role-title'>🎤 Moderierer</div>
                        <div class='role-person'>{rot_info['mod']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_b:
                st.markdown(
                    f"""
                    <div class='role-card proto'>
                        <div class='role-title'>📝 Protokollierer</div>
                        <div class='role-person'>{rot_info['proto']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_c:
                st.markdown(
                    f"""
                    <div class='role-card pause'>
                        <div class='role-title'>☕ Pause</div>
                        <div class='role-person'>{rot_info['pause']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

else:
    st.info(
        "👈 Klicken Sie auf einen blau markierten Donnerstag (📌) im Kalender, um die Rollenverteilung anzuzeigen."
    )
