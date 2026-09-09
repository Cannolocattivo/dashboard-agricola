import streamlit as st
import requests
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

st.set_page_config(page_title="Smart Farming Dashboard", layout="wide")
st.title("🚜 Smart Farming Dashboard")

CROP_DATA = {
    "Tomato": {"water_need": 5.0, "soil_threshold": 0.25, "maturity_days": 100},
    "Corn": {"water_need": 6.0, "soil_threshold": 0.22, "maturity_days": 120},
    "Olive": {"water_need": 2.0, "soil_threshold": 0.15, "maturity_days": 210},
    "Grape": {"water_need": 2.5, "soil_threshold": 0.16, "maturity_days": 150},
    "Potato": {"water_need": 4.5, "soil_threshold": 0.24, "maturity_days": 110},
    "Wheat": {"water_need": 3.5, "soil_threshold": 0.18, "maturity_days": 240}
}

SOIL_TYPES = [
    "Clay", "Sandy", "Silty", "Loamy",
    "Clay Loam", "Sandy Loam", "Calcareous"
]

DB_FILE = "agriculture_dashboard.db"


def db():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            crop TEXT NOT NULL,
            soil_type TEXT NOT NULL,
            flow_rate REAL NOT NULL,
            planting_date TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            activity TEXT NOT NULL,
            irrigation_status TEXT,
            smart_water_mm REAL,
            water_saved_mm REAL,
            temperature_c REAL,
            air_humidity_pct REAL,
            soil_moisture REAL,
            current_rain_mm REAL,
            wind_speed_kmh REAL,
            solar_radiation_wm2 REAL,
            forecast_rain_3d_mm REAL,
            forecast_rain_probability_pct REAL,
            soil_type TEXT,
            manual_override TEXT,
            forced_water_mm REAL,
            override_reason TEXT,
            FOREIGN KEY(field_id) REFERENCES fields(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS harvests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            crop TEXT NOT NULL,
            soil_type TEXT NOT NULL,
            flow_rate REAL NOT NULL,
            planting_date TEXT NOT NULL,
            harvest_date TEXT NOT NULL,
            quantity_quintals REAL NOT NULL,
            quality_notes TEXT
        )
    """)

    conn.commit()
    conn.close()


def load_fields():
    conn = db()
    rows = conn.execute("""
        SELECT id, name, latitude, longitude, crop,
               soil_type, flow_rate, planting_date
        FROM fields ORDER BY id
    """).fetchall()
    conn.close()

    fields = []
    for row in rows:
        fields.append({
            "id": row[0],
            "name": row[1],
            "lat": row[2],
            "lon": row[3],
            "crop": row[4],
            "soil_type": row[5],
            "flow_rate": row[6],
            "planting_date": row[7]
        })

    return fields


def load_harvests():
    conn = db()
    rows = conn.execute("""
        SELECT field_name, latitude, longitude, crop,
               soil_type, flow_rate, planting_date,
               harvest_date, quantity_quintals, quality_notes
        FROM harvests ORDER BY id DESC
    """).fetchall()
    conn.close()
    return rows


def save_field(field):
    conn = db()

    try:
        conn.execute("""
            INSERT INTO fields
            (name, latitude, longitude, crop, soil_type,
             flow_rate, planting_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            field["name"], field["lat"], field["lon"],
            field["crop"], field["soil_type"],
            field["flow_rate"], field["planting_date"]
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        st.error("A field with this name already exists.")
    finally:
        conn.close()


def save_activity(field_id, activity):
    conn = db()

    conn.execute("""
        INSERT INTO activities (
            field_id, timestamp, activity, irrigation_status,
            smart_water_mm, water_saved_mm, temperature_c,
            air_humidity_pct, soil_moisture, current_rain_mm,
            wind_speed_kmh, solar_radiation_wm2,
            forecast_rain_3d_mm, forecast_rain_probability_pct,
            soil_type, manual_override, forced_water_mm,
            override_reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        field_id,
        activity["timestamp"],
        activity["activity"],
        activity.get("irrigation_status"),
        activity.get("smart_water_mm"),
        activity.get("water_saved_mm"),
        activity.get("temperature_c"),
        activity.get("air_humidity_pct"),
        activity.get("soil_moisture"),
        activity.get("current_rain_mm"),
        activity.get("wind_speed_kmh"),
        activity.get("solar_radiation"),
        activity.get("forecast_rain_3d_mm"),
        activity.get("forecast_rain_probability_pct"),
        activity.get("soil_type"),
        activity.get("manual_override"),
        activity.get("forced_water_mm"),
        activity.get("override_reason")
    ))

    conn.commit()
    conn.close()


def load_activities(field_id):
    conn = db()

    rows = conn.execute("""
        SELECT timestamp, activity, irrigation_status,
               smart_water_mm, water_saved_mm, temperature_c,
               air_humidity_pct, soil_moisture, current_rain_mm,
               wind_speed_kmh, solar_radiation_wm2,
               forecast_rain_3d_mm,
               forecast_rain_probability_pct, soil_type,
               manual_override, forced_water_mm, override_reason
        FROM activities
        WHERE field_id = ?
        ORDER BY timestamp DESC
    """, (field_id,)).fetchall()

    conn.close()

    columns = [
        "Date/Time", "Activity", "Irrigation Status",
        "Smart Water (mm)", "Water Saved (mm)",
        "Temperature (°C)", "Air Humidity (%)",
        "Soil Moisture (m³/m³)", "Current Rain (mm)",
        "Wind Speed (km/h)", "Solar Radiation (W/m²)",
        "3-Day Rain Forecast (mm)", "Rain Probability (%)",
        "Soil Type", "Manual Override",
        "Forced Water (mm)", "Override Reason"
    ]

    return pd.DataFrame(rows, columns=columns)


def save_harvest(field, quantity, notes):
    conn = db()

    conn.execute("""
        INSERT INTO harvests (
            field_name, latitude, longitude, crop, soil_type,
            flow_rate, planting_date, harvest_date,
            quantity_quintals, quality_notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        field["name"], field["lat"], field["lon"],
        field["crop"], field["soil_type"],
        field["flow_rate"], field["planting_date"],
        datetime.now().strftime("%d/%m/%Y"),
        quantity, notes
    ))

    conn.commit()
    conn.close()


def delete_field(field_id):
    conn = db()
    conn.execute("DELETE FROM activities WHERE field_id = ?", (field_id,))
    conn.execute("DELETE FROM fields WHERE id = ?", (field_id,))
    conn.commit()
    conn.close()


def clear_database():
    conn = db()
    conn.execute("DELETE FROM activities")
    conn.execute("DELETE FROM harvests")
    conn.execute("DELETE FROM fields")
    conn.commit()
    conn.close()


def get_weather(field):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={field['lat']}&longitude={field['lon']}"
        "&current=temperature_2m,relative_humidity_2m,rain,"
        "wind_speed_10m,shortwave_radiation"
        "&hourly=soil_moisture_3_to_9cm"
        "&daily=temperature_2m_max,temperature_2m_min,rain_sum,"
        "precipitation_probability_max,wind_speed_10m_max"
        "&forecast_days=3&timezone=auto"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def current_weather(data):
    current = data.get("current", {})
    soil_values = data.get("hourly", {}).get(
        "soil_moisture_3_to_9cm", []
    )

    valid_values = []
    for value in soil_values:
        if value is not None:
            valid_values.append(value)

    return {
        "temperature": current.get("temperature_2m", 20.0),
        "air_humidity": current.get("relative_humidity_2m", 50.0),
        "rain": current.get("rain", 0.0),
        "wind": current.get("wind_speed_10m", 0.0),
        "solar": current.get("shortwave_radiation", 0.0),
        "soil_moisture": valid_values[-1] if valid_values else 0.22
    }


def forecast_weather(data):
    daily = data.get("daily", {})

    rain = daily.get("rain_sum", [])[:3]
    probability = daily.get(
        "precipitation_probability_max", []
    )[:3]

    return {
        "dates": daily.get("time", [])[:3],
        "temp_min": daily.get("temperature_2m_min", [])[:3],
        "temp_max": daily.get("temperature_2m_max", [])[:3],
        "rain": rain,
        "probability": probability,
        "wind_max": daily.get("wind_speed_10m_max", [])[:3],
        "rain_3d": sum(rain),
        "max_probability": max(probability) if probability else 0
    }


init_db()

if "fields" not in st.session_state:
    st.session_state.fields = load_fields()


st.sidebar.header("⚙️ Farm Control Panel")

with st.sidebar.form("field_creation_form", clear_on_submit=True):

    st.write("### ➕ Add New Field")

    field_name = st.text_input(
        "Field Name",
        placeholder="e.g. North Olive Grove"
    )

    latitude = st.number_input(
        "Latitude", value=41.8902, format="%.4f"
    )

    longitude = st.number_input(
        "Longitude", value=12.4922, format="%.4f"
    )

    crop = st.selectbox("Crop", list(CROP_DATA.keys()))

    soil_type = st.selectbox("Soil Type", SOIL_TYPES)

    flow_rate = st.number_input(
        "Irrigation Flow Rate (l/h/m²)",
        min_value=0.1,
        value=15.0,
        step=0.5
    )

    planting_date = st.date_input(
        "Planting / Cycle Start Date",
        datetime.now()
    )

    save_button = st.form_submit_button("Save Field")

    if save_button:

        if not field_name.strip():
            st.error("Field name is required.")
        else:
            field = {
                "name": field_name.strip(),
                "lat": latitude,
                "lon": longitude,
                "crop": crop,
                "soil_type": soil_type,
                "flow_rate": flow_rate,
                "planting_date": planting_date.strftime("%Y-%m-%d")
            }

            save_field(field)
            st.session_state.fields = load_fields()
            st.rerun()


if st.sidebar.button("🗑️ Clear Entire Dashboard"):
    clear_database()
    st.session_state.fields = []
    st.rerun()


monitor_tab, map_tab, harvest_tab, archive_tab = st.tabs([
    "📊 Monitoring & Irrigation",
    "🗺️ Field Map",
    "🌾 Harvest Management",
    "🗄️ Historical Archive"
])


with monitor_tab:

    if not st.session_state.fields:
        st.info("No active fields. Add a field from the left panel.")
    else:

        st.write(
            f"## Smart Irrigation Register "
            f"({len(st.session_state.fields)} active)"
        )

        for field in st.session_state.fields:

            crop_data = CROP_DATA[field["crop"]]

            with st.expander(
                f"📋 Field: {field['name']} ({field['crop']})",
                expanded=True
            ):

                st.write(
                    f"**Soil type:** {field['soil_type']}"
                )

                try:
                    weather_data = get_weather(field)
                    current = current_weather(weather_data)
                    forecast = forecast_weather(weather_data)

                    c1, c2, c3, c4 = st.columns(4)

                    c1.metric(
                        "Air Temperature",
                        f"{current['temperature']:.1f} °C"
                    )
                    c2.metric(
                        "Air Humidity",
                        f"{current['air_humidity']:.0f} %"
                    )
                    c3.metric(
                        "Current Rain",
                        f"{current['rain']:.1f} mm"
                    )
                    c4.metric(
                        "Soil Moisture",
                        f"{current['soil_moisture']:.3f}"
                    )

                    c5, c6, c7 = st.columns(3)

                    c5.metric(
                        "Wind Speed",
                        f"{current['wind']:.1f} km/h"
                    )
                    c6.metric(
                        "Solar Radiation",
                        f"{current['solar']:.1f} W/m²"
                    )
                    c7.metric(
                        "Soil Type",
                        field["soil_type"]
                    )

                    water_need = crop_data["water_need"]
                    soil_threshold = crop_data["soil_threshold"]

                    tomorrow_rain = (
                        forecast["rain"][1]
                        if len(forecast["rain"]) > 1
                        else 0.0
                    )

                    if (
                        current["rain"] >= water_need
                        or tomorrow_rain >= water_need
                    ):
                        irrigation_status = (
                            "Suspended - favorable weather"
                        )
                        end_time = "06:00"
                        smart_water = 0.0
                        water_saved = water_need

                    elif current["soil_moisture"] < soil_threshold:

                        irrigation_status = "Active - dry soil"

                        water_to_apply = max(
                            0.0,
                            water_need - current["rain"]
                        )

                        hours = (
                            water_to_apply / field["flow_rate"]
                        )

                        minutes = int(hours * 60)

                        end_time = (
                            datetime.strptime("06:00", "%H:%M")
                            + timedelta(minutes=minutes)
                        ).strftime("%H:%M")

                        smart_water = water_to_apply
                        water_saved = water_need - smart_water

                    else:

                        irrigation_status = (
                            "Suspended - optimal soil moisture"
                        )
                        end_time = "06:00"
                        smart_water = 0.0
                        water_saved = water_need

                    # Save the automatic decision without requiring a button.
                    # One automatic check per field and hour avoids duplicate records
                    # caused by Streamlit reruns.
                    check_time = datetime.now().replace(
                        minute=0, second=0, microsecond=0
                    ).strftime("%Y-%m-%d %H:%M:%S")

                    conn = db()
                    already_recorded = conn.execute(
                        """
                        SELECT 1
                        FROM activities
                        WHERE field_id = ?
                        AND timestamp = ?
                        AND activity = ?
                        LIMIT 1
                        """,
                        (
                            field["id"],
                            check_time,
                            "Automatic weather and irrigation check"
                        )
                    ).fetchone()
                    conn.close()

                    if not already_recorded:
                        activity = {
                            "timestamp": check_time,
                            "activity": "Automatic weather and irrigation check",
                            "irrigation_status": irrigation_status,
                            "smart_water_mm": smart_water,
                            "water_saved_mm": water_saved,
                            "temperature_c": current["temperature"],
                            "air_humidity_pct": current["air_humidity"],
                            "soil_moisture": current["soil_moisture"],
                            "current_rain_mm": current["rain"],
                            "wind_speed_kmh": current["wind"],
                            "solar_radiation": current["solar"],
                            "forecast_rain_3d_mm": forecast["rain_3d"],
                            "forecast_rain_probability_pct": forecast[
                                "max_probability"
                            ],
                            "soil_type": field["soil_type"],
                            "manual_override": "No",
                            "forced_water_mm": None,
                            "override_reason": ""
                        }

                        save_activity(field["id"], activity)

                    st.write("### 🌦️ Three-Day Weather Forecast")

                    forecast_rows = []

                    for i, date in enumerate(forecast["dates"]):

                        min_temp = (
                            forecast["temp_min"][i]
                            if i < len(forecast["temp_min"])
                            else 0.0
                        )

                        max_temp = (
                            forecast["temp_max"][i]
                            if i < len(forecast["temp_max"])
                            else 0.0
                        )

                        rain = (
                            forecast["rain"][i]
                            if i < len(forecast["rain"])
                            else 0.0
                        )

                        probability = (
                            forecast["probability"][i]
                            if i < len(forecast["probability"])
                            else 0
                        )

                        wind = (
                            forecast["wind_max"][i]
                            if i < len(forecast["wind_max"])
                            else 0.0
                        )

                        forecast_rows.append({
                            "Date": datetime.strptime(
                                date, "%Y-%m-%d"
                            ).strftime("%d/%m/%Y"),
                            "Min Temp": f"{min_temp:.1f} °C",
                            "Max Temp": f"{max_temp:.1f} °C",
                            "Rain": f"{rain:.1f} mm",
                            "Rain Probability": f"{probability:.0f} %",
                            "Max Wind": f"{wind:.1f} km/h"
                        })

                    st.dataframe(
                        pd.DataFrame(forecast_rows),
                        use_container_width=True,
                        hide_index=True
                    )

                    if forecast["rain_3d"] >= water_need:
                        recommendation = (
                            "🌧️ Significant rain is expected. "
                            "Automatic irrigation should normally "
                            "remain suspended."
                        )
                    elif (
                        current["soil_moisture"] < soil_threshold
                        and forecast["rain_3d"] < water_need
                    ):
                        recommendation = (
                            "⚠️ Soil moisture is below the crop "
                            "threshold and limited rain is expected. "
                            "Irrigation should be considered."
                        )
                    else:
                        recommendation = (
                            "ℹ️ Conditions are currently within "
                            "the expected range."
                        )

                    st.info(recommendation)

                    st.write("### 💧 Manual Irrigation Override")

                    with st.form(
                        f"manual_irrigation_{field['id']}"
                    ):

                        forced_water = st.number_input(
                            "Water quantity (mm)",
                            min_value=0.1,
                            value=float(water_need),
                            step=0.5
                        )

                        override_reason = st.text_input(
                            "Reason for manual override",
                            value="Manual operator decision"
                        )

                        force_button = st.form_submit_button(
                            "💧 Force Irrigation"
                        )

                        if force_button:

                            activity = {
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "activity": "Manual irrigation override",
                                "irrigation_status": "Forced manually",
                                "smart_water_mm": None,
                                "water_saved_mm": None,
                                "temperature_c": current["temperature"],
                                "air_humidity_pct": current["air_humidity"],
                                "soil_moisture": current["soil_moisture"],
                                "current_rain_mm": current["rain"],
                                "wind_speed_kmh": current["wind"],
                                "solar_radiation": current["solar"],
                                "forecast_rain_3d_mm": forecast["rain_3d"],
                                "forecast_rain_probability_pct": forecast[
                                    "max_probability"
                                ],
                                "soil_type": field["soil_type"],
                                "manual_override": "Yes",
                                "forced_water_mm": forced_water,
                                "override_reason": override_reason
                            }

                            save_activity(
                                field["id"],
                                activity
                            )

                            st.success(
                                "Manual irrigation override recorded."
                            )
                            st.rerun()

                    st.write(
                        "### 📋 Chronological Field Activity Register"
                    )

                    activity_df = load_activities(field["id"])

                    if activity_df.empty:
                        st.info(
                            "No activities recorded for this field yet."
                        )
                    else:
                        st.dataframe(
                            activity_df,
                            use_container_width=True,
                            hide_index=True
                        )

                except requests.RequestException as error:
                    st.error(
                        f"Weather service communication error: {error}"
                    )
                except ValueError as error:
                    st.error(f"Invalid weather data: {error}")


with map_tab:

    if st.session_state.fields:

        st.write("## 🗺️ Agricultural Field Map")

        map_data = []

        for field in st.session_state.fields:
            map_data.append({
                "latitude": field["lat"],
                "longitude": field["lon"]
            })

        st.map(
            pd.DataFrame(map_data),
            zoom=11,
            use_container_width=True
        )

    else:
        st.info("No active fields available.")


with harvest_tab:

    if not st.session_state.fields:

        st.info(
            "No active fields available for harvest management."
        )

    else:

        st.write("## 🌾 Crop Maturity & Harvest Management")

        for field in st.session_state.fields:

            crop_data = CROP_DATA[field["crop"]]

            planting_date = datetime.strptime(
                field["planting_date"],
                "%Y-%m-%d"
            )

            days_elapsed = (
                datetime.now() - planting_date
            ).days

            days_remaining = max(
                0,
                crop_data["maturity_days"] - days_elapsed
            )

            estimated_harvest = (
                datetime.now()
                + timedelta(days=days_remaining)
            ).strftime("%d/%m/%Y")

            st.write(
                f"### 📍 {field['name']} ({field['crop']})"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.write(
                f"📅 **Planting:** "
                f"{planting_date.strftime('%d/%m/%Y')}"
            )

            c2.write(
                f"⏱️ **Days to harvest:** "
                f"~ {days_remaining}"
            )

            c3.write(
                f"🔮 **Estimated harvest:** "
                f"{estimated_harvest}"
            )

            c4.write(
                f"🌱 **Soil:** {field['soil_type']}"
            )

            with st.form(f"harvest_{field['id']}"):

                st.write("⚠️ **Close Crop Cycle**")

                quantity = st.number_input(
                    "Harvest quantity (quintals)",
                    min_value=0.1,
                    step=0.1,
                    format="%.1f",
                    key=f"quantity_{field['id']}"
                )

                notes = st.text_input(
                    "Product quality notes",
                    placeholder="e.g. Excellent quality, dry harvest",
                    key=f"notes_{field['id']}"
                )

                close_button = st.form_submit_button(
                    "🎉 Register Harvest"
                )

                if close_button:

                    save_harvest(
                        field,
                        quantity,
                        notes or "No notes"
                    )

                    delete_field(field["id"])

                    st.session_state.fields = load_fields()

                    st.success(
                        f"Field {field['name']} closed and archived."
                    )
                    st.rerun()

            st.write("---")


with archive_tab:

    st.write("## 🗄️ Historical Harvest Archive")

    harvests = load_harvests()

    if not harvests:

        st.caption("No completed harvests in the archive.")

    else:

        archive_rows = []

        for harvest in harvests:

            archive_rows.append({
                "Field Name": harvest[0],
                "Latitude": harvest[1],
                "Longitude": harvest[2],
                "Crop": harvest[3],
                "Soil Type": harvest[4],
                "Flow Rate": f"{harvest[5]:.1f} l/h/m²",
                "Planting Date": datetime.strptime(
                    harvest[6], "%Y-%m-%d"
                ).strftime("%d/%m/%Y"),
                "Harvest Date": harvest[7],
                "Production": f"{harvest[8]:.1f} q.li",
                "Quality Notes": harvest[9]
            })

        st.dataframe(
            pd.DataFrame(archive_rows),
            use_container_width=True,
            hide_index=True
