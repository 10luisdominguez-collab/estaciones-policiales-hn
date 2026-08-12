import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# Configuración de página
st.set_page_config(page_title="Policía y Postas HN", page_icon="🚨", layout="centered")
st.title("🚨 Estaciones y Postas Policiales Más Cercanas")

# 1. Carga de la API Key única desde los Secrets de Streamlit
if "GOOGLE_MAPS_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
else:
    st.error("⚠️ Falta la variable GOOGLE_MAPS_API_KEY en la sección Secrets de Streamlit.")
    st.stop()

# 2. Dataset con Estaciones y Postas Policiales en Honduras
UNIDADES_POLICIALES_HN = [
    {"nombre": "Posta Policial Jesús de Otoro", "tipo": "Posta", "latitud": 14.1232, "longitud": -87.9786},
    {"nombre": "Posta Policial Siguatepeque DPI", "tipo": "Posta", "latitud": 14.5912, "longitud": -87.8341},
    {"nombre": "Estación Policial La Esperanza", "tipo": "Estación", "latitud": 14.3061, "longitud": -88.1748},
    {"nombre": "Posta Policial Marcala", "tipo": "Posta", "latitud": 14.1537, "longitud": -88.0376},
    {"nombre": "Jefatura Departamental Comayagua", "tipo": "Estación", "latitud": 14.4536, "longitud": -87.6415},
    {"nombre": "Posta Policial Loarque (Tegucigalpa)", "tipo": "Posta", "latitud": 14.0195, "longitud": -87.2183},
    {"nombre": "Estación UMEP-1 El Manchén", "tipo": "Estación", "latitud": 14.1189, "longitud": -87.1891},
]

st.info("🌐 Solicitando ubicación GPS automática de tu dispositivo...")

# 3. Captura automática por GPS (Sin campos manuales)
loc = get_geolocation()

if not loc or 'coords' not in loc:
    st.warning("⚠️ Otorga permisos de ubicación/GPS a tu navegador para mostrar los resultados.")
    st.stop()

# Coordenadas obtenidas del dispositivo
user_lat = loc['coords']['latitude']
user_lon = loc['coords']['longitude']
origen = (user_lat, user_lon)

st.success(f"📍 GPS Detectado: Lat {round(user_lat, 4)}, Lon {round(user_lon, 4)}")

# 4. Cálculo de distancias con la API de Google Maps
destinos = [(u["latitud"], u["longitud"]) for u in UNIDADES_POLICIALES_HN]

try:
    matrix = gmaps.distance_matrix(origen, destinos, mode="driving")
    
    resultados = []
    for idx, unidad in enumerate(UNIDADES_POLICIALES_HN):
        element = matrix['rows'][0]['elements'][idx]
        if element['status'] == 'OK':
            dist_km = element['distance']['value'] / 1000.0  # Convertir metros a km
            tiempo = element['duration']['text']            # Tiempo estimado en auto
        else:
            dist_km = float('inf')
            tiempo = "Sin datos"
            
        resultados.append({
            "Nombre": unidad["nombre"],
            "Tipo": unidad["tipo"],
            "Distancia Real": f"{round(dist_km, 2)} km",
            "Tiempo en Auto": tiempo,
            "dist_num": dist_km,
            "lat": unidad["latitud"],
            "lon": unidad["longitud"]
        })
    
    # 5. Filtrar las 3 más cercanas
    df_top3 = pd.DataFrame(resultados).sort_values("dist_num").head(3)
    
    st.subheader("Top 3 Unidades / Postas Policiales Más Cercanas")
    st.dataframe(df_top3[["Nombre", "Tipo", "Distancia Real", "Tiempo en Auto"]], use_container_width=True)
    
    # 6. Mostrar el mapa interactivo de Google Maps
    unidad_destino = df_top3.iloc[0]
    dest_lat, dest_lon = unidad_destino["lat"], unidad_destino["lon"]
    
    gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={user_lat},{user_lon}&destination={dest_lat},{dest_lon}&mode=driving"
    
    st.subheader(f"🗺️ Ruta a la unidad más cercana: {unidad_destino['Nombre']}")
    st.components.v1.iframe(gmaps_embed_url, height=450)

except Exception as e:
    st.error(f"Error al conectar con Google Maps: {e}")
