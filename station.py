import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# Configuración de página
st.set_page_config(page_title="Policía Cerca HN", page_icon="🚨", layout="centered")

# Estilos CSS avanzados (UI moderna + cursor pointer)
st.markdown("""
    <style>
    /* Transición y manito para tablas */
    [data-testid="stDataFrame"], 
    [data-testid="stDataFrame"] canvas,
    [data-testid="stDataFrame"] iframe {
        cursor: pointer !important;
    }
    
    /* Contenedor de mapa con sombra elegante */
    .map-container {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚨 Localizador Policial Honduras")
st.caption("Encuentra la posta o estación más cercana en tiempo real.")

# 1. Cargar API Key
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

# 2. Captura de GPS del dispositivo que abre la app
loc = get_geolocation()
lat_user, lon_user = None, None

if loc and 'coords' in loc:
    lat_user = loc['coords']['latitude']
    lon_user = loc['coords']['longitude']
    st.success(f"📍 **Ubicación GPS detectada:** ({round(lat_user, 4)}, {round(lon_user, 4)})")

# Coordenadas manuales de respaldo
with st.expander("🌐 Ver / Ajustar Coordenadas Manuales"):
    col1, col2 = st.columns(2)
    with col1:
        lat_input = st.number_input("Latitud", value=float(lat_user) if lat_user else 14.1232, format="%.6f")
    with col2:
        lon_input = st.number_input("Longitud", value=float(lon_user) if lon_user else -87.9786, format="%.6f")

origen = (lat_input, lon_input)

# 3. Consultar la API y guardar en session_state
if st.button("🔎 Buscar Dependencias Cercanas", type="primary", use_container_width=True) or "top3_data" in st.session_state:
    
    if "top3_data" not in st.session_state or st.session_state.get("last_origen") != origen:
        with st.spinner("Buscando estaciones y calculando tiempos de traslado..."):
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

                # Matriz para Auto/Moto (driving)
                matrix_car = gmaps.distance_matrix(origen, destinos, mode="driving")
                # Matriz para A pie (walking)
                matrix_walk = gmaps.distance_matrix(origen, destinos, mode="walking")
                
                resultados_finales = []
                for idx, lugar in enumerate(lista_lugares):
                    elem_car = matrix_car['rows'][0]['elements'][idx]
                    elem_walk = matrix_walk['rows'][0]['elements'][idx]
                    
                    dist_km = elem_car['distance']['value'] / 1000.0 if elem_car['status'] == 'OK' else float('inf')
                    t_carro_moto = elem_car['duration']['text'] if elem_car['status'] == 'OK' else "N/D"
                    t_pie = elem_walk['duration']['text'] if elem_walk['status'] == 'OK' else "N/D"
                    
                    resultados_finales.append({
                        "Dependencia Policial": lugar["Nombre"],
                        "Dirección": lugar["Dirección"],
                        "Distancia": f"{round(dist_km, 2)} km",
                        "🚗 / 🏍️ Auto/Moto": t_carro_moto,
                        "🚶 A pie": t_pie,
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

    # --- MÉTRICAS DESTACADAS ---
    top_opcion = df_top3.iloc[0]
    st.markdown("### 🏆 Punto Policial Más Cercano")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Distancia", top_opcion["Distancia"])
    m2.metric("🚗 / 🏍️ Auto / Moto", top_opcion["🚗 / 🏍️ Auto/Moto"])
    m3.metric("🚶 A Pie", top_opcion["🚶 A pie"])

    st.markdown("---")
    st.subheader("Top 3 Dependencias Encontradas")
    st.info("👇 Haz clic directamente sobre la celda del **Nombre** para trazar la ruta.")

    # 4. Tabla interactiva
    event = st.dataframe(
        df_top3[["Dependencia Policial", "Dirección", "Distancia", "🚗 / 🏍️ Auto/Moto", "🚶 A pie"]],
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-cell",
        hide_index=True
    )

    # 5. Obtener la fila seleccionada
    sel_id = 0
    if event and event.selection and event.selection.cells:
        celda = event.selection.cells[0]
        sel_id = celda[0]

    # 6. Renderizar Mapa
    estacion_elegida = df_top3.iloc[sel_id]
    dest_lat, dest_lon = estacion_elegida["lat"], estacion_elegida["lon"]
    
    # Selector de modo de transporte para el mapa embed
    modo_mapa = st.radio("Modo de ruta en el mapa:", ["🚗 Auto / Moto", "🚶 A pie"], horizontal=True)
    g_mode = "driving" if "Auto" in modo_mapa else "walking"

    gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={origen[0]},{origen[1]}&destination={dest_lat},{dest_lon}&mode={g_mode}"
    
    st.subheader(f"🗺️ Ruta a: {estacion_elegida['Dependencia Policial']}")
    st.components.v1.iframe(gmaps_embed_url, height=450)
