import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# 1. Configuración de Google Maps API Key
# Reemplaza con tu clave de API de Google Maps
GOOGLE_MAPS_API_KEY = "AIzaSyBxOLyStOQaJtay8gMRjjeA0byQVE4q9u8" 

gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY != "AIzaSyBxOLyStOQaJtay8gMRjjeA0byQVE4q9u8" else None

# 2. Dataset con 5 estaciones policiales en Honduras
ESTACIONES_HN = [
    {"nombre": "Policía Nacional Jesús de Otoro", "latitud": 14.1232, "longitud": -87.9786},
    {"nombre": "Posta Policial Central DPI Siguatepeque", "latitud": 14.5912, "longitud": -87.8341},
    {"nombre": "Policía Nacional La Esperanza", "latitud": 14.3061, "longitud": -88.1748},
    {"nombre": "Policía Nacional Marcala La Paz", "latitud": 14.1537, "longitud": -88.0376},
    {"nombre": "Jefatura De Policía Comayagua", "latitud": 14.4536, "longitud": -87.6415},
]

st.set_page_config(page_title="Policía Cerca HN", page_icon="", layout="centered")
st.title(" Estaciones Policiales Más Cercanas")

st.info(" Obteniendo tu ubicación en tiempo real mediante GPS...")

# 3. Captura automática por GPS del dispositivo (Sin inputs de usuario)
loc = get_geolocation()

if not loc or 'coords' not in loc:
    st.warning(" Por favor habilita los permisos de ubicación/GPS en tu navegador o dispositivo móvil para continuar.")
    st.stop()

# Coordenadas exactas obtenidas del GPS
user_lat = loc['coords']['latitude']
user_lon = loc['coords']['longitude']
origen = (user_lat, user_lon)

st.success(f" GPS Detectado: Lat {round(user_lat, 4)}, Lon {round(user_lon, 4)}")

# 4. Cálculo de distancia precisa por carretera (Google Distance Matrix API)
resultados = []

if gmaps:
    destinos = [(e["latitud"], e["longitud"]) for e in ESTACIONES_HN]
    
    # Consulta a Google Maps para calcular ruta en auto
    matrix = gmaps.distance_matrix(origen, destinos, mode="driving")
    
    for idx, est in enumerate(ESTACIONES_HN):
        element = matrix['rows'][0]['elements'][idx]
        if element['status'] == 'OK':
            dist_km = element['distance']['value'] / 1000.0  # Convertir metros a km
            tiempo = element['duration']['text']            # Tiempo estimado en auto
        else:
            dist_km = float('inf')
            tiempo = "N/D"
            
        resultados.append({
            "Estación Policial": est["nombre"],
            "Distancia Real": f"{round(dist_km, 2)} km",
            "Tiempo en Auto": tiempo,
            "dist_num": dist_km,
            "lat": est["latitud"],
            "lon": est["longitud"]
        })
    
    # Ordenar por la distancia más corta por carretera
    df_top3 = pd.DataFrame(resultados).sort_values("dist_num").head(3)
    
    st.subheader("Top 3 Estaciones Más Cercanas (Ruta por Carretera)")
    st.dataframe(df_top3[["Estación Policial", "Distancia Real", "Tiempo en Auto"]], use_container_width=True)
    
    # 5. Generar Mapa Integrado con Google Maps
    # URL dinámica con marcas en Google Maps
    estacion_destino = df_top3.iloc[0]
    dest_lat, dest_lon = estacion_destino["lat"], estacion_destino["lon"]
    
    gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_MAPS_API_KEY}&origin={user_lat},{user_lon}&destination={dest_lat},{dest_lon}&mode=driving"
    
    st.subheader(f" Ruta a: {estacion_destino['Estación Policial']}")
    st.components.v1.iframe(gmaps_embed_url, height=450)

else:
    st.error("Es necesario configurar la variable `GOOGLE_MAPS_API_KEY` para activar el cálculo de ruta y el mapa de Google Maps.")
