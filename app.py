import streamlit as st
import requests

# Configurazione pagina
st.set_page_config(page_title="Dashboard Agricola Smart", layout="wide")
st.title("🚜 Dashboard Agricola con Dizionario Agronomico Online")

# URL del dizionario agronomico ospitato online (puoi sostituirlo con un tuo link JSON su GitHub o API FAO)
# Per questo esempio usiamo un mockup ospitato pubblicamente che contiene i parametri standard
URL_DIZIONARIO_ONLINE = "https://githubusercontent.com"

# Funzione di ripiego (Fallback) nel caso in cui l'API online sia temporaneamente irraggiungibile
DIZIONARIO_LOCALE = {
    "Pomodoro": {"fabbisogno": 5.0, "soglia_umidita": 0.25},
    "Mais": {"fabbisogno": 6.0, "soglia_umidita": 0.22},
    "Olivo": {"fabbisogno": 2.0, "soglia_umidita": 0.15},
    "Vite": {"fabbisogno": 2.5, "soglia_umidita": 0.16}
}

# --- SCARICAMENTO DINAMICO DEL DIZIONARIO ONLINE ---
@st.cache_data(ttl=86400) # Salva i dati in cache per 24 ore per velocizzare l'app
def carica_dizionario_colture():
    try:
        response = requests.get(URL_DIZIONARIO_ONLINE, timeout=5)
        if response.status_code == 200:
            st.sidebar.success("🌍 Dizionario agronomico sincronizzato online!")
            return response.json()
    except Exception:
        st.sidebar.warning("⚠️ Impossibile connettersi al dizionario online. Uso i dati locali di riserva.")
    return DIZIONARIO_LOCALE

# Carica i parametri validi
DIZIONARIO_COLTURE = carica_dizionario_colture()

# Inizializzazione dello stato della sessione per memorizzare i campi dell'utente
if "campi" not in st.session_state:
    st.session_state.campi = [
        {"nome": "Campo Principale", "lat": 41.9028, "lon": 12.4964, "coltura": "Pomodoro", "portata": 15.0}
    ]

# --- PANNELLO DI SINISTRA: GESTIONE E AGGIUNTA CAMPI ---
st.sidebar.header("➕ Gestione Campi Agricoli")

with st.sidebar.form("nuovo_campo_form", clear_on_submit=True):
    st.write("### Aggiungi Nuovo Campo")
    nuovo_nome = st.text_input("Nome Campo", placeholder="es. Uliveto Collina")
    nuova_lat = st.number_input("Latitudine", value=41.8902, format="%.4f")
    nuova_lon = st.number_input("Longitudine", value=12.4922, format="%.4f")
    
    # Il menu a tendina si adatta dinamicamente a quello che viene scaricato dal web
    nuova_coltura = st.selectbox("Tipo di Piantagione (Dati Online)", list(DIZIONARIO_COLTURE.keys()))
    nuova_portata = st.number_input("Portata Impianto (litri/ora per mq)", value=15.0)
    
    submit_nuovo = st.form_submit_button("Salva Campo")
    if submit_nuovo and nuovo_nome:
        st.session_state.campi.append({
            "nome": nuovo_nome, "lat": nuova_lat, "lon": nuova_lon, "coltura": nuova_coltura, "portata": nuova_portata
        })
        st.toast(f"✅ {nuovo_nome} aggiunto!")

# --- VISUALIZZAZIONE SCHEDE E PREVISIONI ---
if st.session_state.campi:
    nomi_campi = [c["nome"] for c in st.session_state.campi]
    tabs = st.tabs(nomi_campi)
    
    for i, tab in enumerate(tabs):
        campo = st.session_state.campi[i]
        
        # Estrazione dinamica dei parametri recuperati online per la coltura selezionata
        coltura_info = DIZIONARIO_COLTURE.get(campo["coltura"], {"fabbisogno": 4.0, "soglia_umidita": 0.20})
        
        with tab:
            st.subheader(f"Analisi Campo: {campo['nome']} | Coltura: {campo['coltura']}")
            
            # Chiamata API Open-Meteo per i dati meteo reali
            url_meteo = f"https://open-meteo.com{campo['lat']}&longitude={campo['lon']}&current=temperature_2m,relative_humidity_2m,rain&hourly=soil_moisture_3_to_9cm&timezone=auto"
            
            try:
                res = requests.get(url_meteo).json()
                current = res["current"]
                soil_mst = res["hourly"]["soil_moisture_3_to_9cm"][-1]
                
                # Visualizzazione Dati Grafici
                col1, col2, col3 = st.columns(3)
                col1.metric("Pioggia Odierna", f"{current['rain']} mm")
                col2.metric("Umidità Suolo Rilevata", f"{soil_mst} m³/m³")
                col3.metric("Fabbisogno Pianta (Da Database Online)", f"{coltura_info['fabbisogno']} mm")
                
                # Regola decisionale
                st.write("### 🧠 Decisione Irrigazione")
                if current['rain'] >= coltura_info['fabbisogno']:
                    st.success("🌧️ Pioggia sufficiente. Non irrigare.")
                elif soil_mst < coltura_info['soglia_umidita']:
                    tempo = coltura_info['fabbisogno'] / campo['portata']
                    st.error(f"🚨 Terreno secco (Soglia critica online: {coltura_info['soglia_umidita']}). Irrigare per {tempo:.2f} ore.")
                else:
                    st.info("✅ Parametri stabili. Nessun intervento richiesto.")
                    
            except Exception as e:
                st.error("Errore nel caricamento dei dati meteo in tempo reale.")
