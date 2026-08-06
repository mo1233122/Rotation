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
# Page Setup & Custom CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Patho ServiceMGMT Rotation", page_icon="📅", layout="centered"
)

# Erweitertes CSS für graue Wochenenden und hübsche Rollen-Karten
st.markdown(
    """
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .header-title {
        text-align: center;
        color: #1e293b;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .role-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        text-align: center;
        border-top: 5px solid #3b82f6;
    }
    .role-card.mod { border-top-color: #3b82f6; }
    .role-card.proto { border-top-color: #10b981; }
    .role-card.pause { border-top-color: #f59e0b; }
    .role-card.cancelled { border-top-color: #ef4444; background-color: #fef2f2; }
    
    .role-title {
        font-size: 0.90rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 8px;
    }
    .role-person {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
    }
    .weekend-cell {
        background-color: #f1f5f9;
        border-radius: 6px;
        padding: 8px 0;
        text-align: center;
        color: #94a3b8;
    }
    .weekday-cell {
        text-align: center;
        padding: 8px 0;
        color: #475569;
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
    # Wochenenden in Kopfzeile auch leicht färben
    color = "#94a3b8" if i >= 5 else "#1e293b"
    col.markdown(
        f"<div style='text-align: center; color: {color}; font-weight: bold;'>{wochentage_kurz[i]}</div>",
        unsafe_allow_html=True,
    )

# Tage rendern
for woche in monats_tage:
    cols = st.columns(7)
    for i, tag in enumerate(woche):
        with cols[i]:
            if tag.month != ausgewaehlter_monat_idx:
                st.markdown(
                    "<div class='weekday-cell' style='opacity: 0.2;'>•</div>",
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
                # Leicht graues Wochenende
                st.markdown(
                    f"<div class='weekend-cell'>{tag.day}</div>",
                    unsafe_allow_html=True,
                )
            else:
                # Regulärer Wochentag
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

    # --- ANZEIGE-MODUS (Farbige Kacheln) ---
    else:
        if rot_info["ausfall"]:
            st.markdown(
                """
                <div class='role-card cancelled'>
                    <div class='role-title' style='color: #ef4444;'>Meeting Status</div>
                    <div class='role-person' style='color: #dc2626;'>❌ Abgesagt / Ausfall</div>
                    <p style='color: #7f1d1d; margin-top: 8px; font-size: 0.9rem;'>
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
