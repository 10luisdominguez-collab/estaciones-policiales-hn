import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation

# Dataset con 5 estaciones policiales de Honduras
ESTACIONES_HN = [
    {"nombre": "Policía Nacional Jesús de Otoro", "latitud": 14.1232, "longitud": -87.9786},
    {"nombre": "Posta Policial Central DPI Siguatepeque", "latitud": 14.5912, "longitud": -87.8341},
    {"nombre": "Policía Nacional La Esperanza", "latitud": 14.3061, "longitud": -88.1748},
    {"nombre": "Policía Nacional Marcala La Paz", "latitud": 14.1537, "longitud": -88.0376},
    {"nombre": "Jefatura De Policía Comayagua", "latitud": 14.4536, "longitud": -87.6415},
]

st.set_page_config(page_title="Policía Cerca HN", page_icon="🚨")
st.title("🚨 Estaciones Policiales Más Cercanas en Honduras")
st.write("Obtén tu ubicación actual por GPS o ingresa coordenadas manualmente.")

# 1. Captura de ubicación automática vía dispositivo
loc = get_geolocation()
lat_default, lon_default = 14.1232, -87.9786

if loc and 'coords' in loc:
    lat_default = loc['coords']['latitude']
    lon_default = loc['coords']['longitude']
    st.success("📍 Ubicación obtenida automáticamente desde tu dispositivo.")

# 2. Formulario de entrada
col1, col2 = st.columns(2)
with col1:
    lat_user = st.number_input("Latitud", value=float(lat_default), format="%.6f")
with col2:
    lon_user = st.number_input("Longitud", value=float(lon_default), format="%.6f")

# 3. Procesamiento al presionar "Buscar"
if st.button("Buscar Estaciones Cercanas"):
    punto_usuario = (lat_user, lon_user)
    
    resultados = []
    for est in ESTACIONES_HN:
        punto_estacion = (est["latitud"], est["longitud"])
        distancia_km = geodesic(punto_usuario, punto_estacion).km
        resultados.append({
            "Estación Policial": est["nombre"],
            "Latitud": est["latitud"],
            "Longitud": est["longitud"],
            "Distancia (km)": round(distancia_km, 2)
        })
    
    # Filtrar las 3 más cercanas
    df = pd.DataFrame(resultados).sort_values("Distancia (km)").head(3)
    
    st.subheader("Top 3 Estaciones Más Cercanas")
    st.dataframe(df[["Estación Policial", "Distancia (km)"]], use_container_width=True)
    
    # Visualización en el mapa
    st.map(df[["Latitud", "Longitud"]].rename(columns={"Latitud": "lat", "Longitud": "lon"}))
