import json
from datetime import datetime
from pathlib import Path
import streamlit as st

# Pfad zur JSON-Speicherdatei
DATEI = Path(__file__).with_name("patho_rotation.json")


def lade_daten():
    if DATEI.exists():
        try:
            return json.loads(DATEI.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "letzte": {"datum": "", "mod": "", "proto": "", "pause": ""},
        "aktuell": {
            "datum": datetime.now().strftime("%d.%m.%Y"),
            "mod": "",
            "proto": "",
            "pause": "",
        },
        "text": "",
    }


def speichere_daten(daten):
    DATEI.write_text(
        json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# Streamlit UI Konfiguration
st.set_page_config(
    page_title="Patho ServiceMGMT Rotation", page_icon="🔄", layout="wide"
)

st.title("Patho ServiceMGMT Meeting Rotation")

# Daten laden
daten = lade_daten()

# Spalten-Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Letzte Rotation (Rückblick)")
    st.text_input(
        "Datum (Rückblick)",
        value=daten["letzte"].get("datum", ""),
        disabled=True,
    )
    st.text_input(
        "Moderierer (Rückblick)",
        value=daten["letzte"].get("mod", ""),
        disabled=True,
    )
    st.text_input(
        "Protokollierer (Rückblick)",
        value=daten["letzte"].get("proto", ""),
        disabled=True,
    )
    st.text_input(
        "Pause (Rückblick)",
        value=daten["letzte"].get("pause", ""),
        disabled=True,
    )

with col2:
    st.subheader("Aktuelle Rotation")
    akt_datum = st.text_input(
        "Datum", value=daten["aktuell"].get("datum", "")
    )
    akt_mod = st.text_input("Moderierer", value=daten["aktuell"].get("mod", ""))
    akt_proto = st.text_input(
        "Protokollierer", value=daten["aktuell"].get("proto", "")
    )
    akt_pause = st.text_input("Pause", value=daten["aktuell"].get("pause", ""))

# Nächste Rotation Button
if st.button("🔄 Nächste Rotation erzeugen", type="primary"):
    if akt_datum and akt_mod and akt_proto and akt_pause:
        # Rotation umsetzen
        neuer_mod = akt_pause
        neuer_proto = akt_mod
        neue_pause = akt_proto

        # Mailtext erzeugen
        mail = f"""Hallo zusammen,

für das Patho ServiceMGMT Meeting am {akt_datum} sind folgende Rollen eingeteilt:

🎤 Moderierer:
{neuer_mod}

📝 Protokollierer:
{neuer_proto}

Vielen Dank!"""

        # Stand aktualisieren
        daten = {
            "letzte": {
                "datum": akt_datum,
                "mod": akt_mod,
                "proto": akt_proto,
                "pause": akt_pause,
            },
            "aktuell": {
                "datum": datetime.now().strftime("%d.%m.%Y"),
                "mod": neuer_mod,
                "proto": neuer_proto,
                "pause": neue_pause,
            },
            "text": mail,
        }

        speichere_daten(daten)
        st.rerun()

st.subheader("Nachricht für Kollegen:")
nachricht = st.text_area(
    "Mailtext", value=daten.get("text", ""), height=220, label_visibility="collapsed"
)

# Äderungen speichern, falls manuell im Textfeld gearbeitet wurde
if nachricht != daten.get("text", ""):
    daten["text"] = nachricht
    speichere_daten(daten)