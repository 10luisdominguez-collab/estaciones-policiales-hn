import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# Configuración de página
st.set_page_config(page_title="Policía Cerca HN", page_icon="🚨", layout="centered")

# --------------------------------------------------------------------------
# Inyección de CSS para forzar la "manito" (cursor: pointer) en la tabla
# --------------------------------------------------------------------------
st.markdown("""
    <style>
    /* Aplica el cursor pointer a todo el área de la tabla e interactivos */
    [data-testid="stDataFrame"], 
    [data-testid="stDataFrame"] canvas,
    [data-testid="stDataFrame"] iframe {
        cursor: pointer !important;
    }
    </style>
""", unsafe_allow_html=True)

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

# 3. Consultar la API y guardar en session_state
if st.button("🔎 Buscar Dependencias Policiales Cercanas") or "top3_data" in st.session_state:
    
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
                        "Tiempo Estimado": tiempo,
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
    st.info("👇 Haz clic directamente sobre el **Nombre de la Dependencia Policial** para actualizar el mapa.")

    # 4. Tabla interactiva configurada para detectar clic directo en celdas
    event = st.dataframe(
        df_top3[["Dependencia Policial", "Dirección", "Distancia", "Tiempo Estimado"]],
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-cell",
        hide_index=True
    )

    # 5. Determinar la fila activa cuando el usuario hace clic directamente en la celda
    sel_id = 0
    if event and event.selection and event.selection.cells:
        celda = event.selection.cells[0]
        # Verificar que el clic haya sido en la columna del Nombre ("Dependencia Policial")
        if celda[1] == 0 or celda[1] == "Dependencia Policial":
            sel_id = celda[0]

    # 6. Renderizar el Mapa según la opción seleccionada
    estacion_elegida = df_top3.iloc[sel_id]
    dest_lat, dest_lon = estacion_elegida["lat"], estacion_elegida["lon"]
    
    gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={origen[0]},{origen[1]}&destination={dest_lat},{dest_lon}&mode=driving"
    
    st.subheader(f"🗺️ Ruta a: {estacion_elegida['Dependencia Policial']}")
    st.components.v1.iframe(gmaps_embed_url, height=450)
