import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta


st.set_page_config(
    page_title="AgriSmart",
    layout="wide"
)

st.title("🚜 Dashboard")


# ============================================================
# CONFIGURAZIONE COLTURE
# ============================================================

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
# SESSION STATE
# ============================================================

if "campi" not in st.session_state:
    st.session_state.campi = [
        {
            "nome": "Campo Nord",
            "lat": 41.9028,
            "lon": 12.4964,
            "coltura": "Pomodoro",
            "portata": 15.0,
            "data_semina": datetime.now().strftime("%Y-%m-%d")
        }
    ]

if "archivio" not in st.session_state:
    st.session_state.archivio = []


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
            "data_semina": n_data.strftime("%Y-%m-%d")
        })

        st.rerun()


if st.sidebar.button("🗑️ Svuota"):

    st.session_state.campi = []
    st.session_state.archivio = []

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

        for idx, campo in enumerate(st.session_state.campi):

            info = DIZIONARIO[campo["coltura"]]

            with st.expander(
                f"🌿 {campo['nome']}",
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

                    cur = res.get("current", {})

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

                    # Velocità vento
                    vent = cur.get(
                        "wind_speed_10m",
                        0.0
                    )

                    # Radiazione solare
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
                        p_prev[1]
                        if len(p_prev) > 1
                        else 0.0
                    )

                    # ====================================================
                    # RIEPILOGO METEO
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

                    g_irr = datetime.now().strftime(
                        "%d/%m/%Y"
                    )

                    # ----------------------------------------------------
                    # Pioggia sufficiente
                    # ----------------------------------------------------

                    if (
                        piog >= fabb
                        or p_dom >= fabb
                    ):

                        s_irr = "🚫 Sospesa"

                        o_fin = "06:00"

                        a_smr = 0.0

                        risp = fabb

                    # ----------------------------------------------------
                    # Terreno sotto soglia
                    # ----------------------------------------------------

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

                    # ----------------------------------------------------
                    # Terreno sufficiente
                    # ----------------------------------------------------

                    else:

                        s_irr = "✅ Sospesa"

                        o_fin = "06:00"

                        a_smr = 0.0

                        risp = fabb

                    # ====================================================
                    # PARAMETRI D'INTERVENTO GIORNALIERI
                    # ====================================================

                    st.write(
                        "### 📋 Parametri d'Intervento Giornalieri"
                    )

                    # La tabella viene costruita ORIZZONTALMENTE:
                    # una riga = un giorno/intervento
                    # colonne = tutti i parametri rilevati/calcolati.

                    df_oriz = pd.DataFrame({
                        "Stato": [
                            s_irr
                        ],

                        "Giorno": [
                            g_irr
                        ],

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

                        "Inizio": [
                            "06:00"
                        ],

                        "Fine": [
                            o_fin
                        ],

                        "Erogata": [
                            f"{a_smr:.1f} mm"
                        ],

                        "Risparmiata": [
                            f"{risp:.1f} mm"
                        ]
                    })

                    st.dataframe(
                        df_oriz,
                        use_container_width=True,
                        hide_index=True
                    )

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

                            campo[
                                "data_raccolto"
                            ] = datetime.now().strftime(
                                "%d/%m/%Y"
                            )

                            campo[
                                "quintali"
                            ] = q_rac

                            campo["note"] = (
                                n_rac
                                if n_rac
                                else "Standard"
                            )

                            st.session_state.archivio.append(
                                campo
                            )

                            st.session_state.campi.pop(
                                idx
                            )

                            st.success(
                                "Archiviato!"
                            )

                            st.rerun()

                except Exception as e:

                    st.error(
                        f"Err: {e}"
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

    st.write("## 🗄️ Storico")

    if not st.session_state.archivio:

        st.caption("Vuoto.")

    else:

        l_arc = [
            {
                "Campo": a["nome"],
                "Coltura": a["coltura"],
                "Semina": a["data_semina"],
                "Raccolto": a["data_raccolto"],
                "Q.li": f"{a['quintali']:.1f}",
                "Note": a["note"]
            }
            for a in st.session_state.archivio
        ]

        st.dataframe(
            pd.DataFrame(l_arc),
            use_container_width=True,
            hide_index=True
        )
