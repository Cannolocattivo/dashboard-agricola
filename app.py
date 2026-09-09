import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# Configurazione della pagina
st.set_page_config(page_title="Dashboard Agricola Professionale", layout="wide")
st.title("🚜 Smart Farming Dashboard: Monitoraggio, Mappe & Gestione Cicli")

# Dizionario agronomico locale di stabilità
# Aggiunti giorni standard di maturazione biologica per stimare il raccolto
DIZIONARIO_LOCALE = {
    "Pomodoro": {"fabbisogno": 5.0, "soglia_umidita": 0.25, "giorni_maturazione": 100},
    "Mais": {"fabbisogno": 6.0, "soglia_umidita": 0.22, "giorni_maturazione": 120},
    "Olivo": {"fabbisogno": 2.0, "soglia_umidita": 0.15, "giorni_maturazione": 210},
    "Vite": {"fabbisogno": 2.5, "soglia_umidita": 0.16, "giorni_maturazione": 150},
    "Patata": {"fabbisogno": 4.5, "soglia_umidita": 0.24, "giorni_maturazione": 110},
    "Grano": {"fabbisogno": 3.5, "soglia_umidita": 0.18, "giorni_maturazione": 240}
}

# Inizializzazione dello stato della sessione per campi attivi e archivio raccolti
if "campi" not in st.session_state:
    st.session_state.campi = [
        {"nome": "Campo Nord", "lat": 41.9028, "lon": 12.4964, "coltura": "Pomodoro", "portata": 15.0, "data_semina": datetime.now().strftime("%Y-%m-%d")}
    ]
if "archivio" not in st.session_state:
    st.session_state.archivio = []

# --- PANNELLO LATERALE: INPUT NUOVI CAMPI ---
st.sidebar.header("⚙️ Pannello di Controllo Aziendale")

with st.sidebar.form("nuovo_campo_form", clear_on_submit=True):
    st.write("### ➕ Aggiungi Nuovo Appezzamento")
    nuovo_nome = st.text_input("Nome Identificativo", placeholder="es. Uliveto Valle")
    nuova_lat = st.number_input("Latitudine", value=41.8902, format="%.4f")
    nuova_lon = st.number_input("Longitudine", value=12.4922, format="%.4f")
    nuova_coltura = st.selectbox("Tipo di Piantagione", list(DIZIONARIO_LOCALE.keys()))
    nuova_portata = st.number_input("Portata Impianto (litri/ora per mq)", value=15.0)
    nuova_data_semina = st.date_input("Data di Semina/Inizio Ciclo", datetime.now())
    
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

# --- SCHERMATA CENTRALE DEL DISPOSITIVO A SCHEDE ---
scheda_monitoraggio, scheda_mappa, scheda_raccolto, scheda_archivio = st.tabs([
    "📊 Monitoraggio & Irrigazione", 
    "🗺️ Mappa Satellitare", 
    "🌾 Gestione Raccolto", 
    "🗄️ Archivio Storico"
])

# --- TAB 1: MONITORAGGIO E IRRIGAZIONE ---
with scheda_monitoraggio:
    if not st.session_state.campi:
        st.info("Nessun campo attivo inserito. Usa il modulo a sinistra per mappare un terreno.")
    else:
        st.write(f"## Registro delle Irrigazioni Intelligenti ({len(st.session_state.campi)} Attivi)")
        
        for campo in st.session_state.campi:
            coltura_info = DIZIONARIO_LOCALE[campo["coltura"]]
            
            with st.expander(f"📋 Registro Campo: {campo['nome']} ({campo['coltura']})", expanded=True):
                url_chiamata = (
                    f"https://api.open-meteo.com/v1/forecast"
                    f"?latitude={campo['lat']}&longitude={campo['lon']}"
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
                        
                        lista_suolo = dati.get("hourly", {}).get("soil_moisture_3_to_9cm", [])
                        lista_valida = [v for v in lista_suolo if v is not None]
                        soil_mst_attuale = lista_valida[-1] if lista_valida else 0.22
                        
                        piogge_previste = dati.get("daily", {}).get("rain_sum", [0.0, 0.0, 0.0])
                        pioggia_domani = piogge_previste[1] if len(piogge_previste) > 1 else 0.0
                        
                        # Mostra Metriche
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Temperatura Aria", f"{temp:.1f} °C")
                        c2.metric("Umidità Aria", f"{int(umidita_aria)} %")
                        c3.metric("Pioggia Oggi", f"{pioggia_odierna:.1f} mm")
                        c4.metric("Umidità Suolo", f"{soil_mst_attuale:.3f} m³/m³")
                        
                        # Logica di calcolo dei risparmi idrici
                        fabbisogno = coltura_info["fabbisogno"]
                        soglia_critica = coltura_info["soglia_umidita"]
                        giorno_irrigazione = datetime.now().strftime("%d/%m/%Y")
                        
                        if pioggia_odierna >= fabbisogno or pioggia_domani >= fabbisogno:
                            stato_irr = "Sospesa (Meteo favorevole)"
                            ora_fine = "06:00"
                            acqua_smart = 0.0
                            risparmio = fabbisogno
                        elif soil_mst_attuale < soglia_critica:
                            stato_irr = "Attiva (Terreno secco)"
                            acqua_da_integrare = max(0.0, fabbisogno - pioggia_odierna)
                            tempo_ore = acqua_da_integrare / campo["portata"]
                            minuti = int(tempo_ore * 60)
                            ora_fine = (datetime.strptime("06:00", "%H:%M") + timedelta(minutes=minuti)).strftime("%H:%M")
                            acqua_smart = acqua_da_integrare
                            risparmio = fabbisogno - acqua_smart
                        else:
                            stato_irr = "Sospesa (Umidità ottimale)"
                            ora_fine = "06:00"
                            acqua_smart = 0.0
                            risparmio = fabbisogno

                        # Griglia dati sintetici
                        df_reg = pd.DataFrame({
                            "Parametro": ["Stato Impianto", "Giorno", "Ora Inizio", "Ora Fine", "Acqua Erogata Smart", "Acqua Risparmiata"],
                            "Valore": [stato_irr, giorno_irrigazione, "06:00", ora_fine, f"{acqua_smart:.1f} mm", f"{risparmio:.1f} mm"]
                        })
                        st.table(df_reg)
                    else:
                        st.error("Rifiuto di comunicazione dal server meteo.")
                except Exception as e:
                    st.error(f"Errore di caricamento: {e}")

# --- TAB 2: MAPPA SATURATA A RICHIESTA ---
with scheda_mappa:
    if st.session_state.campi:
        st.write("## 🗺️ Mappa Satellitare dei Campi Aziendali")
        data_mappa = pd.DataFrame([{"latitude": c["lat"], "longitude": c["lon"]} for c in st.session_state.campi])
        st.map(data_mappa, zoom=11, use_container_width=True)
    else:
        st.info("Nessun campo attivo da mostrare sulla mappa.")

# --- TAB 3: GESTIONE RACCOLTO ED ESTIMATORE IN TEMPO REALE ---
with scheda_raccolto:
    if not st.session_state.campi:
        st.info("Nessun campo attivo da gestire per il raccolto.")
    else:
        st.write("## 🌾 Analisi Maturazione & Chiusura Campo")
        
        for idx, campo in enumerate(st.session_state.campi):
            coltura_info = DIZIONARIO_LOCALE[campo["coltura"]]
            dt_semina = datetime.strptime(campo["data_semina"], "%Y-%m-%d")
            
            # Calcolo dei giorni statistici trascorsi
            giorni_trascorri = (datetime.now() - dt_semina).days
            giorni_teorici_rimanenti = coltura_info["giorni_maturazione"] - giorni_trascorri
            
            # AGGIORNAMENTO IN REAL TIME: Adattamento dinamico basato sulle temperature medie storiche/attuali
            url_stima = f"https://api.open-meteo.com/v1/forecast?latitude={campo['lat']}&longitude={campo['lon']}&current=temperature_2m&timezone=auto"
            aggiustamento_clima = 0
            try:
                res_stima = requests.get(url_stima, timeout=5).json()
                temp_attuale = res_stima.get("current", {}).get("temperature_2m", 20.0)
                if temp_attuale > 28.0:
                    aggiustamento_clima = -5  # Accelera di 5 giorni per clima torrido
                elif temp_attuale < 12.0:
                    aggiustamento_clima = 7   # Ritarda di 7 giorni per blocco da freddo
            except:
                pass
            
            giorni_finali_stima = max(0, giorni_teorici_rimanenti + aggiustamento_clima)
            data_raccolto_stimata = (datetime.now() + timedelta(days=giorni_finali_stima)).strftime("%d/%m/%Y")
            
            st.write(f"### 📍 Appezzamento: {campo['nome']} (Coltura attuale: {campo['coltura']})")
            cr1, cr2, cr3 = st.columns(3)
            cr1.write(f"📅 **Data Semina:** {dt_semina.strftime('%d/%m/%Y')}")
            cr2.write(f"⏱️ **Giorni alla Raccolta:** ~ {giorni_finali_stima} giorni rimanenti")
            cr3.write(f"🔮 **Finestra Raccolta Stimata:** {data_raccolto_stimata}")
            
            # MODULO DI CHIUSURA CAMPO OBBLIGATORIO CON QUANTITÀ
            with st.form(f"chiusura_campo_{idx}"):
                st.write("⚠️ **Modulo di Chiusura Ciclo Coltura (Raccolto)**")
                quantita_raccolta = st.number_input("Quintali (q.li) Raccolti (Valore Obbligatorio)", min_value=0.1, step=0.1, format="%.1f")
                note_raccolto = st.text_input("Note Qualità Prodotto", placeholder="es. Ottima pezzatura, raccolto asciutto")
                
                chiudi_pulsante = st.form_submit_button("🎉 Registra Raccolto e Libera Terreno")
                if chiudi_pulsante:
                    campo["data_raccolto"] = datetime.now().strftime("%d/%m/%Y")
                    campo["quintali"] = quantita_raccolta
                    campo["note_qualita"] = note_raccolto if note_raccolto else "Nessuna nota"
                    
                    # Sposta in archivio e rimuovi dai campi attivi
                    st.session_state.archivio.append(campo)
                    st.session_state.campi.pop(idx)
                    st.success(f"Successo! {campo['nome']} chiuso. Dati salvati in archivio storico.")
                    st.rerun()
            st.write("---")

# --- TAB 4: ARCHIVIO STORICO DEI RACCOLTI ---
with scheda_archivio:
    st.write("## 🗄️ Registro Storico dei Raccolti Conclusi")
    if not st.session_state.archivio:
        st.caption("Nessun raccolto completato in archivio finora.")
    else:
        dati_tabella_archivio = []
        for arch in st.session_state.archivio:
            dati_tabella_archivio.append({
                "Nome Campo": arch["nome"],
                "Varietà Piantata": arch["coltura"],
                "Data Raccolta": arch["data_raccolto"],
                "Produzione Totale (q.li)": f"{arch['quintali']:.1f} q.li",
                "Note Qualità Agronoma": arch["note_qualita"]
            })
        df_archivio = pd.DataFrame(dati_tabella_archivio)
        st.dataframe(df_archivio, use_container_width=True)
