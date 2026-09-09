import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# Configurazione della pagina
st.set_page_config(page_title="Dashboard Agricola Professionale", layout="wide")
st.title("🚜 Smart Farming Dashboard: Monitoraggio, Mappe & Gestione Cicli")

# Dizionario agronomico locale di stabilità con parametri di maturazione biologica
DIZIONARIO_LOCALE = {
    "Pomodoro": {"fabbisogno": 5.0, "soglia_umidita": 0.25, "giorni_maturazione": 100},
    "Mais": {"fabbisogno": 6.0, "soglia_umidita": 0.22, "giorni_maturazione": 120},
    "Olivo": {"fabbisogno": 2.0, "soglia_umidita": 0.15, "giorni_maturazione": 210},
    "Vite": {"fabbisogno": 2.5, "soglia_umidita": 0.16, "giorni_maturazione": 150},
    "Patata": {"fabbisogno": 4.5, "soglia_umidita": 0.24, "giorni_maturazione": 110},
    "Grano": {"fabbisogno": 3.5, "soglia_umidita": 0.18, "giorni_maturazione": 240}
}

# Inizializzazione dello stato della sessione per mantenere persistenti i dati aziendali
if "campi" not in st.session_state:
    st.session_state.campi = [
        {"nome": "Campo Nord", "lat": 41.9028, "lon": 12.4964, "coltura": "Pomodoro", "portata": 15.0, "data_semina": datetime.now().strftime("%Y-%m-%d")}
    ]
if "archivio" not in st.session_state:
    st.session_state.archivio = []

# --- PANNELLO LATERALE: GESTIONE INGRESSI ---
st.sidebar.header("⚙️ Pannello di Controllo Aziendale")

with st.sidebar.form("nuovo_campo_form", clear_on_submit=True):
    st.write("### ➕ Aggiungi Nuovo Appezzamento")
    nuovo_nome = st.text_input("Nome Identificativo", placeholder="es. Uliveto Valle")
    nuova_lat = st.number_input("Latitudine", value=41.8902, format="%.4f")
    nuova_lon = st.number_input("Longitudine", value=12.4922, format="%.4f")
    nuova_coltura = st.selectbox("Tipo di Piantagione", list(DIZIONARIO_LOCALE.keys()))
    nuova_portata = st.number_input("Portata Impianto (litri/ora per mq)", value=15.0)
    nuova_data_semina = st.date_input("Data di Semina / Inizio Ciclo", datetime.now())
    
    submit_nuovo = st.form_submit_button("Salva Campo")
    if submit_nuovo and nuovo_nome:
        st.session_state.campi.append({
            "nome": nuovo_nome, 
            "lat": nuova_lat, 
            "lon": nuova_lon, 
            "coltura": nuova_coltura, 
            "portata": nuova_portata,
            "data_semina": nuova_data_semina.strftime("%Y-%m-%d")
        })
        st.rerun()

if st.sidebar.button("🗑️ Svuota Tutta la Dashboard"):
    st.session_state.campi = []
    st.session_state.archivio = []
    st.rerun()

# --- SCHERMATA CENTRALE ORGANIZZATA A SCHEDE (TAB) ---
scheda_campi, scheda_mappa, scheda_archivio = st.tabs([
    "📊 Campi Attivi & Irrigazione", 
    "🗺️ Mappa Satellitare", 
    "🗄️ Archivio Storico Raccolti"
])

# --- TAB 1: GESTIONE CAMPI ATTIVI, BILANCIO IDRICO, GRAFICI E CHIUSURA ---
with scheda_campi:
    if not st.session_state.campi:
        st.info("Nessun campo attivo inserito. Usa il modulo nel pannello laterale a sinistra per aggiungere il tuo primo terreno.")
    else:
        st.write(f"## Monitoraggio Colture in Corso ({len(st.session_state.campi)} appezzamenti attivi)")
        
        # Sotto-schede per ciascun campo per mantenere pulito il layout grafico
        nomi_campi = [c["nome"] for c in st.session_state.campi]
        sub_tabs = st.tabs(nomi_campi)
        
        for idx, sub_tab in enumerate(sub_tabs):
            campo = st.session_state.campi[idx]
            coltura_info = DIZIONARIO_LOCALE[campo["coltura"]]
            dt_semina = datetime.strptime(campo["data_semina"], "%Y-%m-%d")
            
            with sub_tab:
                st.write(f"### Analisi Agronomica: **{campo['nome']}** | Coltura attuale: **{campo['coltura']}**")
                st.caption(f"Coordinate Geografiche GPS: Lat {campo['lat']}, Lon {campo['lon']} | Portata Erogatore Impianto: {campo['portata']} l/h/mq")
                
                # Composizione URL stringa pulita anti-encoding per Open-Meteo API
                url_chiamata = (
                    f"https://api.open-meteo.com/v1/forecast"
                    f"?latitude={campo['lat']}&longitude={campo['lon']}"
                    f"&current=temperature_2m&current=relative_humidity_2m&current=rain"
                    f"&hourly=soil_moisture_3_to_9cm"
                    f"&daily=rain_sum&forecast_days=3&timezone=auto"
                )
                
                try:
                    risposta = requests.get(url_chiamata, timeout=12)
                    if risposta.status_code == 200:
                        dati = risposta.json()
                        
                        # 1. Dati Meteo Correnti
                        current = dati.get("current", {})
                        temp = current.get("temperature_2m", 20.0)
                        pioggia_odierna = current.get("rain", 0.0)
                        umidita_aria = current.get("relative_humidity_2m", 50.0)
                        
                        # 2. Dati Orari (Umidità Suolo)
                        hourly = dati.get("hourly", {})
                        ore = hourly.get("time", [])
                        lista_suolo = hourly.get("soil_moisture_3_to_9cm", [])
                        lista_valida = [v for v in lista_suolo if v is not None]
                        soil_mst_attuale = lista_valida[-1] if lista_valida else 0.22
                        
                        # 3. Previsioni Pioggia Giornaliere (3 Giorni)
                        daily = dati.get("daily", {})
                        giorni = daily.get("time", [])
                        piogge_previste = daily.get("rain_sum", [0.0, 0.0, 0.0])
                        pioggia_domani = piogge_previste[1] if len(piogge_previste) > 1 else 0.0
                        
                        # Layout Metriche Rapide
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Temperatura Aria", f"{temp:.1f} °C")
                        c2.metric("Umidità Aria", f"{int(umidita_aria)} %")
                        c3.metric("Pioggia Oggi", f"{pioggia_odierna:.1f} mm")
                        c4.metric("Umidità Suolo Attuale", f"{soil_mst_attuale:.3f} m³/m³")
                        
                        # Calcolo Predittivo Maturazione in Real Time
                        giorni_trascorri = (datetime.now() - dt_semina).days
                        giorni_teorici_rimanenti = coltura_info["giorni_maturazione"] - giorni_trascorri
                        
                        # Correzione dinamica basata sul fattore termico in tempo reale
                        aggiustamento_clima = 0
                        if temp > 28.0:
                            aggiustamento_clima = -5  # Accelera maturazione per stress da calore
                        elif temp < 12.0:
                            aggiustamento_clima = 7   # Rallenta maturazione per basse temperature
                            
                        giorni_finali_stima = max(0, giorni_teorici_rimanenti + aggiustamento_clima)
                        data_raccolto_stimata = (datetime.now() + timedelta(days=giorni_finali_stima)).strftime("%d/%m/%Y")
                        
                        # Blocco Info Raccolto Stimato
                        st.info(f"📅 **Stima Raccolto in Real Time:** Inizio ciclo il {dt_semina.strftime('%d/%m/%Y')}. Giorni stimati rimanenti: **{giorni_finali_stima} giorni** (Finestra ipotetica: **{data_raccolto_stimata}**).")
                        
                        # Logica Decisionale Agronomica e Risparmio Idrico
                        fabbisogno = coltura_info["fabbisogno"]
                        soglia_critica = coltura_info["soglia_umidita"]
                        giorno_irrigazione = datetime.now().strftime("%d/%m/%Y")
                        acqua_manuale_standard = fabbisogno
                        
                        if pioggia_odierna >= fabbisogno or pioggia_domani >= fabbisogno:
                            stato_irr = "Sospesa (Previsioni Pioggia)"
                            ora_fine = "06:00"
                            acqua_smart = 0.0
                            risparmio = acqua_manuale_standard
                        elif soil_mst_attuale < soglia_critica:
                            stato_irr = "Attiva (Livelli Sotto Soglia)"
                            acqua_da_integrare = max(0.0, fabbisogno - pioggia_odierna)
                            tempo_ore = acqua_da_integrare / campo["portata"]
                            minuti = int(tempo_ore * 60)
                            ora_fine = (datetime.strptime("06:00", "%H:%M") + timedelta(minutes=minuti)).strftime("%H:%M")
                            acqua_smart = acqua_da_integrare
                            risparmio = acqua_manuale_standard - acqua_smart
                        else:
                            stato_irr = "Sospesa (Umidità Ottimale)"
                            ora_fine = "06:00"
                            acqua_smart = 0.0
                            risparmio = acqua_manuale_standard
                            
                        # Griglia Dati Sintetici Irrigazione
                        st.write("#### 📋 Parametri d'Intervento Giornalieri")
                        df_reg = pd.DataFrame({
                            "Parametro": ["Stato Impianto Automatico", "Giorno d'Intervento", "Ora Inizio Ciclo", "Ora Fine Stimata", "Volume Erogato Smart (l/mq)", "Volume Risparmiato (l/mq)"],
                            "Valore": [stato_irr, giorno_irrigazione, "06:00", ora_fine, f"{acqua_smart:.1f} mm", f"{risparmio:.1f} mm"]
                        })
                        st.table(df_reg)
                        
                        # --- GRAFICO STORICO DELL'UMIDITÀ DEL SUOLO ---
                        st.write("#### 📈 Andamento dell'Umidità del Terreno nelle 72 Ore")
                        if ore and lista_suolo:
                            df_grafico = pd.DataFrame({
                                "Asse Temporale": pd.to_datetime(ore),
                                "Umidità Volumetrica Terreno (m³/m³)": lista_suolo
                            }).set_index("Asse Temporale")
                            st.line_chart(df_grafico)
                        else:
                            st.warning("Dati storici del suolo non disponibili per questo quadrante.")
                            
                        # --- MODULO DI CHIUSURA CICLO E STORICIZZAZIONE IN FONDO ALLA SCHEDA ---
                        st.write("---")
                        st.write("#### 🌾 Fine Ciclo Coltura e Registrazione Raccolto")
                        st.write("Compila il registro di produzione sottostante per chiudere definitivamente questo campo, storicizzare tutti i dati accumulati e liberare il terreno per una nuova semina.")
                        
                        with st.form(f"modulo_chiusura_{idx}"):
                            quantita_raccolta = st.number_input("Quantità Totale Raccolta in Quintali (q.li) *Obbligatorio*", min_value=0.1, step=0.1, format="%.1f")
                            note_qualita = st.text_input("Annotazioni sulla Qualità della Produzione", placeholder="es. Ottima pezzatura, grado zuccherino elevato")
                            
                            pulsante_chiusura = st.form_submit_button("🎉 Registra Raccolto, Storicizza e Resetta Campo")
                            if pulsante_chiusura:
                                # Costruzione record storico comprensivo di tutti i dati
                                record_storico = {
                                    "nome": campo["nome"],
                                    "lat": campo["lat"],
                                    "lon": campo["lon"],
                                    "coltura": campo["coltura"],
                                    "portata": campo["portata"],
                                    "data_semina": campo["data_semina"],
                                    "data_raccolto": datetime.now().strftime("%d/%m/%Y"),
                                    "quintali": quantita_raccolta,
                                    "note_qualita": note_qualita if note_qualita else "Nessuna nota inserita"
                                }
                                # Salvataggio in archivio e rimozione immediata dai campi attivi
                                st.session_state.archivio.append(record_storico)
                                st.session_state.campi.pop(idx)
                                st.success(f"Dati storicizzati con successo! Il {campo['nome']} è stato resettato ed è pronto per una nuova coltivazione.")
                                st.rerun()
                                
                    else:
                        st.error("Il server satellitare Open-Meteo non ha risposto correttamente alle interrogazioni di rete.")
                except Exception as e:
                    st.error(f"Errore durante l'interrogazione dei moduli meteo-agricoli: {e}")

# --- TAB 2: MAPPA SATURATA A RICHIESTA DELL'UTENTE ---
with scheda_mappa:
    if not st.session_state.campi:
        st.info("Nessun campo attivo da localizzare sulla mappa.")
    else:
        st.write("## 🗺️ Mappa Satellitare Globale degli Appezzamenti Attivi")
        st.write("La mappa mostra la geolocalizzazione in tempo reale di tutte le colture non ancora raccolte.")
        df_mappa = pd.DataFrame([{"latitude": c["lat"], "longitude": c["lon"]} for c in st.session_state.campi])
        st.map(df_mappa, zoom=10, use_container_width=True)

# --- TAB 3: ARCHIVIO STORICO GENERALE ---
with scheda_archivio:
    st.write("## 🗄️ Registro Storico Aziendale dei Raccolti Conclusi")
    st.write("In questa sezione sono archiviati tutti i dati storicizzati dei vecchi cicli colturali conclusi.")
    
    if not st.session_state.archivio:
        st.caption("Nessun record memorizzato nel registro storico aziendale finora.")
    else:
        elenco_storicizzato = []
        for arch in st.session_state.archivio:
            elenco_storicizzato.append({
                "Appezzamento": arch["nome"],
                "Varietà Coltivata": arch["coltura"],
                "Data Semina": datetime.strptime(arch["data_semina"], "%Y-%m-%d").strftime("%d/%m/%Y"),
                "Data Raccolta": arch["data_raccolto"],
                "Resa Totale (q.li)": f"{arch['quintali']:.1f} q.li",
                "Note sulla Produzione": arch["note_qualita"],
                "Coordinate GPS": f"{arch['lat']:.4f}, {arch['lon']:.4f}"
            })
        df_archivio = pd.DataFrame(elenco_storicizzato)
        st.dataframe(df_archivio, use_container_width=True)
