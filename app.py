```python
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta


st.set_page_config(
    page_title="Dashboard Agricola Professionale",
    layout="wide"
)

st.title("🚜 Smart Farming Dashboard: Monitoraggio, Mappe & Gestione Cicli")


DIZIONARIO_LOCALE = {
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
    }
}


TIPI_TERRENO = [
    "Argilloso",
    "Sabbioso",
    "Limoso",
    "Franco",
    "Franco-argilloso",
    "Franco-sabbioso",
    "Calcareo"
]


if "campi" not in st.session_state:
    st.session_state.campi = [
        {
            "nome": "Campo Nord",
            "lat": 41.9028,
            "lon": 12.4964,
            "coltura": "Pomodoro",
            "portata": 15.0,
            "data_semina": datetime.now().strftime("%Y-%m-%d"),
            "tipo_terreno": "Franco"
        }
    ]


if "archivio" not in st.session_state:
    st.session_state.archivio = []


st.sidebar.header("⚙️ Pannello di Controllo Aziendale")


with st.sidebar.form("field_creation", clear_on_submit=True):

    st.write("### ➕ Aggiungi Nuovo Appezzamento")

    nuovo_nome = st.text_input(
        "Nome Identificativo",
        placeholder="es. Uliveto Valle"
    )

    nuova_lat = st.number_input(
        "Latitudine",
        value=41.8902,
        format="%.4f"
    )

    nuova_lon = st.number_input(
        "Longitudine",
        value=12.4922,
        format="%.4f"
    )

    nuova_coltura = st.selectbox(
        "Tipo di Piantagione",
        list(DIZIONARIO_LOCALE.keys())
    )

    nuovo_terreno = st.selectbox(
        "Tipologia del Terreno",
        TIPI_TERRENO
    )

    nuova_portata = st.number_input(
        "Portata Impianto (litri/ora per mq)",
        value=15.0
    )

    nuova_data_semina = st.date_input(
        "Data di Semina/Inizio Ciclo",
        datetime.now()
    )

    submit_nuovo = st.form_submit_button("Salva Campo")

    if submit_nuovo and nuovo_nome:

        nuovo_campo = {
            "nome": nuovo_nome,
            "lat": nuova_lat,
            "lon": nuova_lon,
            "coltura": nuova_coltura,
            "tipo_terreno": nuovo_terreno,
            "portata": nuova_portata,
            "data_semina": nuova_data_semina.strftime("%Y-%m-%d")
        }

        st.session_state.campi.append(nuovo_campo)
        st.rerun()


if st.sidebar.button("🗑️ Svuota Tutta la Dashboard"):
    st.session_state.campi = []
    st.session_state.archivio = []
    st.rerun()


scheda_monitoraggio, scheda_mappa, scheda_raccolto, scheda_archivio = st.tabs([
    "📊 Monitoraggio & Irrigazione",
    "🗺️ Mappa Satellitare",
    "🌾 Gestione Raccolto",
    "🗄️ Archivio Storico"
])


# ---------------------------------------------------------
# TAB 1 - MONITORAGGIO E IRRIGAZIONE
# ---------------------------------------------------------

with scheda_monitoraggio:

    if not st.session_state.campi:

        st.info(
            "Nessun campo attivo inserito. "
            "Usa il modulo a sinistra per mappare un terreno."
        )

    else:

        st.write(
            f"## Registro delle Irrigazioni Intelligenti "
            f"({len(st.session_state.campi)} Attivi)"
        )

        for campo in st.session_state.campi:

            coltura_info = DIZIONARIO_LOCALE[campo["coltura"]]

            with st.expander(
                f"📋 Registro Campo: "
                f"{campo['nome']} ({campo['coltura']})",
                expanded=True
            ):

                url_chiamata = (
                    "https://api.open-meteo.com/v1/forecast"
                    f"?latitude={campo['lat']}"
                    f"&longitude={campo['lon']}"
                    "&current="
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "rain,"
                    "wind_speed_10m,"
                    "shortwave_radiation"
                    "&hourly=soil_moisture_3_to_9cm"
                    "&daily=rain_sum"
                    "&forecast_days=3"
                    "&timezone=auto"
                )

                try:

                    risposta = requests.get(
                        url_chiamata,
                        timeout=10
                    )

                    if risposta.status_code == 200:

                        dati = risposta.json()

                        current = dati.get("current", {})

                        temp = current.get(
                            "temperature_2m",
                            20.0
                        )

                        pioggia_odierna = current.get(
                            "rain",
                            0.0
                        )

                        umidita_aria = current.get(
                            "relative_humidity_2m",
                            50.0
                        )

                        velocita_vento = current.get(
                            "wind_speed_10m",
                            0.0
                        )

                        radiazione_solare = current.get(
                            "shortwave_radiation",
                            0.0
                        )

                        lista_suolo = dati.get(
                            "hourly",
                            {}
                        ).get(
                            "soil_moisture_3_to_9cm",
                            []
                        )

                        lista_valida = []

                        for valore in lista_suolo:

                            if valore is not None:
                                lista_valida.append(valore)

                        if lista_valida:
                            soil_mst_attuale = lista_valida[-1]
                        else:
                            soil_mst_attuale = 0.22

                        piogge_previste = dati.get(
                            "daily",
                            {}
                        ).get(
                            "rain_sum",
                            [0.0, 0.0, 0.0]
                        )

                        if len(piogge_previste) > 1:
                            pioggia_domani = piogge_previste[1]
                        else:
                            pioggia_domani = 0.0


                        # -------------------------------------------------
                        # METRICHE PRINCIPALI
                        # -------------------------------------------------

                        c1, c2, c3, c4 = st.columns(4)

                        c1.metric(
                            "Temperatura Aria",
                            f"{temp:.1f} °C"
                        )

                        c2.metric(
                            "Umidità Aria",
                            f"{int(umidita_aria)} %"
                        )

                        c3.metric(
                            "Pioggia Oggi",
                            f"{pioggia_odierna:.1f} mm"
                        )

                        c4.metric(
                            "Umidità Suolo",
                            f"{soil_mst_attuale:.3f} m³/m³"
                        )


                        # -------------------------------------------------
                        # PARAMETRI AGGIUNTIVI
                        # -------------------------------------------------

                        c5, c6, c7 = st.columns(3)

                        c5.metric(
                            "Velocità del Vento",
                            f"{velocita_vento:.1f} km/h"
                        )

                        c6.metric(
                            "Radiazione Solare",
                            f"{radiazione_solare:.1f} W/m²"
                        )

                        c7.metric(
                            "Tipologia del Terreno",
                            campo["tipo_terreno"]
                        )


                        # -------------------------------------------------
                        # LOGICA IRRIGAZIONE
                        # -------------------------------------------------

                        fabbisogno = coltura_info["fabbisogno"]

                        soglia_critica = coltura_info[
                            "soglia_umidita"
                        ]

                        giorno_irrigazione = datetime.now().strftime(
                            "%d/%m/%Y"
                        )


                        if (
                            pioggia_odierna >= fabbisogno
                            or pioggia_domani >= fabbisogno
                        ):

                            stato_irr = (
                                "Sospesa "
                                "(Meteo favorevole)"
                            )

                            ora_fine = "06:00"
                            acqua_smart = 0.0
                            risparmio = fabbisogno

                        elif soil_mst_attuale < soglia_critica:

                            stato_irr = (
                                "Attiva "
                                "(Terreno secco)"
                            )

                            acqua_da_integrare = max(
                                0.0,
                                fabbisogno - pioggia_odierna
                            )

                            tempo_ore = (
                                acqua_da_integrare
                                / campo["portata"]
                            )

                            minuti = int(
                                tempo_ore * 60
                            )

                            ora_fine = (
                                datetime.strptime(
                                    "06:00",
                                    "%H:%M"
                                )
                                + timedelta(minutes=minuti)
                            ).strftime("%H:%M")

                            acqua_smart = acqua_da_integrare

                            risparmio = (
                                fabbisogno
                                - acqua_smart
                            )

                        else:

                            stato_irr = (
                                "Sospesa "
                                "(Umidità ottimale)"
                            )

                            ora_fine = "06:00"
                            acqua_smart = 0.0
                            risparmio = fabbisogno


                        # -------------------------------------------------
                        # GRIGLIA DATI
                        # -------------------------------------------------

                        df_reg = pd.DataFrame({
                            "Parametro": [
                                "Stato Impianto",
                                "Giorno",
                                "Ora Inizio",
                                "Ora Fine",
                                "Acqua Erogata Smart",
                                "Acqua Risparmiata",
                                "Velocità del Vento",
                                "Radiazione Solare",
                                "Tipologia del Terreno"
                            ],

                            "Valore": [
                                stato_irr,
                                giorno_irrigazione,
                                "06:00",
                                ora_fine,
                                f"{acqua_smart:.1f} mm",
                                f"{risparmio:.1f} mm",
                                f"{velocita_vento:.1f} km/h",
                                f"{radiazione_solare:.1f} W/m²",
                                campo["tipo_terreno"]
                            ]
                        })

                        st.table(df_reg)

                    else:

                        st.error(
                            "Rifiuto di comunicazione "
                            "dal server meteo."
                        )

                except requests.RequestException as errore:

                    st.error(
                        f"Errore di comunicazione "
                        f"con il servizio meteo: {errore}"
                    )


# ---------------------------------------------------------
# TAB 2 - MAPPA
# ---------------------------------------------------------

with scheda_mappa:

    if st.session_state.campi:

        st.write(
            "## 🗺️ Mappa Satellitare "
            "dei Campi Aziendali"
        )

        dati_mappa = []

        for campo in st.session_state.campi:

            dati_mappa.append({
                "latitude": campo["lat"],
                "longitude": campo["lon"]
            })

        data_mappa = pd.DataFrame(dati_mappa)

        st.map(
            data_mappa,
            zoom=11,
            use_container_width=True
        )

    else:

        st.info(
            "Nessun campo attivo "
            "da mostrare sulla mappa."
        )


# ---------------------------------------------------------
# TAB 3 - GESTIONE RACCOLTO
# ---------------------------------------------------------

with scheda_raccolto:

    if not st.session_state.campi:

        st.info(
            "Nessun campo attivo "
            "da gestire per il raccolto."
        )

    else:

        st.write(
            "## 🌾 Analisi Maturazione "
            "& Chiusura Campo"
        )

        for idx, campo in enumerate(
            st.session_state.campi
        ):

            coltura_info = DIZIONARIO_LOCALE[
                campo["coltura"]
            ]

            dt_semina = datetime.strptime(
                campo["data_semina"],
                "%Y-%m-%d"
            )

            giorni_trascorsi = (
                datetime.now() - dt_semina
            ).days

            giorni_teorici_rimanenti = (
                coltura_info["giorni_maturazione"]
                - giorni_trascorsi
            )


            url_stima = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={campo['lat']}"
                f"&longitude={campo['lon']}"
                "&current=temperature_2m"
                "&timezone=auto"
            )

            aggiustamento_clima = 0

            try:

                res_stima = requests.get(
                    url_stima,
                    timeout=5
                )

                res_stima.raise_for_status()

                dati_stima = res_stima.json()

                temp_attuale = dati_stima.get(
                    "current",
                    {}
                ).get(
                    "temperature_2m",
                    20.0
                )

                if temp_attuale > 28.0:

                    aggiustamento_clima = -5

                elif temp_attuale < 12.0:

                    aggiustamento_clima = 7

            except (
                requests.RequestException,
                ValueError
            ):

                temp_attuale = 20.0


            giorni_finali_stima = max(
                0,
                giorni_teorici_rimanenti
                + aggiustamento_clima
            )

            data_raccolto_stimata = (
                datetime.now()
                + timedelta(days=giorni_finali_stima)
            ).strftime("%d/%m/%Y")


            st.write(
                f"### 📍 Appezzamento: "
                f"{campo['nome']} "
                f"(Coltura attuale: "
                f"{campo['coltura']})"
            )


            cr1, cr2, cr3, cr4 = st.columns(4)

            cr1.write(
                f"📅 **Data Semina:** "
                f"{dt_semina.strftime('%d/%m/%Y')}"
            )

            cr2.write(
                f"⏱️ **Giorni alla Raccolta:** "
                f"~ {giorni_finali_stima} "
                f"giorni rimanenti"
            )

            cr3.write(
                f"🔮 **Finestra Raccolta Stimata:** "
                f"{data_raccolto_stimata}"
            )

            cr4.write(
                f"🌱 **Terreno:** "
                f"{campo['tipo_terreno']}"
            )


            with st.form(
                f"crop_close_{idx}"
            ):

                st.write(
                    "⚠️ **Modulo di Chiusura "
                    "Ciclo Coltura (Raccolto)**"
                )

                quantita_raccolta = st.number_input(
                    "Quintali (q.li) Raccolti "
                    "(Valore Obbligatorio)",
                    min_value=0.1,
                    step=0.1,
                    format="%.1f"
                )

                note_raccolto = st.text_input(
                    "Note Qualità Prodotto",
                    placeholder=(
                        "es. Ottima pezzatura, "
                        "raccolto asciutto"
                    )
                )

                chiudi_pulsante = st.form_submit_button(
                    "🎉 Registra Raccolto "
                    "e Libera Terreno"
                )


                if chiudi_pulsante:

                    campo["data_raccolto"] = (
                        datetime.now().strftime(
                            "%d/%m/%Y"
                        )
                    )

                    campo["quintali"] = (
                        quantita_raccolta
                    )

                    campo["note_qualita"] = (
                        note_raccolto
                        if note_raccolto
                        else "Nessuna nota"
                    )


                    # Il tipo di terreno viene
                    # conservato automaticamente
                    # nello storico.

                    st.session_state.archivio.append(
                        campo.copy()
                    )

                    st.session_state.campi.pop(idx)

                    st.success(
                        f"Successo! "
                        f"{campo['nome']} chiuso. "
                        f"Dati salvati "
                        f"in archivio storico."
                    )

                    st.rerun()

            st.write("---")


# ---------------------------------------------------------
# TAB 4 - ARCHIVIO STORICO
# ---------------------------------------------------------

with scheda_archivio:

    st.write(
        "## 🗄️ Registro Storico "
        "dei Raccolti Conclusi"
    )

    if not st.session_state.archivio:

        st.caption(
            "Nessun raccolto completato "
            "in archivio finora."
        )

    else:

        dati_tabella_archivio = []

        for arch in st.session_state.archivio:

            dati_tabella_archivio.append({
                "Nome Campo": arch["nome"],
                "Varietà Piantata": arch["coltura"],
                "Tipologia Terreno": arch["tipo_terreno"],
                "Data Raccolta": arch["data_raccolto"],
                "Produzione Totale (q.li)": (
                    f"{arch['quintali']:.1f} q.li"
                ),
                "Note Qualità Agronoma": (
                    arch["note_qualita"]
                )
            })


        df_archivio = pd.DataFrame(
            dati_tabella_archivio
        )

        st.dataframe(
            df_archivio,
            use_container_width=True
        )
```
