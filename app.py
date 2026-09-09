import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# Configurazione della pagina
st.set_page_config(page_title="Dashboard Agricola Professionale", layout="wide")
st.title("🚜 Smart Farming Dashboard: Monitoraggio, Mappe & Gestione Cicli")

# Dizionario agronomico locale di stabilità
DIZIONARIO_LOCALE = {
    "Pomodoro": {"fabbisogno": 5.0, "soglia_umidita": 0.25},
    "Mais": {"fabbisogno": 6.0, "soglia_umidita": 0.22},
    "Olivo": {"fabbisogno": 2.0, "soglia_umidita": 0.15},
    "Vite": {"fabbisogno": 2.5, "soglia_umidita": 0.16},
    "Patata": {"fabbisogno": 4.5, "soglia_umidita": 0.24},
    "Grano": {"fabbisogno": 3.5, "soglia_umidita": 0.18}
}

# Inizializzazione dello stato della sessione per campi attivi e archivio raccolti
if "campi" not in st.session_state:
    st.session_state.campi = [
        {"nome": "Campo Nord", "lat": 41.9028, "lon": 12.4964, "coltura": "Pomodoro", "portata": 15.0}
    ]
if "archivio" not in st.session_state:
    st.session_state.archivio = []

# --- PANNELLO LATERALE: AZIONI E GESTIONE ---
st.sidebar.header("⚙️ Pannello di Controllo Aziendale")

# 1. Modulo per aggiungere un nuovo campo
with st.sidebar.form("nuovo_campo_form", clear_on_submit=True):
    st.write("### ➕ Aggiungi Nuovo Appezzamento")
    nuovo_nome = st.text_input("Nome Identificativo", placeholder="es. Uliveto Valle")
    nuova_lat = st.number_input("Latitudine", value=41.8902, format="%.4f")
    nuova_lon = st.number_input("Longitudine", value=12.4922, format="%.4f")
    nuova_coltura = st.selectbox("Tipo di Piantagione", list(DIZIONARIO_LOCALE.keys()))
    nuova_portata = st.number_input("Portata Impianto (litri/ora per mq)", value=15.0)
    
    submit_nuovo = st.form_submit_button("Salva Campo")
    if submit_nuovo and nuovo_nome:
        st.session_state.campi.append({
            "nome": nuovo_nome, "lat": nuova_lat, "lon": nuova_lon, "coltura": nuova_coltura, "portata": nuova_portata
        })
        st.rerun()

# 2. Modulo per la gestione del ciclo di vita dei campi esistenti
if st.session_state.campi:
    st.sidebar.write("---")
    st.sidebar.write("### 🌾 Azioni sui Campi Attivi")
    campo_selezionato_azione = st.sidebar.selectbox("Seleziona Campo su cui agire", [c["nome"] for c in st.session_state.campi])
    
    col_acc1, col_acc2 = st.sidebar.columns(2)
    
    with col_acc1:
        # Archiviazione post-raccolto
        if st.button("🎉 Effettua Raccolto"):
            for c in st.session_state.campi:
                if c["nome"] == campo_selezionato_azione:
                    c["data_raccolto"] = datetime.now().strftime("%d/%m/%Y")
                    st.session_state.archivio.append(c)
                    st.session_state.campi.remove(c)
                    st.toast(f"🌾 {campo_selezionato_azione} archiviato con successo nei raccolti!")
                    st.rerun()
                    
    with col_acc2:
        # Cancellazione definitiva
        if st.button("🗑️ Elimina Campo"):
            for c in st.session_state.campi:
                if c["nome"] == campo_selezionato_azione:
                    st.session_state.campi.remove(c)
                    st.toast(f"❌ {campo_selezionato_azione} eliminato definitivamente.")
                    st.rerun()

# --- SCHERMATA CENTRALE ---

# Sezione 1: Mappa Globale dell'Azienda Agricola
if st.session_state.campi:
    st.write("## 🗺️ Mappa Satellitare dei Campi Aziendali")
    data_mappa = pd.DataFrame([
        {"latitude": c["lat"], "longitude": c["lon"], "Nome": f"{c['nome']} ({c['coltura']})"}
        for c in st.session_state.campi
    ])
    st.map(data_mappa, zoom=10, use_container_width=True)
    st.write("---")

# Sezione 2: Monitoraggio e Griglie per Campo
if not st.session_state.campi:
    st.info("Nessun campo attivo inserito. Usa il modulo a sinistra per mappare un terreno o reiniziare dopo un raccolto.")
else:
    st.write(f"## 📊 Analisi e Registro delle Irrigazioni Intelligenti")
    
    nomi_campi = [c["nome"] for c in st.session_state.campi]
    tabs = st.tabs(nomi_campi)
    
    for i, tab in enumerate(tabs):
        campo = st.session_state.campi[i]
        coltura_info = DIZIONARIO_LOCALE[campo["coltura"]]
        
        with tab:
            st.write(f"### Campo: {campo['nome']} | Coltura: **{campo['coltura']}**")
            
            url_chiamata = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={campo['lat']}"
                f"&longitude={campo['lon']}"
                f"&current=temperature_2m&current=relative_humidity_2m&current=rain"
                f"&hourly=soil_moisture_3_to_9cm"
                f"&daily=rain_sum&forecast_days=3&timezone=auto"
            )
            
            try:
                risposta = requests.get(url_chiamata, timeout=10)
                if risposta.status_code == 200:
                    dati = risposta.json()
                    
                    current = dati.get("current", {})
                    temp = current.get("temperature_2m", 20.0)
                    pioggia_odierna = current.get("rain", 0.0)
                    umidita_aria = current.get("relative_humidity_2m", 50.0)
                    
                    hourly = dati.get("hourly", {})
                    ore = hourly.get("time", [])
                    lista_suolo = hourly.get("soil_moisture_3_to_9cm", [])
                    lista_valida = [v for v in lista_suolo if v is not None]
                    soil_mst_attuale = lista_valida[-1] if lista_valida else 0.22
                    
                    daily = dati.get("daily", {})
                    piogge_previste = daily.get("rain_sum", [0.0, 0.0, 0.0])
                    pioggia_domani = piogge_previste[1] if len(piogge_previste) > 1 else 0.0
                    
                    cm1, cm2, cm3, cm4 = st.columns(4)
                    cm1.metric("Temperatura Aria", f"{temp:.1f} °C")
                    cm2.metric("Umidità Aria", f"{int(umidita_aria)} %")
                    cm3.metric("Pioggia Oggi", f"{pioggia_odierna:.1f} mm")
                    cm4.metric("Umidità Suolo", f"{soil_mst_attuale:.3f} m³/m³")
                    
                    fabbisogno = coltura_info["fabbisogno"]
                    soglia_critica = coltura_info["soglia_umidita"]
                    acqua_erogata_manuale_standard = fabbisogno
                    
                    giorno_irrigazione = datetime.now().strftime("%d/%m/%Y")
                    ora_inizio = "06:00"
                    
                    if pioggia_odierna >= fabbisogno or pioggia_domani >= fabbisogno:
                        stato_irrigazione = "Sospesa (Meteo favorevole)"
                        ora_fine = "06:00"
                        acqua_erogata_smart = 0.0
                        acqua_risparmiata = acqua_erogata_manuale_standard
                    elif soil_mst_attuale < soglia_critica:
                        stato_irrigazione = "Attiva (Terreno secco)"
                        acqua_da_integrare = max(0.0, fabbisogno - pioggia_odierna)
                        tempo_ore = acqua_da_integrare / campo["portata"]
                        minuti_lavoro = int(tempo_ore * 60)
                        
                        orario_fine_dt = datetime.strptime(ora_inizio, "%H:%M") + timedelta(minutes=minuti_lavoro)
                        ora_fine = orario_fine_dt.strftime("%H:%M")
                        
                        acqua_erogata_smart = acqua_da_integrare
                        acqua_risparmiata = acqua_erogata_manuale_standard - acqua_erogata_smart
                    else:
                        stato_irrigazione = "Sospesa (Umidità ottimale)"
                        ora_fine = "06:00"
                        acqua_erogata_smart = 0.0
                        acqua_risparmiata = acqua_erogata_manuale_standard

                    st.write("#### 📋 Registro d'Intervento Giornaliero Calcolato")
                    
                    riga_registro = {
                        "Parametro": ["Stato Impianto", "Giorno Intervento", "Ora Inizio", "Ora Fine Stima", "Acqua Erogata Smart (l/mq)", "Acqua Risparmiata (l/mq)"],
                        "Valore": [stato_irrigazione, giorno_irrigazione, ora_inizio, ora_fine, f"{acqua_erogata_smart:.1f} mm", f"{acqua_risparmiata:.1f} mm"]
                    }
                    df_registro = pd.DataFrame(riga_registro)
                    st.table(df_registro)
                    
                    if acqua_risparmiata > 0:
                        st.success(f"💡 **Risparmio Risorse**: Questo campo oggi ha risparmiato **{acqua_risparmiata:.1f} litri d'acqua per ogni metro quadro** rispetto a un'irrigazione manuale a tempo fisso.")
                    
                    with st.expander("📈 Mostra Grafico Storico Umidità Terreno (72 Ore)"):
                        if ore and lista_suolo:
                            df_grafico = pd.DataFrame({"Data/Ora": pd.to_datetime(ore), "Umidità Suolo": lista_suolo}).set_index("Data/Ora")
                            st.line_chart(df_grafico)
                            
                else:
                    st.error("Rifiuto di connessione dal server meteo.")
            except Exception as e:
                st.error(f"Errore caricamento dati: {e}")

# Sezione 3: Registro dei Campi Archiviati (Storico Raccolti)
st.write("---")
st.write("## 🗄️ Archivio Storico dei Raccolti Effettuati")
if not st.session_state.archivio:
    st.caption("Nessun raccolto registrato finora in questa stagione.")
else:
    df_archivio = pd.DataFrame([
        {
            "Nome Campo Originale": a["nome"],
            "Coltura Raccolta": a["coltura"],
            "Posizione GPS": f"{a['lat']}, {a['lon']}",
            "Data Chiusura Ciclo": a["data_raccolto"]
        }
        for a in st.session_state.archivio
    ])
    st.dataframe(df_archivio, use_container_width=True)
