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
# Hilfsfunktionen für Datenhaltung (Laden / Speichern)
# ---------------------------------------------------------
def lade_daten():
    if DATEI.exists():
        try:
            daten = json.loads(DATEI.read_text(encoding="utf-8"))
            return daten
        except Exception:
            pass
    return {
        "personen": STANDARD_PERSONEN,
        "ausfaelle": [],  # Liste von Datums-Strings "YYYY-MM-DD"
        "manuelle_anpassungen": {},  # "YYYY-MM-DD": {"mod": ..., "proto": ..., "pause": ...}
    }


def speichere_daten(daten):
    DATEI.write_text(
        json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# Daten laden
daten = lade_daten()


# ---------------------------------------------------------
# Rotations-Engine
# ---------------------------------------------------------
def alle_donnerstage_bis(ziel_datum: date):
    """Generiert alle Donnerstage ab START_DATUM bis zum Zieldatum."""
    aktuell = START_DATUM
    donnerstage = []
    while aktuell <= ziel_datum:
        donnerstage.append(aktuell)
        aktuell += timedelta(days=7)
    return donnerstage


def berechne_rotation_fuer_datum(ziel_datum: date, daten: dict):
    """Berechnet fair die Rollen für einen bestimmten Donnerstag unter Berücksichtigung von Ausfällen."""
    if ziel_datum.weekday() != 3:
        return None  # Kein Donnerstag

    ziel_str = ziel_datum.isoformat()

    # 1. Wenn manuell angepasst, diese Werte priorisieren
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

    # 2. Berechnen, wie viele AKTIVE (nicht ausgefallene) Donnerstage vorher lagen
    alle_ststage = alle_donnerstage_bis(ziel_datum)
    aktiver_index = 0

    for d in alle_ststage:
        d_str = d.isoformat()
        ist_ausfall = d_str in daten.get("ausfaelle", [])

        if d == ziel_datum:
            if ist_ausfall:
                # Fällt heute aus? Kein Zähler-Inkrement für Rotation
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

    # Rotation basierend auf aktiver_index
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
# Streamlit Benutzeroberfläche (UI)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Patho ServiceMGMT Rotation", page_icon="📅", layout="centered"
)

st.markdown(
    "<h1 style='text-align: center;'>Patho ServiceMGMT Meeting Rotation</h1>",
    unsafe_allow_html=True,
)

# 1. Monats- & Jahresauswahl für den Kalender
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

# Selected Date State initialisieren
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None
if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = False

# 2. Kalender darstellen
cal = calendar.Calendar(firstweekday=0)  # Montag startet
monats_tage = cal.monthdatescalendar(
    ausgewaehltes_jahr, ausgewaehlter_monat_idx
)

st.markdown(
    "### 📅 "
    + monate[ausgewaehlter_monat_idx - 1]
    + f" {ausgewaehltes_jahr}"
)

# Wochentage Header
cols_header = st.columns(7)
wochentage_kurz = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
for i, col in enumerate(cols_header):
    col.markdown(f"**{wochentage_kurz[i]}**")

# Tage rendern
for woche in monats_tage:
    cols = st.columns(7)
    for i, tag in enumerate(woche):
        with cols[i]:
            # Prüfen ob Tag im aktuellen Monat liegt
            if tag.month != ausgewaehlter_monat_idx:
                st.caption(f"{tag.day}")
                continue

            tag_str = tag.isoformat()
            ist_donnerstag = tag.weekday() == 3

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
            else:
                st.text(f"{tag.day}")

st.divider()

# 3. Details / Bearbeiten-Bereich für das gewählte Datum
sel_tag = st.session_state.get("selected_date")

if sel_tag:
    sel_str = sel_tag.isoformat()
    rot_info = berechne_rotation_fuer_datum(sel_tag, daten)

    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.subheader(f"Meeting am Donnerstag, {sel_tag.strftime('%d.%m.%Y')}")
    with head_col2:
        if st.button("✏️ Bearbeiten / Anpassen"):
            st.session_state["edit_mode"] = not st.session_state["edit_mode"]

    # --- BEARBEITUNGS-MODUS ---
    if st.session_state["edit_mode"]:
        st.info("🛠️ **Eingaben anpassen**")
        with st.form("edit_form"):
            ist_ausfall_chk = st.checkbox(
                "❌ Meeting fällt aus (Rotation verschiebt sich auf nächste Woche)",
                value=rot_info["ausfall"],
            )

            st.write("**Rollenverteilung anpassen:**")
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
                # Ausfall speichern / entfernen
                if ist_ausfall_chk:
                    if sel_str not in daten["ausfaelle"]:
                        daten["ausfaelle"].append(sel_str)
                else:
                    if sel_str in daten["ausfaelle"]:
                        daten["ausfaelle"].remove(sel_str)

                # Manuelle Rollen speichern
                if "manuelle_anpassungen" not in daten:
                    daten["manuelle_anpassungen"] = {}

                daten["manuelle_anpassungen"][sel_str] = {
                    "mod": mod_val,
                    "proto": proto_val,
                    "pause": pause_val,
                }

                speichere_daten(daten)
                st.session_state["edit_mode"] = False
                st.success("Änderungen gespeichert!")
                st.rerun()

    # --- ANZEIGE-MODUS ---
    else:
        if rot_info["ausfall"]:
            st.warning("⚠️ **Dieses Meeting fällt aus!**")
            st.caption(
                "Die geplante Rotation verschiebt sich automatisch auf den nächsten Donnerstag."
            )
        else:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("🎤 Moderierer", rot_info["mod"])
            col_b.metric("📝 Protokollierer", rot_info["proto"])
            col_c.metric("☕ Pause", rot_info["pause"])

            st.markdown("#### E-Mail Nachricht für Kolleginnen:")
            mail_text = f"""Hallo zusammen,

für das Patho ServiceMGMT Meeting am {sel_tag.strftime('%d.%m.%Y')} sind folgende Rollen eingeteilt:

🎤 Moderierer:
{rot_info['mod']}

📝 Protokollierer:
{rot_info['proto']}

Vielen Dank!"""
            st.code(mail_text, language="text")

else:
    st.info("👈 Klicken Sie auf einen blau markierten Donnerstag (📌) im Kalender, um die Rollenverteilung zu sehen.")
