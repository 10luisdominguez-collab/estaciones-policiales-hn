import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# Configuración de página
st.set_page_config(page_title="Policía Cerca HN", page_icon="🚨", layout="centered")
st.title(" Estaciones Policiales Más Cercanas")

# Cargar la API Key desde los Secretos de Streamlit
if "GOOGLE_MAPS_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
else:
    st.error(" No se encontró la variable GOOGLE_MAPS_API_KEY en los secretos de Streamlit Cloud.")
    st.stop()

# Dataset con 5 estaciones policiales de Honduras
ESTACIONES_HN = [
    {"nombre": "Policía Nacional Jesús de Otoro", "latitud": 14.1232, "longitud": -87.9786},
    {"nombre": "Posta Policial Central DPI Siguatepeque", "latitud": 14.5912, "longitud": -87.8341},
    {"nombre": "Policía Nacional La Esperanza", "latitud": 14.3061, "longitud": -88.1748},
    {"nombre": "Policía Nacional Marcala La Paz", "latitud": 14.1537, "longitud": -88.0376},
    {"nombre": "Jefatura De Policía Comayagua", "latitud": 14.4536, "longitud": -87.6415},
]

st.info(" Solicitando ubicación GPS automática de tu dispositivo...")

# Captura de ubicación automática vía GPS
loc = get_geolocation()

if not loc or 'coords' not in loc:
    st.warning(" Por favor, autoriza los permisos de ubicación/GPS en tu navegador para continuar.")
    st.stop()

# Coordenadas exactas obtenidas del GPS del teléfono/PC
user_lat = loc['coords']['latitude']
user_lon = loc['coords']['longitude']
origen = (user_lat, user_lon)

st.success(f" Ubicación detectada: Lat {round(user_lat, 4)}, Lon {round(user_lon, 4)}")

# Cálculo de distancia precisa por carretera utilizando Google Maps API
destinos = [(e["latitud"], e["longitud"]) for e in ESTACIONES_HN]

try:
    matrix = gmaps.distance_matrix(origen, destinos, mode="driving")
    
    resultados = []
    for idx, est in enumerate(ESTACIONES_HN):
        element = matrix['rows'][0]['elements'][idx]
        if element['status'] == 'OK':
            dist_km = element['distance']['value'] / 1000.0  # metros a kilómetros
            tiempo = element['duration']['text']            # tiempo en auto
        else:
            dist_km = float('inf')
            tiempo = "Sin datos"
            
        resultados.append({
            "Estación Policial": est["nombre"],
            "Distancia Real": f"{round(dist_km, 2)} km",
            "Tiempo Estimado": tiempo,
            "dist_num": dist_km,
            "lat": est["latitud"],
            "lon": est["longitud"]
        })
    
    # Seleccionar las 3 más cercanas según el recorrido vial
    df_top3 = pd.DataFrame(resultados).sort_values("dist_num").head(3)
    
    st.subheader("Top 3 Estaciones Más Cercanas por Carretera")
    st.dataframe(df_top3[["Estación Policial", "Distancia Real", "Tiempo Estimado"]], use_container_width=True)
    
    # Mostrar mapa de Google Maps navegable con la estación más cercana
    estacion_destino = df_top3.iloc[0]
    dest_lat, dest_lon = estacion_destino["lat"], estacion_destino["lon"]
    
    gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={user_lat},{user_lon}&destination={dest_lat},{dest_lon}&mode=driving"
    
    st.subheader(f"🗺️ Ruta a la estación más cercana: {estacion_destino['Estación Policial']}")
    st.components.v1.iframe(gmaps_embed_url, height=450)

except Exception as e:
    st.error(f"Error al conectar con Google Maps: {e}")
