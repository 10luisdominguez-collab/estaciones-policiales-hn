import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# Configuración de página
st.set_page_config(page_title="Policía Cerca HN", page_icon="🚨", layout="centered")
st.title("🚨 Localizador de Policía y Postas HN")

# 1. Cargar API Key desde los Secretos de Streamlit
if "GOOGLE_MAPS_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    try:
        gmaps = googlemaps.Client(key=API_KEY)
    except Exception as e:
        st.error(f"Error al inicializar Google Maps: {e}")
        st.stop()
else:
    st.error("⚠️ No se encontró la clave GOOGLE_MAPS_API_KEY en la sección Secrets de Streamlit.")
    st.stop()

st.write("Presiona el botón para detectar tu GPS o ingresa coordenadas manualmente.")

# 2. Captura de GPS con botón de apoyo
loc = get_geolocation()

lat_user, lon_user = None, None

if loc and 'coords' in loc:
    lat_user = loc['coords']['latitude']
    lon_user = loc['coords']['longitude']
    st.success(f"📍 GPS detectado: Lat {round(lat_user, 4)}, Lon {round(lon_user, 4)}")

# Campos de respaldo en caso de que el GPS sea bloqueado por el navegador
with st.expander("🌐 Ver / Ajustar Coordenadas Manuales"):
    col1, col2 = st.columns(2)
    with col1:
        lat_input = st.number_input("Latitud", value=float(lat_user) if lat_user else 14.1232, format="%.6f")
    with col2:
        lon_input = st.number_input("Longitud", value=float(lon_user) if lon_user else -87.9786, format="%.6f")

# Usar coordenadas manuales si no hay GPS activo
origen = (lat_input, lon_input)

# 3. Botón de Búsqueda
if st.button("🔎 Buscar Dependencias Policiales Cercanas"):
    with st.spinner("Consultando dependencias policiales cercanas en Google Maps..."):
        try:
            # Búsqueda dinámica con Places API
            places_result = gmaps.places_nearby(
                location=origen,
                rank_by='distance',
                keyword='policia'
            )
            
            status = places_result.get('status')
            resultados_raw = places_result.get('results', [])

            if status != 'OK' and status != 'ZERO_RESULTS':
                st.error(f"⚠️ La API de Google devolvió el estado: {status}. Revisa tus restricciones de API Key.")
                st.stop()

            if not resultados_raw:
                st.warning("No se encontraron estaciones o postas policiales registradas cerca de tu ubicación.")
            else:
                destinos = []
                lista_lugares = []
                
                # Tomar únicamente las primeras 10 opciones para no sobrecargar
                for place in resultados_raw[:10]:
                    plat = place['geometry']['location']['lat']
                    plon = place['geometry']['location']['lng']
                    destinos.append((plat, plon))
                    lista_lugares.append({
                        "Nombre": place.get('name', 'Policía'),
                        "Dirección": place.get('vicinity', 'Sin dirección'),
                        "lat": plat,
                        "lon": plon
                    })

                # Calcular distancias reales por carretera (Distance Matrix)
                matrix = gmaps.distance_matrix(origen, destinos, mode="driving")
                
                resultados_finales = []
                for idx, lugar in enumerate(lista_lugares):
                    element = matrix['rows'][0]['elements'][idx]
                    if element['status'] == 'OK':
                        dist_km = element['distance']['value'] / 1000.0
                        tiempo = element['duration']['text']
                    else:
                        dist_km = float('inf')
                        tiempo = "Sin datos"
                        
                    resultados_finales.append({
                        "Dependencia Policial": lugar["Nombre"],
                        "Dirección": lugar["Dirección"],
                        "Distancia Real": f"{round(dist_km, 2)} km",
                        "Tiempo estimado": tiempo,
                        "dist_num": dist_km,
                        "lat": lugar["lat"],
                        "lon": lugar["lon"]
                    })
                
                # Seleccionar las 3 más cercanas por carretera
                df_top3 = pd.DataFrame(resultados_finales).sort_values("dist_num").head(3)
                
                st.subheader("Top 3 Puntos Policiales Más Cercanos")
                st.dataframe(df_top3[["Dependencia Policial", "Dirección", "Distancia Real", "Tiempo estimado"]], use_container_width=True)
                
                # Mapa interactivo con la opción más cercana
                mas_cercana = df_top3.iloc[0]
                dest_lat, dest_lon = mas_cercana["lat"], mas_cercana["lon"]
                
                gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={origen[0]},{origen[1]}&destination={dest_lat},{dest_lon}&mode=driving"
                
                st.subheader(f"🗺️ Ruta a: {mas_cercana['Dependencia Policial']}")
                st.components.v1.iframe(gmaps_embed_url, height=450)

        except Exception as e:
            st.error(f"❌ Error al procesar la solicitud: {e}")
