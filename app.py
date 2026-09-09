import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configurazione della pagina
st.set_page_config(page_title="Dashboard Agricola Smart", layout="wide")
st.title("🚜 Dashboard Agricola: Monitoraggio & Previsioni")

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
            
            # BLINDATURA REALE: Usiamo sessioni HTTP separate ed escludiamo la funzione di encoding 
            # iniettando i parametri separati da "&" nativi direttamente all'interno della stringa dell'URL.
            url_chiamata = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={campo['lat']}"
                f"&longitude={campo['lon']}"
                f"&current=temperature_2m&current=relative_humidity_2m&current=rain"
                f"&hourly=soil_moisture_3_to_9cm"
                f"&daily=rain_sum"
                f"&forecast_days=3"
                f"&timezone=auto"
            )
            
            try:
                # Interroghiamo l'indirizzo web forzato
                sessione = requests.Session()
                risposta = sessione.get(url_chiamata, timeout=12)
                
                if risposta.status_code != 200:
                    st.error(f"⚠️ Errore di comunicazione (Codice server: {risposta.status_code}).")
                    st.text(f"Dettaglio tecnico del rifiuto: {risposta.text}")
                else:
                    dati = risposta.json()
                    
                    # 1. ESTREZIONE DATI ATTUALI
                    current = dati.get("current", {})
                    temp = current.get("temperature_2m", 20.0)
                    pioggia_odierna = current.get("rain", 0.0)
                    umidita_aria = current.get("relative_humidity_2m", 50.0)
                    
                    # 2. ESTREZIONE DATI DEL SUOLO E GRAFICO
                    hourly = dati.get("hourly", {})
                    ore = hourly.get("time", [])
                    lista_suolo = hourly.get("soil_moisture_3_to_9cm", [])
                    
                    lista_valida = [v for v in lista_suolo if v is not None]
                    soil_mst_attuale = lista_valida[-1] if lista_valida else 0.22
                    
                    # 3. ESTREZIONE PREVISIONI 3 GIORNI
                    daily = dati.get("daily", {})
                    giorni = daily.get("time", [])
                    piogge_previste = daily.get("rain_sum", [0.0, 0.0, 0.0])
                    
                    pioggia_oggi_prev = piogge_previste[0] if len(piogge_previste) > 0 else 0.0
                    pioggia_domani = piogge_previste[1] if len(piogge_previste) > 1 else 0.0
                    pioggia_dopodomani = piogge_previste[2] if len(piogge_previste) > 2 else 0.0
                    
                    # --- INTERFACCIA: METRICHE METEO ---
                    st.write("### 🌦️ Stato Attuale")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Temperatura Aria", f"{temp:.1f} °C")
                    c2.metric("Umidità Aria", f"{int(umidita_aria)} %")
                    c3.metric("Pioggia Reale Oggi", f"{pioggia_odierna:.1f} mm")
                    c4.metric("Umidità Suolo", f"{soil_mst_attuale:.3f} m³/m³")
                    
                    # --- INTERFACCIA: PREVISIONI 3 GIORNI ---
                    st.write("### 📅 Previsioni Pioggia (Prossimi 3 Giorni)")
                    cp1, cp2, cp3 = st.columns(3)
                    
                    def formatta_data(data_str):
                        try:
                            return datetime.strptime(data_str, "%Y-%m-%d").strftime("%d/%m")
                        except:
                            return data_str
                    
                    data_oggi = formatta_data(giorni[0]) if giorni else "Oggi"
                    data_domani = formatta_data(giorni[1]) if len(giorni) > 1 else "Domani"
                    data_dopodomani = formatta_data(giorni[2]) if len(giorni) > 2 else "Dopodomani"
                    
                    cp1.metric(f"Oggi ({data_oggi})", f"{pioggia_oggi_prev:.1f} mm")
                    cp2.metric(f"Domani ({data_domani})", f"{pioggia_domani:.1f} mm")
                    cp3.metric(f"Dopodomani ({data_dopodomani})", f"{pioggia_dopodomani:.1f} mm")
                    
                    # --- INTERFACCIA: GRAFICO STORICO ---
                    st.write("### 📈 Andamento dell'Umidità del Suolo (72 Ore)")
                    if ore and lista_suolo:
                        df_grafico = pd.DataFrame({
                            "Data e Ora": pd.to_datetime(ore),
                            "Umidità Suolo (m³/m³)": lista_suolo
                        })
                        df_grafico.set_index("Data e Ora", inplace=True)
                        st.line_chart(df_grafico)
                    else:
                        st.warning("Dati storici del suolo temporaneamente non disponibili per il grafico.")
                    
                    # --- MOTORE DECISIONALE AGRONOMICO AVANZATO ---
                    st.write("### 🧠 Bilancio Idrico Predittivo e Consiglio di Irrigazione")
                    fabbisogno_coltura = coltura_info["fabbisogno"]
                    soglia_critica = coltura_info["soglia_umidita"]
                    
                    if pioggia_odierna >= fabbisogno_coltura:
                        st.success(f"🌧️ **NON IRRIGARE:** La pioggia reale di oggi ({pioggia_odierna:.1f} mm) copre il fabbisogno del {campo['coltura']}.")
                    elif pioggia_domani >= fabbisogno_coltura:
                        st.warning(f"⚠️ **SOSPENSIONE PREVENTIVA:** Il terreno è asciutto, ma per domani sono previsti {pioggia_domani:.1f} mm di pioggia. Si consiglia di posticipare l'irrigazione.")
                    elif soil_mst_attuale < soglia_critica:
                        acqua_da_integrare = max(0.0, fabbisogno_coltura - pioggia_odierna)
                        tempo_ore = acqua_da_integrare / campo["portata"]
                        minuti = int(tempo_ore * 60)
                        
                        st.error(f"🚨 **IRRIGAZIONE RICHIESTA:** L'umidità del suolo ({soil_mst_attuale:.3f}) è inferiore alla soglia critica ({soglia_critica}).")
                        st.warning(f"⏱ **Dosaggio consigliato:** Attiva l'impianto per **{minuti}** minuti per erogare i {acqua_da_integrare:.1f} mm necessari.")
                    else:
                        st.info(f"✅ **IDRATAZIONE OTTIMALE:** L'umidità del suolo ({soil_mst_attuale:.3f}) è stabile. Nessun intervento richiesto.")
                        
            except Exception as e:
                st.error(f"❌ Impossibile caricare o elaborare i dati: {e}")
