import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# Configuración de página
st.set_page_config(page_title="Policía Cerca HN", page_icon="🚨", layout="centered")
st.title("🚨 Localizador de Policía")

# 1. Cargar API Key desde los Secretos de Streamlit
if "GOOGLE_MAPS_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
else:
    st.error("⚠️ Falta la variable GOOGLE_MAPS_API_KEY en la sección Secrets de Streamlit.")
    st.stop()

st.info("🌐 Detectando tu ubicación por GPS...")

# 2. Captura automática por GPS del dispositivo
loc = get_geolocation()

if not loc or 'coords' not in loc:
    st.warning("⚠️ Permite el acceso a la ubicación/GPS en tu navegador para realizar la búsqueda.")
    st.stop()

user_lat = loc['coords']['latitude']
user_lon = loc['coords']['longitude']
origen = (user_lat, user_lon)

st.success(f"📍 GPS Detectado: Lat {round(user_lat, 4)}, Lon {round(user_lon, 4)}")

# 3. Búsqueda activa en tiempo real mediante Google Places API
try:
    # Busca lugares tipo 'police' o con palabra clave 'policia' en un radio de 50 km
    places_result = gmaps.places_nearby(
        location=origen,
        radius=50000,
        type='police',
        keyword='policia'
    )
    
    resultados_raw = places_result.get('results', [])
    
    if not resultados_raw:
        st.warning("No se encontraron estaciones o postas policiales registradas cerca de tu ubicación.")
        st.stop()
        
    destinos = []
    lista_lugares = []
    
    for place in resultados_raw:
        plat = place['geometry']['location']['lat']
        plon = place['geometry']['location']['lng']
        destinos.append((plat, plon))
        lista_lugares.append({
            "Nombre": place.get('name', 'Policía'),
            "Dirección": place.get('vicinity', 'Sin dirección'),
            "lat": plat,
            "lon": plon
        })

    # 4. Cálculo de distancias reales por carretera (Distance Matrix)
    matrix = gmaps.distance_matrix(origen, destinos, mode="driving")
    
    resultados_finales = []
    for idx, lugar in enumerate(lista_lugares):
        element = matrix['rows'][0]['elements'][idx]
        if element['status'] == 'OK':
            dist_km = element['distance']['value'] / 1000.0  # metros a kilómetros
            tiempo = element['duration']['text']            # tiempo en auto
        else:
            dist_km = float('inf')
            tiempo = "Sin datos"
            
        resultados_finales.append({
            "Dependencia Policial": lugar["Nombre"],
            "Dirección / Referencia": lugar["Dirección"],
            "Distancia Real": f"{round(dist_km, 2)} km",
            "Tiempo en Auto": tiempo,
            "dist_num": dist_km,
            "lat": lugar["lat"],
            "lon": lugar["lon"]
        })
    
    # 5. Filtrar e identificar las 3 más cercanas
    df_top3 = pd.DataFrame(resultados_finales).sort_values("dist_num").head(3)
    
    st.subheader("Top 3 Puntos Policiales Más Cercanos")
    st.dataframe(df_top3[["Dependencia Policial", "Dirección / Referencia", "Distancia Real", "Tiempo en Auto"]], use_container_width=True)
    
    # 6. Mostrar el mapa interactivo de Google Maps hacia el punto #1
    mas_cercana = df_top3.iloc[0]
    dest_lat, dest_lon = mas_cercana["lat"], mas_cercana["lon"]
    
    gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={user_lat},{user_lon}&destination={dest_lat},{dest_lon}&mode=driving"
    
    st.subheader(f"🗺️ Ruta a la opción más cercana: {mas_cercana['Dependencia Policial']}")
    st.components.v1.iframe(gmaps_embed_url, height=450)

except Exception as e:
    st.error(f"Error en la consulta con Google Maps: {e}")
