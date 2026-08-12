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
    st.error("⚠️ No se encontró la clave GOOGLE_MAPS_API_KEY en los Secrets de Streamlit.")
    st.stop()

# 2. Captura de GPS del dispositivo
loc = get_geolocation()
lat_user, lon_user = None, None

if loc and 'coords' in loc:
    lat_user = loc['coords']['latitude']
    lon_user = loc['coords']['longitude']
    st.success(f"📍 GPS detectado: Lat {round(lat_user, 4)}, Lon {round(lon_user, 4)}")

# Coordenadas manuales de respaldo
with st.expander("🌐 Ver / Ajustar Coordenadas Manuales"):
    col1, col2 = st.columns(2)
    with col1:
        lat_input = st.number_input("Latitud", value=float(lat_user) if lat_user else 14.1232, format="%.6f")
    with col2:
        lon_input = st.number_input("Longitud", value=float(lon_user) if lon_user else -87.9786, format="%.6f")

origen = (lat_input, lon_input)

# 3. Botón para ejecutar la consulta
if st.button("🔎 Buscar Dependencias Policiales Cercanas") or "top3_data" in st.session_state:
    
    # Guardar la consulta en session_state para evitar recalcular la API si el usuario solo cambia de opción en la tabla
    if "top3_data" not in st.session_state or st.session_state.get("last_origen") != origen:
        with st.spinner("Consultando Google Maps..."):
            try:
                places_result = gmaps.places_nearby(
                    location=origen,
                    rank_by='distance',
                    keyword='policia'
                )
                
                resultados_raw = places_result.get('results', [])
                if not resultados_raw:
                    st.warning("No se encontraron dependencias policiales cercanas.")
                    st.stop()

                destinos = []
                lista_lugares = []
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

                matrix = gmaps.distance_matrix(origen, destinos, mode="driving")
                
                resultados_finales = []
                for idx, lugar in enumerate(lista_lugares):
                    element = matrix['rows'][0]['elements'][idx]
                    dist_km = element['distance']['value'] / 1000.0 if element['status'] == 'OK' else float('inf')
                    tiempo = element['duration']['text'] if element['status'] == 'OK' else "N/D"
                    
                    resultados_finales.append({
                        "Dependencia Policial": lugar["Nombre"],
                        "Dirección": lugar["Dirección"],
                        "Distancia": f"{round(dist_km, 2)} km",
                        "Tiempo": tiempo,
                        "dist_num": dist_km,
                        "lat": lugar["lat"],
                        "lon": lugar["lon"]
                    })
                
                df_top3 = pd.DataFrame(resultados_finales).sort_values("dist_num").head(3).reset_index(drop=True)
                st.session_state["top3_data"] = df_top3
                st.session_state["last_origen"] = origen

            except Exception as e:
                st.error(f"❌ Error al consultar la API: {e}")
                st.stop()

    df_top3 = st.session_state["top3_data"]

    st.subheader("Top 3 Puntos Policiales Más Cercanos")
    
    # 4. Selector interactivo para cambiar el mapa dinámicamente
    opciones = [
        f"{row['Dependencia Policial']} — {row['Distancia']} ({row['Tiempo']})" 
        for _, row in df_top3.iterrows()
    ]
    
    seleccion = st.radio(
        "📌 Selecciona una opción para trazar la ruta en el mapa:",
        options=opciones,
        index=0  # La #1 más cercana por defecto
    )
    
    # Identificar el índice seleccionado
    idx_seleccionado = opciones.index(seleccion)
    estacion_elegida = df_top3.iloc[idx_seleccionado]

    # Mostrar detalles en tabla resumida
    st.dataframe(df_top3[["Dependencia Policial", "Dirección", "Distancia", "Tiempo"]], use_container_width=True)

    # 5. Renderizar el mapa dinámicamente según la selección del usuario
    dest_lat, dest_lon = estacion_elegida["lat"], estacion_elegida["lon"]
    gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={origen[0]},{origen[1]}&destination={dest_lat},{dest_lon}&mode=driving"
    
    st.subheader(f"🗺️ Ruta a: {estacion_elegida['Dependencia Policial']}")
    st.components.v1.iframe(gmaps_embed_url, height=450)
