import streamlit as st
import requests
import pandas as pd
import json
import pydeck as pdk
from pathlib import Path
from datetime import datetime, timedelta

# Configurazione

st.set_page_config(
    page_title="AgriSmart",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
   """
   <style>
     .stApp {
       background: linear-gradient(180deg, #f6f8f5 0%, #ffffff 28%);
        }

      .block-container {
          max-width: 1450px;
          padding-top: 1.35rem;
          padding-bottom: 2.5rem;
        }

        /* Header */
        .agri-header {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 1.15rem;
        }

        .agri-logo {
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 14px;
            background: #e8f3e9;
            font-size: 25px;
            box-shadow: inset 0 0 0 1px #d6e8d8;
        }

        .agri-title {
            margin: 0;
            color: #203126;
            font-size: 2rem;
            font-weight: 750;
            letter-spacing: -0.03em;
        }

        .agri-subtitle {
            margin: 2px 0 0 0;
            color: #6a756e;
            font-size: 0.93rem;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #f7faf7;
            border-right: 1px solid #e5ebe6;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.2rem;
        }

        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #28412f;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            font-weight: 650;
            color: #68736b;
            padding-top: 0.75rem;
            padding-bottom: 0.75rem;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #275a32;
        }

        div[data-baseweb="tab-highlight"] {
            background-color: #3c7d48;
            height: 3px;
            border-radius: 3px;
        }

        /* Metriche */
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e2e9e3;
            border-radius: 11px;
            padding: 0.45rem 0.7rem;
            min-height: 0;
            box-shadow: 0 1px 6px rgba(34, 58, 39, 0.035);
        }

        div[data-testid="stMetricLabel"] p {
            color: #6b776f;
            font-size: 0.68rem;
            font-weight: 650;
            margin-bottom: 0.05rem;
        }

        div[data-testid="stMetricValue"] {
            color: #24462c;
            font-size: 1.05rem;
            line-height: 1.15;
            font-weight: 750;
        }

        /* Schede campi */
        div[data-testid="stExpander"] {
            border: 1px solid #dfe7e1;
            border-radius: 16px;
            overflow: hidden;
            background: #ffffff;
            box-shadow: 0 4px 16px rgba(37, 62, 42, 0.045);
            margin-bottom: 0.8rem;
        }

        div[data-testid="stExpander"] summary {
            background: #fbfdfb;
            padding-top: 0.95rem !important;
            padding-bottom: 0.95rem !important;
        }

        div[data-testid="stExpander"] summary:hover {
            background: #f6faf6;
        }

        /* Tabelle */
        div[data-testid="stDataFrame"] {
            border: 1px solid #e1e8e2;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(35, 54, 41, 0.035);
        }

        /* Pulsanti */
        .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 10px;
            font-weight: 650;
            min-height: 2.5rem;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            border-color: #4b8b57;
            color: #275a32;
        }

        /* Input */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div {
            border-radius: 10px;
        }

        /* Messaggi */
        div[data-testid="stAlert"] {
            border-radius: 12px;
        }

        hr {
            border-color: #e6ece7;
            margin: 1.2rem 0;
        }
    </style>

    <div class="agri-header">
        <div class="agri-logo">🌱</div>
        <div>
            <div class="agri-title">AgriSmart</div>
            <div class="agri-subtitle">Controllo dei campi, condizioni meteo e gestione dell'irrigazione</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


FILE_DATI = Path("agri_data.json")


DIZIONARIO = {
    "Pomodoro": {
        "fabbisogno": 5.0,
        "soglia_umidita": 0.25,
        "giorni_maturazione": 100
    },
    "Mais": {
        "fabbisogno": 6.0,
        "soglia_umidita": 0.22,
        "giorni_maturazione": 120
    },
    "Olivo": {
        "fabbisogno": 2.0,
        "soglia_umidita": 0.15,
        "giorni_maturazione": 210
    },
    "Vite": {
        "fabbisogno": 2.5,
        "soglia_umidita": 0.16,
        "giorni_maturazione": 150
    },
    "Patata": {
        "fabbisogno": 4.5,
        "soglia_umidita": 0.24,
        "giorni_maturazione": 110
    },
    "Grano": {
        "fabbisogno": 3.5,
        "soglia_umidita": 0.18,
        "giorni_maturazione": 240
    },
    "Peperone": {
        "fabbisogno": 5.0,
        "soglia_umidita": 0.24,
        "giorni_maturazione": 90
    },
    "Melanzana": {
        "fabbisogno": 5.0,
        "soglia_umidita": 0.24,
        "giorni_maturazione": 90
    },
    "Zucchina": {
        "fabbisogno": 4.5,
        "soglia_umidita": 0.25,
        "giorni_maturazione": 55
    },
    "Cetriolo": {
        "fabbisogno": 5.0,
        "soglia_umidita": 0.25,
        "giorni_maturazione": 60
    },
    "Lattuga": {
        "fabbisogno": 3.0,
        "soglia_umidita": 0.23,
        "giorni_maturazione": 45
    },
    "Cipolla": {
        "fabbisogno": 3.0,
        "soglia_umidita": 0.18,
        "giorni_maturazione": 120
    },
    "Carota": {
        "fabbisogno": 3.0,
        "soglia_umidita": 0.20,
        "giorni_maturazione": 80
    },
    "Fragola": {
        "fabbisogno": 4.0,
        "soglia_umidita": 0.23,
        "giorni_maturazione": 70
    },
    "Melo": {
        "fabbisogno": 3.5,
        "soglia_umidita": 0.18,
        "giorni_maturazione": 180
    },
    "Pesco": {
        "fabbisogno": 4.0,
        "soglia_umidita": 0.18,
        "giorni_maturazione": 150
    },
    "Agrumi": {
        "fabbisogno": 4.0,
        "soglia_umidita": 0.17,
        "giorni_maturazione": 210
    },
    "Girasole": {
        "fabbisogno": 3.5,
        "soglia_umidita": 0.18,
        "giorni_maturazione": 120
    },
    "Soia": {
        "fabbisogno": 4.0,
        "soglia_umidita": 0.20,
        "giorni_maturazione": 130
    },
    "Melone": {
        "fabbisogno": 5.5,
        "soglia_umidita": 0.25,
        "giorni_maturazione": 85
    },
    "Cocomero": {
        "fabbisogno": 6.0,
        "soglia_umidita": 0.25,
        "giorni_maturazione": 90
    },
    "Broccolo": {
        "fabbisogno": 4.0,
        "soglia_umidita": 0.22,
        "giorni_maturazione": 75
    },
    "Cavolfiore": {
        "fabbisogno": 4.0,
        "soglia_umidita": 0.22,
        "giorni_maturazione": 90
    },
    "Spinaci": {
        "fabbisogno": 3.0,
        "soglia_umidita": 0.23,
        "giorni_maturazione": 45
    },
    "Fagiolo": {
        "fabbisogno": 4.0,
        "soglia_umidita": 0.22,
        "giorni_maturazione": 70
    },
    "Pisello": {
        "fabbisogno": 3.5,
        "soglia_umidita": 0.21,
        "giorni_maturazione": 70
    },
    "Riso": {
        "fabbisogno": 6.0,
        "soglia_umidita": 0.30,
        "giorni_maturazione": 160
    },
    "Orzo": {
        "fabbisogno": 3.0,
        "soglia_umidita": 0.18,
        "giorni_maturazione": 150
    },
    "Avena": {
        "fabbisogno": 3.0,
        "soglia_umidita": 0.18,
        "giorni_maturazione": 150
    },
    "Mandorlo": {
        "fabbisogno": 3.0,
        "soglia_umidita": 0.16,
        "giorni_maturazione": 210
    },
    "Noce": {
        "fabbisogno": 3.0,
        "soglia_umidita": 0.16,
        "giorni_maturazione": 210
    },
    "Erba medica": {
        "fabbisogno": 4.0,
        "soglia_umidita": 0.20,
        "giorni_maturazione": 60
    }
}

TIPI_TERRENO = [
    "Sabbioso",
    "Franco-sabbioso",
    "Franco",
    "Franco-argilloso",
    "Argilloso"
]

# Terreni normalmente più adatti alle singole colture.
# Non è un vincolo: serve solo come controllo prima del salvataggio.
TERRENI_OTTIMALI = {
    "Pomodoro": ["Franco-sabbioso", "Franco"],
    "Mais": ["Franco", "Franco-argilloso"],
    "Olivo": ["Sabbioso", "Franco-sabbioso", "Franco"],
    "Vite": ["Sabbioso", "Franco-sabbioso", "Franco"],
    "Patata": ["Sabbioso", "Franco-sabbioso"],
    "Grano": ["Franco", "Franco-argilloso"],
    "Peperone": ["Franco-sabbioso", "Franco"],
    "Melanzana": ["Franco-sabbioso", "Franco"],
    "Zucchina": ["Franco", "Franco-sabbioso"],
    "Cetriolo": ["Franco-sabbioso", "Franco"],
    "Lattuga": ["Franco", "Franco-sabbioso"],
    "Cipolla": ["Sabbioso", "Franco-sabbioso"],
    "Carota": ["Sabbioso", "Franco-sabbioso"],
    "Fragola": ["Franco-sabbioso", "Franco"],
    "Melo": ["Franco", "Franco-argilloso"],
    "Pesco": ["Franco-sabbioso", "Franco"],
    "Agrumi": ["Sabbioso", "Franco-sabbioso", "Franco"],
    "Girasole": ["Franco", "Franco-argilloso"],
    "Soia": ["Franco", "Franco-argilloso"],
    "Melone": ["Sabbioso", "Franco-sabbioso"],
    "Cocomero": ["Sabbioso", "Franco-sabbioso"],
    "Broccolo": ["Franco", "Franco-sabbioso"],
    "Cavolfiore": ["Franco", "Franco-sabbioso"],
    "Spinaci": ["Franco", "Franco-sabbioso"],
    "Fagiolo": ["Franco", "Franco-sabbioso"],
    "Pisello": ["Franco", "Franco-sabbioso"],
    "Riso": ["Franco-argilloso", "Argilloso"],
    "Orzo": ["Franco", "Franco-argilloso"],
    "Avena": ["Franco", "Franco-argilloso"],
    "Mandorlo": ["Sabbioso", "Franco-sabbioso", "Franco"],
    "Noce": ["Franco", "Franco-argilloso"],
    "Erba medica": ["Franco", "Franco-argilloso"]
}

# Il terreno modifica la soglia di umidità: sui terreni più drenanti
# conviene intervenire prima, mentre quelli argillosi trattengono più acqua.
FATTORE_TERRENO = {
    "Sabbioso": 1.15,
    "Franco-sabbioso": 1.08,
    "Franco": 1.00,
    "Franco-argilloso": 0.94,
    "Argilloso": 0.88
}


# Il servizio meteo ogni tanto può metterci qualche secondo in più.
# Evitiamo quindi di far pesare questo problema su tutta la dashboard.
@st.cache_data(ttl=600, show_spinner=False)
def richiesta_meteo(url):
    ultimo_errore = None

    for _ in range(2):
        try:
            risposta = requests.get(url, timeout=(5, 15))
            risposta.raise_for_status()
            dati = risposta.json()

            if not isinstance(dati, dict) or "current" not in dati:
                raise ValueError("risposta meteo non valida")

            return dati

        except (requests.RequestException, ValueError) as errore:
            ultimo_errore = errore

    raise RuntimeError(f"servizio meteo non raggiungibile: {ultimo_errore}")


def leggi_meteo(campo):
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={campo['lat']}&"
        f"longitude={campo['lon']}&"
        "current="
        "temperature_2m,"
        "relative_humidity_2m,"
        "rain,"
        "wind_speed_10m,"
        "shortwave_radiation&"
        "hourly=soil_moisture_3_to_9cm&"
        "daily=rain_sum&"
        "forecast_days=3&"
        "timezone=auto"
    )

    try:
        dati = richiesta_meteo(url)

        # Teniamo in memoria l'ultima risposta buona, così un piccolo
        # problema di rete non manda in tilt il monitoraggio.
        campo["ultimo_meteo"] = {
            "current": dati.get("current", {}),
            "hourly": {
                "time": dati.get("hourly", {}).get("time", []),
                "soil_moisture_3_to_9cm": dati.get("hourly", {}).get(
                    "soil_moisture_3_to_9cm", []
                )
            },
            "daily": {
                "rain_sum": dati.get("daily", {}).get("rain_sum", [])
            },
            "aggiornato": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return dati, True, "Meteo aggiornato correttamente."

    except Exception:
        ultimo = campo.get("ultimo_meteo")

        if ultimo and ultimo.get("current"):
            quando = ultimo.get("aggiornato", "in precedenza")
            return (
                ultimo,
                False,
                f"Il servizio meteo non risponde. Sto usando l'ultima lettura valida ({quando})."
            )

        # Se non abbiamo nemmeno una lettura precedente, non inventiamo
        # valori che potrebbero far partire un'irrigazione per errore.
        return (
            {
                "current": {},
                "hourly": {"time": [], "soil_moisture_3_to_9cm": []},
                "daily": {"rain_sum": [0.0]}
            },
            False,
            "Il servizio meteo non risponde e non ci sono ancora dati disponibili per questo campo."
        )

# Persistenza

def salva_dati():
    dati = {
        "campi": st.session_state.campi,
        "archivio": st.session_state.archivio
    }

    try:
        FILE_DATI.write_text(
            json.dumps(
                dati,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )
    except Exception as e:
        st.error(f"Errore salvataggio dati: {e}")


def carica_dati():
    if not FILE_DATI.exists():
        return {
            "campi": [],
            "archivio": []
        }

    try:
        dati = json.loads(
            FILE_DATI.read_text(
                encoding="utf-8"
            )
        )

        return {
            "campi": dati.get("campi", []),
            "archivio": dati.get("archivio", [])
        }

    except Exception:
        return {
            "campi": [],
            "archivio": []
        }


if "dati_caricati" not in st.session_state:

    dati = carica_dati()

    st.session_state.campi = dati["campi"]
    st.session_state.archivio = dati["archivio"]

    if not st.session_state.campi and not st.session_state.archivio:
        st.session_state.campi = [
            {
                "nome": "Campo Nord",
                "lat": 41.9028,
                "lon": 12.4964,
                "coltura": "Pomodoro",
                "terreno": "Franco",
                "portata": 15.0,
                "data_semina": datetime.now().strftime("%Y-%m-%d"),
                "registro": []
            }
        ]

    for campo in st.session_state.campi:
        campo.setdefault("registro", [])
        campo.setdefault("terreno", "Franco")
        campo.setdefault("coltura", "Pomodoro")

    for campo in st.session_state.archivio:
        campo.setdefault("registro", [])
        campo.setdefault("terreno", "Franco")
        campo.setdefault("coltura", "Pomodoro")

    st.session_state.dati_caricati = True

# Funzioni Registro

def registra_giornata(campo, dati_giorno):
    """
    Aggiunge automaticamente una sola registrazione per campo e giorno.
    Se il giorno è già presente, aggiorna la registrazione.
    """

    data = dati_giorno["data"]

    registro = campo.setdefault("registro", [])

    esistente = None

    for riga in registro:
        # La riga giornaliera può essere aggiornata durante la giornata,
        # ma gli eventi manuali devono restare come registrazioni separate.
        if (
            riga.get("data") == data
            and riga.get("tipo_evento", "giornaliero") == "giornaliero"
        ):
            esistente = riga
            break

    if esistente:
        esistente.update(dati_giorno)
    else:
        registro.append(dati_giorno)

    registro.sort(
        key=lambda x: x.get("data", "")
    )


def registra_evento(campo, evento):
    registro = campo.setdefault("registro", [])
    registro.append(evento)
    registro.sort(key=lambda x: (x.get("data", ""), x.get("ora_rilevazione", "")))


def dati_registro(campo, dati_giorno):
    """
    Costruisce una riga completa del registro giornaliero.
    """

    return {
        "campo": dati_giorno.get("campo", campo.get("nome", "")),
        "coltura": dati_giorno.get("coltura", campo.get("coltura", "")),
        "terreno": dati_giorno.get("terreno", campo.get("terreno", "Franco")),
        "data": dati_giorno["data"],
        "ora_rilevazione": dati_giorno["ora_rilevazione"],
        "stato": dati_giorno["stato"],
        "temperatura": round(dati_giorno["temperatura"], 1),
        "umidita_aria": round(dati_giorno["umidita_aria"], 1),
        "pioggia": round(dati_giorno["pioggia"], 1),
        "vento": round(dati_giorno["vento"], 1),
        "radiazione": round(dati_giorno["radiazione"], 1),
        "umidita_suolo": round(dati_giorno["umidita_suolo"], 3),
        "pioggia_giornaliera": round(
            dati_giorno["pioggia_giornaliera"],
            1
        ),
        "inizio": dati_giorno["inizio"],
        "fine": dati_giorno["fine"],
        "erogata": round(dati_giorno["erogata"], 1),
        "risparmiata": round(dati_giorno["risparmiata"], 1)
    }


def mostra_registro(campo):
    registro = campo.get("registro", [])

    if not registro:
        st.info("Nessuna registrazione disponibile.")
        return

    righe = []

    for r in reversed(registro):
        righe.append({
            "Campo": campo.get("nome", ""),
            "Coltivazione": ", ".join(campo.get("coltura", "")),
            "Terreno": campo.get("terreno", "Franco"),
            "Data": r.get("data", ""),
            "Ora": r.get("ora_rilevazione", ""),
            "Evento": r.get("tipo_evento", "giornaliero"),
            "Stato": r.get("stato", ""),
            "Temp.": f"{r.get('temperatura', 0):.1f} °C",
            "Umidità aria": f"{r.get('umidita_aria', 0):.1f} %",
            "Pioggia": f"{r.get('pioggia', 0):.1f} mm",
            "Vento": f"{r.get('vento', 0):.1f} km/h",
            "Radiazione": f"{r.get('radiazione', 0):.0f} W/m²",
            "Umidità suolo": f"{r.get('umidita_suolo', 0):.3f}",
            "Pioggia giorno": f"{r.get('pioggia_giornaliera', 0):.1f} mm",
            "Inizio": r.get("inizio", ""),
            "Fine": r.get("fine", ""),
            "Erogata": f"{r.get('erogata', 0):.1f} mm",
            "Risparmiata": f"{r.get('risparmiata', 0):.1f} mm",
            "Durata irrigazione": (
                f"{r.get('minuti_irrigazione', 0):.0f} min"
                if r.get("tipo_evento") == "irrigazione_forzata"
                else ""
            )
        })

    st.dataframe(
        pd.DataFrame(righe),
        use_container_width=True,
        hide_index=True
    )


def coltura_non_ottimale(coltura, terreno):
    """Restituisce le colture che non sono nella fascia di terreno consigliata."""
    problemi = []
    for coltura in [coltura]:
        terreni_ok = TERRENI_OTTIMALI.get(coltura, TIPI_TERRENO)
        if terreno not in terreni_ok:
            problemi.append({
                "coltura": coltura,
                "terreni_ok": terreni_ok
            })
    return problemi


def salva_nuovo_campo(dati):
    st.session_state.campi.append(dati)
    salva_dati()
    st.rerun()

# Pannello laterale

st.sidebar.header("⚙️ Opzioni")


with st.sidebar.form("form_c", clear_on_submit=True):

    st.write("### ➕ Nuovo Campo")

    n_nome = st.text_input("Nome")

    n_lat = st.number_input(
        "Lat",
        value=41.8902,
        format="%.4f"
    )

    n_lon = st.number_input(
        "Lon",
        value=12.4922,
        format="%.4f"
    )

    n_colt = st.selectbox(
        "Coltivazione",
        list(DIZIONARIO.keys()),
        index=list(DIZIONARIO.keys()).index("Pomodoro") if "Pomodoro" in DIZIONARIO else 0,
    )

    n_terr = st.selectbox(
        "Tipologia di terreno",
        TIPI_TERRENO,
        index=2
    )

    n_port = st.number_input(
        "Portata l/h/mq",
        value=15.0
    )

    n_data = st.date_input(
        "Data Semina",
        datetime.now()
    )

    sub = st.form_submit_button("Salva")

    if sub and n_nome and n_colt:
        nuovo_campo = {
            "nome": n_nome,
            "lat": n_lat,
            "lon": n_lon,
            "coltura": n_colt[0],
            "terreno": n_terr,
            "portata": n_port,
            "data_semina": n_data.strftime("%Y-%m-%d"),
            "registro": []
        }

        problemi_terreno = coltura_non_ottimale(n_colt, n_terr)

        if problemi_terreno:
            st.session_state.campo_da_confermare = nuovo_campo
            st.session_state.problemi_terreno = problemi_terreno
            st.rerun()
        else:
            salva_nuovo_campo(nuovo_campo)


# Se la combinazione coltivazione/terreno non è consigliata,
# chiediamo una conferma esplicita prima di creare il campo.
if st.session_state.get("campo_da_confermare"):
    campo_proposto = st.session_state.campo_da_confermare
    problemi_terreno = st.session_state.get("problemi_terreno", [])

    st.sidebar.warning(
        f"La combinazione scelta per **{campo_proposto['nome']}** non è quella normalmente consigliata."
    )

    for problema in problemi_terreno:
        st.sidebar.write(
            f"**{problema['coltura']}** → terreno **{campo_proposto['terreno']}**. "
            f"Più indicati: {', '.join(problema['terreni_ok'])}."
        )

    conferma = st.sidebar.checkbox(
        "Voglio comunque utilizzare questo terreno",
        key="conferma_terreno"
    )

    c_ok, c_no = st.sidebar.columns(2)

    with c_ok:
        if st.button("Conferma", key="conferma_campo", disabled=not conferma, use_container_width=True):
            salva_nuovo_campo(campo_proposto)

    with c_no:
        if st.button("Annulla", key="annulla_campo", use_container_width=True):
            st.session_state.pop("campo_da_confermare", None)
            st.session_state.pop("problemi_terreno", None)
            st.session_state.pop("conferma_terreno", None)
            st.rerun()


if st.sidebar.button("💾 Salva dati"):

    salva_dati()
    st.sidebar.success("Dati salvati.")

# Schede principali

t_mon, t_map, t_arc = st.tabs([
    "📊 Monitoraggio",
    "🗺️ Mappa",
    "🗄️ Archivio"
])

# Monitoraggio dei campi

with t_mon:

    if not st.session_state.campi:

        st.info("Nessun campo.")

    else:
        totale_campi = len(st.session_state.campi)
        totale_colture = len(st.session_state.campi)
        terreni_presenti = len(set(
            c.get("terreno", "Franco") for c in st.session_state.campi
        ))

        k1, k2, k3 = st.columns(3)
        k1.metric("Campi attivi", totale_campi)
        k2.metric("Coltivazioni gestite", totale_colture)
        k3.metric("Tipi di terreno", terreni_presenti)

        st.markdown("<hr>", unsafe_allow_html=True)


        for idx, campo in enumerate(
            st.session_state.campi
        ):

            coltura = campo.get("coltura", "Pomodoro")
            terreno = campo.get("terreno", "Franco")

            with st.expander(
                f"🌿 {campo['nome']} — {coltura}",
                expanded=True
            ):

                conferma_ok = st.session_state.get("irrigazione_forzata_confermata")
                if conferma_ok and conferma_ok.get("campo") == campo["nome"]:
                    st.success(
                        f"Irrigazione forzata registrata alle {conferma_ok['timestamp']} "
                        f"per {conferma_ok['minuti']:.0f} minuti."
                    )
                    st.session_state.pop("irrigazione_forzata_confermata", None)

# Dati Meteo

                meteo, meteo_aggiornato, meteo_nota = leggi_meteo(campo)

                cur = meteo.get("current", {})
                temp = cur.get("temperature_2m", 0.0)
                umid = cur.get("relative_humidity_2m", 0.0)
                piog = cur.get("rain", 0.0)
                vent = cur.get("wind_speed_10m", 0.0)
                rads = cur.get("shortwave_radiation", 0.0)

                hrs = meteo.get("hourly", {})
                l_soil = hrs.get("soil_moisture_3_to_9cm", [])
                l_val = [v for v in l_soil if v is not None]
                soil = l_val[-1] if l_val else None

                dly = meteo.get("daily", {})
                p_prev = dly.get("rain_sum", [0.0])
                p_dom = p_prev[0] if p_prev else 0.0

                if not meteo_aggiornato:
                    st.warning(meteo_nota)

                meteo_pronto = bool(meteo_aggiornato or campo.get("ultimo_meteo"))
                if soil is None:
                    meteo_pronto = False
                    soil = 0.0

                # RIEPILOGO
                # ====================================================

                ultimo_aggiornamento = campo.get("ultimo_meteo", {}).get("aggiornato")

                if ultimo_aggiornamento:
                    try:
                        ultimo_aggiornamento = datetime.strptime(
                            ultimo_aggiornamento, "%Y-%m-%d %H:%M:%S"
                        ).strftime("%d/%m/%Y %H:%M:%S")
                    except ValueError:
                        pass

                testo_meteo = (
                    f"Meteo aggiornato correttamente. Ultimo aggiornamento: {ultimo_aggiornamento}"
                    if ultimo_aggiornamento
                    else "Meteo aggiornato correttamente."
                )

                st.markdown(
                    f"""
                    <div style="display:flex; align-items:baseline; gap:12px; margin:0.75rem 0 0.5rem 0;">
                        <h3 style="margin:0; font-size:1.17rem; line-height:1.3;">🌤️ Condizioni attuali</h3>
                        <span style="color:#6b776f; font-size:0.8rem;">{testo_meteo}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                c1, c2, c3, c4, c5, c6 = st.columns(6)

                c1.metric(
                    "Temp. Aria",
                    f"{temp:.1f} °C"
                )

                c2.metric(
                    "Umidità Aria",
                    f"{umid:.0f} %"
                )

                c3.metric(
                    "Pioggia",
                    f"{piog:.1f} mm"
                )

                c4.metric(
                    "Vento",
                    f"{vent:.1f} km/h"
                )

                c5.metric(
                    "Radiazione",
                    f"{rads:.0f} W/m²"
                )

                c6.metric(
                    "Umidità Suolo",
                    f"{soil:.3f}"
                )

# Calcolo Irrigazione

                oggi = datetime.now().strftime("%Y-%m-%d")
                g_irr = datetime.now().strftime("%d/%m/%Y")
                ora_rilevazione = datetime.now().strftime("%H:%M:%S")

                # Ogni coltivazione viene calcolata separatamente.
                # Il campo però ha un solo impianto: se la coltivazione
                # vengono irrigate insieme, il tempo di funzionamento
                # necessario è quello della coltivazione che richiede più acqua.
                fattore_terreno = FATTORE_TERRENO.get(terreno, 1.0)
                calcoli_irr = []

                for coltura in [coltura]:
                    info = DIZIONARIO[coltura]
                    fabb = info["fabbisogno"] * fattore_terreno
                    sogl = info["soglia_umidita"]
                    intg = max(0.0, fabb - piog)

                    if piog >= fabb or p_dom >= fabb:
                        stato_colt = "🚫 Sospesa"
                        acqua = 0.0
                    elif soil < sogl:
                        stato_colt = "💧 Attiva"
                        acqua = intg
                    else:
                        stato_colt = "✅ Sospesa"
                        acqua = 0.0

                    minuti = (acqua / campo["portata"]) * 60 if campo["portata"] > 0 else 0
                    calcoli_irr.append({
                        "coltura": coltura,
                        "fabbisogno": fabb,
                        "soglia": sogl,
                        "stato": stato_colt,
                        "acqua": acqua,
                        "minuti": minuti,
                        "maturazione": info["giorni_maturazione"]
                    })

                # Irrigazione contemporanea: un solo impianto alimenta
                # tutte la coltivazione del campo, quindi non sommiamo
                # i minuti delle colture (evitando di irrigare due volte).
                attive = [x for x in calcoli_irr if x["stato"] == "💧 Attiva"]
                if not meteo_pronto:
                    attive = []
                a_smr = max((x["acqua"] for x in attive), default=0.0)
                minuti_irr = max((x["minuti"] for x in attive), default=0.0)

                if not meteo_pronto:
                    s_irr = "⚠️ In attesa del meteo"
                elif attive:
                    s_irr = "💧 Attiva"
                else:
                    s_irr = "🚫 Sospesa"

                o_fin = (
                    datetime.strptime("06:00", "%H:%M")
                    + timedelta(minutes=int(minuti_irr))
                ).strftime("%H:%M")

                risp = max(
                    0.0,
                    max((x["fabbisogno"] for x in calcoli_irr), default=0.0) - a_smr
                )

                st.write("### 🌱 Irrigazione per coltivazione")
                df_irr = pd.DataFrame([
                    {
                        "Coltivazione": x["coltura"],
                        "Terreno": terreno,
                        "Fabbisogno": f"{x['fabbisogno']:.1f} mm",
                        "Soglia suolo": f"{x['soglia']:.3f}",
                        "Stato": x["stato"],
                        "Acqua necessaria": f"{x['acqua']:.1f} mm",
                        "Tempo": f"{x['minuti']:.0f} min"
                    }
                    for x in calcoli_irr
                ])
                st.dataframe(
                    df_irr,
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    f"Terreno: {terreno}. Con un unico impianto la coltivazione "
                    f"vengono gestite insieme: il tempo impostato è quello "
                    f"della richiesta maggiore ({minuti_irr:.0f} minuti)."
                )

# Irrigazione Forzata

                st.write("#### 💧 Comando irrigazione")

                forza_key = f"forza_attiva_{idx}"
                durata_key = f"durata_forza_{idx}"

                if st.button(
                    "💧 Forza irrigazione del campo",
                    key=f"forza_irr_{idx}",
                    use_container_width=False
                ):
                    st.session_state[forza_key] = True
                    st.session_state.pop("irrigazione_forzata_confermata", None)
                    st.rerun()

                if st.session_state.get(forza_key, False):
                    st.warning(
                        f"Stai per irrigare manualmente **{campo['nome']}**. "
                        "Indica la durata e conferma l'intervento."
                    )

                    minuti_forzati = st.number_input(
                        "Durata irrigazione (minuti)",
                        min_value=1,
                        max_value=1440,
                        value=30,
                        step=5,
                        key=durata_key
                    )

                    acqua_forzata = (
                        campo["portata"] * minuti_forzati / 60
                        if campo.get("portata", 0) > 0
                        else 0.0
                    )
                    ora_inizio_forzata = datetime.now()
                    fine_forzata = (
                        ora_inizio_forzata
                        + timedelta(minutes=int(minuti_forzati))
                    ).strftime("%H:%M")

                    st.caption(
                        f"Durata scelta: **{minuti_forzati:.0f} minuti** · "
                        f"Acqua stimata: **{acqua_forzata:.1f} mm** · "
                        f"Fine prevista: **{fine_forzata}**"
                    )

                    c_forza1, c_forza2 = st.columns(2)

                    with c_forza1:
                        conferma_forzatura = st.button(
                            "Conferma irrigazione",
                            key=f"conferma_forza_{idx}",
                            type="primary",
                            use_container_width=True
                        )

                    with c_forza2:
                        annulla_forzatura = st.button(
                            "Annulla",
                            key=f"annulla_forza_{idx}",
                            use_container_width=True
                        )

                    if annulla_forzatura:
                        st.session_state.pop(forza_key, None)
                        st.session_state.pop(durata_key, None)
                        st.rerun()

                    if conferma_forzatura:
                        ora_forzatura = datetime.now()
                        minuti_forzati = float(st.session_state.get(durata_key, minuti_forzati))
                        acqua_forzata = (
                            campo["portata"] * minuti_forzati / 60
                            if campo.get("portata", 0) > 0
                            else 0.0
                        )
                        fine_forzata = (
                            ora_forzatura
                            + timedelta(minutes=int(minuti_forzati))
                        ).strftime("%H:%M")

                        evento_forzatura = {
                            "campo": campo["nome"],
                            "coltura": n_colt,
                            "terreno": terreno,
                            "data": ora_forzatura.strftime("%Y-%m-%d"),
                            "ora_rilevazione": ora_forzatura.strftime("%H:%M:%S"),
                            "stato": "💧 IRRIGAZIONE FORZATA",
                            "tipo_evento": "irrigazione_forzata",
                            "confermata": True,
                            "temperatura": round(temp, 1),
                            "umidita_aria": round(umid, 1),
                            "pioggia": round(piog, 1),
                            "vento": round(vent, 1),
                            "radiazione": round(rads, 1),
                            "umidita_suolo": round(soil, 3),
                            "pioggia_giornaliera": round(p_dom, 1),
                            "inizio": ora_forzatura.strftime("%H:%M"),
                            "fine": fine_forzata,
                            "erogata": round(acqua_forzata, 1),
                            "risparmiata": 0.0,
                            "minuti_irrigazione": round(minuti_forzati, 1),
                            "coltura_calcolata": calcoli_irr
                        }

                        registra_evento(campo, evento_forzatura)
                        salva_dati()

                        # Pulizia immediata dello stato della richiesta.
                        # Non usiamo un flag di conferma persistente: dopo il rerun
                        # la finestra di autorizzazione non viene ricreata.
                        st.session_state.pop(forza_key, None)
                        st.session_state.pop(durata_key, None)
                        st.session_state["irrigazione_forzata_confermata"] = {
                            "campo": campo["nome"],
                            "minuti": minuti_forzati,
                            "timestamp": ora_forzatura.strftime("%H:%M:%S")
                        }
                        st.rerun()

# Registrazione Automatica Giornaliera

                dati_giorno = {
                    "campo": campo["nome"],
                    "coltura": n_colt,
                    "terreno": terreno,
                    "tipo_evento": "giornaliero",
                    "data": oggi,
                    "ora_rilevazione": ora_rilevazione,
                    "stato": s_irr,
                    "temperatura": temp,
                    "umidita_aria": umid,
                    "pioggia": piog,
                    "vento": vent,
                    "radiazione": rads,
                    "umidita_suolo": soil,
                    "pioggia_giornaliera": p_dom,
                    "inizio": "06:00",
                    "fine": o_fin,
                    "erogata": a_smr,
                    "risparmiata": risp
                }

                registra_giornata(
                    campo,
                    dati_registro(
                        campo,
                        dati_giorno
                    )
                )

                # Salvataggio automatico.
                # La stessa data viene aggiornata e non duplicata.
                salva_dati()

# Parametri D'Intervento Giornalieri

                st.write(
                    "### 📋 Parametri d'Intervento Giornalieri"
                )

                righe_intervento = [{
                    "Campo": campo["nome"],
                    "Coltivazione": coltivazione,
                    "Terreno": terreno,
                    "Tipo": "Automatico",
                    "Stato": s_irr,
                    "Giorno": g_irr,
                    "Temp. Aria": f"{temp:.1f} °C",
                    "Umidità Aria": f"{umid:.0f} %",
                    "Pioggia": f"{piog:.1f} mm",
                    "Vento": f"{vent:.1f} km/h",
                    "Radiazione Solare": f"{rads:.0f} W/m²",
                    "Umidità Suolo": f"{soil:.3f}",
                    "Pioggia Giorno": f"{p_dom:.1f} mm",
                    "Inizio": "06:00",
                    "Fine": o_fin,
                    "Erogata": f"{a_smr:.1f} mm",
                    "Durata": f"{minuti_irr:.0f} min",
                    "Risparmiata": f"{risp:.1f} mm"
                }]

                # Le irrigazioni forzate sono eventi indipendenti dalla riga
                # giornaliera: vengono mostrate qui e restano nello storico.
                for evento in campo.get("registro", []):
                    if (
                        evento.get("data") == oggi
                        and evento.get("tipo_evento") == "irrigazione_forzata"
                        and evento.get("confermata") is True
                    ):
                        righe_intervento.append({
                            "Campo": evento.get("campo", campo["nome"]),
                            "Coltivazione": evento.get("coltura", coltura),
                            "Terreno": evento.get("terreno", terreno),
                            "Tipo": "Forzatura manuale",
                            "Stato": evento.get("stato", "💧 IRRIGAZIONE FORZATA"),
                            "Giorno": datetime.strptime(evento["data"], "%Y-%m-%d").strftime("%d/%m/%Y"),
                            "_ora_evento": evento.get("ora_rilevazione", "00:00:00"),
                            "Temp. Aria": f"{evento.get('temperatura', 0):.1f} °C",
                            "Umidità Aria": f"{evento.get('umidita_aria', 0):.0f} %",
                            "Pioggia": f"{evento.get('pioggia', 0):.1f} mm",
                            "Vento": f"{evento.get('vento', 0):.1f} km/h",
                            "Radiazione Solare": f"{evento.get('radiazione', 0):.0f} W/m²",
                            "Umidità Suolo": f"{evento.get('umidita_suolo', 0):.3f}",
                            "Pioggia Giorno": f"{evento.get('pioggia_giornaliera', 0):.1f} mm",
                            "Inizio": evento.get("inizio", ""),
                            "Fine": evento.get("fine", ""),
                            "Erogata": f"{evento.get('erogata', 0):.1f} mm",
                            "Durata": f"{evento.get('minuti_irrigazione', 0):.0f} min",
                            "Risparmiata": "0.0 mm"
                        })

                # Mettiamo sempre l'evento più recente in alto.
                # Per la riga automatica usiamo l'orario di rilevazione;
                # per le forzature usiamo l'orario in cui sono state autorizzate.
                def _ordine_intervento(riga):
                    if riga.get("Tipo") == "Forzatura manuale":
                        try:
                            return datetime.strptime(
                                riga.get("Giorno", "01/01/1970") + " " + riga.get("_ora_evento", "00:00:00"),
                                "%d/%m/%Y %H:%M:%S"
                            )
                        except ValueError:
                            return datetime.min

                    try:
                        return datetime.strptime(
                            riga.get("Giorno", "01/01/1970") + " " + riga.get("_ora_evento", "00:00:00"),
                            "%d/%m/%Y %H:%M:%S"
                        )
                    except ValueError:
                        return datetime.min

                righe_intervento[0]["_ora_evento"] = ora_rilevazione

                for riga in righe_intervento[1:]:
                    if not riga.get("_ora_evento"):
                        riga["_ora_evento"] = "00:00:00"

                righe_intervento.sort(key=_ordine_intervento, reverse=True)

                for riga in righe_intervento:
                    riga.pop("_ora_evento", None)

                df_oggi = pd.DataFrame(righe_intervento)

                st.dataframe(
                    df_oggi,
                    use_container_width=True,
                    hide_index=True
                )

# Registro Cronologico Del Campo

                st.write(
                    "### 📚 Registro cronologico del campo"
                )

                mostra_registro(campo)

# Grafico Umidità Suolo

                if (
                    l_soil
                    and hrs.get("time")
                ):

                    df_g = pd.DataFrame({
                        "Ora": pd.to_datetime(
                            hrs["time"]
                        ),
                        "Umidità": l_soil
                    }).set_index("Ora")

                    st.write(
                        "#### 📈 Umidità del suolo"
                    )

                    st.line_chart(
                        df_g,
                        height=150
                    )

# Previsione Raccolta

                d_sem = datetime.strptime(
                    campo["data_semina"],
                    "%Y-%m-%d"
                )

                g_pass = (
                    datetime.now() -
                    d_sem
                ).days

                corr = 0

                if temp > 28.0:
                    corr = -4

                if temp < 12.0:
                    corr = 6

                previsione = []
                for calcolo in calcoli_irr:
                    g_rim = max(
                        0,
                        (calcolo["maturazione"] - g_pass) + corr
                    )
                    d_rac = (
                        datetime.now() +
                        timedelta(days=g_rim)
                    ).strftime("%d/%m/%Y")
                    previsione.append({
                        "Coltivazione": calcolo["coltura"],
                        "Giorni rimasti": g_rim,
                        "Data stimata": d_rac
                    })

                st.write("### 🌾 Previsione raccolta")
                st.dataframe(
                    pd.DataFrame(previsione),
                    use_container_width=True,
                    hide_index=True
                )

# Chiusura Campo

                with st.form(
                    f"f_ch_{idx}"
                ):

                    st.write("🏁 Chiusura")

                    cx1, cx2 = st.columns(2)

                    with cx1:

                        q_rac = st.number_input(
                            "Quintali *",
                            min_value=0.1,
                            step=0.1,
                            key=f"q_{idx}"
                        )

                    with cx2:

                        n_rac = st.text_input(
                            "Note",
                            key=f"n_{idx}"
                        )

                    btn = st.form_submit_button(
                        "🎉 Salva"
                    )

                    if btn:

                        campo["data_raccolto"] = (
                            datetime.now().strftime(
                                "%d/%m/%Y"
                            )
                        )

                        campo["quintali"] = q_rac

                        campo["note"] = (
                            n_rac
                            if n_rac
                            else "Standard"
                        )

                        # Salviamo nel registro anche l'evento
                        # di raccolta, mantenendo la cronologia.
                        campo.setdefault(
                            "registro",
                            []
                        ).append({
                            "data": oggi,
                            "ora_rilevazione": (
                                datetime.now().strftime(
                                    "%H:%M:%S"
                                )
                            ),
                            "stato": "🎉 RACCOLTA",
                            "temperatura": temp,
                            "umidita_aria": umid,
                            "pioggia": piog,
                            "vento": vent,
                            "radiazione": rads,
                            "umidita_suolo": soil,
                            "pioggia_giornaliera": p_dom,
                            "inizio": "",
                            "fine": "",
                            "erogata": 0.0,
                            "risparmiata": 0.0,
                            "quintali": q_rac,
                            "note": (
                                n_rac
                                if n_rac
                                else "Standard"
                            )
                        })

                        # Il campo raccolto passa nello storico
                        # mantenendo TUTTO il registro.
                        st.session_state.archivio.append(
                            campo.copy()
                        )

                        st.session_state.campi.pop(
                            idx
                        )

                        salva_dati()

                        st.success(
                            "Campo archiviato con registro completo!"
                        )

                        st.rerun()

# Mappa dei campi

with t_map:

    if st.session_state.campi:

        df_m = pd.DataFrame([
            {
                "latitude": c["lat"],
                "longitude": c["lon"],
                "Campo": c["nome"],
                "Coltivazione": ", ".join(
                    c.get("coltura", "")
                ),
                "Terreno": c.get("terreno", "Franco")
            }
            for c in st.session_state.campi
        ])

        # Punti ben visibili anche con i temi chiari/scuri di Streamlit.
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_m,
            get_position="[longitude, latitude]",
            get_radius=180,
            get_fill_color=[38, 122, 72, 210],
            get_line_color=[20, 70, 40, 255],
            line_width_min_pixels=2,
            pickable=True,
            stroked=True,
            filled=True
        )

        labels = pdk.Layer(
            "TextLayer",
            data=df_m,
            get_position="[longitude, latitude]",
            get_text="Campo",
            get_size=17,
            get_color=[30, 45, 35, 255],
            get_alignment_baseline="bottom",
            get_pixel_offset=[0, -18],
            billboard=True,
            pickable=False
        )

        colture_labels = pdk.Layer(
            "TextLayer",
            data=df_m,
            get_position="[longitude, latitude]",
            get_text="Coltivazione",
            get_size=12,
            get_color=[70, 80, 70, 255],
            get_alignment_baseline="top",
            get_pixel_offset=[0, 18],
            billboard=True,
            pickable=False
        )

        view = pdk.ViewState(
            latitude=df_m["latitude"].mean(),
            longitude=df_m["longitude"].mean(),
            zoom=12
        )

        st.pydeck_chart(
            pdk.Deck(
                layers=[layer, labels, colture_labels],
                initial_view_state=view,
                map_style="light",
                tooltip={
                    "html": "<b>{Campo}</b><br/>Coltivazione: {Coltivazione}<br/>Terreno: {Terreno}",
                }
            ),
            use_container_width=True
        )

        st.caption("I nomi dei campi sono mostrati direttamente sulla mappa; passando sul punto trovi anche coltivazione e terreno.")

    else:

        st.info("Nessun campo.")

# Archivio

with t_arc:

    st.write("## 🗄️ Storico campi")

    if not st.session_state.archivio:

        st.caption("Vuoto.")

    else:

        for campo in st.session_state.archivio:

            coltivazione_arch = campo.get("coltura", "")
            terreno_arch = campo.get("terreno", "Franco")

            with st.expander(
                f"🌾 {campo['nome']} — {coltivazione_arch}",
                expanded=False
            ):

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Quintali",
                    f"{campo.get('quintali', 0):.1f}"
                )

                c2.metric(
                    "Semina",
                    campo.get(
                        "data_semina",
                        "-"
                    )
                )

                c3.metric(
                    "Raccolto",
                    campo.get(
                        "data_raccolto",
                        "-"
                    )
                )

                c4.metric(
                    "Terreno",
                    terreno_arch
                )

                st.write("**Coltivazione:** " + coltivazione_arch)
                st.write(f"**Tipologia terreno:** {terreno_arch}")
                st.write(
                    f"**Note:** {campo.get('note', '-')}"
                )

                st.write(
                    "### 📚 Registro cronologico completo"
                )

                mostra_registro(campo)

# Salvataggio automatico

st.sidebar.caption(
    "💾 Il registro giornaliero viene salvato "
    "automaticamente in agri_data.json"
)
