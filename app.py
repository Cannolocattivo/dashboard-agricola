import streamlit as st
import requests
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta


# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(
    page_title="AgriSmart",
    layout="wide"
)

st.title("🚜 Dashboard")


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
    }
}


# ============================================================
# PERSISTENZA
# ============================================================

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
                "portata": 15.0,
                "data_semina": datetime.now().strftime("%Y-%m-%d"),
                "registro": []
            }
        ]

    for campo in st.session_state.campi:
        campo.setdefault("registro", [])

    for campo in st.session_state.archivio:
        campo.setdefault("registro", [])

    st.session_state.dati_caricati = True


# ============================================================
# FUNZIONI REGISTRO
# ============================================================

def registra_giornata(campo, dati_giorno):
    """
    Aggiunge automaticamente una sola registrazione per campo e giorno.
    Se il giorno è già presente, aggiorna la registrazione.
    """

    data = dati_giorno["data"]

    registro = campo.setdefault("registro", [])

    esistente = None

    for riga in registro:
        if riga.get("data") == data:
            esistente = riga
            break

    if esistente:
        esistente.update(dati_giorno)
    else:
        registro.append(dati_giorno)

    registro.sort(
        key=lambda x: x.get("data", "")
    )


def dati_registro(campo, dati_giorno):
    """
    Costruisce una riga completa del registro giornaliero.
    """

    return {
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
            "Data": r.get("data", ""),
            "Ora": r.get("ora_rilevazione", ""),
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
            "Risparmiata": f"{r.get('risparmiata', 0):.1f} mm"
        })

    st.dataframe(
        pd.DataFrame(righe),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# SIDEBAR
# ============================================================

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
        "Pianta",
        list(DIZIONARIO.keys())
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

    if sub and n_nome:

        st.session_state.campi.append({
            "nome": n_nome,
            "lat": n_lat,
            "lon": n_lon,
            "coltura": n_colt,
            "portata": n_port,
            "data_semina": n_data.strftime("%Y-%m-%d"),
            "registro": []
        })

        salva_dati()
        st.rerun()


if st.sidebar.button("💾 Salva dati"):

    salva_dati()
    st.sidebar.success("Dati salvati.")


if st.sidebar.button("🗑️ Svuota"):

    st.session_state.campi = []
    st.session_state.archivio = []

    salva_dati()
    st.rerun()


# ============================================================
# TABS
# ============================================================

t_mon, t_map, t_arc = st.tabs([
    "📊 Monitoraggio",
    "🗺️ Mappa",
    "🗄️ Archivio"
])


# ============================================================
# MONITORAGGIO
# ============================================================

with t_mon:

    if not st.session_state.campi:

        st.info("Nessun campo.")

    else:

        for idx, campo in enumerate(
            st.session_state.campi
        ):

            info = DIZIONARIO[campo["coltura"]]

            with st.expander(
                f"🌿 {campo['nome']} — {campo['coltura']}",
                expanded=True
            ):

                # ====================================================
                # DATI METEO
                # ====================================================

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

                    res = requests.get(
                        url,
                        timeout=10
                    ).json()

                    cur = res.get(
                        "current",
                        {}
                    )

                    temp = cur.get(
                        "temperature_2m",
                        20.0
                    )

                    umid = cur.get(
                        "relative_humidity_2m",
                        50
                    )

                    piog = cur.get(
                        "rain",
                        0.0
                    )

                    vent = cur.get(
                        "wind_speed_10m",
                        0.0
                    )

                    rads = cur.get(
                        "shortwave_radiation",
                        0.0
                    )

                    # ====================================================
                    # UMIDITÀ SUOLO
                    # ====================================================

                    hrs = res.get(
                        "hourly",
                        {}
                    )

                    l_soil = hrs.get(
                        "soil_moisture_3_to_9cm",
                        []
                    )

                    l_val = [
                        v
                        for v in l_soil
                        if v is not None
                    ]

                    soil = (
                        l_val[-1]
                        if l_val
                        else 0.22
                    )

                    # ====================================================
                    # PIOGGIA GIORNALIERA
                    # ====================================================

                    dly = res.get(
                        "daily",
                        {}
                    )

                    p_prev = dly.get(
                        "rain_sum",
                        [0.0, 0.0, 0.0]
                    )

                    p_dom = (
                        p_prev[0]
                        if p_prev
                        else 0.0
                    )

                    # ====================================================
                    # RIEPILOGO
                    # ====================================================

                    st.write("### 🌤️ Condizioni attuali")

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

                    # ====================================================
                    # CALCOLO IRRIGAZIONE
                    # ====================================================

                    fabb = info["fabbisogno"]
                    sogl = info["soglia_umidita"]
                    gg_m = info["giorni_maturazione"]

                    oggi = datetime.now().strftime(
                        "%Y-%m-%d"
                    )

                    g_irr = datetime.now().strftime(
                        "%d/%m/%Y"
                    )

                    ora_rilevazione = datetime.now().strftime(
                        "%H:%M:%S"
                    )

                    if (
                        piog >= fabb
                        or p_dom >= fabb
                    ):

                        s_irr = "🚫 Sospesa"

                        o_fin = "06:00"

                        a_smr = 0.0

                        risp = fabb

                    elif soil < sogl:

                        s_irr = "💧 Attiva"

                        intg = max(
                            0.0,
                            fabb - piog
                        )

                        t_ore = (
                            intg /
                            campo["portata"]
                        )

                        minu = int(
                            t_ore * 60
                        )

                        o_fin = (
                            datetime.strptime(
                                "06:00",
                                "%H:%M"
                            )
                            + timedelta(
                                minutes=minu
                            )
                        ).strftime("%H:%M")

                        a_smr = intg

                        risp = max(
                            0.0,
                            fabb - a_smr
                        )

                    else:

                        s_irr = "✅ Sospesa"

                        o_fin = "06:00"

                        a_smr = 0.0

                        risp = fabb

                    # ====================================================
                    # REGISTRAZIONE AUTOMATICA GIORNALIERA
                    # ====================================================

                    dati_giorno = {
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

                    # ====================================================
                    # PARAMETRI D'INTERVENTO GIORNALIERI
                    # ====================================================

                    st.write(
                        "### 📋 Parametri d'Intervento Giornalieri"
                    )

                    df_oggi = pd.DataFrame({
                        "Stato": [s_irr],
                        "Giorno": [g_irr],
                        "Temp. Aria": [
                            f"{temp:.1f} °C"
                        ],
                        "Umidità Aria": [
                            f"{umid:.0f} %"
                        ],
                        "Pioggia": [
                            f"{piog:.1f} mm"
                        ],
                        "Vento": [
                            f"{vent:.1f} km/h"
                        ],
                        "Radiazione Solare": [
                            f"{rads:.0f} W/m²"
                        ],
                        "Umidità Suolo": [
                            f"{soil:.3f}"
                        ],
                        "Pioggia Giorno": [
                            f"{p_dom:.1f} mm"
                        ],
                        "Inizio": ["06:00"],
                        "Fine": [o_fin],
                        "Erogata": [
                            f"{a_smr:.1f} mm"
                        ],
                        "Risparmiata": [
                            f"{risp:.1f} mm"
                        ]
                    })

                    st.dataframe(
                        df_oggi,
                        use_container_width=True,
                        hide_index=True
                    )

                    # ====================================================
                    # REGISTRO CRONOLOGICO DEL CAMPO
                    # ====================================================

                    st.write(
                        "### 📚 Registro cronologico del campo"
                    )

                    mostra_registro(campo)

                    # ====================================================
                    # GRAFICO UMIDITÀ SUOLO
                    # ====================================================

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

                    # ====================================================
                    # PREVISIONE RACCOLTA
                    # ====================================================

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

                    g_rim = max(
                        0,
                        (gg_m - g_pass) + corr
                    )

                    d_rac = (
                        datetime.now() +
                        timedelta(days=g_rim)
                    ).strftime(
                        "%d/%m/%Y"
                    )

                    st.info(
                        f"🌾 Giorni rimasti: "
                        f"{g_rim} ({d_rac})"
                    )

                    # ====================================================
                    # CHIUSURA CAMPO
                    # ====================================================

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

                except Exception as e:

                    st.error(
                        f"Errore dati meteo: {e}"
                    )


# ============================================================
# MAPPA
# ============================================================

with t_map:

    if st.session_state.campi:

        df_m = pd.DataFrame([
            {
                "latitude": c["lat"],
                "longitude": c["lon"]
            }
            for c in st.session_state.campi
        ])

        st.map(
            df_m,
            zoom=12,
            use_container_width=True
        )

    else:

        st.info("Nessun campo.")


# ============================================================
# ARCHIVIO
# ============================================================

with t_arc:

    st.write("## 🗄️ Storico campi")

    if not st.session_state.archivio:

        st.caption("Vuoto.")

    else:

        for campo in st.session_state.archivio:

            with st.expander(
                f"🌾 {campo['nome']} — {campo['coltura']}",
                expanded=False
            ):

                c1, c2, c3 = st.columns(3)

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

                st.write(
                    f"**Note:** {campo.get('note', '-')}"
                )

                st.write(
                    "### 📚 Registro cronologico completo"
                )

                mostra_registro(campo)


# ============================================================
# NOTA PERSISTENZA
# ============================================================

st.sidebar.caption(
    "💾 Il registro giornaliero viene salvato "
    "automaticamente in agri_data.json"
)
