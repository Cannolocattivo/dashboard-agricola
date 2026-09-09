import streamlit as st
import requests

# Configurazione pagina
st.set_page_config(page_title="Dashboard Agricola", layout="wide")
st.title("🚜 Dashboard Agricola: Meteo & Irrigazione")

# Input coordinate aziendali (Default: Roma)
st.sidebar.header("📍 Posizione Azienda")
lat = st.sidebar.number_input("Latitudine", value=41.9028, format="%.4f")
lon = st.sidebar.number_input("Longitudine", value=12.4964, format="%.4f")

# URL Corretto: i dati del suolo vengono richiesti nel parametro "hourly"
url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain&hourly=soil_moisture_3_to_9cm&timezone=auto"

try:
    response = requests.get(url).json()
    
    # 1. Estrazione dati meteo correnti
    current = response["current"]
    temp = current["temperature_2m"]
    umidita = current["relative_humidity_2m"]
    pioggia = current["rain"]
    
    # 2. Estrazione ultimo dato orario disponibile sull'umidità del suolo
    hourly_soil = response["hourly"]["soil_moisture_3_to_9cm"]
    soil_mst = hourly_soil[-1] if hourly_soil else 0.0

    # Layout a colonne per i dati meteo
    st.header("🌦️ Condizioni Meteo in Tempo Reale")
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperatura dell'Aria", f"{temp} °C")
    col2.metric("Umidità Relativa", f"{umidita} %")
    col3.metric("Precipitazioni Odierne", f"{pioggia} mm")

    # Sezione Irrigazione
    st.header("💧 Gestione Irrigazione")
    col4, col5 = st.columns(2)
    
    with col4:
        st.subheader("Stato del Terreno")
        st.metric("Umidità del Suolo (3-9cm)", f"{soil_mst} m³/m³")
        
        # Logica decisionale automatica
        if soil_mst < 0.20 and pioggia == 0:
            st.error("🚨 STATO: Terreno troppo secco. Irrigazione CONSIGLIATA.")
        elif pioggia > 2:
            st.success("🌧️ STATO: Pioggia recente o in corso. Irrigazione NON necessaria.")
        else:
            st.info("✅ STATO: Livelli di umidità ottimali. Nessuna azione richiesta.")

    with col5:
        st.subheader("Pianificazione Intervento")
        portata = st.number_input("Portata impianto (litri/ora per mq)", value=15)
        fabbisogno = st.number_input("Fabbisogno idrico coltura (litri/mq)", value=5)
        
        tempo_irrigazione = fabbisogno / portata
        st.warning(f"⏱️ Tempo di irrigazione stimato: **{tempo_irrigazione:.2f} ore** ({int(tempo_irrigazione*60)} minutes)")

except Exception as e:
    st.error(f"Errore nel recupero dati: {e}")
