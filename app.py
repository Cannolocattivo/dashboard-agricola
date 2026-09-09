import streamlit as st
import requests

# Configurazione della pagina
st.set_page_config(page_title="Dashboard Agricola Smart", layout="wide")
st.title("🚜 Dashboard Agricola: Monitoraggio Campi")

# Dizionario agronomico locale di stabilità
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
            st.caption(f"Coordinate: {campo['lat']}, {campo['lon']} | Impianto: {campo['portata']} l/h/mq")
            
            # FORMATO FUNZIONANTE: Parametri passati come stringhe fisse senza array Python
            url_base = "https://open-meteo.com"
            parametri_api = {
                "latitude": float(campo["lat"]),
                "longitude": float(campo["lon"]),
                "current": "temperature_2m,relative_humidity_2m,rain",
                "hourly": "soil_moisture_3_to_9cm",
                "timezone": "auto"
            }
            
            try:
                # Chiamata HTTP con stringhe pulite
                risposta = requests.get(url_base, params=parametri_api, timeout=10)
                
                # Intercettiamo gli errori HTTP prima del parsing JSON
                if risposta.status_code != 200:
                    st.error(f"⚠️ Il server meteo ha risposto con codice di errore {risposta.status_code}.")
                    st.text(f"Risposta del server: {risposta.text}")
                else:
                    dati = risposta.json()
                    
                    if "current" in dati and "hourly" in dati:
                        # Estrazione dati correnti
                        current = dati["current"]
                        temp = current.get("temperature_2m", 0.0)
                        umidita_aria = current.get("relative_humidity_2m", 0.0)
                        pioggia = current.get("rain", 0.0)
                        
                        # Estrazione sicura umidità suolo
                        lista_suolo = dati["hourly"].get("soil_moisture_3_to_9cm", [])
                        lista_valida = [v for v in lista_suolo if v is not None]
                        soil_mst = lista_valida[-1] if lista_valida else 0.22
                        
                        # Interfaccia grafica a colonne
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Temperatura Aria", f"{temp:.1f} °C")
                        c2.metric("Umidità Aria", f"{int(umidita_aria)} %")
                        c3.metric("Pioggia Odierna", f"{pioggia:.1f} mm")
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
                            
                            st.error(f"🚨 **IRRIGAZIONE RICHIESTA:** Il terreno è sotto la soglia di stress idrico ({soil_mst:.3f} < {soglia_critica}).")
                            st.warning(f"⏱ **Dosaggio consigliato:** Attiva l'impianto per **{minuti} minuti** per erogare i {acqua_da_integrare:.1f} mm mancanti.")
                        else:
                            st.info(f"✅ **IDRATAZIONE OTTIMALE:** Umidità del suolo stabile ({soil_mst:.3f}). Non è necessario irrigare.")
                    else:
                        st.error("⚠️ Struttura dati meteo incompleta ricevuta dal server.")
                        
            except Exception as e:
                st.error(f"❌ Errore durante la richiesta: {e}")
