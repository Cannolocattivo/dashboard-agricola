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
        return dati, True, ""

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
                "registro": [],
            "irrigazione_attiva": False,
            "irrigazione_forzata": False
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
        # I parametri visualizzati nel registro devono essere quelli
        # effettivamente associati alla singola registrazione, non quelli
        # attualmente impostati sul campo. In questo modo, dopo una
        # modifica del campo, lo storico conserva i parametri precedenti.
        righe.append({
            "Campo": r.get("campo", campo.get("nome", "")),
            "Coltivazione": r.get("coltura", campo.get("coltura", "")),
            "Terreno": r.get("terreno", campo.get("terreno", "Franco")),
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
    """Controlla la singola coltura del campo rispetto al terreno scelto."""
    problemi = []
    terreni_ok = TERRENI_OTTIMALI.get(coltura, TIPI_TERRENO)
    if terreno not in terreni_ok:
        problemi.append({
            "coltura": coltura,
            "terreno": terreno,
            "terreni_ok": terreni_ok,
            "messaggio": (
                f"Terreni consigliati: {', '.join(terreni_ok)}."
            )
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
            "coltura": n_colt,
            "terreno": n_terr,
            "portata": n_port,
            "data_semina": n_data.strftime("%Y-%m-%d"),
            "registro": [],
            "irrigazione_attiva": False,
            "irrigazione_forzata": False
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


        # Ogni campo viene gestito come una scheda indipendente,
        # visualizzata in un TabControl. In questo modo i campi non
        # occupano verticalmente tutta la pagina e si lavora su un
        # campo alla volta.
        etichette_campi = []
        for campo in st.session_state.campi:
            coltura_tab = campo.get("coltura", "Pomodoro")
            stato_tab = campo.get("stato", "")
            etichetta_tab = f"🌿 {campo['nome']} — {coltura_tab}"
            if stato_tab == "campo cancellato":
                etichetta_tab += " — campo cancellato"
            etichette_campi.append(etichetta_tab)

        schede_campi = st.tabs(etichette_campi)

        for idx, (campo, scheda_campo) in enumerate(
            zip(st.session_state.campi, schede_campi)
        ):

            coltura = campo.get("coltura", "Pomodoro")
            terreno = campo.get("terreno", "Franco")

            stato_campo = campo.get("stato", "")

            with scheda_campo:

                # Modifica dei parametri del campo già creato.
                # La modifica aggiorna il campo attivo senza alterare il registro
                # storico delle giornate già registrate. Al successivo rerun i
                # Parametri d'Intervento Giornalieri vengono ricalcolati con i nuovi valori.
                if st.button(
                    "✏️ Modifica parametri del campo",
                    key=f"modifica_parametri_{idx}",
                    use_container_width=True
                ):
                    st.session_state[f"modifica_campo_{idx}"] = True

                if st.session_state.get(f"modifica_campo_{idx}", False):
                    st.info(
                        "Modifica i parametri del campo. Le registrazioni già presenti "
                        "nel registro cronologico non verranno riscritte."
                    )

                    with st.form(f"form_modifica_campo_{idx}"):
                        m_nome = st.text_input(
                            "Nome",
                            value=campo.get("nome", "")
                        )
                        m_lat = st.number_input(
                            "Lat",
                            value=float(campo.get("lat", 41.8902)),
                            format="%.4f"
                        )
                        m_lon = st.number_input(
                            "Lon",
                            value=float(campo.get("lon", 12.4922)),
                            format="%.4f"
                        )
                        m_colt = st.selectbox(
                            "Coltivazione",
                            list(DIZIONARIO.keys()),
                            index=(
                                list(DIZIONARIO.keys()).index(campo.get("coltura"))
                                if campo.get("coltura") in DIZIONARIO
                                else 0
                            )
                        )
                        m_terr = st.selectbox(
                            "Tipologia di terreno",
                            TIPI_TERRENO,
                            index=(
                                TIPI_TERRENO.index(campo.get("terreno"))
                                if campo.get("terreno") in TIPI_TERRENO
                                else 0
                            )
                        )
                        m_port = st.number_input(
                            "Portata l/h/mq",
                            min_value=0.0,
                            value=float(campo.get("portata", 15.0))
                        )
                        data_semina_orig = campo.get("data_semina", datetime.now().strftime("%Y-%m-%d"))
                        try:
                            data_semina_mod = datetime.strptime(
                                data_semina_orig, "%Y-%m-%d"
                            ).date()
                        except (TypeError, ValueError):
                            data_semina_mod = datetime.now().date()

                        m_data = st.date_input(
                            "Data Semina",
                            value=data_semina_mod
                        )

                        m_salva, m_annulla = st.columns(2)
                        with m_salva:
                            conferma_modifica = st.form_submit_button(
                                "💾 Salva modifiche",
                                type="primary",
                                use_container_width=True
                            )
                        with m_annulla:
                            annulla_modifica = st.form_submit_button(
                                "Annulla",
                                use_container_width=True
                            )

                    if conferma_modifica:
                        if not m_nome.strip():
                            st.error("Il nome del campo non può essere vuoto.")
                        else:
                            problemi_modifica = coltura_non_ottimale(m_colt, m_terr)
                            if problemi_modifica:
                                st.session_state[f"problemi_modifica_campo_{idx}"] = problemi_modifica
                                st.session_state[f"dati_modifica_campo_{idx}"] = {
                                    "nome": m_nome.strip(),
                                    "lat": m_lat,
                                    "lon": m_lon,
                                    "coltura": m_colt,
                                    "terreno": m_terr,
                                    "portata": m_port,
                                    "data_semina": m_data.strftime("%Y-%m-%d")
                                }
                                st.rerun()
                            else:
                                campo.update({
                                    "nome": m_nome.strip(),
                                    "lat": m_lat,
                                    "lon": m_lon,
                                    "coltura": m_colt,
                                    "terreno": m_terr,
                                    "portata": m_port,
                                    "data_semina": m_data.strftime("%Y-%m-%d")
                                })
                                st.session_state.pop(f"problemi_modifica_campo_{idx}", None)
                                st.session_state.pop(f"dati_modifica_campo_{idx}", None)
                                st.session_state[f"modifica_campo_{idx}"] = False
                                salva_dati()
                                st.success("Parametri del campo aggiornati correttamente.")
                                st.rerun()

                    if annulla_modifica:
                        st.session_state[f"modifica_campo_{idx}"] = False
                        st.session_state.pop(f"problemi_modifica_campo_{idx}", None)
                        st.session_state.pop(f"dati_modifica_campo_{idx}", None)
                        st.rerun()

                # Conferma separata quando la nuova combinazione coltura/terreno
                # non è quella consigliata.
                problemi_modifica = st.session_state.get(
                    f"problemi_modifica_campo_{idx}", []
                )
                dati_modifica = st.session_state.get(
                    f"dati_modifica_campo_{idx}", {}
                )
                if problemi_modifica and dati_modifica:
                    st.warning(
                        f"La combinazione scelta per **{dati_modifica.get('nome', campo['nome'])}** "
                        "non è quella normalmente consigliata."
                    )
                    for problema in problemi_modifica:
                        st.write(
                            f"**{problema['coltura']}** → terreno **{problema['terreno']}**. "
                            f"{problema['messaggio']}"
                        )
                    conf_terreno_mod = st.checkbox(
                        "Voglio comunque utilizzare questo terreno",
                        key=f"conferma_terreno_modifica_{idx}"
                    )
                    c_mod_ok, c_mod_no = st.columns(2)
                    with c_mod_ok:
                        if st.button(
                            "Conferma modifica",
                            key=f"conferma_modifica_terreno_{idx}",
                            type="primary",
                            use_container_width=True,
                            disabled=not conf_terreno_mod
                        ):
                            campo.update(dati_modifica)
                            st.session_state.pop(f"problemi_modifica_campo_{idx}", None)
                            st.session_state.pop(f"dati_modifica_campo_{idx}", None)
                            st.session_state.pop(f"conferma_terreno_modifica_{idx}", None)
                            st.session_state[f"modifica_campo_{idx}"] = False
                            salva_dati()
                            st.success("Parametri del campo aggiornati correttamente.")
                            st.rerun()
                    with c_mod_no:
                        if st.button(
                            "Annulla modifica",
                            key=f"annulla_modifica_terreno_{idx}",
                            use_container_width=True
                        ):
                            st.session_state.pop(f"problemi_modifica_campo_{idx}", None)
                            st.session_state.pop(f"dati_modifica_campo_{idx}", None)
                            st.session_state.pop(f"conferma_terreno_modifica_{idx}", None)
                            st.session_state[f"modifica_campo_{idx}"] = False
                            st.rerun()

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
                    f"Dati meteo aggiornati alle : {datetime.strptime(ultimo_aggiornamento, '%d/%m/%Y %H:%M:%S').strftime('%H:%M:%S %d/%m/%Y')}"
                    if ultimo_aggiornamento
                    else ""
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

                for coltura in [campo.get("coltura", "")]:
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
                        "coltura": n_colt,
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
                    f"Terreno: {terreno}. Tempo di irrigazione impostato: {minuti_irr:.0f} minuti."
                )

# Irrigazione Forzata

                st.write("#### 💧 Comando irrigazione")

                irrigazione_forzata_attiva = bool(
                    campo.get("irrigazione_forzata", False)
                )

                forza_disabilitata = (
                    s_irr != "🚫 Sospesa"
                    or irrigazione_forzata_attiva
                )

                col_forza, col_stop = st.columns(2)

                with col_forza:
                    richiesta_forza = st.button(
                        "💧 Forza irrigazione",
                        key=f"azione_forza_{idx}",
                        disabled=forza_disabilitata,
                        use_container_width=True
                    )

                with col_stop:
                    ferma_forzatura = st.button(
                        "⏹️ Ferma irrigazione forzata",
                        key=f"azione_stop_forza_{idx}",
                        disabled=not irrigazione_forzata_attiva,
                        use_container_width=True
                    )

                if richiesta_forza and not forza_disabilitata:
                    st.session_state[f"richiesta_forza_{idx}"] = True
                    st.rerun()

                if st.session_state.get(f"richiesta_forza_{idx}", False):
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
                        key=f"durata_forza_{idx}"
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
                            key=f"conferma_forza_btn_{idx}",
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
                        st.session_state[f"richiesta_forza_{idx}"] = False
                        st.rerun()

                    if conferma_forzatura:
                        ora_forzatura = datetime.now()
                        minuti_forzati = float(
                            st.session_state.get(
                                f"durata_forza_{idx}",
                                minuti_forzati
                            )
                        )

                        acqua_forzata = (
                            campo["portata"] * minuti_forzati / 60
                            if campo.get("portata", 0) > 0
                            else 0.0
                        )

                        fine_forzata = (
                            ora_forzatura
                            + timedelta(minutes=int(minuti_forzati))
                        ).strftime("%H:%M")

                        campo["irrigazione_forzata"] = True
                        campo["irrigazione_attiva"] = True
                        campo["forzatura_inizio"] = (
                            ora_forzatura.strftime("%Y-%m-%d %H:%M:%S")
                        )
                        campo["forzatura_fine_prevista"] = fine_forzata

                        evento_forzatura = {
                            "campo": campo["nome"],
                            "coltura": campo.get("coltura", ""),
                            "terreno": terreno,
                            "data": ora_forzatura.strftime("%Y-%m-%d"),
                            "ora_rilevazione": ora_forzatura.strftime("%H:%M:%S"),
                            "stato": "💧 IRRIGAZIONE FORZATA ATTIVA",
                            "tipo_evento": "irrigazione_forzata_avvio",
                            "confermata": True,
                            "operazione": "Avvio irrigazione forzata",
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
                            "minuti_irrigazione": round(minuti_forzati, 1)
                        }

                        registra_evento(campo, evento_forzatura)
                        salva_dati()

                        st.session_state[f"richiesta_forza_{idx}"] = False
                        st.rerun()

                if ferma_forzatura and irrigazione_forzata_attiva:
                    ora_stop = datetime.now()

                    campo["irrigazione_forzata"] = False
                    campo["irrigazione_attiva"] = False
                    campo["forzatura_fine_effettiva"] = (
                        ora_stop.strftime("%Y-%m-%d %H:%M:%S")
                    )

                    evento_stop = {
                        "campo": campo["nome"],
                        "coltura": campo.get("coltura", ""),
                        "terreno": terreno,
                        "data": ora_stop.strftime("%Y-%m-%d"),
                        "ora_rilevazione": ora_stop.strftime("%H:%M:%S"),
                        "stato": "⏹️ IRRIGAZIONE FORZATA FERMATA",
                        "tipo_evento": "irrigazione_forzata_stop",
                        "confermata": True,
                        "operazione": "Arresto irrigazione forzata",
                        "temperatura": round(temp, 1),
                        "umidita_aria": round(umid, 1),
                        "pioggia": round(piog, 1),
                        "vento": round(vent, 1),
                        "radiazione": round(rads, 1),
                        "umidita_suolo": round(soil, 3),
                        "pioggia_giornaliera": round(p_dom, 1),
                        "inizio": "",
                        "fine": ora_stop.strftime("%H:%M"),
                        "erogata": 0.0,
                        "risparmiata": 0.0,
                        "minuti_irrigazione": 0.0
                    }

                    registra_evento(campo, evento_stop)
                    salva_dati()

                    st.success(
                        f"Irrigazione forzata fermata alle "
                        f"{ora_stop.strftime('%H:%M:%S')}."
                    )
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
                    "Coltivazione": campo.get("coltura", ""),
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
                        and evento.get("tipo_evento") in ("irrigazione_forzata", "irrigazione_forzata_avvio", "irrigazione_forzata_stop")
                        and evento.get("confermata") is True
                    ):
                        righe_intervento.append({
                            "Campo": evento.get("campo", campo["nome"]),
                            "Coltivazione": evento.get("coltura", coltura),
                            "Terreno": evento.get("terreno", terreno),
                            "Tipo": evento.get("operazione", "Forzatura manuale"),
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

                # Azioni finali della scheda del campo.
                # I due pulsanti sono sempre visibili e chiedono conferma
                # prima di eseguire l'azione.
                col_salva, col_cancella = st.columns(2)

                with col_salva:
                    if st.button(
                        "Salva e chiudi campo",
                        key=f"azione_salva_{idx}",
                        use_container_width=True
                    ):
                        st.session_state[f"richiesta_salva_{idx}"] = True

                with col_cancella:
                    if st.button(
                        "Cancella senza salvare",
                        key=f"azione_cancella_{idx}",
                        use_container_width=True
                    ):
                        st.session_state[f"richiesta_cancella_{idx}"] = True

                if st.session_state.get(f"richiesta_salva_{idx}", False):
                    st.warning(
                        f"Vuoi davvero salvare i dati e chiudere il campo **{campo['nome']}**?"
                    )
                    c_ok, c_no = st.columns(2)

                    with c_ok:
                        if st.button(
                            "Conferma e chiudi",
                            key=f"conferma_salvataggio_btn_{idx}",
                            type="primary",
                            use_container_width=True
                        ):
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

                            # Il campo salvato e chiuso passa nello storico
                            # come "campo raccolto", mantenendo TUTTO il registro.
                            campo["stato"] = "campo raccolto"
                            campo["campo_raccolto"] = True
                            campo["data_raccolta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            st.session_state.archivio.append(
                                campo.copy()
                            )

                            st.session_state.campi.pop(
                                idx
                            )

                            salva_dati()
                            st.session_state[f"richiesta_salva_{idx}"] = False
                            st.session_state[f"campo_chiuso_{idx}"] = True

                            st.success(
                                "Campo archiviato con registro completo!"
                            )

                            st.rerun()

                    with c_no:
                        if st.button(
                            "Annulla",
                            key=f"annulla_salva_{idx}",
                            use_container_width=True
                        ):
                            st.session_state[f"richiesta_salva_{idx}"] = False
                            st.rerun()

                if st.session_state.get(f"richiesta_cancella_{idx}", False):
                    st.warning(
                        f"Vuoi davvero cancellare le modifiche del campo **{campo['nome']}** senza salvarle?"
                    )
                    c_ok, c_no = st.columns(2)

                    with c_ok:
                        if st.button(
                            "Conferma cancellazione",
                            key=f"conferma_cancellazione_btn_{idx}",
                            type="primary",
                            use_container_width=True
                        ):
                            # Non eliminiamo il campo fisicamente: lo
                            # manteniamo nello storico e lo marchiamo
                            # come "campo cancellato".
                            campo["stato"] = "campo cancellato"
                            campo["campo_cancellato"] = True
                            campo["data_cancellazione"] = (
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )

                            st.session_state.archivio.append(
                                campo.copy()
                            )

                            st.session_state.campi.pop(
                                idx
                            )

                            salva_dati()

                            st.session_state[f"richiesta_cancella_{idx}"] = False
                            st.session_state[f"campo_chiuso_{idx}"] = True

                            st.rerun()

                    with c_no:
                        if st.button(
                            "Annulla",
                            key=f"annulla_cancella_{idx}",
                            use_container_width=True
                        ):
                            st.session_state[f"richiesta_cancella_{idx}"] = False
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
            stato_arch = campo.get("stato", "")

            # Nel nome dello storico evidenziamo esplicitamente i campi
            # cancellati; i campi salvati e chiusi restano con il loro nome.
            nome_arch = f"🌾 {campo['nome']} — {coltivazione_arch}"
            if stato_arch == "campo cancellato":
                nome_arch += " — campo cancellato"

            with st.expander(
                nome_arch,
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

                if stato_arch == "campo raccolto":
                    st.write("**Descrizione:** campo raccolto")
                elif stato_arch == "campo cancellato":
                    st.write("**Descrizione:** campo cancellato")
                else:
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
