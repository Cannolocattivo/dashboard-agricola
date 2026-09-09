import streamlit as st
import requests

# Configurazione della pagina
st.set_page_config(page_title="Dashboard Agricola Smart", layout="wide")
st.title("🚜 Dashboard Agricola: Integrazione Database Online")

# DIZIONARIO ONLINE REALE: Dataset pubblico open-source con i parametri FAO per l'irrigazione
URL_DIZIONARIO_ONLINE = "https://githubusercontent.com"

# Dizionario locale completo di riserva (Fallback robusto se internet cade)
DIZIONARIO_LOCALE = {
    "Pomodoro": {"fabbisogno": 5.0, "soglia_umidita": 0.25},
    "Mais": {"fabbisogno": 6.0, "soglia_umidita": 0.22},
    "Olivo": {"fabbisogno": 2.0, "soglia_umidita": 0.15},
    "Vite": {"fabbisogno": 2.5, "soglia_umidita": 0.16},
    "Patata": {"fabbisogno": 4.5, "soglia_umidita": 0.24},
    "Grano": {"fabbisogno": 3.5, "soglia_umidita": 0.18}
}

# Scaricamento sicuro del dizionario online con gestione degli errori
@st.cache_data(ttl=3600) 
def carica_dizionario_colture():
    try:
        response = requests.get(URL_DIZIONARIO_ONLINE, timeout=5)
        if response.status_code == 200:
            dati_web = response.json()
            if isinstance(dati_web, dict) and len(dati_web) > 0:
                st.sidebar.success("🌍 Database agronomico online sincronizzato!")
                return dati_web
    except Exception:
        pass
    st.sidebar.warning("⚠️ Database online non raggiungibile. Uso i dati locali di riserva.")
    return DIZIONARIO_LOCALE

# Inizializzazione database piante
DIZIONARIO_COLTURE = carica_dizionario_colture()

# Stato della sessione per non perdere i dati inseriti dall'utente al ricaricamento
if "campi" not in st.session_state:
    st.session_state.campi = [
        {"nome": "Campo Nord", "lat": 41.9028, "lon": 12.4964, "coltura": "Pomodoro", "portata": 15.0}
    ]

# --- PANNELLO DI SINISTRA: INPUT UTENTE ---
st.sidebar.header("➕ Gestione Campi Agricoli")

with st.sidebar.form("nuovo_campo_form", clear_on_submit=True):
    st.write("### Aggiungi Nuovo Appezzamento")
    nuovo_nome = st.text_input("Nome Identificativo", placeholder="es. Uliveto Valle")
    nuova_lat = st.number_input("Latitudine", value=41.8902, format="%.4f")
    nuova_lon = st.number_input("Longitudine", value=12.4922, format="%.4f")
    nuova_coltura = st.selectbox("Tipo di Piantagione", list(DIZIONARIO_COLTURE.keys()))
    nuova_portata = st.number_input("Portata Impianto (litri/ora per mq)", value=15.0)
    
    submit_nuovo = st.form_submit_button("Salva Campo")
    if submit_nuovo and nuovo_nome:
        st.session_state.campi.append({
            "nome": nuovo_nome, "lat": nuova_lat, "lon": nuova_lon, "coltura": nuova_coltura, "portata": nuova_portata
        })
        st.rerun()

if st.sidebar.button("🗑️ Svuota Lista Campi"):
    st.session_state.campi = []
    st.rerun()

# --- PANNELLO PRINCIPALE: CALCOLI AGRO-METEO ---
if not st.session_state.campi:
    st.info("Nessun campo inserito. Usa il modulo a sinistra per mappare il tuo primo terreno.")
else:
    st.write(f"Monitoraggio attivo su **{len(st.session_state.campi)}** zone aziendali:")
    
    nomi_campi = [c["nome"] for c in st.session_state.campi]
    tabs = st.tabs(nomi_campi)
    
    for i, tab in enumerate(tabs):
        campo = st.session_state.campi[i]
        coltura_info = DIZIONARIO_COLTURE.get(campo["coltura"], {"fabbisogno": 4.0, "soglia_umidita": 0.20})
        
        with tab:
            st.subheader(f"Analisi Campo: {campo['nome']} | Coltura attuale: {campo['coltura']}")
            st.caption(f"Coordinate GPS: {campo['lat']}, {campo['lon']} | Impianto: {campo['portata']} l/h/mq")
            
            # COSTRUZIONE DI SICUREZZA DELL'URL SENZA INVERSIONE DI CARATTERI
            lat_str = str(campo['lat']).strip()
            lon_str = str(campo['lon']).strip()
            url_meteo = f"https://open-meteo.com{lat_str}&longitude={lon_str}&current=temperature_2m,relative_humidity_2m,rain&hourly=soil_moisture_3_to_9cm&timezone=auto"
            
            try:
                res = requests.get(url_meteo, timeout=10).json()
                
                if "current" in res and "hourly" in res:
                    current = res["current"]
                    pioggia = current.get("rain", 0.0)
                    temp = current.get("temperature_2m", 0.0)
                    umidita_aria = current.get("relative_humidity_2m", 0.0)
                    
                    lista_suolo = res["hourly"].get("soil_moisture_3_to_9cm", [])
                    lista_suolo_valida = [v for v in lista_suolo if v is not None]
                    soil_mst = lista_suolo_valida[-1] if lista_suolo_valida else 0.20
                    
                    # Interfaccia Metriche
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Temperatura Aria", f"{temp} °C")
                    c2.metric("Umidità Aria", f"{umidita_aria} %")
                    c3.metric("Pioggia Odierna", f"{pioggia} mm")
                    c4.metric("Umidità Suolo", f"{soil_mst:.3f} m³/m³")
                    
                    # Motore Decisionale Agronomico
                    st.write("### 🧠 Bilancio Idrico e Consiglio di Irrigazione")
                    fabbisogno_coltura = coltura_info["fabbisogno"]
                    soglia_critica = coltura_info["soglia_umidita"]
                    
                    if pioggia >= fabbisogno_coltura:
                        st.success(f"🌧️ **NON IRRIGARE:** La pioggia naturale ({pioggia} mm) copre interamente il fabbisogno di oggi ({fabbisogno_coltura} mm).")
                    elif soil_mst < soglia_critica:
                        acqua_da_integrare = max(0.0, fabbisogno_coltura - pioggia)
                        tempo_ore = acqua_da_integrare / campo["portata"]
                        minuti = int(tempo_ore * 60)
                        
                        st.error(f"🚨 **IRRIGAZIONE RICHIESTA:** Il terreno è sotto la soglia di stress idrico ({soil_mst:.3f} < {soglia_critica}).")
                        st.warning(f"⏱️ **Dosaggio:** Attiva l'irrigazione per **{minuti} minuti** per erogare i {acqua_da_integrare:.1f} mm mancanti.")
                    else:
                        st.info(f"✅ **IDRATAZIONE OTTIMALE:** L'umidità del suolo ({soil_mst:.3f}) è superiore al punto di stress ({soglia_critica}). Trattamento non necessario.")
                else:
                    st.error("⚠️ Il server meteo ha risposto ma mancano alcuni dati essenziali per questa coordinata.")
                    
            except Exception as e:
                st.error(f"❌ Errore di rete o timeout durante la connessione ai dati meteo satellitari. Dettaglio: {e}")
