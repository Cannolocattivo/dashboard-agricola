import streamlit as st
import openmeteo_requests
import requests_cache
import requests
from retry_requests import retry

# Configurazione della pagina
st.set_page_config(page_title="Dashboard Agricola Smart", layout="wide")
st.title("🚜 Dashboard Agricola Professionale")

# Impostazione del client Open-Meteo ufficiale con cache e tentativi automatici
@st.cache_resource
def inizializza_meteo_client():
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)

openmeteo = inizializza_meteo_client()

# Database agronomico locale di stabilità
DIZIONARIO_LOCALE = {
    "Pomodoro": {"fabbisogno": 5.0, "soglia_umidita": 0.25},
    "Mais": {"fabbisogno": 6.0, "soglia_umidita": 0.22},
    "Olivo": {"fabbisogno": 2.0, "soglia_umidita": 0.15},
    "Vite": {"fabbisogno": 2.5, "soglia_umidita": 0.16},
    "Patata": {"fabbisogno": 4.5, "soglia_umidita": 0.24},
    "Grano": {"fabbisogno": 3.5, "soglia_umidita": 0.18}
}

# Configurazione iniziale dei campi nella sessione
if "campi" not in st.session_state:
    st.session_state.campi = [
        {"nome": "Campo Nord", "lat": 41.9028, "lon": 12.4964, "coltura": "Pomodoro", "portata": 15.0}
    ]

# --- PANNELLO LATERALE ---
st.sidebar.header("➕ Gestione Campi Agricoli")

with st.sidebar.form("nuovo_campo_form", clear_on_submit=True):
    st.write("### Aggiungi Nuovo Appezzamento")
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

if st.sidebar.button("🗑️ Svuota Lista Campi"):
    st.session_state.campi = []
    st.rerun()

# --- SCHERMATA CENTRALE ---
if not st.session_state.campi:
    st.info("Nessun campo inserito. Usa il modulo a sinistra per mappare il tuo primo terreno.")
else:
    st.write(f"Monitoraggio attivo su **{len(st.session_state.campi)}** zone aziendali:")
    
    nomi_campi = [c["nome"] for c in st.session_state.campi]
    tabs = st.tabs(nomi_campi)
    
    for i, tab in enumerate(tabs):
        campo = st.session_state.campi[i]
        coltura_info = DIZIONARIO_LOCALE[campo["coltura"]]
        
        with tab:
            st.subheader(f"Analisi Campo: {campo['nome']} | Coltura: {campo['coltura']}")
            
            # Configurazione dei parametri tramite dizionario strutturato (Niente URL manuali)
            params = {
                "latitude": campo["lat"],
                "longitude": campo["lon"],
                "current": ["temperature_2m", "relative_humidity_2m", "rain"],
                "hourly": "soil_moisture_3_to_9cm",
                "timezone": "auto"
            }
            
            try:
                # Chiamata tramite SDK ufficiale Open-Meteo
                responses = openmeteo.weather_api("https://open-meteo.com", params=params)
                response = responses[0]
                
                # Elaborazione dati correnti
                current = response.Current()
                temp = current.Variables(0).Value()
                umidita_aria = current.Variables(1).Value()
                pioggia = current.Variables(2).Value()
                
                # Elaborazione dati del suolo (orari)
                hourly = response.Hourly()
                soil_moisture_vals = hourly.Variables(0).ValuesAsNumpy()
                soil_mst = float(soil_moisture_vals[-1]) if soil_moisture_vals is not None else 0.22
                
                # Interfaccia grafica a colonne
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Temperatura Aria", f"{temp:.1f} °C")
                c2.metric("Umidità Aria", f"{int(umidita_aria)} %")
                c3.metric("Pioggia Odierna", f"{pioxia:.1f} mm" if 'pioxia' in locals() else f"{pioggia:.1f} mm")
                c4.metric("Umidità Suolo", f"{soil_mst:.3f} m³/m³")
                
                # Regola decisionale agronomica
                st.write("### 🧠 Bilancio Idrico e Consiglio di Irrigazione")
                fabbisogno_coltura = coltura_info["fabbisogno"]
                soglia_critica = coltura_info["soglia_umidita"]
                
                if pioggia >= fabbisogno_coltura:
                    st.success(f"🌧️ **NON IRRIGARE:** La pioggia odierna ({pioggia:.1f} mm) copre il fabbisogno della pianta ({fabbisogno_coltura} mm).")
                elif soil_mst < soglia_critica:
                    acqua_da_integrare = max(0.0, fabbisogno_coltura - pioggia)
                    tempo_ore = acqua_da_integrare / campo["portata"]
                    minuti = int(tempo_ore * 60)
                    
                    st.error(f"🚨 **IRRIGAZIONE RICHIESTA:** Il terreno è sotto la soglia di stress idrico per il {campo['coltura']} ({soil_mst:.3f} < {soglia_critica}).")
                    st.warning(f"⏱️ **Dosaggio consigliato:** Attiva l'impianto per **{minuti} minuti**.")
                else:
                    st.info(f"✅ **IDRATAZIONE OTTIMALE:** Umidità del suolo stabile. Non è necessario irrigare.")
                    
            except Exception as e:
                st.error(f"❌ Errore durante l'elaborazione dei dati meteo dell'SDK: {e}")
