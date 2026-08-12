import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# --------------------------------------------------------------------------
# Configuración de Página e Inyección CSS de Diseño Avanzado
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Emergencia Policial HN", 
    page_icon="🚨", 
    layout="centered"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    /* Estilo para los contenedores tipo tarjeta */
    .police-card {
        background-color: #ffffff;
        border: 1px solid #e0e6ed;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
    }
    
    .police-card:hover {
        border-color: #0066cc;
        box-shadow: 0 6px 12px -2px rgba(0, 102, 204, 0.15);
    }

    /* Badge de tipo/distancia */
    .badge-dist {
        background-color: #e6f0fa;
        color: #0052cc;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
    }

    .badge-time {
        background-color: #eef9f2;
        color: #107c41;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
    }

    /* Cambiar cursor a la manito interactiva en las tablas */
    [data-testid="stDataFrame"], 
    [data-testid="stDataFrame"] canvas {
        cursor: pointer !important;
    }
    
    /* Botón de llamada rápida o acción */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Encabezado Principal
# --------------------------------------------------------------------------
st.markdown("## 🚨 Asistencia Policial Honduras")
st.caption("Ubica la Estación, Posta o Jefatura Policial más cercana en tiempo real.")

# 1. Cargar API Key desde Secrets
if "GOOGLE_MAPS_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    try:
        gmaps = googlemaps.Client(key=API_KEY)
    except Exception as e:
        st.error(f"Error al inicializar la conexión con Google Maps: {e}")
        st.stop()
else:
    st.error("⚠️ No se encontró la clave GOOGLE_MAPS_API_KEY en la sección Secrets de Streamlit.")
    st.stop()

# 2. Captura de Ubicación GPS
loc = get_geolocation()
lat_user, lon_user = None, None

if loc and 'coords' in loc:
    lat_user = loc['coords']['latitude']
    lon_user = loc['coords']['longitude']
    st.success(f"📍 GPS Activo: Lat {round(lat_user, 4)}, Lon {round(lon_user, 4)}")
else:
    st.info("🌐 Obteniendo coordenadas GPS de tu dispositivo...")

# Opción de ajuste manual en acordeón elegante
with st.expander("⚙️ Ajustar ubicación manualmente (Respaldo)"):
    c1, c2 = st.columns(2)
    with c1:
        lat_input = st.number_input("Latitud", value=float(lat_user) if lat_user else 14.1232, format="%.6f")
    with c2:
        lon_input = st.number_input("Longitud", value=float(lon_user) if lon_user else -87.9786, format="%.6f")

origen = (lat_input, lon_input)

# 3. Lógica de Consulta y Cache en session_state
st.markdown("---")

btn_buscar = st.button("🔎 Buscar Dependencias Más Cercanas", type="primary", use_container_width=True)

if btn_buscar or "top3_data" in st.session_state:
    
    if "top3_data" not in st.session_state or st.session_state.get("last_origen") != origen:
        with st.spinner("Escaneando red de postas y estaciones cercanas..."):
            try:
                places_result = gmaps.places_nearby(
                    location=origen,
                    rank_by='distance',
                    keyword='policia'
                )
                
                resultados_raw = places_result.get('results', [])
                if not resultados_raw:
                    st.warning("No se encontraron dependencias policiales en el radio cercano.")
                    st.stop()

                destinos = []
                lista_lugares = []
                for place in resultados_raw[:10]:
                    plat = place['geometry']['location']['lat']
                    plon = place['geometry']['location']['lng']
                    destinos.append((plat, plon))
                    lista_lugares.append({
                        "Nombre": place.get('name', 'Policía Nacional'),
                        "Dirección": place.get('vicinity', 'Sin dirección especificada'),
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
                st.error(f"❌ Error al consultar Google Maps: {e}")
                st.stop()

    df_top3 = st.session_state["top3_data"]

    # --------------------------------------------------------------------------
    # Tarjetas de Resumen (KPIs)
    # --------------------------------------------------------------------------
    st.markdown("### 🏆 Top 3 Dependencias Detectadas")
    
    # Mostrar la más cercana como tarjeta destacada
    opcion_top1 = df_top3.iloc[0]
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.metric(label="Más Cercana", value=opcion_top1["Distancia"])
    with col_kpi2:
        st.metric(label="Tiempo estimado", value=opcion_top1["Tiempo Estimado"])
    with col_kpi3:
        st.metric(label="Opciones Encontradas", value=f"{len(df_top3)} Puntos")

    st.markdown("---")
    st.info("💡 **Haz clic directamente sobre la fila o celda** de la dependencia que deseas trazar en el mapa.")

    # --------------------------------------------------------------------------
    # Tabla Interactiva Mejorada
    # --------------------------------------------------------------------------
    event = st.dataframe(
        df_top3[["Dependencia Policial", "Dirección", "Distancia", "Tiempo Estimado"]],
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-cell",
        hide_index=True,
        column_config={
            "Dependencia Policial": st.column_config.TextColumn("Dependencia Policial", width="medium"),
            "Dirección": st.column_config.TextColumn("Dirección / Referencia", width="large"),
            "Distancia": st.column_config.TextColumn("Distancia", width="small"),
            "Tiempo Estimado": st.column_config.TextColumn("Tiempo", width="small"),
        }
    )

    # Identificar la fila seleccionada
    sel_id = 0
    if event and event.selection and event.selection.cells:
        celda = event.selection.cells[0]
        sel_id = celda[0]  # Obtiene el índice de la fila seleccionada

    estacion_elegida = df_top3.iloc[sel_id]

    # --------------------------------------------------------------------------
    # Mapa Interactivo Integrado
    # --------------------------------------------------------------------------
    st.markdown(f"### 🗺️ Ruta a: **{estacion_elegida['Dependencia Policial']}**")
    
    dest_lat, dest_lon = estacion_elegida["lat"], estacion_elegida["lon"]
    gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={origen[0]},{origen[1]}&destination={dest_lat},{dest_lon}&mode=driving"
    
    # Contenedor para el iframe con diseño de borde
    st.components.v1.iframe(gmaps_embed_url, height=480)
    
    # --------------------------------------------------------------------------
    # Información de Emergencia Útil en Honduras
    # --------------------------------------------------------------------------
    with st.container():
        st.markdown("""
        > 📞 **Líneas Directas de Emergencia en Honduras:**  
        > • **911:** Sistema Nacional de Emergencias  
        > • **143:** Policía Nacional / Denuncia Ciudadana
        """)
